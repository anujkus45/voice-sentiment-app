# Voice Sentiment App

## Deploy to Render

This repo includes `render.yaml`, so Render can auto-configure the service.

### Steps
1. Push the repo to GitHub.
2. In Render, choose **New +** > **Blueprint** and select this repo.
3. Confirm the service name and plan, then deploy.

### Notes
- Build command installs CPU-only PyTorch wheels via `PIP_EXTRA_INDEX_URL` (already in `render.yaml`).
- Python version is pinned via `PYTHON_VERSION` in `render.yaml`.
- App starts with `gunicorn app:app` on `$PORT`.

If you need a manual setup (no Blueprint), create a **Web Service** and use the same build/start commands from `render.yaml`.
