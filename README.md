# Real Translator

Real Translator is a real-time translation product with two fronts:

- a user-facing app for direct usage
- a SaaS API for companies with subscription-oriented access

## Product idea

The project is positioned as a practical translation platform that can evolve from direct consumer usage into B2B integration.

## Current capabilities

- web app for translation flow
- SaaS API with API key access
- usage tracking
- Stripe-ready billing webhook path
- local learning memory for repeated corrections

## Main stack

- Python
- FastAPI
- Gradio or custom local UI entry points
- SQLite
- Stripe integration path

## Run the web app

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main_web.py --host 127.0.0.1 --port 7892
```

Open:

- `http://127.0.0.1:7892`

## Run the SaaS API

```bash
source .venv/bin/activate
uvicorn saas_api.app:app --host 0.0.0.0 --port 8080 --reload
```

Swagger:

- `http://127.0.0.1:8080/docs`

## Important endpoints

- `POST /v1/admin/companies`
- `POST /v1/translate`
- `GET /v1/usage`
- `POST /v1/billing/stripe/webhook`

## Mobile integration story

The backend is already positioned for mobile integration:

- mobile captures audio
- STT converts speech to text
- translated text is requested through the API
- result is displayed in the app

## Next upgrades

1. strengthen the UI and product narrative
2. add speech-to-text pipeline options
3. improve billing and company management
4. expose translation quality and usage analytics
