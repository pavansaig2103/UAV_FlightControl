"""Dispatch invariants and real Streamlit interactions, without network calls."""

import copy
import importlib.util
import math
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("mission_control", ROOT / "ui" / "app.py")
app = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = app
SPEC.loader.exec_module(app)


@pytest.fixture(autouse=True)
def isolate_ambient_credentials(monkeypatch):
    # UI tests never pick up a developer's real key from their local environment.
    monkeypatch.setattr("ui.state.settings", lambda: {})


def mission(**overrides):
    options = dict(text="Critical requirement for 2 kg O-Negative blood immediately.", hospital_id="HOSP_03",
                   fleet=app.fresh_fleet(), wind=18.0, hazard=False)
    options.update(overrides)
    return app.run_pipeline(**options)


@pytest.mark.parametrize("text,weight,item", [
    ("Urgent 2.0 kg O negative blood", 2, "O-Negative Blood"),
    ("Emergency 1500 g AED defibrillator", 1.5, "AED Defibrillator"),
    ("Transplant organ weighs 4.5 kilograms", 4.5, "Transplant Organ Container"),
    ("Routine 0.5 kg plasma shipment", 0.5, "Plasma"),
    ("Priority 1 kg blood products", 1, "Blood Products"),
    ("Critical 800 grams vaccine shipment", 0.8, "Temperature-Controlled Medication"),
])
def test_triage_mass_and_item(text, weight, item):
    triage = app.parse_triage(text)
    assert triage.payload_weight_kg == weight
    assert triage.item_type == item
    assert not triage.weight_assumed


@pytest.mark.parametrize("text", ["", "Short", "Emergency -2 kg medicine", "Emergency 0 kg plasma"])
def test_invalid_request(text):
    with pytest.raises(ValueError):
        app.parse_triage(text)


def test_gemini_failure_and_malformed_json_preserve_local_simulator():
    for response in (RuntimeError("unavailable"), Mock(text="not json")):
        fake_client = Mock()
        fake_client.__enter__ = Mock(return_value=fake_client)
        fake_client.__exit__ = Mock(return_value=False)
        if isinstance(response, Exception):
            fake_client.models.generate_content.side_effect = response
        else:
            fake_client.models.generate_content.return_value = response
        with patch.object(app.genai, "Client", return_value=fake_client):
            triage, mode, notice = app.enhance_triage("Emergency 2 kg medicine", "test-key", "test-model")
        assert mode == "LOCAL FALLBACK"
        assert triage.payload_weight_kg == 2
        assert "test-key" not in notice


def test_csp_excludes_busy_underpowered_and_low_battery_aircraft():
    fleet = app.fresh_fleet()
    for drone in fleet:
        if drone["id"] == "UAV-N2":
            drone["battery_pct"] = 19
    selected, candidates = app.choose_aircraft(fleet, app.HOSPITAL_BY_ID["HOSP_03"], 4)
    assert selected and selected["eligible"]
    assert all(not candidate["eligible"] for candidate in candidates if candidate["id"] in {"UAV-N1", "UAV-N2", "UAV-W2"})


def test_suitability_ranking_and_ties_are_deterministic():
    template = next(row for row in app.fresh_fleet() if row["id"] == "UAV-N2")
    fleet = [{**template, "id": id_, "status": "READY"} for id_ in ("TEST-A", "TEST-B")]
    selected, _ = app.choose_aircraft(fleet, app.HOSPITALS[2], 2)
    assert selected["id"] == "TEST-A"
    selected_reversed, _ = app.choose_aircraft(list(reversed(fleet)), app.HOSPITALS[2], 2)
    assert selected_reversed["id"] == selected["id"]
    fleet[1]["battery_pct"] = 100
    selected, _ = app.choose_aircraft(fleet, app.HOSPITALS[2], 2)
    assert selected["id"] == "TEST-B"
    assert math.isclose(sum(selected["score_components"].values()), selected["match_score"], abs_tol=0.005)


