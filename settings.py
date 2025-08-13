from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

class Settings(BaseModel):
    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_number: str = os.getenv("TWILIO_NUMBER", "")
    forward_to: str = os.getenv("FORWARD_TO", "")

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    app_base_url: str = os.getenv("APP_BASE_URL", "")
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./calls.db")

    recruiter_always_connect: bool = os.getenv("RECRUITER_ALWAYS_CONNECT", "true").lower() == "true"
    timezone: str = os.getenv("TIMEZONE", "America/Chicago")

settings = Settings()
