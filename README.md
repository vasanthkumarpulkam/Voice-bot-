# AI Call Screener

**An AI receptionist that answers your phone, works out who's calling and why, and decides whether to put them through.**

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Twilio](https://img.shields.io/badge/Twilio-F22F46?logo=twilio&logoColor=white)](https://twilio.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?logo=openai&logoColor=white)](https://openai.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Overview

Job hunting means recruiters call at unpredictable times — mixed in with telemarketers, spam, and the occasional call that actually matters.

This service answers every inbound call, asks the caller who they are and why they're calling, sends that to an LLM for classification, and then either connects the call immediately or takes a message and texts you a summary. Every call is logged and browsable in a dashboard.

Recruiters get through. Promotions don't.

## How it works

```
   Inbound call
        │
        ▼
  Twilio webhook  ──►  POST /voice
        │
        ▼
  <Gather> speech: "Who's calling, and what's it regarding?"
        │
        ▼
  classify.py  ──►  OpenAI
        │           returns strict JSON:
        │             caller_type    recruiter | family | friend | promotion | unknown
        │             priority       high | medium | low
        │             urgency_minutes
        │             action         connect_now | take_message
        ▼
   ┌────────────────┬─────────────────────┐
   │ connect_now    │ take_message        │
   │ forward call   │ record + SMS you    │
   └────────────────┴─────────────────────┘
        │
        ▼
  SQLite call log  ──►  Streamlit dashboard
```

### Classification rules

The system prompt encodes explicit routing policy rather than leaving it to model judgement:

- Recruiters → `high` priority, `connect_now`
- Promotions and telemarketing → `low` priority, `take_message`
- Family emergencies → `high`, `connect_now`; family otherwise → `medium`
- When uncertain, decide conservatively

## Features

- Natural-speech intake via Twilio `<Gather>` — no keypad menus
- LLM classification returning strict, schema-constrained JSON
- Automatic call forwarding for high-priority callers
- Voicemail capture with SMS summary sent to your phone
- Async persistence to SQLite via SQLAlchemy 2.0 + aiosqlite
- Streamlit dashboard over the full call history
- Deploys to any Procfile-based host (Heroku, Railway, Render)

## Tech stack

| Component | Technology |
|---|---|
| Web framework | FastAPI 0.115 + Uvicorn |
| Telephony | Twilio Programmable Voice + SMS |
| Intelligence | OpenAI Chat Completions |
| Database | SQLAlchemy 2.0 (async) + aiosqlite |
| Dashboard | Streamlit |
| Templating | Jinja2 |

## Getting started

### Prerequisites

- Python 3.11+
- A Twilio account with a voice-capable phone number
- An OpenAI API key
- A public HTTPS URL for the webhook (ngrok works for local development)

### Install

```bash
git clone https://github.com/vasanthkumarpulkam/Voice-bot-.git
cd Voice-bot-
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Configure

Create a `.env` file:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=+1...
MY_NUMBER=+1...            # where calls forward and SMS summaries go
DATABASE_URL=sqlite+aiosqlite:///./calls.db
```

### Run

```bash
uvicorn app:app --reload --port 8000
ngrok http 8000
```

Point your Twilio number's **A Call Comes In** webhook at:

```
https://<your-ngrok-domain>/voice     (HTTP POST)
```

### Dashboard

```bash
streamlit run dashboard.py
```

## Project structure

```
Voice-bot-/
├── app.py             FastAPI app — Twilio webhooks and TwiML responses
├── classify.py        OpenAI caller classification
├── db.py              Async SQLAlchemy models and call-log persistence
├── notify.py          Outbound SMS notifications
├── settings.py        Pydantic settings loaded from environment
├── dashboard.py       Streamlit call-log dashboard
├── templates/         Jinja2 templates
├── Procfile           Process definition for PaaS deployment
├── runtime.txt        Python runtime pin
└── requirements.txt
```

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/voice` | Twilio entry point — greets and gathers caller intent |
| `POST` | `/handle` | Processes gathered speech, classifies, routes the call |
| `POST` | `/recording` | Receives voicemail recordings |

## Roadmap

- [ ] Migrate `@app.on_event("startup")` to FastAPI lifespan handlers
- [ ] Move from SQLite to Postgres for deployments with ephemeral filesystems
- [ ] Validate Twilio request signatures on all webhooks
- [ ] Caller allowlist / blocklist
- [ ] Tests for the classification layer with recorded fixtures

## License

MIT — see [LICENSE](LICENSE).

## Author

**Vasanth Kumar Pulkam** — [GitHub](https://github.com/vasanthkumarpulkam)
