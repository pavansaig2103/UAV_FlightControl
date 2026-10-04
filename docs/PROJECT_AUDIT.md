# Project Structure Audit

## Published Structure

```text
.
|-- .github/workflows/ci.yml
|-- .streamlit/config.toml
|-- .env.example
|-- .gitattributes
|-- .gitignore
|-- .python-version
|-- render.yaml
|-- start.py
|-- requirements.txt
|-- requirements-dev.txt
|-- README.md
|-- docs/
|   |-- RENDER_DEPLOYMENT.md
|   `-- PROJECT_AUDIT.md
|-- tests/
`-- ui/
    |-- app.py
    |-- data.py
    |-- mission_engine.py
    |-- state.py
    |-- styles.py
    |-- themes.py
    |-- components/
    `-- static/
        |-- daylight_basemap.json
        `-- night_basemap.json
```

## Cleanup and Boundaries

- The old optional FastAPI `backend/` was not imported by the Streamlit application and used an older, smaller city configuration. It has been preserved locally outside this published project, under `../.archive/legacy-backend-20261004/`, rather than deleting historical source code.
- Its existing credentials file was moved to the application's ignored root `.env` before archiving. Credentials were not copied into documentation, templates or version control.
- Generated screenshots were preserved outside the repository under `../.archive/ui-artifacts-20261004/`. Bytecode, test caches and runtime logs are excluded from publication. Current local runtime logs are outside the project under `../.archive/runtime/`.
- The separate older sibling project is unchanged. Render requires only this repository, not the local archive or any sibling directory.

## Deployment Changes

- One Python 3.12 Web Service with a launcher that reads `PORT`, binds to `0.0.0.0`, and starts the official Streamlit module.
- Explicit tested direct dependency versions; timezone data is installed on both Linux and Windows.
- Headless mode, bundled static basemaps, CORS and XSRF protections remain enabled. Streamlit telemetry is disabled.
- Environment credentials now load from the project `.env` or process environment only; process environment wins.
- The server API key is no longer copied into a browser password widget. Browser-entered overrides still work and server-side credential fallback remains available.
- GitHub Actions tests Python 3.12 on Linux; the Render Blueprint waits for successful checks on subsequent automatic deployments.
- Light/Dark themes, network profiles, fleet constraints, dispatch, route geometry, authorization and playback behavior are retained.

## Remaining Limits

This remains a session-local simulator without login, durable records or shared fleet coordination. Gemini is optional and depends on account/model access. A configured API key is not proof of a successful model call. CI and service health do not certify real-world aviation or medical safety. The Render deployment checklist documents these limits and the required dashboard settings.
