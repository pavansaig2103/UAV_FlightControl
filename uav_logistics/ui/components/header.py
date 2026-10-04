"""Global identity and configuration-only sidebar."""
import streamlit as st
from uav_logistics.core.data import *
from uav_logistics.core.mission_engine import credential, settings
from uav_logistics.ui.state import preset_changed, resolve_api_key
from uav_logistics.ui.components.shared import esc, markup, pill
from uav_logistics.ui.themes import THEMES


def sidebar():
    mission = st.session_state.mission
    active = bool(mission and mission["status"] in ACTIVE_STATUSES)
    ready = sum(row["status"] in AVAILABLE_STATUSES for row in st.session_state.fleet)
    with st.sidebar:
        markup('<div class="command-brand"><div class="brand-mark">VJ</div><div><div class="brand-title">Flight Control</div><div class="small">Vijayawada Network</div></div></div>')
        st.segmented_control("Appearance", list(THEMES), key="theme", required=True, width="stretch",
                             format_func=lambda mode: f":material/{'light_mode' if mode == 'Light' else 'dark_mode'}: {mode}")
        markup(f'<div class="sidebar-status"><strong><span class="online-dot"></span>Autonomous Core Online</strong><p>{ready} ready / {len(FLEET_SPEC)} total aircraft</p></div>')
        markup('<div class="control-label">Mission Configuration</div>')
        st.selectbox("Mission preset", list(PRESETS), key="preset", on_change=preset_changed, disabled=active)
        markup('<div class="control-label">AI Intelligence</div>')
        with st.expander("Gemini Mission Intelligence"):
            st.text_input("Gemini API Key", key="api_key", type="password", disabled=active)
            st.caption(settings().get("GEMINI_MODEL", "gemini-2.5-flash"))
        mode = mission["ai_mode"] if mission else "KEY CONFIGURED" if resolve_api_key(st.session_state.api_key) else "LOCAL FALLBACK"
        markup(pill(mode, "green" if mode == "GEMINI AUGMENTED" else "muted"))
        markup('<div class="control-label">Environment</div>')
        wind = float(st.session_state.wind)
        markup(f'<div class="environment-value"><strong>{wind:g}</strong><span> km/h wind</span></div>')
        st.slider("Wind speed", 0.0, 50.0, step=0.5, key="wind", label_visibility="collapsed", disabled=active)
        st.selectbox("Wind direction / from", list(WIND_DIRECTIONS), key="wind_direction", disabled=active)
        st.toggle("Dynamic Airspace Hazard", key="hazard", disabled=active)
        if wind > 45:
            markup(pill("WIND LIMIT EXCEEDED", "red"))
        markup('<div class="control-label">Network</div>')
        markup(f'<div class="telemetry-row"><span>Operational hubs</span><strong>{len(BASES)}</strong></div><div class="telemetry-row"><span>Medical nodes</span><strong>{len(HOSPITALS)}</strong></div><div class="telemetry-row"><span>Aircraft</span><strong>{len(FLEET_SPEC)}</strong></div>')
        markup('<div class="bottom-note">Simulation / session-local operations<br>Wind direction is meteorological FROM.</div>')


def header():
    ready = sum(row["status"] in AVAILABLE_STATUSES and row["battery_pct"] >= 20 for row in st.session_state.fleet)
    markup(f'''<div class="hero"><div><div class="eyebrow">AUTONOMOUS MEDICAL AIR MOBILITY</div><h1>Vijayawada Mission Control</h1><div class="subline">Citywide emergency UAV logistics orchestration</div></div><div class="network-status"><div><label>Network</label><strong><span class="online-dot"></span>Online</strong></div><div><label>Airspace</label><strong>Monitored</strong></div><div><label>AI Core</label><strong>Ready</strong></div><div><label>Fleet</label><strong>{ready} / {len(FLEET_SPEC)} Ready</strong></div></div></div>''')
