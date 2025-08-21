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


decision = classify(name_company, reason)
return PlainTextResponse(str(vr), media_type="text/xml")