@pytest.mark.parametrize("hospital", app.HOSPITALS)
def test_hazard_changes_route_and_risk_without_entering_obstacles(hospital):
    nominal = mission(hospital_id=hospital.id)
    hazard = mission(hospital_id=hospital.id, hazard=True)
    assert nominal["safety"]["clearance"] and hazard["safety"]["clearance"]
    assert 1.03 <= nominal["route"]["distance_km"] / nominal["route"]["direct_distance_km"] <= 1.1
    assert 1.15 <= hazard["route"]["distance_km"] / hazard["route"]["direct_distance_km"] <= 1.3
    assert app.route_clear(hazard["route"]["path"], hazard["route"]["hazard"])
    assert hazard["risk"]["score_pct"] > nominal["risk"]["score_pct"]
    assert len(hazard["route"]["waypoints"]) >= 4
    repeated = mission(hospital_id=hospital.id, hazard=True)
    assert {key: value for key, value in hazard["route"].items() if key != "id"} == {key: value for key, value in repeated["route"].items() if key != "id"}


@pytest.mark.parametrize("wind,cleared", [(45, True), (45.5, False), (50, False)])
def test_wind_clearance_boundary(wind, cleared):
    result = mission(wind=wind)
    assert result["safety"]["clearance"] is cleared
    assert result["status"] == ("PREFLIGHT" if cleared else "BLOCKED")


def test_no_eligible_aircraft_blocks_dispatch_and_does_not_mutate_fleet():
    fleet = app.fresh_fleet()
    before = copy.deepcopy(fleet)
    result = mission(text="Critical request for 20 kg blood", fleet=fleet)
    assert result["status"] == "BLOCKED"
    assert result["aircraft"] is None and result["route"]["path"] == []
    assert fleet == before
    assert app.choose_aircraft([], app.HOSPITALS[0], 2) == (None, [])


def test_playback_pause_completion_and_idempotent_release():
    result = mission()
    fleet = app.fresh_fleet()
    drone = next(drone for drone in fleet if drone["id"] == result["aircraft"]["id"])
    drone["status"] = "RESERVED"
    app.launch_mission(result, fleet)
    start = result["last_tick"]
    app.advance_mission(result, start + 10)
    result["status"] = "PAUSED"
    app.advance_mission(result, start + 1000)
    assert math.isclose(result["progress"], 10 / (app.SIMULATION_SECONDS * 0.65))
    result["status"] = "IN FLIGHT"
    result["last_tick"] = start + 1000
    assert not app.advance_mission(result, start + 1030)
    assert result["status"] == "RETURNING"
    assert app.advance_mission(result, start + 1050)
    assert result["status"] == "DELIVERED"
    assert app.flight_position(result) == result["route"]["path"][0]
    app.release_aircraft(result, fleet)
    battery = drone["battery_pct"]
    app.release_aircraft(result, fleet)
    assert drone["status"] == "READY" and battery < result["aircraft"]["battery_pct"]
    assert battery == drone["battery_pct"]


def test_streamlit_preset_dispatch_pause_resume_abort_and_new_dispatch():
    ui = AppTest.from_file(str(ROOT / "ui" / "app.py"), default_timeout=15)
    ui.session_state["api_key"] = ""
    ui.run()
    assert not ui.exception
    ui.selectbox(key="preset").select("Transplant Organ Container").run()
    assert "4.5 kg" in ui.text_area(key="emergency_notes").value
    next(button for button in ui.button if button.label == "Execute Optimal Dispatch").click().run()
    assert not ui.exception
    assert ui.session_state["mission"]["status"] == "PREFLIGHT"
    next(button for button in ui.button if button.label == "Launch Authorized Mission").click().run()
    assert ui.session_state["mission"]["status"] == "IN FLIGHT"
    next(button for button in ui.button if button.label == "Pause").click().run()
    assert ui.session_state["mission"]["status"] == "PAUSED"
    next(button for button in ui.button if button.label == "Resume").click().run()
    assert ui.session_state["mission"]["status"] == "IN FLIGHT"
    next(button for button in ui.button if button.label == "Abort mission").click().run()
    assert not ui.exception
    assert ui.session_state["mission"]["status"] == "RETURNING"
    ui.session_state["mission"]["last_tick"] -= 10
    ui.run()
    assert ui.session_state["mission"]["status"] == "ABORTED"
    selected_id = ui.session_state["mission"]["aircraft"]["id"]
    assert next(row for row in ui.session_state["fleet"] if row["id"] == selected_id)["status"] == "READY"
    ui.slider(key="wind").set_value(50.0).run()
    next(button for button in ui.button if button.label == "Execute Optimal Dispatch").click().run()
    assert not ui.exception
    assert ui.session_state["mission"]["status"] == "BLOCKED"
    assert len(ui.session_state["history"]) == 2


