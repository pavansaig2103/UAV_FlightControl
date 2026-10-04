"""Deployment configuration and server-only credential boundaries."""

import os
from pathlib import Path
import sys
import tomllib

import pytest
from streamlit.testing.v1 import AppTest
import yaml

from start import build_command, main
from uav_logistics.core import mission_engine
from uav_logistics.ui.state import resolve_api_key

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("environment,port", [({}, "8501"), ({"PORT": "10000"}, "10000"), ({"PORT": "1"}, "1"), ({"PORT": "65535"}, "65535")])
def test_launcher_binds_render_port(environment, port):
    command = build_command(environment)
    assert command[:5] == [sys.executable, "-m", "streamlit", "run", "app.py"]
    assert command[command.index("--server.address") + 1] == "0.0.0.0"
    assert command[command.index("--server.port") + 1] == port
    assert command[command.index("--server.headless") + 1] == "true"
    assert command[command.index("--global.developmentMode") + 1] == "false"


@pytest.mark.parametrize("value", ["", "abc", "0", "-1", "65536", "3.5"])
def test_launcher_rejects_invalid_ports(value):
    with pytest.raises(ValueError, match="PORT must be an integer"):
        build_command({"PORT": value})


def test_main_uses_project_root_and_executes_streamlit(monkeypatch):
    calls = {}
    monkeypatch.setenv("PORT", "10000")
    monkeypatch.setattr(os, "chdir", lambda path: calls.update(directory=path))
    monkeypatch.setattr(os, "execv", lambda executable, command: calls.update(executable=executable, command=command))
    main()
    assert calls["directory"] == ROOT
    assert calls["executable"] == sys.executable
    assert calls["command"] == build_command({"PORT": "10000"})


def test_blueprint_matches_launcher_and_keeps_keys_out():
    blueprint = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))
    assert len(blueprint["services"]) == 1
    service = blueprint["services"][0]
    assert service["type"] == "web"
    assert service["runtime"] == "python"
    assert service["branch"] == "main"
    assert service["buildCommand"] == "python -m pip install -r requirements.txt"
    assert service["startCommand"] == "python start.py"
    assert service["healthCheckPath"] == "/_stcore/health"
    assert service["autoDeployTrigger"] == "checksPass"
    assert not service.get("rootDir")
    environment = {item["key"]: item["value"] for item in service["envVars"]}
    assert environment["GEMINI_MODEL"] == "gemini-2.5-flash"
    assert "GEMINI_API_KEY" not in environment
    assert "PORT" not in environment
    assert (ROOT / ".python-version").read_text().strip() == "3.12"


def test_streamlit_retains_static_serving_and_security():
    config = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text())
    assert config["server"]["headless"]
    assert config["server"]["enableStaticServing"]
    assert config["server"]["enableCORS"]
    assert config["server"]["enableXsrfProtection"]
    assert not config["browser"]["gatherUsageStats"]


def test_root_environment_loading_and_process_priority(tmp_path, monkeypatch):
    monkeypatch.setattr(mission_engine, "ROOT", tmp_path)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    assert mission_engine.settings() == {}
    (tmp_path / ".env").write_text("GEMINI_API_KEY=file-test-key\nGEMINI_MODEL=file-model\n")
    assert mission_engine.settings()["GEMINI_API_KEY"] == "file-test-key"
    monkeypatch.setenv("GEMINI_API_KEY", "environment-test-key")
    monkeypatch.setenv("GEMINI_MODEL", "environment-model")
    assert mission_engine.settings()["GEMINI_API_KEY"] == "environment-test-key"
    assert mission_engine.settings()["GEMINI_MODEL"] == "environment-model"


def test_server_key_never_prefills_browser_widget(monkeypatch):
    configuration = {"GEMINI_API_KEY": "server-only-dummy-key", "GEMINI_MODEL": "gemini-2.5-flash"}
    monkeypatch.setattr("uav_logistics.ui.state.settings", lambda: configuration)
    monkeypatch.setattr("uav_logistics.ui.components.header.settings", lambda: configuration)
    ui = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
    assert not ui.exception
    assert ui.text_input(key="api_key").value == ""
    assert ui.session_state["api_key"] == ""
    assert all("server-only-dummy-key" not in element.value for element in ui.markdown)
    assert resolve_api_key("") == "server-only-dummy-key"
    ui.text_input(key="api_key").set_value("session-dummy-key").run()
    assert not ui.exception
    assert resolve_api_key(ui.session_state["api_key"]) == "session-dummy-key"
