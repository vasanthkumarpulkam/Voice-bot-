# Voice Call Triage Assistant

FastAPI + Twilio voice bot that answers calls, captures the caller's name and reason, classifies priority using OpenAI, then either connects the call to you or sends the caller to voicemail. All calls are logged in SQLite and viewable in a simple Streamlit dashboard. Includes a local simulation form for testing without Twilio.

## Features
- Intelligent caller classification via OpenAI (configurable rules)
- Twilio Voice IVR using speech Gather
- Auto-connect high priority calls or collect voicemail otherwise
- SMS summary notification for each call (optional)
- SQLite persistence with async SQLAlchemy
- Streamlit dashboard to review calls, priorities, and recordings
- Local simulation form to create call logs without a phone call

## Requirements
- Python 3.11 (see `runtime.txt`)
- Twilio account (number + Voice webhook)
- OpenAI API key

## Quickstart (Local)
1) Create and fill your environment file
```
cp .env.example .env
# Edit .env with your keys and phone numbers
```

2) Install dependencies and run the API
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

3) Open the simulator in your browser
```
http://localhost:8000/
```
Submit the form to create a simulated call log. This exercises the same classification logic without Twilio.

4) Launch the dashboard (optional)
```
streamlit run dashboard.py
```
This reads `calls.db` and shows prioritized calls. As calls arrive, this will populate. If the DB is empty, the dashboard shows a helpful message.

## Twilio Setup
1) Expose your local API with a tunnel such as `ngrok` or `cloudflared`.
   - Example: `ngrok http 8000`
2) In the Twilio Console, set your phone number's Voice webhook to:
   - `POST` to `https://YOUR_PUBLIC_URL/voice`
3) Ensure `.env` has `APP_BASE_URL=https://YOUR_PUBLIC_URL` so TwiML callbacks reference public URLs for redirect, recording, and voicemail callbacks.

## Environment Variables
See `.env.example` for a complete list. Key ones:
- `APP_BASE_URL` — Public base URL for Twilio callbacks
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_NUMBER` — Twilio credentials and your Twilio phone number
- `FORWARD_TO` — The personal phone number to connect high-priority calls to
- `OPENAI_API_KEY`, `OPENAI_MODEL` — Classification model and key (default `gpt-4o-mini`)
- `DATABASE_URL` — Default `sqlite+aiosqlite:///./calls.db`
- `RECRUITER_ALWAYS_CONNECT` — If `true`, recruiter calls are always high/connect_now
- `TIMEZONE` — Display timezone (not yet used in UI)

## API Endpoints
- `POST /voice` — Entry point from Twilio
- `POST /gather_name` — Captures name/company
- `POST /route` — Captures reason, classifies, returns TwiML to connect or record voicemail
- `POST /post_dial` — Post-dial status (marks `connected`)
- `POST /recording_status` — Saves live call recording URL
- `POST /voicemail_complete` — Saves voicemail recording URL
- `GET /` — Simulation form
- `POST /simulate_twilio_call` — Creates a simulated call log locally
- `GET /health` — Health check

## Deployment
This repo includes a `Procfile` and `runtime.txt` suitable for Heroku-like platforms.
- Set required env vars in your hosting platform
- Scale a web dyno/process that runs: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- Point your Twilio webhook at `https://YOUR_DEPLOYED_URL/voice` and set `APP_BASE_URL` accordingly

## Notes
- If OpenAI fails or is not configured, the classifier safely falls back to a conservative default.
- If Twilio SMS creds are not configured, SMS notifications are skipped with a log warning.
- Database file is `calls.db` in project root by default.