@pytest.mark.parametrize("bearing,cardinal", [(0, "N"), (44, "NE"), (90, "E"), (135, "SE"), (180, "S"), (225, "SW"), (270, "W"), (315, "NW"), (359, "N")])
def test_bearing_cardinal_boundaries(bearing, cardinal):
    assert app.bearing_to_cardinal(bearing) == cardinal


def test_wind_from_semantics_and_eta():
    drone = app.fresh_fleet()[0]
    headwind = app.calculate_ground_speed(drone, 0, 20, "N")
    tailwind = app.calculate_ground_speed(drone, 0, 20, "S")
    assert headwind["wind_effect_kmph"] < 0 < tailwind["wind_effect_kmph"]
    result = mission()
    assert math.isclose(result["eta_minutes"], result["route"]["distance_km"] / result["performance"]["ground_speed_kmph"] * 60)
    opposite = mission(wind_direction="SE")
    assert result["performance"]["ground_speed_kmph"] != opposite["performance"]["ground_speed_kmph"]


@pytest.mark.parametrize("change,reason", [(dict(range_km=1), "range"), (dict(battery_pct=21), "reserve"), (dict(status="MAINTENANCE"), "Unavailable"), (dict(cold_chain=False), "Temperature")])
def test_extended_hard_constraints(change, reason):
    aircraft = {**next(row for row in app.fresh_fleet() if row["id"] == "UAV-N2"), **change}
    rows = app.rank_fleet_candidates([aircraft], app.HOSPITALS[2], app.parse_triage("Critical 2 kg O-negative blood"), 18, False)
    assert not rows[0]["eligible"]
    assert reason.lower() in "; ".join(rows[0]["reasons"]).lower()


def reserve(result, fleet):
    next(row for row in fleet if row["id"] == result["aircraft"]["id"])["status"] = "RESERVED"


def test_override_updates_all_derived_values_and_preserves_recommendation():
    fleet = app.fresh_fleet()
    result = mission(fleet=fleet)
    reserve(result, fleet)
    original_id = result["aircraft"]["id"]
    original_route = copy.deepcopy(result["route"])
    original_bearing = result["performance"]["bearing"]
    alternative = next(row for row in result["candidates"] if row["eligible"] and row["base_id"] != result["aircraft"]["base_id"])
    app.reassign_mission(result, fleet, alternative["id"])
    assert result["operator_override"] and result["original_recommendation"] == original_id
    assert result["aircraft"]["id"] == alternative["id"]
    assert result["route"]["path"] != original_route["path"]
    assert result["performance"]["bearing"] != original_bearing
    assert result["eta_minutes"] == alternative["eta_minutes"]
    assert result["risk"] == alternative["risk"] and result["safety"]["clearance"]
    assert next(row for row in fleet if row["id"] == original_id)["status"] == "READY"
    assert next(row for row in fleet if row["id"] == alternative["id"])["status"] == "RESERVED"


def test_rejected_override_is_transactional_and_airborne_override_denied():
    fleet = app.fresh_fleet()
    result = mission(fleet=fleet)
    reserve(result, fleet)
    snapshot, fleet_snapshot = copy.deepcopy(result), copy.deepcopy(fleet)
    with pytest.raises(ValueError, match="ASSIGNMENT DENIED"):
        app.reassign_mission(result, fleet, "UAV-E1")
    assert result == snapshot and fleet == fleet_snapshot
    app.launch_mission(result, fleet)
    with pytest.raises(ValueError, match="preflight"):
        app.reassign_mission(result, fleet, "UAV-W1")


