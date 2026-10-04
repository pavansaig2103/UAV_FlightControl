"""Presentation-only lifecycle clarity and compact operational surfaces."""

import copy
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

from uav_logistics.ui.components.fleet_network import fleet_status, role_tag
from uav_logistics.ui.components.mission_control import hud, mission_phase_timeline, telemetry_snapshot
from uav_logistics.ui.components.reports import mission_lifecycle, mission_outcome, report_document
from uav_logistics.core.data import fresh_fleet
from uav_logistics.core.mission_engine import abort_mission, advance_mission, launch_mission, run_pipeline

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def preflight():
    fleet = fresh_fleet()
    mission = run_pipeline("Critical 2 kg O-negative blood", "HOSP_03", fleet, 18, False)
    next(row for row in fleet if row["id"] == mission["aircraft"]["id"])["status"] = "RESERVED"
    return mission, fleet


def test_preflight_cancel_does_not_invent_launch_or_return(preflight):
    mission, _ = preflight
    abort_mission(mission)
    assert [label for label, _ in mission_lifecycle(mission)] == ["Authorized", "Preflight Cancelled", "Mission Closed"]
    title, detail, color = mission_outcome(mission)
    assert title == "Preflight Cancelled" and color == "red"
    assert "never launched" in detail
    assert "Delivery cancelled" in report_document(mission)
    assert "## Pre-Launch Verification" in report_document(mission)
    assert telemetry_snapshot(mission)["arrival"] == "CANCELLED"
    with patch("uav_logistics.ui.components.mission_control.markup") as render:
        hud(mission)
    assert "CANCELLED" in render.call_args.args[0]


def test_airborne_abort_closes_only_after_return(preflight):
    mission, fleet = preflight
    launch_mission(mission, fleet)
    advance_mission(mission, mission["last_tick"] + 10)
    abort_mission(mission)
    before = copy.deepcopy(mission)
    assert mission_lifecycle(mission)[-1] == ("Aircraft Returning", "current")
    assert "Destination not reached" in mission_outcome(mission)[1]
    assert "Aircraft returning" in report_document(mission)
    assert mission == before
    advance_mission(mission, mission["last_tick"] + 9)
    assert mission_lifecycle(mission)[-1] == ("Mission Closed", "done")
    assert "Standby" in mission_outcome(mission)[1]
    with patch("uav_logistics.ui.components.mission_control.markup") as render:
        mission_phase_timeline(mission)
    markup = render.call_args.args[0]
    assert 'class="interrupted"' in markup
    assert '<div class="done"><span>06</span>DELIVERY' not in markup
    assert '<div class="done"><span>07</span>RETURN' in markup


def test_delivered_report_separates_delivery_from_return(preflight):
    mission, fleet = preflight
    launch_mission(mission, fleet)
    advance_mission(mission, mission["last_tick"] + 30)
    assert mission["status"] == "RETURNING"
    assert mission_lifecycle(mission)[-1] == ("Aircraft Returning", "current")
    assert "Delivery Complete" in mission_outcome(mission)[0]
    advance_mission(mission, mission["last_tick"] + 16)
    assert [label for label, _ in mission_lifecycle(mission)] == ["Authorized", "Launched", "Cruise", "Delivered", "Return / Standby"]
    assert "Delivered / Mission Closed" in report_document(mission)


def test_blocked_report_never_claims_authorization():
    mission = run_pipeline("Critical 2 kg blood", "HOSP_03", fresh_fleet(), 50, False)
    assert mission_lifecycle(mission) == [("Request Received", "done"), ("Launch Blocked", "cancelled")]
    assert mission_outcome(mission)[2] == "amber"


@pytest.mark.parametrize("status,label,color", [("READY", "READY", "green"), ("IDLE", "IDLE", "green"), ("ACTIVE", "ACTIVE", "blue"), ("RECHARGING", "CHARGING", "amber"), ("MAINTENANCE", "MAINTENANCE", "red"), ("RESERVED", "RESERVED", "muted")])
def test_fleet_status_is_presentation_only(status, label, color):
    assert fleet_status(status) == (label, color)


def test_role_tags_reflect_actual_aircraft_capabilities():
    fleet = {row["id"]: row for row in fresh_fleet()}
    assert role_tag(fleet["UAV-N2"]) == "ORGAN"
    assert role_tag(fleet["UAV-W2"]) == "AED"
    assert role_tag(fleet["UAV-W1"]) == "HEAVY"
    assert role_tag(fleet["UAV-S1"]) == "COLD-CHAIN"


def test_execution_trace_is_collapsed_without_losing_agents(monkeypatch):
    monkeypatch.setattr("uav_logistics.ui.state.settings", lambda: {})
    ui = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
    next(button for button in ui.button if button.label == "Execute Optimal Dispatch").click().run()
    assert not ui.exception
    trace = next(expander for expander in ui.expander if expander.label == "Detailed Execution Trace")
    assert trace.proto.expanded is False
    trace_html = " ".join(element.value for element in trace.markdown)
    assert trace_html.count('class="timeline-entry"') == 10
    intelligence = " ".join(element.value for element in ui.tabs[2].markdown)
    assert intelligence.count('class="orchestration-phase"') == 4
    assert 'class="registry-meta"' in " ".join(element.value for element in ui.tabs[1].markdown)


def test_basemap_polish_changes_paint_not_geographic_sources():
    style = json.loads((ROOT / "static/daylight_basemap.json").read_text())
    layers = {layer["id"]: layer for layer in style["layers"]}
    assert layers["water"]["paint"]["fill-color"] == "#c2ddeb"
    assert layers["place_city_r6"]["paint"]["text-color"] == "#52687d"
    assert style["sources"]["carto"]["url"].startswith("https://tiles.basemaps.cartocdn.com/")
