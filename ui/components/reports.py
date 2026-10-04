"""Mission logbook, verification stamps and clinical documentation."""
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st
from ui.data import BASE_BY_ID
from ui.mission_engine import report_markdown, route_clear
from ui.components.shared import *


def local_time(iso_time):
    return datetime.fromisoformat(iso_time).astimezone(ZoneInfo("Asia/Kolkata")).strftime("%H:%M:%S")


def flight_log_view():
    markup('<div class="workspace-heading"><div class="eyebrow">04 / OPERATIONS LOGBOOK</div><h2>Flight Reports</h2><p>Mission documentation and audit trail</p></div>')
    history = st.session_state.history
    if not history:
        markup('<div class="standby-band"><div><strong>No completed mission selected</strong><p>No mission records in this session.</p></div>' + pill("LOGBOOK READY", "muted") + '</div>')
        return
    missions = {mission["id"]: mission for mission in history}
    selected = st.selectbox("Mission record", list(missions), format_func=lambda id_: f"{id_} / {missions[id_]['destination']['name']}", key="report_mission")
    mission = missions[selected]
    display = presentation_mission(mission)
    report = report_markdown(display)
    drone, triage = mission["aircraft"], mission["triage"]
    markup('<div class="report-masthead"><label>OPERATIONS RECORD / VIJAYAWADA</label><h3>Autonomous Medical Logistics Mission Report</h3></div>')
    markup(f'<div class="mission-line"><span><b>{mission["id"]}</b> / {len(history)} session records</span>' + pill(mission["status"], "green" if mission["status"] == "DELIVERED" else "red" if mission["status"] in {"BLOCKED", "ABORTED"} else "cyan") + '</div>')
    arrived = bool(mission.get("delivered_at"))
    verified_count = sum(mission["safety"]["checks"].values())
    values = [("Mission", mission["destination"]["name"], "Operator override" if mission["operator_override"] else "Autonomous recommendation"),
              ("Payload", f"{triage['item_type']} / {triage['payload_weight_kg']:g} kg", triage["urgency"].title()),
              ("Aircraft", drone["id"] if drone else "Unassigned", BASE_BY_ID[drone["base_id"]].name if drone else "No eligible aircraft"),
              ("Navigation", f"{mission['route']['distance_km']:.2f} km / {mission['eta_minutes']:.1f} min planned", "Obstacle-clear corridor" if route_clear(mission["route"]["path"], mission["route"].get("hazard")) else "Clearance unavailable"),
              ("Risk", f"{mission['risk']['score_pct']:.1f}% / {mission['risk']['classification']}" if mission["risk"] else "Not assessed / no eligible aircraft", "Simulation risk model"),
              ("Safety", f"{verified_count} / {len(mission['safety']['checks'])} rules passed", "Authorized" if mission["safety"]["clearance"] else "Launch blocked"),
              ("Delivery", "Completed / " + local_time(mission["delivered_at"]) if arrived else "Cancelled" if mission["abort_requested"] else "Pending", "Simulated lifecycle"),
              ("Verification", mission["ai_mode"].title(), f"Original recommendation / {mission['original_recommendation'] or 'None'}")]
    markup('<div class="report-summary">' + ''.join(f'<div><label>{label}</label><strong>{esc(value)}</strong><small>{esc(detail)}</small></div>' for label, value, detail in values) + '</div>')
    verified = [("Triage Verified", 1), ("Payload Verified", 2), ("Fleet Verified", 4), ("Route Verified", 5), ("Safety Verified", 8), ("Mission Authorized", 9)]
    markup('<div class="safety-strip">' + ''.join(pill(chr(10003) + " " + label if mission["trace"][index]["state"] == "VERIFIED" else label.replace("Verified", "Not Verified").replace("Authorized", "Not Authorized"), "green" if mission["trace"][index]["state"] == "VERIFIED" else "red") for label, index in verified) + '</div>')
    st.download_button("Download flight log", data=report, file_name=f"{mission['id']}-flight-log.md", mime="text/markdown", icon=":material/download:")
    section("AUDIT", "Mission Timeline", "LOCAL TIME / IST")
    entries = [(mission["trace"][0].get("completed_at", local_time(mission["created_at"])), "Request received", mission["destination"]["name"])]
    entries += [(row.get("completed_at", "--"), row["name"].title(), row["detail"]) for row in display["trace"]]
    entries += [(event["time"], event["event"], "Operator / aircraft lifecycle") for event in reversed(st.session_state.events) if event["mission"] == mission["id"]]
    if arrived:
        entries.append((local_time(mission["delivered_at"]), "Medical delivery complete", "Destination reached / return initiated"))
    if mission.get("completed_at"):
        entries.append((local_time(mission["completed_at"]), "Return confirmed", "Aircraft at origin hub"))
    # ISO-derived milestones and session events share local wall-clock ordering.
    entries.sort(key=lambda entry: entry[0])
    markup('<div class="timeline audit-timeline">' + ''.join(f'<div class="timeline-entry"><time>{esc(stamp)}</time><div><b>{esc(title)}</b><p>{esc(detail)}</p></div></div>' for stamp, title, detail in entries) + '</div>')
    with st.expander("Detailed clinical mission report"):
        st.markdown(report)