def test_launch_revalidates_changed_battery():
    fleet = app.fresh_fleet()
    result = mission(fleet=fleet)
    reserve(result, fleet)
    next(row for row in fleet if row["id"] == result["aircraft"]["id"])["battery_pct"] = 10
    with pytest.raises(ValueError, match="Launch denied"):
        app.launch_mission(result, fleet)
    assert result["status"] == "PREFLIGHT"


def test_network_schema_and_initial_operational_mix():
    assert len(app.get_hospitals()) == 16 and len(app.BASES) == 6 and len(app.fresh_fleet()) == 16
    assert all(set(node) >= {"id", "name", "latitude", "longitude", "category", "capabilities", "priority"} for node in app.get_hospitals())
    assert set(row["status"] for row in app.fresh_fleet()) == {"IDLE", "READY", "ACTIVE", "RESERVED", "RECHARGING", "MAINTENANCE"}


def test_gemini_cannot_remove_explicit_cold_chain_or_downgrade_critical_request():
    fake_client = Mock()
    fake_client.__enter__ = Mock(return_value=fake_client)
    fake_client.__exit__ = Mock(return_value=False)
    fake_client.models.generate_content.return_value = Mock(text='{"payload_weight_kg": 9, "urgency": "LOW", "item_type": "Spare Parts"}')
    with patch.object(app.genai, "Client", return_value=fake_client):
        triage, mode, _ = app.enhance_triage("Critical 2 kg O-negative blood needed", "test-key", "test-model")
    assert mode == "GEMINI AUGMENTED"
    assert triage.payload_weight_kg == 2 and triage.urgency == "CRITICAL"
    assert "COLD-CHAIN" in app.payload_handling(triage)


def test_streamlit_override_persists_through_reruns():
    ui = AppTest.from_file(str(ROOT / "ui" / "app.py"), default_timeout=20)
    ui.session_state["api_key"] = ""
    ui.run()
    next(button for button in ui.button if button.label == "Execute Optimal Dispatch").click().run()
    current = ui.session_state["mission"]
    original = current["aircraft"]["id"]
    alternative = next(row for row in current["candidates"] if row["eligible"] and row["base_id"] != current["aircraft"]["base_id"])
    key = f"comparison-{current['id']}-{original}"
    ui.selectbox(key=key).select(alternative["id"]).run()
    next(button for button in ui.button if button.label == "Assign This UAV").click().run()
    ui.run()
    assert not ui.exception
    assert ui.session_state["mission"]["operator_override"]
    assert ui.session_state["mission"]["aircraft"]["id"] == alternative["id"]
    assert ui.session_state["mission"]["original_recommendation"] == original


def test_four_workspaces_keep_operational_content_separate():
    ui = AppTest.from_file(str(ROOT / "ui" / "app.py"), default_timeout=20)
    ui.session_state["api_key"] = ""
    ui.run()
    assert not ui.exception
    assert [tab.label for tab in ui.tabs] == app.WORKSPACES
    operational = " ".join(element.value for element in ui.tabs[0].markdown)
    assert "Tactical Airspace" in operational
    assert "agent-module" not in operational and "candidate-row" not in operational
    assert "No active reasoning session" in " ".join(element.value for element in ui.tabs[2].markdown)
    assert "No completed mission selected" in " ".join(element.value for element in ui.tabs[3].markdown)


