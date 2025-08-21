import os
from fastapi import FastAPI, Request, Response, Form
from fastapi.responses import PlainTextResponse, HTMLResponse
from twilio.twiml.voice_response import VoiceResponse, Gather
from settings import settings
from classify import classify
from db import init_db, AsyncSessionLocal, save_call, update_call, get_call
from notify import sms_me
from fastapi.templating import Jinja2Templates
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


templates = Jinja2Templates(directory="templates")


app = FastAPI()


@app.get("/")
async def health_check():
    return {"status": "healthy", "message": "Vasanth's AI Assistant is running"}


@app.on_event("startup")
async def startup():
    await init_db()


async def _ensure_log(call_sid: str, from_number: str):
    async with AsyncSessionLocal() as s:
        existing = await get_call(s, call_sid)
        if existing:
            return existing
        return await save_call(s, call_sid=call_sid, from_number=from_number)


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
        action=f"{settings.app_base_url}/gather_name?sid={call_sid}",
        method="POST",
        speech_timeout="auto",
        timeout=6
    )
    gather.say("Hi, you have reached Vasanth's assistant. I'll grab your name and company. What is your name and company?")
    vr.append(gather)
    vr.redirect(f"{settings.app_base_url}/voice")
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
        action=f"{settings.app_base_url}/route?sid={call_sid}",
        method="POST",
        speech_timeout="auto",
        timeout=8
    )
    gather.say("Thanks. Briefly, what is this regarding?")
    vr.append(gather)
    vr.redirect(f"{settings.app_base_url}/gather_name?sid={call_sid}")
    return PlainTextResponse(str(vr), media_type="text/xml")


@app.post("/route")
async def route_call(request: Request):
    form = await request.form()
    call_sid = request.query_params.get("sid", form.get("CallSid", ""))
    reason = (form.get("SpeechResult") or "").strip()
    logger.info(f"Reason: {reason}")

    async with AsyncSessionLocal() as s:
        log = await get_call(s, call_sid)
        name_company = log.caller_name or ""

        # Classify the call
        decision = classify(name_company, reason)
        logger.info(f"Classification: {decision}")

        # Update call log with classification and reason
        await update_call(s, call_sid,
                         reason=reason,
                         caller_type=decision.get("caller_type"),
                         priority=decision.get("priority"),
                         action=decision.get("action"),
                         urgency_minutes=decision.get("urgency_minutes"))

    vr = VoiceResponse()

    # Handle the decision
    if decision.get("action") == "connect_now":
        vr.say("Please hold while I connect you to Vasanth.")
        # In a real implementation, you would dial Vasanth's number here
        # vr.dial(settings.vasanth_phone_number)
        vr.say("Sorry, Vasanth is not available right now. Please leave a message after the beep.")
        vr.record(
            action=f"{settings.app_base_url}/recording?sid={call_sid}",
            method="POST",
            max_length=60,
            finish_on_key="#"
        )
    else:
        # Take a message
        vr.say("Thanks for calling. Please leave a detailed message after the beep, and Vasanth will get back to you.")
        vr.record(
            action=f"{settings.app_base_url}/recording?sid={call_sid}",
            method="POST",
            max_length=60,
            finish_on_key="#"
        )

    # Send notification if high priority
    if decision.get("priority") == "high":
        try:
            from notify import sms_me
            sms_me(f"High priority call from {name_company}: {reason}")
        except Exception as e:
            logger.error(f"Failed to send SMS notification: {e}")

    return PlainTextResponse(str(vr), media_type="text/xml")


@app.post("/recording")
async def handle_recording(request: Request):
    """Handle the recording from the caller"""
    form = await request.form()
    call_sid = request.query_params.get("sid", form.get("CallSid", ""))
    recording_url = form.get("RecordingUrl", "")

    async with AsyncSessionLocal() as s:
        await update_call(s, call_sid, recording_url=recording_url)

    vr = VoiceResponse()
    vr.say("Thank you for your message. Vasanth will get back to you soon. Goodbye!")
    vr.hangup()

    return PlainTextResponse(str(vr), media_type="text/xml")
