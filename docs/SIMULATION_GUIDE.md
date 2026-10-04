# Vijayawada Autonomous Medical Air Mobility

The official Python/Streamlit/PyDeck interface contains four operator workspaces. The city network contains 16 medical destinations, 6 operational hubs and 16 heterogeneous aircraft. `app.py` launches the modular application without an API server.

## Workspaces

- **Mission Control:** request, authorization, six planned KPIs, tactical map and live aircraft telemetry. Request editing collapses after dispatch.
- **Fleet & Network:** readiness, sector coverage, aircraft profiles, full candidate ranking, rejected units and safe preflight reassignment.
- **Autonomous Intelligence:** Understand / Optimize / Navigate / Verify orchestration, ten agent modules, measured engine durations, decision rationale, suitability and risk contributions.
- **Flight Reports:** session records, verification stamps, clinical documentation, delivery/return events and downloadable logs.

Native tabs retain request and comparison controls across navigation. Live flight playback continues while another workspace is open. Planned ETA stays unchanged after delivery; live outbound, return and final readings are explicitly distinguished. The completed aircraft is at its origin hub after return, not still cruising at the receiving hospital.

## Run

Requires Python 3.12. For hosted deployment, follow [the Render checklist](RENDER_DEPLOYMENT.md). The repository includes a `render.yaml` Blueprint, a port-aware launcher and Linux test CI.

From this directory:

```powershell
py -3.12 -m pip install -r requirements.txt
py -3.12 -m streamlit run app.py
```

With Streamlit on your PATH, the equivalent launch is:

```bash
streamlit run app.py
```

Open the URL printed by Streamlit, normally `http://localhost:8501`. CARTO basemap tiles need internet access and no map token. Network objects, route overlays and telemetry remain available if tile services are unavailable.

The bundled daylight basemap style is served from `static/` using Streamlit's static serving configuration. It retains CARTO's geographic sources and attribution with white and cool-gray land surfaces, pale-blue water and high-contrast mission overlays. Map labels use a stable system font and character set, independent of web-font loading.

## Configuration

Copy `.env.example` to `.env` for local configuration, or use environment variables, which take precedence. The password field stays empty: configured server credentials are never prefilled into browser widgets. A user-entered key can override the server key for that browser session. `GEMINI_MODEL` defaults to `gemini-2.5-flash`. Gemini is optional: failed, unavailable or malformed responses use deterministic local triage. A call is bounded to three seconds with no automatic retries. API keys are never included in reports or exception messages shown by the app.

An empty or placeholder session key falls back to configured credentials. Gemini availability does not decide flight clearance: all local payload, fleet, route and safety checks still run. Operator notices and downloaded reports use a concise fallback message; bounded technical diagnostics remain in the server log. `.env` variants and `.streamlit/secrets.toml` are ignored, while `.env.example` templates remain shareable. Never place a real key in a template or commit it.

For a headless production-style startup on a specific port:

```powershell
py -3.12 -m streamlit run app.py --server.address 127.0.0.1 --server.port 8502 --server.headless true --global.developmentMode false
```

All installs include `tzdata` for IST report timestamps. Session state and history are in memory, not durable storage; a server restart or new browser session starts a fresh simulation. Bind to localhost for local use. A shared deployment needs authentication and appropriate network controls. The supplied Render configuration is for a public demonstration, not real flight operations.

Configure wind speed, meteorological wind direction, obstacle interference, destination and request. Wind direction means where the wind comes **from**: wind from NW assists a southeast-bound aircraft and opposes a northwest-bound aircraft. Ground speed uses along-track wind and crosswind correction; ETA is planned distance divided by adjusted ground speed.

## Operator Workflow

1. Execute optimal dispatch to interpret the payload and evaluate the full fleet.
2. Open Autonomous Intelligence for decision rationale, measured agent stages and score components.
3. Open Fleet & Network to compare an alternative aircraft. Eligible alternatives can be assigned during preflight, with every constraint rechecked.
4. Launch the authorized mission. Pause, resume or abort from the live controls.
5. Follow launch, climb, cruise, approach, delivery and return. Delivery and return are accelerated to approximately 45 seconds total, separately from operational ETA.
6. Inspect and download the clinical flight log from Flight Reports. Restore the configured readiness profile from Fleet & Network between scenarios.

An airborne mission cannot be transferred to another aircraft. Abort sends it back along its traveled corridor. The aircraft remains unavailable until return completes. Preflight cancellation releases its reservation immediately. Records and aircraft changes are isolated to each browser session.

## Assignment Model

