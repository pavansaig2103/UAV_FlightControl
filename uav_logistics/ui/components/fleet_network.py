"""Fleet comparison and safe operator reassignment."""
import streamlit as st
from uav_logistics.core.mission_engine import *
from uav_logistics.ui.state import add_event
from uav_logistics.ui.components.shared import *
from uav_logistics.ui.components.tactical_map import build_map


def fleet_status(status):
    return {
        "READY": ("READY", "green"), "IDLE": ("IDLE", "green"),
        "ACTIVE": ("ACTIVE", "blue"), "RECHARGING": ("CHARGING", "amber"),
        "MAINTENANCE": ("MAINTENANCE", "red"), "RESERVED": ("RESERVED", "muted"),
    }.get(status, (status, "muted"))


def role_tag(drone):
    role = drone["medical_role"]
    if role == "ORGAN_TRANSPORT":
        return "ORGAN"
    if role == "AED_RESPONSE":
        return "AED"
    if "Heavy" in drone["model"]:
        return "HEAVY"
    if drone["cold_chain"]:
        return "COLD-CHAIN"
    return "EMERGENCY" if role == "EMERGENCY" else "MEDICAL"

def fleet_comparison(mission: dict) -> None:
    left, right = st.columns([1.2, 1], gap="large")
    eligible = [row for row in mission["candidates"] if row["eligible"]]
    with left:
        markup(f'<div class="node-meta candidate-summary">{len(eligible)} ELIGIBLE / {len(mission["candidates"])} SCANNED</div>')
        for rank, row in enumerate(eligible, 1):
            selected = row["id"] == mission["aircraft"]["id"] if mission["aircraft"] else False
            recommended = row["id"] == mission["original_recommendation"]
            label = "RECOMMENDED / SELECTED" if selected and recommended else "OPERATOR SELECTION" if selected else "RECOMMENDED" if recommended else f"RANK {rank:02d}"
            markup(f'<div class="candidate-row {"selected" if selected else ""}"><div><strong>{row["id"]}</strong><span>{esc(row["model"])}</span><small>{esc(BASE_BY_ID[row["base_id"]].name)}</small></div><div><label>ARRIVAL</label><b>{row["eta_minutes"]:.1f} min</b><small>{row["distance_km"]:.2f} km</small></div><div><label>BATTERY / RISK</label><b>{row["battery_pct"]:.0f}% / {row["risk"]["score_pct"]:.1f}%</b><small>{row["max_payload_kg"]:g} kg capacity</small></div><div><label>{label}</label><b class="cyan">{row["match_score"]:.1f}%</b><small>SIMULATION MATCH</small></div></div>')
        rejected = [row for row in mission["candidates"] if not row["eligible"]]
        with st.expander(f"Rejected / unavailable aircraft ({len(rejected)})"):
            for row in rejected:
                markup(f'<div class="rejection-row"><b>{row["id"]}</b><span>{esc("; ".join(row["reasons"]))}</span></div>')
    with right:
        section("ALT", "Alternative Aircraft", "PREFLIGHT COMPARISON")
        options = {row["id"]: row for row in mission["candidates"]}
        alternatives = [id_ for id_ in options if not mission["aircraft"] or id_ != mission["aircraft"]["id"]]
        if not alternatives:
            markup('<div class="standby">No alternative aircraft in the current solution.</div>')
            return
        selected_id = st.selectbox("Compare another fleet unit", alternatives,
                                   format_func=lambda id_: f"{id_} / {options[id_]['model']} / {'ELIGIBLE' if options[id_]['eligible'] else 'REJECTED'}",
                                   key=f"comparison-{mission['id']}-{mission['aircraft']['id'] if mission['aircraft'] else 'blocked'}")
        alternative = options[selected_id]
        current = mission["aircraft"]
        units = [("Operator selection" if mission["operator_override"] else "Autonomous selection", current), ("Alternative", alternative)]
        markup('<div class="aircraft-comparison">' + ''.join(
            f'<div><label>{label}</label><strong>{row["id"]}</strong><dl><dt>Arrival</dt><dd>{row["eta_minutes"]:.1f} min</dd><dt>Risk</dt><dd>{row["risk"]["score_pct"]:.1f}%</dd><dt>Battery</dt><dd>{row["battery_pct"]:.0f}%</dd><dt>Payload margin</dt><dd>{row["payload_margin_kg"]:.1f} kg</dd></dl></div>'
            for label, row in units if row) + '</div>')
        detail_grid([("GROUND SPEED", f"{alternative['performance']['ground_speed_kmph']:.1f} km/h"),
                     ("ALTERNATIVE ROUTE", f"{alternative['distance_km']:.2f} km")])
        if current:
            markup(f'<div class="comparison-delta"><label>DIFFERENCE / ALTERNATIVE MINUS CURRENT</label>{alternative["eta_minutes"] - mission["eta_minutes"]:+.1f} min arrival<br>{alternative["risk"]["score_pct"] - mission["risk"]["score_pct"]:+.1f} risk points<br>{alternative["payload_margin_kg"] - current["payload_margin_kg"]:+.1f} kg payload margin<br>{alternative["distance_km"] - mission["route"]["distance_km"]:+.2f} km route</div>')
        if not alternative["eligible"]:
            markup('<div class="notice amber">ASSIGNMENT DENIED / ' + esc('; '.join(alternative["reasons"])) + '</div>')
        enabled = mission["status"] == "PREFLIGHT" and alternative["eligible"]
        if st.button("Assign This UAV", icon=":material/swap_horiz:", disabled=not enabled, width="stretch", key="operator-assignment", help="Operator override. Rechecks all mission constraints before changing the reservation."):
            try:
                reassign_mission(mission, st.session_state.fleet, selected_id)
                add_event(mission, f"Operator override / {selected_id}")
                st.rerun()
            except ValueError as error:
                markup(f'<div class="notice red">{esc(error)}</div>')
        control = "OPERATOR OVERRIDE" if mission["operator_override"] else "AUTONOMOUS RECOMMENDATION"
        markup(f'<div class="decision-policy {"override" if mission["operator_override"] else ""}"><label>CONTROL MODE</label><strong>{control}</strong><p>Original recommendation: {mission["original_recommendation"] or "NONE"}<br>Active selection: {current["id"] if current else "UNASSIGNED"}</p></div>')


