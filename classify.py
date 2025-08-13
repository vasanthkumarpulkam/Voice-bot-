from openai import OpenAI
from settings import settings
import json
import logging

logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = (
    "You classify inbound phone calls for Vasanth. Return ONLY strict JSON with keys: "
    "caller_type (recruiter|family|friend|promotion|unknown), "
    "priority (high|medium|low), urgency_minutes (integer or null), action (connect_now|take_message). "
    "Rules: Recruiters are connect_now/high. Promotions/telemarketing -> low/take_message. "
    "Family emergencies -> high/connect_now, otherwise medium. Decide conservatively when unsure."
)

def classify(name_company: str, reason: str):
    """
    Calls OpenAI to classify the caller and returns a dict with:
    caller_type, priority, urgency_minutes, action
    """
    text = f"Caller info: {name_company}\nReason: {reason}"
    try:
        msg = client.chat.completions.create(
            model=settings.openai_model,
            temperature=0.0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
        )
        data = json.loads(msg.choices[0].message.content)
        caller_type = data.get("caller_type", "unknown")
        priority = data.get("priority", "low")
        urgency = data.get("urgency_minutes")
        action = data.get("action", "take_message")

        # Enforce recruiter rule if flag is enabled
        if settings.recruiter_always_connect and caller_type == "recruiter":
            priority = "high"
            action = "connect_now"

        return {
            "caller_type": caller_type,
            "priority": priority,
            "urgency_minutes": urgency,
            "action": action,
        }
    except Exception as e:
        logger.error(f"Classification error: {e}")
        # Safe fallback
        return {
            "caller_type": "unknown",
            "priority": "low",
            "urgency_minutes": None,
            "action": "take_message",
        }
