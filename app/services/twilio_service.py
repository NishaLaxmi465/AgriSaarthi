"""Twilio WhatsApp messaging service."""

import logging
from app.config import settings

logger = logging.getLogger(__name__)


class TwilioService:
    def __init__(self):
        self.from_number = settings.TWILIO_WHATSAPP_NUMBER
        self._client = None

    def _get_client(self):
        if not self._client and settings.TWILIO_ACCOUNT_SID:
            from twilio.rest import Client
            self._client = Client(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
        return self._client

    async def send_message(self, to: str, body: str) -> bool:
        """Send WhatsApp message via Twilio."""
        # Truncate to WhatsApp limit
        if len(body) > 4096:
            body = body[:4090] + "..."

        client = self._get_client()
        if not client:
            # Development mode - just log the message
            logger.info(f"📤 [DEV] To: {to[:8]}****\n{body}\n{'='*40}")
            return True

        try:
            message = client.messages.create(
                from_=self.from_number,
                to=to,
                body=body,
            )
            logger.info(f"✅ Message sent | SID: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