def test_final_telemetry_preserves_planned_eta_and_home_position():
    from ui.components.mission_control import telemetry_snapshot
    fleet = app.fresh_fleet()
    result = mission(fleet=fleet)
    reserve(result, fleet)
    app.launch_mission(result, fleet)
    planned_eta = result["eta_minutes"]
    app.advance_mission(result, result["last_tick"] + 30)
    returning = telemetry_snapshot(result)
    assert returning["returning"] and returning["arrival"] == "ARRIVED"
    assert returning["remaining_km"] > 0
    app.advance_mission(result, result["last_tick"] + 20)
    final = telemetry_snapshot(result)
    assert final["final"] and final["phase"] == "DELIVERED"
    assert final["label"] == "FINAL" and not final["moving"]
    assert final["arrival"] == "ARRIVED" and final["remaining_km"] == 0
    assert result["eta_minutes"] == planned_eta > 0
    assert app.flight_position(result) == result["route"]["path"][0]


def test_paused_and_aborted_telemetry_do_not_claim_live_cruise_or_arrival():
    from ui.components.mission_control import telemetry_snapshot
    result = mission()
    result["status"] = "PAUSED"
    live = telemetry_snapshot(result)
    assert live["speed"] == 0 and not live["moving"]
    result.update(status="ABORTED", abort_requested=True)
    cancelled = telemetry_snapshot(result)
    assert cancelled["arrival"] == "CANCELLED" and not cancelled["arrived"]


def test_subsecond_agent_timings_are_not_rounded_to_zero():
    from ui.components.intelligence import duration_label, pipeline_markup
    assert duration_label(.00003) == "<0.1 ms"
    assert duration_label(.002) == "2.00 ms"
    result = mission()
    visual = pipeline_markup(result["trace"], result)
    assert visual.count('class="orchestration-phase"') == 4
    assert visual.count('class="agent-module') == 10
    assert "0.00 s" not in visual


def test_handwritten_request_and_comparison_survive_workspace_reruns():
    ui = AppTest.from_file(str(ROOT / "ui" / "app.py"), default_timeout=20)
    ui.session_state["api_key"] = ""
    ui.run()
    request = "Critical handwritten request for 2 kg O-negative blood."
    ui.text_area(key="emergency_notes").set_value(request).run()
    next(button for button in ui.button if button.label == "Execute Optimal Dispatch").click().run()
    identity = ui.session_state["mission"]["id"]
    ui.selectbox(key="fleet_sector").select("NORTH").run()
    ui.selectbox(key="report_mission").select(identity).run()
    assert not ui.exception
    assert ui.session_state["mission"]["id"] == identity
    assert ui.session_state["mission"]["request"] == request
    assert ui.text_area(key="emergency_notes").value == request
    intelligence = " ".join(element.value for element in ui.tabs[2].markdown)
    assert "Suitability Breakdown" in intelligence and "Risk Intelligence" in intelligence


def test_return_map_does_not_connect_destination_to_live_aircraft():
    import json
    from types import SimpleNamespace
    from ui.components import tactical_map
    fleet = app.fresh_fleet()
    result = mission(fleet=fleet, hazard=True)
    reserve(result, fleet)
    app.launch_mission(result, fleet)
    app.advance_mission(result, result["last_tick"] + 30)
    app.advance_mission(result, result["last_tick"] + 5)
    with patch.object(tactical_map.st, "session_state", SimpleNamespace(fleet=fleet, destination_id="HOSP_03")):
        layers = {layer["id"]: layer for layer in json.loads(tactical_map.build_map(result).to_json())["layers"]}
    outbound = layers["executed-flight"]["data"][0]["path"]
    inbound = layers["return-flight"]["data"][0]["path"]
    assert outbound[-1] == result["route"]["path"][-1]
    assert inbound[-1] == app.flight_position(result)
    assert outbound[-1] != inbound[-1]
    assert app.route_clear(outbound, result["route"]["hazard"])
    assert app.route_clear(inbound, result["route"]["hazard"])


def test_api_key_priority_and_placeholder_fallback(monkeypatch):
    from ui.state import resolve_api_key
    monkeypatch.setenv("GEMINI_API_KEY", "environment-test-value")
    config = app.settings()
    assert resolve_api_key("operator-test-value", config) == "operator-test-value"
    assert resolve_api_key("", config) == "environment-test-value"
    assert resolve_api_key("YOUR_KEY_HERE", config) == "environment-test-value"
    assert resolve_api_key("", {}) == ""


