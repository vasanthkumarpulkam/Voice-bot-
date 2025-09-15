import os
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, HTMLResponse
from twilio.twiml.voice_response import VoiceResponse, Gather
from settings import settings
from classify import classify
from db import init_db, AsyncSessionLocal, save_call, update_call, get_call
from notify import sms_me
from fastapi.templating import Jinja2Templates
import logging
import uuid


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


templates = Jinja2Templates(directory="templates")


app = FastAPI()


@app.on_event("startup")
async def startup():
    await init_db()


async def _ensure_log(call_sid: str, from_number: str):
    async with AsyncSessionLocal() as s:
        existing = await get_call(s, call_sid)
        if existing:
            return existing
        return await save_call(s, call_sid=call_sid, from_number=from_number)

def _url(path: str) -> str:
    base = settings.app_base_url.rstrip("/") if settings.app_base_url else ""
    if base:
        return f"{base}{path}"
    return path


@app.post("/voice")
async def voice(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid", "")
    from_number = form.get("From", "")
    logger.info(f"Incoming call {call_sid} from {from_number}")
    await _ensure_log(call_sid, from_number)

    vr = VoiceResponse()
    gather = Gather(
        input="speech",
        action=_url(f"/gather_name?sid={call_sid}"),
        method="POST",
        speech_timeout="auto",
        timeout=6,
    )
    gather.say("Hi, you have reached Vasanth's assistant. I'll grab your name and company. What is your name and company?")
    vr.append(gather)
    vr.redirect(_url(f"/voice"))
    return PlainTextResponse(str(vr), media_type="text/xml")


@app.post("/gather_name")
async def gather_name(request: Request):
    form = await request.form()
    call_sid = request.query_params.get("sid", form.get("CallSid", ""))
    name_company = (form.get("SpeechResult") or "").strip()
    logger.info(f"Gathered name/company: {name_company}")

    async with AsyncSessionLocal() as s:
        await update_call(s, call_sid, caller_name=name_company)

    vr = VoiceResponse()
    gather = Gather(
        input="speech",
        action=_url(f"/route?sid={call_sid}"),
        method="POST",
        speech_timeout="auto",
        timeout=8,
    )
    gather.say("Thanks. Briefly, what is this regarding?")
    vr.append(gather)
    vr.redirect(_url(f"/gather_name?sid={call_sid}"))
    return PlainTextResponse(str(vr), media_type="text/xml")


@app.post("/route")
async def route_call(request: Request):
    form = await request.form()
    call_sid = request.query_params.get("sid", form.get("CallSid", ""))
    reason = (form.get("SpeechResult") or "").strip()
    logger.info(f"Reason: {reason}")

    async with AsyncSessionLocal() as s:
        log = await get_call(s, call_sid)
        name_company = (log.caller_name or "") if log else ""

    decision = classify(name_company, reason)

    # Persist decision
    async with AsyncSessionLocal() as s:
        await update_call(
            s,
            call_sid,
            reason=reason,
            caller_type=decision["caller_type"],
            priority=decision["priority"],
            action=decision["action"],
            urgency_minutes=decision.get("urgency_minutes"),
        )

    # SMS summary
    try:
        sms_me(
            (
                f"Call {call_sid}: {name_company} | '{reason}'\n"
                f"Type: {decision['caller_type']} | Priority: {decision['priority']} | Action: {decision['action']}"
            )
        )
    except Exception:
        logger.exception("Failed to send SMS summary")

    vr = VoiceResponse()
    if decision.get("action") == "connect_now" and settings.forward_to:
        vr.say("Thanks. Connecting you now.")
        vr.dial(
            number=settings.forward_to,
            caller_id=(settings.twilio_number or None),
            action=_url(f"/post_dial?sid={call_sid}"),
            record="record-from-answer",
            recording_status_callback=_url(f"/recording_status?sid={call_sid}"),
        )
    else:
        vr.say("Thanks. Please leave a brief message after the beep.")
        vr.record(
            max_length=120,
            play_beep=True,
            timeout=4,
            recording_status_callback=_url(f"/voicemail_complete?sid={call_sid}"),
        )
        vr.say("Goodbye.")

    return PlainTextResponse(str(vr), media_type="text/xml")

@app.post("/post_dial")
async def post_dial(request: Request):
    form = await request.form()
    call_sid = request.query_params.get("sid", form.get("CallSid", ""))
    dial_call_status = form.get("DialCallStatus", "")
    logger.info(f"Post dial status for {call_sid}: {dial_call_status}")
    async with AsyncSessionLocal() as s:
        await update_call(s, call_sid, connected=(dial_call_status == "completed"))
    return PlainTextResponse("", media_type="text/xml")

@app.post("/recording_status")
async def recording_status(request: Request):
    form = await request.form()
    call_sid = request.query_params.get("sid", form.get("CallSid", ""))
    recording_url = form.get("RecordingUrl", "")
    status = form.get("RecordingStatus", "")
    logger.info(f"Recording for {call_sid}: {status} {recording_url}")
    if recording_url:
        async with AsyncSessionLocal() as s:
            await update_call(s, call_sid, recording_url=recording_url)
    return PlainTextResponse("", media_type="text/xml")

@app.post("/voicemail_complete")
async def voicemail_complete(request: Request):
    form = await request.form()
    call_sid = request.query_params.get("sid", form.get("CallSid", ""))
    recording_url = form.get("RecordingUrl", "")
    logger.info(f"Voicemail for {call_sid}: {recording_url}")
    if recording_url:
        async with AsyncSessionLocal() as s:
            await update_call(s, call_sid, voicemail_url=recording_url)
    return PlainTextResponse("", media_type="text/xml")

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("simulate_form.html", {"request": request})

@app.post("/simulate_twilio_call")
async def simulate_twilio_call(request: Request):
    form = await request.form()
    name_company = (form.get("name_company") or "").strip()
    reason = (form.get("reason") or "").strip()
    call_sid = f"SIM-{uuid.uuid4().hex[:10]}"
    from_number = "+10000000000"

    await _ensure_log(call_sid, from_number)

    decision = classify(name_company, reason)
    async with AsyncSessionLocal() as s:
        await update_call(
            s,
            call_sid,
            caller_name=name_company,
            reason=reason,
            caller_type=decision["caller_type"],
            priority=decision["priority"],
            action=decision["action"],
            urgency_minutes=decision.get("urgency_minutes"),
        )

    html = (
        f"<h2>Simulated Call Logged</h2>"
        f"<p>SID: {call_sid}</p>"
        f"<p>Name/Company: {name_company}</p>"
        f"<p>Reason: {reason}</p>"
        f"<p>Decision: {decision}</p>"
        f"<p><a href='/'>&larr; Back</a></p>"
    )
    return HTMLResponse(html)

@app.get("/health")
async def health():
    return {"status": "ok"}
