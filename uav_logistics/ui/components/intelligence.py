"""Agent orchestration, measured execution and transparent decision analytics."""
import streamlit as st
from uav_logistics.core.data import *
from uav_logistics.core.mission_engine import new_trace, payload_handling, role_fit
from uav_logistics.ui.components.shared import *


PHASES = [("Understand", [0, 1, 2]), ("Optimize", [3, 4]), ("Navigate", [5, 6]), ("Verify", [7, 8, 9])]
AGENT_NAMES = ["Request Ingestion", "Medical Triage", "Payload Classifier", "Fleet Filter", "CSP Optimizer",
               "Route Planner", "Wind Correction", "Risk Engine", "Safety Verifier", "Mission Authorization"]


def duration_label(seconds):
    if seconds is None:
        return "Not executed"
    if seconds < .0001:
        return "<0.1 ms"
    if seconds < .01:
        return f"{seconds * 1000:.2f} ms"
    return f"{seconds:.2f} s"


def pipeline_markup(trace, mission=None):
    groups = []
    for number, (title, indices) in enumerate(PHASES, 1):
        modules = []
        for index in indices:
            row = trace[index]
            state = row["state"]
            color = "green" if state == "VERIFIED" else "red" if state == "BLOCKED" else "cyan" if state == "PROCESSING" else "muted"
            engine = f'<p>{pill(mission["ai_mode"], "muted")}</p>' if index == 1 and mission else ""
            detail = row["detail"]
            if index == 1 and mission:
                triage = mission["triage"]
                detail = f"{triage['item_type']} / {triage['payload_weight_kg']:g} kg / {triage['urgency']}"
                engine += f'<p>Input / {esc(mission["request"][:90])}{"..." if len(mission["request"]) > 90 else ""}</p>'
                engine += '<div class="agent-output-label">OUTPUT</div>'
            authorized = index == 9 and state == "VERIFIED" and mission and mission["safety"]["clearance"]
            modules.append(f'<div class="agent-module {state.lower()} {"authorized" if authorized else ""}"><strong class="agent-title">{AGENT_NAMES[index]}</strong>{pill(state, color)}{engine}<p>{esc(detail)}</p><div class="execution">Execution / {duration_label(row["seconds"])}</div></div>')
        groups.append(f'<div class="orchestration-phase" data-phase="{title.lower()}"><h3><span class="phase-number">{number:02d}</span>{title}</h3>' + ''.join(modules) + '</div>')
    return '<div class="orchestration">' + ''.join(groups) + '</div>'


def score_bars(drone):
    markup(f'<div class="analytics-score">{drone["match_score"]:.1f}<small> / 100 simulation points</small></div>')
    for label, value in drone["score_components"].items():
        name, maximum_text = label.rsplit(" / ", 1)
        maximum = int(maximum_text)
        markup(f'<div class="bar-row"><span>{esc(name)}</span><div class="bar-track"><i style="width:{min(100, value / maximum * 100):.1f}%"></i></div><b>{value:.1f} / {maximum}</b></div>')


def intelligence_panel():
    mission = st.session_state.mission
    markup('<div class="workspace-heading"><div class="eyebrow">03 / AGENT ORCHESTRATION</div><h2>Autonomous Intelligence</h2><p>Multi-agent mission reasoning and verification</p></div>')
    if not mission:
        markup('<div class="standby-band"><div><strong>No active reasoning session</strong><p>Awaiting a mission decision trace.</p></div>' + pill("CORE READY", "green") + '</div>')
        markup(pipeline_markup(new_trace()))
        return
    trace = presentation_mission(mission)["trace"]
    total = sum(row["seconds"] or 0 for row in trace)
    markup(f'<div class="mission-line"><span><b>{mission["id"]}</b> / {esc(mission["ai_mode"])}</span>{pill("ENGINE TIME / " + duration_label(total), "blue")}</div>')
    markup(pipeline_markup(trace, mission))
    drone = mission["aircraft"]
    if drone:
        why, score, risk_col = st.columns([1.1, 1.05, 1], gap="large")
        with why:
            section("WHY", f"Why {drone['id']}?", "CURRENT SELECTION")
            triage = mission["triage"]
            reasons = [f"Carries the required {triage['payload_weight_kg']:g} kg payload",
                       f"{drone['payload_margin_kg']:.1f} kg payload headroom",
                       f"{drone['battery_pct']:.0f}% dispatch battery",
                       f"{BASE_BY_ID[drone['base_id']].name} / {drone['distance_km']:.2f} km planned route",
                       f"{drone['medical_role'].replace('_', ' ').title()} profile / {payload_handling(triage)}",
                       f"{drone['match_score']:.1f}% mission suitability",
                       "Operator-selected eligible aircraft" if mission["operator_override"] else "Highest ranked eligible aircraft"]
            markup('<ul class="reason-list">' + ''.join(f'<li>{esc(reason)}</li>' for reason in reasons) + '</ul>')
            markup(f'<div class="decision-policy"><label>ORIGINAL RECOMMENDATION</label><strong>{mission["original_recommendation"]}</strong></div>')
            for alternative in [row for row in mission["candidates"] if row["eligible"] and row["id"] != drone["id"]][:2]:
                markup(f'<div class="comparison-delta"><b>{alternative["id"]}</b> / {alternative["eta_minutes"] - mission["eta_minutes"]:+.1f} min / {alternative["risk"]["score_pct"] - mission["risk"]["score_pct"]:+.1f} risk points</div>')
        with score:
            section("CSP", "Suitability Breakdown", "WEIGHTED SCORE")
            score_bars(drone)
        with risk_col:
            risk = mission["risk"]
            section("RISK", "Risk Intelligence", "SIMULATION MODEL")
            markup(f'<div class="analytics-score {risk["color"]}">{risk["score_pct"]:.1f}%</div>' + pill(risk["classification"], risk["color"]))
            markup('<div class="risk-bars">' + ''.join(f'<div class="bar-row {"elevated" if value >= 20 else ""}"><span>{esc(label)}</span><div class="bar-track"><i style="width:{min(100, value / 42 * 100):.1f}%"></i></div><b>+{value:.1f}</b></div>' for label, value in risk["factors"].items()) + '</div>')
    else:
        markup('<div class="notice red">No aircraft met all dispatch constraints. Safety verification suppressed launch.</div>')
    markup('<div class="analytics-band"></div>')
    with st.expander("Detailed Execution Trace", expanded=False):
        section("TRACE", "AI Execution Trace", "WALL CLOCK / ENGINE DURATION")
        entries = []
        for index, row in enumerate(trace):
            entries.append(f'<div class="timeline-entry"><time>{esc(row.get("completed_at", "--"))}</time><div><b>{AGENT_NAMES[index]}</b><p>{esc(row["detail"])}</p></div><span class="execution">{duration_label(row["seconds"])}</span></div>')
        markup('<div class="timeline">' + ''.join(entries) + '</div>')
    markup('<div class="notice muted">' + esc(friendly_ai_notice(mission)) + '</div>')
