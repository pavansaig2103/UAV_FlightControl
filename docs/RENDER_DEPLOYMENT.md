# Render Deployment Checklist

Repository: [pavansaig2103/UAV_FlightControl](https://github.com/pavansaig2103/UAV_FlightControl).

Deploy one **Python Web Service**, not a Static Site. This application runs Streamlit directly; it does not need another API service, Node build, database or map token.

## Before Deploying

- Sign in to Render and connect GitHub. Grant Render access to this repository.
- Check the `main` branch and the latest **Python Tests** workflow in GitHub Actions. Resolve any failing check before deploying.
- Use `.python-version` from the repository: it selects Python 3.12. Do not accidentally run with Render's default Python version. A dashboard `PYTHON_VERSION` overrides the file and must specify a full version if used. [Render Python versions](https://render.com/docs/python-version).
- Decide whether to enable Gemini. No key is required for the deterministic simulator. A public service using your server key can consume your quota; omit the key for a keyless public demo, or add access controls before sharing a paid AI configuration.
- Never upload `.env`, paste secrets into build/start commands, or put actual keys into `.env.example` or `render.yaml`.

## Option A: Blueprint

1. In Render choose **New > Blueprint** and connect this repository.
2. Select `main` and use the root `render.yaml` file.
3. Review the proposed `uav-flightcontrol` Web Service, Singapore region and Free instance. Apply only when you are ready to create the service.
4. Open the resulting service's **Environment** page to add an optional `GEMINI_API_KEY`. Save and redeploy if enabling AI after creation.

The Blueprint sets the build command, launcher, health path and automatic deployments after CI passes. The API key is intentionally absent. Do not also create Option B's service unless you want a second deployment. [Blueprint configuration](https://render.com/docs/blueprint-spec).

## Option B: Manual Web Service

Choose **New > Web Service**, connect the GitHub repository and enter:

| Render Setting | Value |
| --- | --- |
| Repository | `https://github.com/pavansaig2103/UAV_FlightControl.git` |
| Name | `uav-flightcontrol` or another available name |
| Branch | `main` |
| Root Directory | **Leave blank** |
| Language / Runtime | Python 3 |
| Region | Singapore |
| Build Command | `python -m pip install -r requirements.txt` |
| Start Command | `python start.py` |
| Instance Type | Free for a demonstration; select paid hosting yourself if needed |
| Health Check Path | `/_stcore/health` |
| Auto-Deploy | After CI Checks Pass |

The published project is already at the repository root. Do **not** enter `ui`, `backend` or your local workspace folder as Root Directory. `start.py` binds to `0.0.0.0` and Render's assigned `PORT`; Render normally supplies port 10000. Do not hardcode localhost for a hosted service. [Web Service settings](https://render.com/docs/web-services).

## Environment Values

| Variable | What to Add |
| --- | --- |
| `GEMINI_API_KEY` | Optional: your real Google API key, entered only in Render Environment. Never commit it. |
| `GEMINI_MODEL` | `gemini-2.5-flash` |
| `PYTHONUNBUFFERED` | `1` |
| `PYTHONDONTWRITEBYTECODE` | `1` |
| `PORT` | Nothing: Render sets it automatically. |
| `PYTHON_VERSION` | Nothing: the repository's `.python-version` selects 3.12. |

Do not add a `VITE_*` URL, Mapbox key, backend port or database URL. The password input is only for a session override and does not display your configured server key. Its being empty does not mean your Render key is missing.

## After Deployment

1. Wait for Render to report **Live** and open its assigned HTTPS URL.
2. Visit `https://YOUR-SERVICE.onrender.com/_stcore/health`; expect HTTP 200 and `ok`. This verifies service readiness, not Gemini availability or mission correctness. [Health checks](https://render.com/docs/health-checks).
3. Verify `/app/static/daylight_basemap.json` and `/app/static/night_basemap.json` return JSON. Open Mission Control and check the map, network overlays, all four workspaces and both Light / Dark themes.
4. Execute an emergency blood dispatch. Confirm preflight authorization, candidate ranking and agent results. If a server key is configured, `KEY CONFIGURED` means presence only; `GEMINI AUGMENTED` after dispatch confirms a successful AI response. `LOCAL FALLBACK` means local triage was used.
5. Launch the authorized mission, pause and resume, then wait approximately 45 seconds of running playback for delivery and return. Confirm the aircraft becomes available again and download a report from Flight Reports.
6. Change theme during another mission and verify the mission and aircraft reservation remain intact. A separate browser session should have an independent fleet/history and default Light theme.

## Hosting Limits and Safety

Free hosting is a demonstration tier, not production hosting. Render can spin a free service down after 15 minutes without HTTP or WebSocket traffic; waking it may take about a minute. Its filesystem is ephemeral. This app stores fleet and history in session memory, so restarts and new browser sessions reset simulation records. Download reports you need to retain. [Free service limits](https://render.com/docs/free).

Render supports Streamlit's WebSocket connection. Deployments and restarts can disconnect clients; refresh after a restart and expect a new simulation session. Do not disable CORS or XSRF protection to work around connection failures. [WebSocket hosting](https://render.com/docs/websocket).

There is no application login, rate limiting or durable mission database in this demo. Add authentication and quota controls before exposing a shared server key, and do not submit patient-identifying information to an AI service. This is a logistics simulator, not certified navigation, aviation authorization or clinical decision support. Real operations require a separate safety, security and regulatory review.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Cannot find `ui/app.py` or requirements | Root Directory must be blank; verify `main` contains the published app. |
| No listening port / deploy timeout | Use `python start.py`; remove localhost bindings and manually entered `PORT`. |
| Dependency or Python errors | Use the committed requirements and `.python-version`; remove conflicting `PYTHON_VERSION` overrides, then rebuild. |
| Blank map background | Verify static JSON URLs and browser access to CARTO tiles. No map token is required. |
| AI stays on local fallback | Verify key, quota, model access and server logs. Key presence alone is not proof that `gemini-2.5-flash` is available to your account. |
| Gemini HTTP 404 | Verify that the requested model is available to the key/account. The simulator remains usable; do not publish the key in diagnostic screenshots. |
| Reconnecting or slow first load | Wait for a free-tier cold start; refresh after deployment/restart. Check browser WebSocket errors. |
| Reports/history disappear | Expected session-memory behavior, not durable storage. Download reports before restarting. |
| Pushes do not auto-deploy | Check GitHub integration, main branch, Auto-Deploy setting and successful CI checks. |

Do not share `.env` files or full credentials when requesting help. Repository preparation does not itself create a Render account, service or public deployment.
