"""WhatsApp Webhook Handler - receives messages from Twilio."""

from fastapi import APIRouter, Form, BackgroundTasks, Request, Response, HTTPException
from typing import Optional
import logging

from app.services.message_processor import MessageProcessor
from app.utils.twilio_validator import validate_twilio_signature

logger = logging.getLogger(__name__)
router = APIRouter()
message_processor = MessageProcessor()


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    MessageSid: str = Form(...),
    From: str = Form(...),
    Body: Optional[str] = Form(None),
    NumMedia: int = Form(0),
    MediaUrl0: Optional[str] = Form(None),
    MediaContentType0: Optional[str] = Form(None),
    ProfileName: Optional[str] = Form(None),
):
    """
    Receive incoming WhatsApp messages via Twilio webhook.
    Returns 200 immediately; processes message in background.
    """
    # Validate Twilio signature (security)
    # validate_twilio_signature(request)  # Enable in production

    logger.info(f"📩 Incoming message from {From[:8]}**** | Media: {NumMedia}")

    # Build webhook data dict
    webhook_data = {
        "message_sid": MessageSid,
        "from_number": From,
        "body": Body or "",
        "num_media": NumMedia,
        "media_url": MediaUrl0,
        "media_content_type": MediaContentType0,
        "profile_name": ProfileName,
    }

    # Queue for async processing (prevents Twilio 15s timeout)
    background_tasks.add_task(
        message_processor.process_incoming_message,
        webhook_data
    )

    return Response(status_code=200)


@router.get("/webhook/whatsapp")
async def whatsapp_webhook_verify():
    """Health check endpoint for Twilio webhook verification."""
    return {"status": "AgriSaarthi webhook active 🌾"}