Hard constraints enforce operational status (`READY` or `IDLE`), payload capacity, minimum battery, round-trip range, modeled energy draw plus 20% reserve, cold-chain handling, aircraft wind tolerance, the 45 km/h network wind ceiling, destination existence and obstacle-clear geometry.

Eligible candidates receive a transparent simulation suitability score: distance 30%, battery 20%, payload headroom 20%, medical role 15%, wind-adjusted speed 10%, and risk 5%. Highest score wins; adjusted ETA and aircraft ID break ties. Operator overrides are labelled explicitly and preserve the original recommendation.

The route engine uses NetworkX A* over a Shapely-checked waypoint visibility graph, including demonstration restricted polygons and a dynamic obstacle buffer. Wind changes corridor geometry and performance. Flights include an altitude profile, navigation samples, waypoint labels, heading, route deviation and return path. This is not full space-time conflict resolution across real air traffic.

## Architecture

```text
Emergency Request
  -> Streamlit Mission Control
  -> AI Triage / Payload Classification
  -> Fleet Hard Constraints / CSP Optimizer
  -> A* Route / Wind Performance Model
  -> Simulation Risk / Safety Verification
  -> Mission Authorization / Optional Operator Override
  -> Launch / Delivery / Return
  -> PyDeck Tactical Visualization / Operational Report
```

The application is a single Streamlit service. The unused older API implementation has been archived outside this repository; no separate backend or frontend service is needed. See [the structure audit](PROJECT_AUDIT.md).

UI ownership is split between `app.py` (launcher), `uav_logistics/core/data.py` (network profiles), `uav_logistics/core/mission_engine.py` (preserved autonomous engine), `uav_logistics/ui/state.py` (session records), `uav_logistics/ui/themes.py` (light/dark tokens), `uav_logistics/ui/styles.py` (layout and styling), and `uav_logistics/ui/components/` (workspaces and tactical map). The UI refactor preserves dispatch, routing, scoring and aircraft lifecycle behavior.

### Appearance

The sidebar's **Appearance** control switches between white/platinum **Light** (default) and charcoal **Dark**. The selection is session-local and remains available during flight. Switching preserves the emergency request, fleet reservation, mission, comparison selection and report history. A new browser session defaults to Light.

Both themes use shared tokens for surfaces, controls, status badges and map overlays. The daylight and night basemap styles are bundled under `static/`; geographic tiles still require access to CARTO's public endpoints. Theme switching changes presentation only, never dispatch constraints, route geometry or safety decisions.

The light theme uses a blue-gray canvas, white operational surfaces and restrained shadows. Fleet cards carry capability tags and differentiated readiness pills. The detailed agent execution trace is collapsed by default. Reports separate pre-launch verification from delivery, abort and return milestones; a preflight cancellation never claims a launch or return. These lifecycle summaries are also included in downloaded logs.

## Tests

```powershell
py -3.12 -m pip install -r requirements-dev.txt
py -3.12 -m pytest tests -q
```

Tests exercise triage and Gemini fallback, hard constraints, scoring, wind vectors, range and battery reserve, deterministic geometry and selection, preflight reservation, transactional reassignment, launch validation, pause, abort, return, workspace isolation, Streamlit widget state, final telemetry semantics and return-path rendering.

Presentation tests also cover credential priority, friendly fallback notices, report summaries for blocked and authorized missions, finite blood/organ/AED mission data, and secret-file ignore rules. The theme changes are isolated from the mission engine.

Deployment tests cover Render port binding, Blueprint settings, secure Streamlit configuration, environment precedence, and keeping server credentials out of browser widgets. GitHub Actions runs the suite on Python 3.12 / Linux before subsequent automatic Render deployments.

## Network Data

The original ten facilities retain their supplied coordinates. The six additional nodes use approximate metropolitan coordinates and modeled capabilities for simulation, not verified receiving-site logistics or clinical capability guarantees. Facility identities and areas were checked against primary sources: [Sentini Hospitals](https://sentinihospitals.com/contact-us.php), [Rainbow Currency Nagar](https://www.rainbowhospitals.in/our-centre/vijayawada/currency-nagar), [Rainbow Governorpet](https://www.rainbowhospitals.in/our-centre/vijayawada/governorpet), [Latha Super Speciality Hospital](https://lathasuperspecialityhospital.com/), [NRI Academy of Sciences](https://nrias.ac.in/contact-us), and [AIIMS Mangalagiri](https://www.aiimsmangalagiri.edu.in/).

Hubs, fleet, airspace volumes, energy assumptions, risk and suitability scores are demonstration models. This is a logistics simulator, not certified aviation navigation, dispatch authorization or clinical medical advice.
