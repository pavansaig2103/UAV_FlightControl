"""Launch Streamlit using Render's assigned port."""

import os
from pathlib import Path
import sys
from collections.abc import Mapping


def build_command(environment: Mapping[str, str] | None = None) -> list[str]:
    environment = os.environ if environment is None else environment
    value = environment.get("PORT", "8501")
    try:
        port = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError("PORT must be an integer between 1 and 65535.") from error
    if not 1 <= port <= 65535:
        raise ValueError("PORT must be an integer between 1 and 65535.")
    return [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.address", "0.0.0.0", "--server.port", str(port),
        "--server.headless", "true", "--global.developmentMode", "false",
    ]


def main() -> None:
    try:
        command = build_command()
    except ValueError as error:
        raise SystemExit(str(error)) from error
    os.chdir(Path(__file__).resolve().parent)
    os.execv(sys.executable, command)


if __name__ == "__main__":
    main()
