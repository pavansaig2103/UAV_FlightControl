# Vijayawada UAV Logistics

A Streamlit dashboard for simulating medical deliveries across Vijayawada: plan a dispatch, compare aircraft, follow a flight, and download its report. The demo includes 16 medical destinations, 6 hubs, and 16 aircraft.

## Get it running

Install **Python 3.12** and Git. No separate backend, database, or map API key is needed. Run all commands from the repository root.

### Windows (PowerShell)

```powershell
git clone https://github.com/pavansaig2103/UAV_FlightControl.git
cd UAV_FlightControl
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

### macOS / Linux

```bash
git clone https://github.com/pavansaig2103/UAV_FlightControl.git
cd UAV_FlightControl
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Open **http://localhost:8501**. Stop the app with **Ctrl+C**. If you already have the project, skip cloning and enter its folder. These commands use the virtual environment directly, so activation is optional.

## Optional Gemini configuration

The simulator works without Gemini using local triage. To enable Gemini, copy `.env.example` to `.env` in the project root:

```powershell
Copy-Item .env.example .env
```

On macOS / Linux, use `cp .env.example .env`. Set the values in that file:

```dotenv
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
```

Restart the app after editing. Process environment variables override `.env`. The sidebar key field stays empty even when a server key is configured; it accepts an optional session override. Failed or unavailable Gemini calls fall back to local triage. `.env` is ignored by Git.

## Try a delivery

1. In **Mission Control**, choose a destination and enter a request, such as `Urgent 2 kg O-negative blood`.
2. Select **Execute Optimal Dispatch** to check fleet, payload, weather, and route constraints.
3. Review aircraft choices in **Fleet & Network** and the decision trace in **Autonomous Intelligence**.
4. If authorized, select **Launch Authorized Mission**. Pause, resume, or abort using the flight controls.
5. Watch delivery and return to the origin hub, then download the log from **Flight Reports**.

Flight playback takes roughly 45 seconds; planned operational ETA is shown separately. Each browser session has its own fleet and history. Restarting the server resets records.

## Project layout

```text
UAV_FlightControl/
|-- app.py                       # Streamlit entry point and workspace layout
|-- start.py                     # Hosted launcher; reads PORT
|-- uav_logistics/
|   |-- core/
|   |   |-- data.py              # Hospitals, hubs, fleet, and presets
|   |   `-- mission_engine.py    # Triage, dispatch, routing, flight lifecycle
|   `-- ui/
|       |-- components/          # Workspace views and tactical map
|       |-- state.py             # Browser-session state and event records
|       |-- styles.py            # Shared CSS
|       `-- themes.py            # Light/dark palette and map styles
|-- static/                      # Streamlit-served basemap JSON
|-- tests/                       # Engine, UI, theme, and deployment checks
|-- docs/                        # Detailed behavior and deployment guides
|-- .streamlit/config.toml       # Streamlit settings
|-- .github/workflows/ci.yml     # Python 3.12 test workflow
|-- .env.example                 # Optional configuration template
|-- requirements.txt            # Runtime dependencies
|-- requirements-dev.txt        # Runtime + test dependencies
`-- render.yaml                 # Render service configuration
```

Add simulation logic to `core/`, interface changes to `ui/`, and supporting guides to `docs/`. Static files sit beside `app.py` so Streamlit can serve them at `/app/static/`.

## Run checks

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest tests -q
```

On macOS / Linux, replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`. GitHub Actions runs the tests on Python 3.12 / Linux.

## Deploy on Render

Connect the repository using the included `render.yaml`, or set:

- **Root directory:** leave blank
- **Build command:** `python -m pip install -r requirements.txt`
- **Start command:** `python start.py`
- **Health check:** `/_stcore/health`

The launcher binds to Render's assigned `PORT`. Add an optional Gemini key through Render's environment settings. See [the deployment guide](docs/RENDER_DEPLOYMENT.md) for the full checklist.

## Troubleshooting

| Problem | What to do |
| --- | --- |
| Python 3.12 is missing | Install Python 3.12, then recreate `.venv`. On Windows, `py -0p` lists installed versions. |
| `ModuleNotFoundError` | Install requirements with the same virtual-environment Python used to launch the app. |
| Port 8501 is busy | Add `--server.port 8502` to the Streamlit command, then open `http://localhost:8502`. |
| Map background is blank | Allow internet access to CARTO tiles; no map token is needed. |
| Gemini uses local fallback | Check the key, model access, quota, and server logs. Local dispatch remains available. |
| History disappears | Records live in browser-session memory. Download reports before restarting. |

For scoring, constraints, themes, and model limitations, read [the simulation guide](docs/SIMULATION_GUIDE.md). For file ownership, read [the structure guide](docs/PROJECT_AUDIT.md).

This project is a demonstration simulator. Network capabilities, airspace, energy use, and risk scores are modeled; it is not certified flight or clinical decision software.
