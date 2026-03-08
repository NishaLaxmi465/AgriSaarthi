"""Twilio webhook signature validation for security."""

import hmac
import hashlib
import base64
import logging
from fastapi import Request, HTTPException
from app.config import settings

logger = logging.getLogger(__name__)


def validate_twilio_signature(request: Request):
    """
    Validate that webhook request actually came from Twilio.
    Prevents spoofing attacks.
    """
    if not settings.TWILIO_AUTH_TOKEN:
        logger.warning("⚠️ Twilio auth token not set - skipping validation")
        return

    signature = request.headers.get("X-Twilio-Signature", "")
    if not signature:
        raise HTTPException(status_code=403, detail="Missing Twilio signature")

    # Reconstruct expected signature
    url = str(request.url)
    token = settings.TWILIO_AUTH_TOKEN.encode("utf-8")
    
    expected = base64.b64encode(
        hmac.new(token, url.encode("utf-8"), hashlib.sha1).digest()
    ).decode("utf-8")

    if not hmac.compare_digest(signature, expected):
        logger.warning(f"❌ Invalid Twilio signature from {request.client.host}")
        raise HTTPException(status_code=403, detail="Invalid signature")
