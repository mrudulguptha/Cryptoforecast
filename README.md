# CryptoForecast Minimal Flask Starter

Minimal Flask application prepared for Render free tier deployment.

## Endpoints
- `/` returns JSON health status.

## Local Run
```bash
python app.py
```

## Render Settings
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`

This repo intentionally keeps dependencies lightweight for reliable free-tier startup.
