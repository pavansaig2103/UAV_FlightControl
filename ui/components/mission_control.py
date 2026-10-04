"""Mission setup, authorization and live tactical monitoring only."""
import time
import streamlit as st
from ui.data import *
from ui.mission_engine import *
from ui.state import add_event, resolve_api_key
from ui.components.shared import *
from ui.components.tactical_map import build_map


def telemetry_snapshot(mission):
    """Label planned, outbound, return and final values without mutating a mission."""
    drone = mission["aircraft"]
    returning = mission["status"] == "RETURNING"
    final = mission["status"] in {"DELIVERED", "ABORTED"}
    moving = mission["status"] in {"IN FLIGHT", "RETURNING"}
    performance = drone["return_performance"] if returning or final else mission["performance"]
    fraction = mission["return_progress"] if returning else mission["progress"]
    distance = mission["route"]["distance_km"] * max(0, 1 - fraction)
    if final:
        distance = 0
    arrived = bool(mission.get("delivered_at")) or mission["status"] == "DELIVERED"
    arrival = "ARRIVED" if arrived else "CANCELLED" if mission["abort_requested"] else f"{mission['eta_minutes'] * (1 - mission['progress']):.1f} min"
    heading = f"{performance['bearing']:.0f} deg {performance['cardinal']}"
    return dict(final=final, moving=moving, returning=returning, arrived=arrived,
                label="FINAL" if final else "LIVE" if moving or mission["status"] == "PAUSED" else "PLANNED",
                phase=mission["status"] if final else flight_phase(mission), heading=heading,
                speed=performance["ground_speed_kmph"] if moving else 0,
                remaining_km=distance, arrival=arrival, performance=performance,
                battery=max(0, drone["battery_pct"] - drone["energy_pct"] / 2 * (mission["progress"] + mission["return_progress"])))


def authorization(mission):
    if not mission:
        ready = sum(row["status"] in AVAILABLE_STATUSES for row in st.session_state.fleet)
        markup(f'<div class="authorization standby-auth"><div class="eyebrow">MISSION AUTHORIZATION</div><div class="auth-state">Mission standby</div><p>Awaiting emergency logistics request.</p><div class="auth-grid"><div><label>FLEET AVAILABLE</label><strong>{ready} / 16 aircraft</strong></div><div><label>AIRSPACE</label><strong>Monitored</strong></div><div><label>AUTONOMOUS CORE</label><strong>Ready</strong></div><div><label>MEDICAL NETWORK</label><strong>16 facilities</strong></div></div></div>')
        return
    triage = mission["triage"]
    state = "MISSION AUTHORIZED" if mission["status"] == "PREFLIGHT" else mission["status"]
    color = "red" if state in {"BLOCKED", "ABORTED"} else "green" if state == "DELIVERED" else "cyan"
    values = [("PRIORITY", triage["urgency"]), ("PAYLOAD", f"{triage['item_type']} / {triage['payload_weight_kg']:g} kg"),
              ("CONTROL MODE", "Operator override" if mission["operator_override"] else "Autonomous"), ("AI MODE", mission["ai_mode"])]
    passed = mission["safety"]["clearance"]
    state_color = "green" if passed and state == "MISSION AUTHORIZED" else color
    seal = f'<div class="authorization-seal">&#10003; {sum(mission["safety"]["checks"].values())} / {len(mission["safety"]["checks"])} safety rules verified</div>' if passed else ""
    markup(f'<div class="authorization compact {"pass" if passed else ""}"><div class="mission-line"><div class="eyebrow">MISSION AUTHORIZATION</div><div class="auth-state {state_color}">{state}</div></div><div class="auth-grid">' + ''.join(f'<div><label>{label}</label><strong>{esc(value)}</strong></div>' for label, value in values) + '</div>' + seal + '</div>')


