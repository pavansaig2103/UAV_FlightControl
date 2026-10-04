"""Small, escaped presentation primitives."""
import html
import copy
import logging
import streamlit as st
from uav_logistics.core.data import COLORS


def friendly_ai_notice(mission: dict) -> str:
    if mission["ai_mode"] == "LOCAL FALLBACK":
        if "unavailable" in mission["ai_notice"].lower():
            return "Gemini service unavailable. Deterministic clinical triage completed successfully."
        return "Deterministic clinical triage completed successfully."
    return mission["ai_notice"]


def presentation_mission(mission: dict) -> dict:
    """Keep technical fallback diagnostics in mission state, not in operator-facing reports."""
    display = copy.deepcopy(mission)
    display["ai_notice"] = friendly_ai_notice(mission)
    if display["ai_mode"] == "LOCAL FALLBACK":
        display["trace"][1]["detail"] = display["ai_notice"]
    return display


def log_fallback(mission: dict) -> None:
    if mission["ai_mode"] == "LOCAL FALLBACK" and "unavailable" in mission["ai_notice"].lower():
        # Log the engine's bounded diagnostic, never exception bodies or credentials.
        logging.getLogger("uav.triage").warning("Mission %s: %s", mission["id"], mission["ai_notice"])

def esc(value) -> str:
    return html.escape(str(value), quote=True)



def markup(value: str, target=None) -> None:
    (target or st).markdown(value, unsafe_allow_html=True)



def pill(label: str, color: str = "cyan") -> str:
    return f'<span class="pill {color}"><span class="status-dot"></span>{esc(label)}</span>'



def section(number: str, title: str, subtitle: str = "") -> None:
    markup(f'<div class="section-heading"><div><span class="section-index">{esc(number)}</span><b>{esc(title)}</b></div><span>{esc(subtitle)}</span></div>')



def detail_grid(values: list[tuple[str, str]]) -> None:
    markup('<div class="detail-grid">' + ''.join(f'<div><label>{esc(label)}</label><strong>{esc(value)}</strong></div>' for label, value in values) + '</div>')