def fleet_view():
    fleet = st.session_state.fleet
    markup('<div class="workspace-heading"><div class="eyebrow">02 / NETWORK OPERATIONS</div><h2>Fleet & Network</h2><p>Aircraft readiness, sector coverage and mission alternatives</p></div>')
    counts = [("TOTAL UAVs", len(fleet)), ("READY / IDLE", sum(row["status"] in AVAILABLE_STATUSES for row in fleet))]
    counts += [(label, sum(row["status"] == status for row in fleet)) for label, status in
               (("ACTIVE", "ACTIVE"), ("CHARGING", "RECHARGING"), ("MAINTENANCE", "MAINTENANCE"), ("RESERVED", "RESERVED"))]
    markup('<div class="fleet-summary">' + ''.join(f'<div><label>{label}</label><strong>{count:02d}</strong></div>' for label, count in counts) + '</div>')
    coverage, network = st.columns([1.6, 1], gap="large")
    with coverage:
        section("GEO", "Hub Network", "6 OPERATING SECTORS")
        st.pydeck_chart(build_map(None, "Plan"), height=340, width="stretch", key="fleet-network-map")
    with network:
        section("HUB", "Sector Availability", "LIVE READINESS")
        for base in BASES:
            aircraft = [row for row in fleet if row["base_id"] == base.id]
            available = sum(row["status"] in AVAILABLE_STATUSES for row in aircraft)
            markup(f'<div class="telemetry-row"><span>{esc(base.name)}</span><strong>{available} / {len(aircraft)} ready</strong></div>')
        mission = st.session_state.mission
        if st.button("Restore fleet readiness", icon=":material/battery_charging_full:", disabled=bool(mission and mission["status"] in ACTIVE_STATUSES)):
            st.session_state.fleet = fresh_fleet()
            if mission:
                add_event(mission, "Fleet recharged and restored")
            st.rerun()
    section("AIR", "Aircraft Availability", "CONFIGURED FLEET")
    sector = st.selectbox("Operating sector", ["All sectors"] + [base.sector for base in BASES], key="fleet_sector")
    cards = []
    for drone in fleet:
        base = BASE_BY_ID[drone["base_id"]]
        if sector != "All sectors" and base.sector != sector:
            continue
        status, color = fleet_status(drone["status"])
        role = role_tag(drone)
        specs = [("BATTERY", f"{drone['battery_pct']:.0f}%"), ("PAYLOAD", f"{drone['max_payload_kg']:g} kg"),
                 ("CRUISE", f"{drone['nominal_speed_kmph']} km/h"), ("RANGE", f"{drone['range_km']:g} km")]
        cards.append(f'<div class="registry-item" data-status="{esc(drone["status"])}"><div class="mission-line"><strong>{drone["id"]}</strong>{pill(status, color)}</div><div class="role">{esc(drone["model"])}</div><div class="registry-meta"><span class="hub">{esc(base.name)}</span><span class="role-tag">{role}</span></div><div class="specs">' + ''.join(f'<div><label>{label}</label>{value}</div>' for label, value in specs) + '</div></div>')
    markup('<div class="registry-grid">' + ''.join(cards) + '</div>')
    if mission:
        section("CSP", "Current Mission Candidates", mission["id"])
        fleet_comparison(mission)
    else:
        markup('<div class="standby-band"><div><strong>No mission candidates yet</strong><p>Aircraft readiness is shown above.</p></div>' + pill("FLEET READY", "green") + '</div>')

