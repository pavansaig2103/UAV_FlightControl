"""Launch the four-workspace application with `streamlit run ui/app.py`."""
from pathlib import Path
import sys
import time

import streamlit as st

st.set_page_config(
    page_title="Vijayawada Mission Control",
    page_icon="\u2708\ufe0f",
    layout="wide",
    initial_sidebar_state="auto",
)

# Direct Streamlit execution places ui/, rather than the project root, on sys.path.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.mission_engine import *
from ui.state import initialize_state, add_event
from ui.styles import inject_css
from ui.components.header import sidebar, header
from ui.components.mission_control import request_panel, live_operations
from ui.components.fleet_network import fleet_view
from ui.components.intelligence import intelligence_panel
from ui.components.reports import flight_log_view
from ui.components.shared import markup


WORKSPACES = ["Mission Control", "Fleet & Network", "Autonomous Intelligence", "Flight Reports"]


def main():
    initialize_state()
    inject_css()
    mission = st.session_state.mission
    if mission and advance_mission(mission, time.monotonic()):
        release_aircraft(mission, st.session_state.fleet)
        add_event(mission, "Return confirmed / " + mission["status"])
    sidebar()
    header()
    control, fleet, intelligence, reports = st.tabs(WORKSPACES)
    # Eager native tabs keep request/comparison widget state alive and flight playback running.
    with control:
        request_panel()
        with st.container(key="live-operations"):
            live_operations()
    with fleet:
        fleet_view()
    with intelligence:
        intelligence_panel()
    with reports:
        flight_log_view()
    markup('<div class="bottom-note">SIMULATION / Approximate added-node coordinates and modeled clinical capabilities. Demonstration airspace, flight times, risk and suitability are not certified dispatch metrics. Playback includes delivery and return to the origin hub.</div>')


if __name__ == "__main__":
    main()