def request_panel():
    mission = st.session_state.mission
    active = bool(mission and mission["status"] in ACTIVE_STATUSES)
    request_col, authorization_col = st.columns([1.65, 1], gap="large")
    with request_col:
        section("01", "Mission Request", "DESTINATION / PAYLOAD")
        # Widgets stay rendered inside the expander so handwritten requests survive reruns.
        with st.expander("Mission request" if not mission else "Edit request", expanded=not bool(mission)):
            node_col, notes_col = st.columns([1, 1.15], gap="medium")
            with node_col:
                st.selectbox("Destination node", list(HOSPITAL_BY_ID), format_func=lambda id_: HOSPITAL_BY_ID[id_].name,
                             key="destination_id", disabled=active)
                destination = HOSPITAL_BY_ID[st.session_state.destination_id]
                markup(f'<div class="node-meta">{destination.id} / {destination.sector}<br><b>{esc(" / ".join(destination.capabilities))}</b></div>')
            with notes_col:
                st.text_area("Clinical emergency request", key="emergency_notes", height=100, disabled=active)
            execute = st.button("Execute Optimal Dispatch", type="primary", icon=":material/route:", width="stretch", disabled=active)
        if mission:
            markup(f'<div class="mission-line"><span>{esc(mission["destination"]["name"])}</span>{pill(mission["triage"]["urgency"], "amber")}</div><div class="node-meta">{esc(mission["triage"]["item_type"])} / {mission["triage"]["payload_weight_kg"]:g} kg</div>')
    with authorization_col:
        authorization(mission)
    if execute:
        st.session_state.dispatch_error = ""
        with st.status("Mission authorization / queued", expanded=False) as progress:
            def observe(trace):
                current = next((row for row in trace if row["state"] == "PROCESSING"), None)
                if current:
                    progress.update(label="Processing / " + current["name"].title())
                    time.sleep(.055)
            try:
                new = run_pipeline(st.session_state.emergency_notes, st.session_state.destination_id,
                                   st.session_state.fleet, float(st.session_state.wind), st.session_state.hazard,
                                   resolve_api_key(st.session_state.api_key), settings().get("GEMINI_MODEL", "gemini-2.5-flash"), observe,
                                   st.session_state.wind_direction)
                new["last_tick"] = time.monotonic()
                st.session_state.mission = new
                st.session_state.history.insert(0, new)
                st.session_state.history = st.session_state.history[:30]
                log_fallback(new)
                if new["status"] == "PREFLIGHT":
                    next(row for row in st.session_state.fleet if row["id"] == new["aircraft"]["id"])["status"] = "RESERVED"
                add_event(new, "Mission authorized / preflight reservation" if new["status"] == "PREFLIGHT" else "Dispatch blocked")
                progress.update(label="Mission authorized" if new["status"] == "PREFLIGHT" else "Dispatch blocked", state="complete" if new["status"] == "PREFLIGHT" else "error")
                st.rerun()
            except ValueError as error:
                st.session_state.dispatch_error = str(error)
                progress.update(label="Request requires attention", state="error")
    if st.session_state.dispatch_error:
        markup(f'<div class="notice red">{esc(st.session_state.dispatch_error)}</div>')


