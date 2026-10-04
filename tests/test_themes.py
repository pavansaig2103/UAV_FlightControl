"""Theme contrast, map fidelity and session-safe appearance switching."""
import copy
import json
import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

from ui.components import tactical_map
from ui.data import fresh_fleet
from ui.mission_engine import run_pipeline
from ui.styles import CSS, theme_css
from ui.themes import BASEMAP_STYLES, THEMES, palette, rgb, theme_name

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def isolate_credentials(monkeypatch):
    monkeypatch.setattr("ui.state.settings", lambda: {})


@pytest.mark.parametrize("value", [None, "invalid", "light"])
def test_unknown_theme_defaults_to_light(value):
    assert theme_name(value) == "Light"
    assert palette(value) is THEMES["Light"]


@pytest.mark.parametrize("mode", THEMES)
def test_theme_css_resolves_every_shared_token(mode):
    assert set(THEMES[mode]) == set(THEMES["Light"])
    referenced = set(re.findall(r"var\(--([\w-]+)\)", CSS)) - {"phase-color"}
    assert referenced <= THEMES[mode].keys()
    generated = theme_css(mode)
    assert "__THEME_TOKENS__" not in generated
    assert f"color-scheme:{mode.lower()}" in generated
    assert f"--surface:{THEMES[mode]['surface']}" in generated


def luminance(color):
    channels = [value / 255 for value in rgb(color)]
    linear = [value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4 for value in channels]
    return sum(value * weight for value, weight in zip(linear, (.2126, .7152, .0722)))


@pytest.mark.parametrize("mode", THEMES)
def test_foreground_and_status_text_contrast(mode):
    tokens = palette(mode)
    pairs = [(role, "surface") for role in ("text", "secondary", "muted", "blue", "teal", "green", "gold", "amber", "red")]
    pairs += [("green", "success-surface"), ("red", "danger-surface"), ("gold", "warning-surface"), ("blue", "blue-surface"), ("teal", "teal-surface")]
    for foreground, background in pairs:
        levels = sorted([luminance(tokens[foreground]), luminance(tokens[background])])
        assert (levels[1] + .05) / (levels[0] + .05) >= 4.5, (mode, foreground, background)


@pytest.mark.parametrize("mode", THEMES)
def test_map_changes_palette_without_changing_mission_or_geography(mode):
    fleet = fresh_fleet()
    mission = run_pipeline("Critical 2 kg O-negative blood", "HOSP_03", fleet, 18, True)
    before = copy.deepcopy(mission)
    specs = {}
    for name in ("Light", mode):
        with patch.object(tactical_map.st, "session_state", SimpleNamespace(fleet=fleet, destination_id="HOSP_03", theme=name)):
            specs[name] = json.loads(tactical_map.build_map(mission).to_json())
    assert specs[mode]["mapStyle"] == BASEMAP_STYLES[mode]
    assert specs[mode]["initialViewState"] == specs["Light"]["initialViewState"]
    current = {layer["id"]: layer for layer in specs[mode]["layers"]}
    original = {layer["id"]: layer for layer in specs["Light"]["layers"]}
    assert current.keys() == original.keys()
    assert current["flight-corridor"]["data"] == original["flight-corridor"]["data"]
    assert current["flight-corridor"]["getColor"] == rgb(palette(mode)["blue"]) + [230]
    assert len(current["hospital-nodes"]["data"]) == 16
    assert mission == before
    style = json.loads((ROOT / "ui" / "static" / Path(BASEMAP_STYLES[mode]).name).read_text(encoding="utf-8"))
    assert style["version"] == 8
    assert all(layer.get("layout", {}).get("text-letter-spacing", 0) == 0 for layer in style["layers"])


def test_appearance_switch_preserves_preflight_request_fleet_and_history():
    ui = AppTest.from_file(str(ROOT / "ui" / "app.py"), default_timeout=20).run()
    assert not ui.exception
    assert ui.session_state["theme"] == "Light"
    request = "Critical handwritten 2 kg O-negative blood request."
    ui.text_area(key="emergency_notes").set_value(request).run()
    next(button for button in ui.button if button.label == "Execute Optimal Dispatch").click().run()
    identity = ui.session_state["mission"]["id"]
    comparison = f"comparison-{identity}-{ui.session_state['mission']['aircraft']['id']}"
    ui.selectbox(key=comparison).select("UAV-W3").run()
    fleet = copy.deepcopy(ui.session_state["fleet"])
    for mode in ("Dark", "Light", "Dark"):
        ui.button_group(key="theme").set_value(mode).run()
        assert not ui.exception
        assert ui.session_state["theme"] == mode
        assert ui.session_state["mission"]["id"] == identity
        assert ui.session_state["mission"]["status"] == "PREFLIGHT"
        assert ui.session_state["mission"]["request"] == request
        assert ui.session_state["fleet"] == fleet
        assert len(ui.session_state["history"]) == 1
        assert ui.selectbox(key=comparison).value == "UAV-W3"


def test_theme_switch_is_available_while_flight_is_paused_and_session_local():
    ui = AppTest.from_file(str(ROOT / "ui" / "app.py"), default_timeout=20).run()
    next(button for button in ui.button if button.label == "Execute Optimal Dispatch").click().run()
    next(button for button in ui.button if button.label == "Launch Authorized Mission").click().run()
    next(button for button in ui.button if button.label == "Pause").click().run()
    before = copy.deepcopy(ui.session_state["mission"])
    ui.button_group(key="theme").set_value("Dark").run()
    assert not ui.exception
    assert ui.session_state["mission"] == before
    other = AppTest.from_file(str(ROOT / "ui" / "app.py"), default_timeout=20).run()
    assert other.session_state["theme"] == "Light"
    assert other.session_state["mission"] is None