def test_friendly_fallback_preserves_original_diagnostics_and_clearance():
    from ui.components.shared import presentation_mission
    result = mission()
    result["ai_notice"] = "Gemini unavailable (HTTP 404); local parser completed triage"
    result["trace"][1]["detail"] = result["ai_notice"]
    before = copy.deepcopy(result)
    display = presentation_mission(result)
    assert "HTTP" not in display["ai_notice"]
    assert "completed successfully" in display["ai_notice"]
    assert display["safety"]["clearance"] and display["status"] == "PREFLIGHT"
    assert "HTTP" not in app.report_markdown(display)
    assert result == before


def test_all_workspaces_hide_raw_fallback_errors():
    result = mission()
    result["ai_notice"] = "Gemini unavailable (HTTP 404); local parser completed triage"
    result["trace"][1]["detail"] = result["ai_notice"]
    ui = AppTest.from_file(str(ROOT / "ui" / "app.py"), default_timeout=20)
    ui.session_state["api_key"] = ""
    ui.run()
    reserve(result, ui.session_state["fleet"])
    ui.session_state["mission"] = result
    ui.session_state["history"] = [result]
    ui.run()
    assert not ui.exception
    visible = " ".join(element.value for element in ui.markdown)
    assert "HTTP 404" not in visible
    assert "Gemini service unavailable" in visible
    assert "MISSION AUTHORIZED" in visible
    assert "11 / 11 safety rules verified" in visible


@pytest.mark.parametrize("clinical_request,hospital,wind,hazard,direction", [
    ("Critical 2 kg O-negative blood", "HOSP_03", 0, False, "N"),
    ("Critical 4.5 kg transplant organ", "HOSP_14", 18, True, "NW"),
    ("Critical 1.5 kg AED defibrillator", "HOSP_12", 45, True, "E"),
    ("Emergency 1 kg medication", "HOSP_15", 50, False, "S"),
])
def test_data_quality_across_payload_weather_and_hazard_scenarios(clinical_request, hospital, wind, hazard, direction):
    import json
    result = mission(text=clinical_request, hospital_id=hospital, wind=wind, hazard=hazard, wind_direction=direction)
    json.dumps(result, allow_nan=False)
    assert result["eta_minutes"] >= 0 and result["route"]["distance_km"] >= 0
    assert len(result["candidates"]) == 16
    for candidate in result["candidates"]:
        assert candidate["eta_minutes"] > 0 and candidate["distance_km"] > 0
        if candidate["eligible"]:
            assert candidate["status"] in {"READY", "IDLE"}
            assert candidate["battery_pct"] - candidate["energy_pct"] >= 20
            assert result["triage"]["payload_weight_kg"] <= candidate["max_payload_kg"]
        for lng, lat, altitude in candidate["route"]["path"]:
            assert 80 < lng < 82 and 16 < lat < 17 and altitude >= 0


def test_secret_files_are_ignored_and_environment_examples_are_allowed(tmp_path):
    import shutil
    import subprocess
    if not shutil.which("git"):
        pytest.skip("Git is unavailable for ignore-rule validation")
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    shutil.copyfile(ROOT / ".gitignore", tmp_path / ".gitignore")
    paths = [".env", ".env.local", "backend/.env", ".streamlit/secrets.toml", "ui/.streamlit/secrets.toml"]
    check = subprocess.run(["git", "-C", str(tmp_path), "check-ignore", "--no-index", *paths], capture_output=True, text=True)
    assert check.returncode == 0 and set(check.stdout.splitlines()) == set(paths)
    examples = subprocess.run(["git", "-C", str(tmp_path), "check-ignore", "--no-index", ".env.example", "backend/.env.example"], capture_output=True, text=True)
    assert examples.returncode == 1


