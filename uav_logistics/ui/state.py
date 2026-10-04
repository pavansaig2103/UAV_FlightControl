"""Session-local fleet, mission history and audit events."""
import streamlit as st
from datetime import datetime
from uav_logistics.core.mission_engine import credential, settings
from uav_logistics.core.data import *


def resolve_api_key(value: str, configuration: dict | None = None) -> str:
    config = settings() if configuration is None else configuration
    return credential(value) or credential(config.get("GEMINI_API_KEY", ""))


def preset_changed() -> None:
    selected = st.session_state.preset
    if PRESETS[selected]:
        st.session_state.emergency_notes = PRESETS[selected]



def initialize_state() -> None:
    if st.session_state.get("schema_version") != 2:
        st.session_state.update(fleet=fresh_fleet(), mission=None, history=[], events=[], schema_version=2)
    defaults = {"fleet": fresh_fleet(), "mission": None, "history": [], "events": [], "preset": "O-Negative Blood Units (Trauma)",
                "emergency_notes": PRESETS["O-Negative Blood Units (Trauma)"], "destination_id": "HOSP_03", "wind": 18.0,
                "hazard": False, "wind_direction": "NW", "api_key": "", "dispatch_error": "", "theme": "Light"}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value



def add_event(mission: dict, title: str) -> None:
    st.session_state.events.insert(0, {"time": datetime.now().astimezone().strftime("%H:%M:%S"), "mission": mission["id"], "event": title})
    st.session_state.events = st.session_state.events[:80]

