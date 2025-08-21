import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    # OpenAI configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    # Database configuration
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./calls.db")
    
    # Application configuration
    app_base_url: str = os.getenv("APP_BASE_URL", "http://localhost:8000")
    
    # Recruiter settings
    recruiter_always_connect: bool = os.getenv("RECRUITER_ALWAYS_CONNECT", "false").lower() == "true"
    
    # Twilio configuration
    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_number: str = os.getenv("TWILIO_PHONE_NUMBER", "")

    # Notification settings
    forward_to: str = os.getenv("ADMIN_PHONE_NUMBER", "")

settings = Settings()