@pytest.mark.parametrize("wind", [18, 50])
def test_document_summary_keeps_authorized_and_blocked_missions_readable(wind):
    result = mission(wind=wind)
    ui = AppTest.from_file(str(ROOT / "ui" / "app.py"), default_timeout=20)
    ui.session_state["api_key"] = ""
    ui.run()
    ui.session_state["mission"] = result
    ui.session_state["history"] = [result]
    ui.run()
    assert not ui.exception
    report = " ".join(element.value for element in ui.tabs[3].markdown)
    assert "Autonomous Medical Logistics Mission Report" in report
    assert report.count("<small>") == 8
    assert 'class="timeline audit-timeline"' in report
    assert ("Launch blocked" if wind > 45 else "Authorized") in report


def test_daylight_basemap_uses_a_style_url_and_stable_map_labels():
    import json
    from types import SimpleNamespace
    from ui.components import tactical_map
    with patch.object(tactical_map.st, "session_state", SimpleNamespace(fleet=app.fresh_fleet(), destination_id="HOSP_03")):
        spec = json.loads(tactical_map.build_map(None).to_json())
    assert spec["mapStyle"] == "/app/static/daylight_basemap.json"
    assert spec["mapProvider"] == "carto"
    style = json.loads((ROOT / "ui" / "static" / "daylight_basemap.json").read_text(encoding="utf-8"))
    assert style["sources"]["carto"]["url"].startswith("https://tiles.basemaps.cartocdn.com/")
    assert next(layer for layer in style["layers"] if layer["id"] == "background")["paint"]["background-color"] == "#f7f9fc"
    labels = next(layer for layer in spec["layers"] if layer["id"] == "network-labels")
    assert labels["fontFamily"] == "Arial"
    assert all(set(row["short"]) <= set(labels["characterSet"]) for row in labels["data"])
    assert len(labels["data"]) == 7
    hospitals = next(layer for layer in spec["layers"] if layer["id"] == "hospital-nodes")
    assert len(hospitals["data"]) == 16


def test_route_camera_leaves_room_for_compact_map_viewports():
    import json
    from types import SimpleNamespace
    from ui.components import tactical_map
    result = mission()
    with patch.object(tactical_map.st, "session_state", SimpleNamespace(fleet=app.fresh_fleet(), destination_id="HOSP_03")):
        spec = json.loads(tactical_map.build_map(result).to_json())
    assert spec["initialViewState"]["zoom"] <= 12
    layers = {layer["id"]: layer for layer in spec["layers"]}
    assert len(layers["route-waypoints"]["data"]) == 6
    assert [row["label"] for row in layers["waypoint-labels"]["data"]] == ["LAUNCH", "WP-03", "DESTINATION"]


def test_light_theme_and_live_readout_refresh_styles():
    import tomllib
    from ui.styles import theme_css
    CSS = theme_css("Light")
    theme = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8"))["theme"]
    assert theme["base"] == "light"
    assert theme["textColor"] == "#202632"
    assert "--surface:#ffffff" in CSS
    assert '.st-key-live-operations [data-testid="stElementContainer"][data-stale="true"]:has(' in CSS
    assert 'st.container(key="live-operations")' in (ROOT / "ui" / "app.py").read_text(encoding="utf-8")


@pytest.mark.parametrize("role", ["cyan", "blue", "green", "gold", "amber", "red", "muted"])
def test_light_palette_text_meets_normal_text_contrast(role):
    from ui.data import COLORS
    channels = [int(COLORS[role][offset:offset + 2], 16) / 255 for offset in (1, 3, 5)]
    linear = [value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4 for value in channels]
    luminance = sum(value * weight for value, weight in zip(linear, (.2126, .7152, .0722)))
    assert 1.05 / (luminance + .05) >= 4.5


@pytest.mark.parametrize("status,color", [("PREFLIGHT", "green"), ("ABORTED", "red"), ("BLOCKED", "red")])
def test_authorization_color_distinguishes_clearance_from_cancellation(status, color):
    from ui.components import mission_control
    result = mission()
    result["status"] = status
    if status == "BLOCKED":
        result["safety"]["clearance"] = False
    with patch.object(mission_control, "markup") as render:
        mission_control.authorization(result)
    assert f'class="auth-state {color}"' in render.call_args.args[0]
