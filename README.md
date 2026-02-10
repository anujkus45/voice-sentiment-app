# Voice Sentiment App

This repo contains a Flask-based demo and a Streamlit wrapper for audio emotion classification.

Quickly deploy to Streamlit Cloud

- Ensure `requirements.txt` contains `streamlit` (already included).
- In Streamlit Cloud, create a new app and connect your GitHub repo.
- Set the app entry file to `streamlit_app.py` on branch `main`.
- (Optional) Add the environment variable `HF_API_TOKEN` in the Streamlit app settings if you want to use the Hugging Face Inference API for audio classification.

Notes on secrets

- Streamlit Cloud auto-deploys when connected to a GitHub repo; no token is required for that flow.
- If you later want the GitHub Action to explicitly trigger redeploys via Streamlit's API, create a Streamlit Personal Access Token and store it in the repository Secrets as `STREAMLIT_TOKEN` and the app id as `STREAMLIT_APP_ID`.

CI

- A minimal GitHub Actions workflow is added at `.github/workflows/ci.yml` to run a smoke check on push and PRs to `main`.

Running locally

1. Create and activate a Python virtual environment.
2. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

3. Run the Streamlit app locally:

```bash
streamlit run streamlit_app.py
```