def hud(mission):
    if not mission or not mission["aircraft"]:
        markup('<div class="standby-band"><div><strong>City network / mission standby</strong><p>6 operating hubs / 16 medical facilities / 16 specialized aircraft</p></div>' + pill("DISPATCH BLOCKED" if mission else "OPERATIONS READY", "red" if mission else "green") + '</div>')
        return
    drone, route, perf, risk = (mission[key] for key in ("aircraft", "route", "performance", "risk"))
    arrived = mission["progress"] >= 1 and not mission["abort_requested"]
    values = [("AIRCRAFT", drone["id"], drone["model"], "blue"),
              ("ROUTE", f"{route['distance_km']:.2f} km", BASE_BY_ID[drone["base_id"]].name, ""),
              ("COURSE", f"{perf['bearing']:.0f} deg {perf['cardinal']}", "Planned departure heading", ""),
              ("GROUND SPEED", f"{perf['ground_speed_kmph']:.0f} km/h", "Planned / wind adjusted", ""),
              ("PLANNED ETA", f"{mission['eta_minutes']:.1f} min", "ARRIVED" if arrived else "CANCELLED" if mission["abort_requested"] else "Outbound delivery estimate", ""),
              ("RISK / CLEARANCE", f"{risk['score_pct']:.1f}%", risk["classification"] + " / " + ("PASS" if mission["safety"]["clearance"] else "BLOCKED"), risk["color"])]
    markup('<div class="hud">' + ''.join(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value {color}">{esc(value)}</div><div class="metric-sub">{esc(detail)}</div></div>' for label, value, detail, color in values) + '</div>')


def telemetry_group(title, values):
    markup(f'<div class="telemetry-group"><h4>{esc(title)}</h4>' + ''.join(f'<div class="telemetry-row"><span>{esc(label)}</span><strong>{esc(value)}</strong></div>' for label, value in values) + '</div>')


def active_aircraft_panel(mission):
    if not mission or not mission["aircraft"]:
        section("AIR", "Network Readiness", "STANDBY")
        telemetry_group("OPERATIONS", [("Ready aircraft", str(sum(row["status"] in AVAILABLE_STATUSES for row in st.session_state.fleet))),
                                       ("Airspace", "Monitored"), ("Medical nodes", "16"), ("Operational hubs", "6")])
        telemetry_group("ENVIRONMENT", [("Wind / from", f"{st.session_state.wind:g} km/h {st.session_state.wind_direction}"), ("Dynamic hazard", "Enabled" if st.session_state.hazard else "Off")])
        return
    drone = mission["aircraft"]
    live = telemetry_snapshot(mission)
    perf = live["performance"]
    title = "Mission Aircraft" if live["final"] else "Active Aircraft"
    section("AIR", title, live["label"])
    markup(f'<div class="aircraft-name blue">{drone["id"]}</div><div class="aircraft-role">{esc(drone["model"])}</div>' + pill(live["phase"], "green" if live["final"] and live["arrived"] else "cyan"))
    if live["final"]:
        # Keep the medical delivery location distinct from the aircraft's returned position.
        minutes, seconds = divmod(round(mission["eta_minutes"] * 60), 60)
        telemetry_group("FINAL / RETURN CONFIRMED" if not mission["abort_requested"] else "FINAL / CANCELLED", [
            ("Delivery", "Completed" if live["arrived"] else "Cancelled"),
            ("Delivery node", mission["destination"]["name"] if live["arrived"] else "Not reached"),
            ("Aircraft position", BASE_BY_ID[drone["base_id"]].name),
            ("Aircraft state", "Return / Standby"),
            ("Simulated flight time", f"{minutes}m {seconds:02d}s planned"),
            ("Outbound playback", f"{SIMULATION_SECONDS * .65:.1f} s" if live["arrived"] else "Interrupted"),
            ])
    else:
        speed = f"{live['speed']:.1f} km/h" if live["moving"] else "Paused" if mission["status"] == "PAUSED" else "Awaiting launch"
        eta = mission["route"]["distance_km"] * (1 - mission["return_progress"]) / perf["ground_speed_kmph"] * 60 if live["returning"] else None
        telemetry_group(live["label"] + " / FLIGHT", [("Ground speed", speed), ("Course", live["heading"]),
                            ("Return remaining" if live["returning"] else "Distance remaining", f"{live['remaining_km']:.2f} km"),
                            ("Hub arrival" if live["returning"] else "Delivery arrival", f"{eta:.1f} min" if eta is not None else live["arrival"])])
    telemetry_group("AIRCRAFT", [("Battery", f"{live['battery']:.1f}%"), ("Payload", f"{mission['triage']['payload_weight_kg']:g} / {drone['max_payload_kg']:g} kg"),
                  ("Range reserve", f"{drone['range_km'] - mission['route']['distance_km'] * 2:.1f} km")])
    telemetry_group("ENVIRONMENT / MODELED", [("Wind / from", f"{mission['wind']:g} km/h {mission['wind_direction']}"),
                    ("Airflow effect", f"{perf['wind_effect_kmph']:+.1f} km/h"), ("Crosswind", f"{perf['crosswind_kmph']:.1f} km/h")])


def mission_phase_timeline(mission):
    names = ["PREFLIGHT", "LAUNCH", "CLIMB", "CRUISE", "APPROACH", "DELIVERY", "RETURN"]
    phase = flight_phase(mission)
    index = 6 if phase == "RETURN / STANDBY" else names.index(phase) if phase in names else -1
    final = bool(mission and mission["status"] == "DELIVERED")
    markup('<div class="phase-timeline">' + ''.join(f'<div class="{"done" if pos < index or final else "current" if pos == index else ""}"><span>{pos + 1:02d}</span>{name}</div>' for pos, name in enumerate(names)) + '</div>')


def mission_controls(mission):
    if not mission or mission["status"] not in {"PREFLIGHT", "IN FLIGHT", "PAUSED"}:
        return
    launch_col, abort_col, note = st.columns([1.5, 1, 2], gap="medium")
    with launch_col:
        if mission["status"] == "PREFLIGHT":
            if st.button("Launch Authorized Mission", icon=":material/flight_takeoff:", type="primary", width="stretch"):
                try:
                    launch_mission(mission, st.session_state.fleet)
                    add_event(mission, f"{mission['aircraft']['id']} launch initiated")
                    st.rerun()
                except ValueError as error:
                    markup(f'<div class="notice red">{esc(error)}</div>')
        else:
            paused = mission["status"] == "PAUSED"
            if st.button("Resume" if paused else "Pause", icon=":material/play_arrow:" if paused else ":material/pause:", width="stretch"):
                mission.update(status="IN FLIGHT" if paused else "PAUSED", last_tick=time.monotonic())
                add_event(mission, "Flight resumed" if paused else "Flight paused")
                st.rerun()
    with abort_col:
        if st.button("Abort mission", icon=":material/stop_circle:", width="stretch", key="abort-mission"):
            abort_mission(mission)
            release_aircraft(mission, st.session_state.fleet)
            add_event(mission, "Abort requested / return to hub" if mission["status"] == "RETURNING" else "Preflight cancelled")
            st.rerun()
    with note:
        markup(f'<div class="node-meta">SIMULATION / {SIMULATION_SECONDS:.0f} s round-trip playback<br>Operator assignment available before launch.</div>')


@st.fragment(run_every=1.0)
def live_operations():
    mission = st.session_state.mission
    if mission:
        previous = mission["status"]
        if advance_mission(mission, time.monotonic()):
            release_aircraft(mission, st.session_state.fleet)
            add_event(mission, "Return confirmed / " + mission["status"])
            st.rerun()
        if previous == "IN FLIGHT" and mission["status"] == "RETURNING":
            add_event(mission, "Medical delivery confirmed / return initiated")
            st.rerun()
        markup(f'<div class="mission-line"><span><b>{mission["id"]}</b> / {esc(mission["destination"]["name"])}</span>' + pill(mission["status"], "green" if mission["status"] == "DELIVERED" else "red" if mission["status"] in {"BLOCKED", "ABORTED"} else "cyan") + '</div>')
    hud(mission)
    if mission and mission.get("delivered_at"):
        markup(f'<div class="completion-strip"><strong>DELIVERY VERIFIED / MEDICAL NODE REACHED</strong><span>{esc(mission["destination"]["name"])} / {"Aircraft returned to hub" if mission["status"] == "DELIVERED" else "Return in progress"}</span></div>')
    map_col, support_col = st.columns([2.7, 1], gap="large")
    with map_col:
        title, mode = st.columns([2.8, 1])
        with title:
            markup('<div class="map-bar"><div class="map-title">Tactical Airspace<small>Vijayawada Metropolitan Medical Corridor</small></div><div class="map-legend"><span><i style="background:var(--green)"></i>Hubs</span><span><i style="background:var(--red)"></i>Medical</span><span><i style="background:var(--blue)"></i>Aircraft</span></div></div>')
        with mode:
            view = st.segmented_control("Map view", ["Tactical", "Plan"], default="Tactical", key="map_view", label_visibility="collapsed") or "Tactical"
        navigable = bool(mission and mission["route"]["path"] and mission["safety"]["clearance"])
        airspace = "REROUTED" if navigable and mission["hazard_enabled"] else "CLEAR" if navigable else "BLOCKED" if mission else "MONITORED"
        markup('<div class="map-status">' + pill("AIRSPACE / " + airspace, "green" if navigable else "red" if mission else "muted") + pill("GPS / SIMULATED FIX" if navigable else "GPS / STANDBY", "muted") + pill("NAV / NOMINAL" if navigable else "NAV / STANDBY", "muted") + '</div>')
        st.pydeck_chart(build_map(mission, view), height=610, width="stretch", key="tactical-airspace")
        mission_phase_timeline(mission)
    with support_col:
        active_aircraft_panel(mission)
    mission_controls(mission)
    point = flight_position(mission) if mission else None
    values = [("ROUTE DEVIATION", f"+{mission['route'].get('deviation_pct', 0):.1f}%" if mission and mission["route"]["path"] else "Standby"),
              ("DELIVERY", "ARRIVED" if mission and mission["progress"] >= 1 and not mission["abort_requested"] else f"{mission['progress'] * 100:.0f}%" if mission else "Standby"),
              ("ALTITUDE", f"{point[2]:.0f} m" if point else "Network standby"),
              ("POSITION / WGS84", f"{point[1]:.4f} N / {point[0]:.4f} E" if point else "Vijayawada sector")]
    markup('<div class="telemetry-strip">' + ''.join(f'<div><label>{label}</label><strong>{esc(value)}</strong></div>' for label, value in values) + '</div>')
    if mission:
        markup(f'<div class="mission-progress"><i style="width:{mission["progress"] * 100}%"></i></div>')
        if mission["status"] == "BLOCKED":
            markup('<div class="notice red">MISSION BLOCKED / ' + esc(', '.join(mission["safety"]["violations"])) + '</div>')
