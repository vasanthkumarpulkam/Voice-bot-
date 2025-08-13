from twilio.rest import Client
from settings import settings
import logging

logger = logging.getLogger(__name__)

_twilio = Client(settings.twilio_account_sid, settings.twilio_auth_token)

def sms_me(body: str):
    """
    Send an SMS to your personal number with call info.
    """
    if not (settings.twilio_number and settings.forward_to):
        logger.warning("Twilio number or forward_to not configured; SMS not sent.")
        return
    try:
        _twilio.messages.create(
            to=settings.forward_to,
            from_=settings.twilio_number,
            body=body[:1600]  # ensure within Twilio limit
        )
        logger.info("SMS sent successfully.")
    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
