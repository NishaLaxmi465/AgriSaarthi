"""Configuration settings for AgriSaarthi."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Anthropic API (primary AI)
    ANTHROPIC_API_KEY: Optional[str] = None

    # AWS (kept for DynamoDB + S3)
    AWS_REGION: str = "ap-south-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None

    # These are in .env so we keep them to avoid validation errors
    BEDROCK_MODEL_ID: Optional[str] = None
    BEDROCK_VISION_MODEL_ID: Optional[str] = None
    REDIS_URL: Optional[str] = None
    SESSION_TTL_SECONDS: int = 1800

    # Twilio / WhatsApp
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_WHATSAPP_NUMBER: str = "whatsapp:+14155238886"

    # AWS DynamoDB
    DYNAMODB_TABLE_USERS: str = "agrisaarthi-users"
    DYNAMODB_TABLE_CONVERSATIONS: str = "agrisaarthi-conversations"
    DYNAMODB_TABLE_PEST_DETECTIONS: str = "agrisaarthi-pest-detections"

    # AWS S3
    S3_BUCKET_IMAGES: str = "agrisaarthi-crop-images"

    # External APIs
    OPENWEATHER_API_KEY: Optional[str] = None
    AGMARKNET_BASE_URL: str = "https://agmarknet.gov.in/SearchCommodityWise.aspx"

    # App settings
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"   # allow any extra keys from .env without crashing


settings = Settings()
