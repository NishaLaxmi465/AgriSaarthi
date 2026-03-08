"""
AgriSaarthi - Test Suite
Tests for webhook handler, intent classification, and service responses.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "AgriSaarthi"


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_webhook_returns_200():
    """Webhook must return 200 immediately to prevent Twilio timeout."""
    with patch("app.services.message_processor.MessageProcessor.process_incoming_message", new_callable=AsyncMock):
        response = client.post(
            "/api/v1/webhook/whatsapp",
            data={
                "MessageSid": "SMtest123",
                "From": "whatsapp:+919876543210",
                "Body": "नमस्ते",
                "NumMedia": "0",
            }
        )
    assert response.status_code == 200


def test_webhook_with_greeting():
    """Test that greeting triggers onboarding."""
    with patch("app.services.message_processor.MessageProcessor.process_incoming_message", new_callable=AsyncMock) as mock:
        response = client.post(
            "/api/v1/webhook/whatsapp",
            data={
                "MessageSid": "SMtest456",
                "From": "whatsapp:+919876543210",
                "Body": "Hi",
                "NumMedia": "0",
            }
        )
    assert response.status_code == 200
    mock.assert_called_once()


class TestIntentClassification:
    """Test rule-based intent classification."""

    def setup_method(self):
        from app.services.message_processor import MessageProcessor
        self.processor = MessageProcessor()

    @pytest.mark.asyncio
    async def test_weather_intent(self):
        intent = await self.processor._classify_intent("आज मौसम कैसा रहेगा?")
        assert intent == "weather"

    @pytest.mark.asyncio
    async def test_mandi_intent(self):
        intent = await self.processor._classify_intent("गेहूं का भाव क्या है?")
        assert intent == "mandi_price"

    @pytest.mark.asyncio
    async def test_scheme_intent(self):
        intent = await self.processor._classify_intent("PM-KISAN योजना के बारे में बताएं")
        assert intent == "government_scheme"

    @pytest.mark.asyncio
    async def test_pest_intent(self):
        intent = await self.processor._classify_intent("फसल में कीड़े लग गए हैं")
        assert intent == "pest_help"

    @pytest.mark.asyncio
    async def test_unknown_intent(self):
        intent = await self.processor._classify_intent("यह क्या है")
        assert intent == "general"


class TestMandiService:
    def test_mock_wheat_prices(self):
        from app.services.mandi_service import MandiService
        service = MandiService()
        # Should return formatted string with ₹ sign
        import asyncio
        result = asyncio.run(service.get_prices("ludhiana", "wheat"))
        assert "₹" in result
        assert "गेहूं" in result

    def test_msp_comparison(self):
        from app.services.mandi_service import MandiService, MSP_RATES
        assert MSP_RATES["wheat"] == 2275
        assert MSP_RATES["rice"] == 2300


class TestSchemeService:
    def test_pm_kisan_query(self):
        from app.services.scheme_service import SchemeService
        service = SchemeService()
        import asyncio
        result = asyncio.run(service.get_scheme_info("PM-KISAN के बारे में बताएं"))
        assert "₹6,000" in result
        assert "pmkisan.gov.in" in result

    def test_pmfby_query(self):
        from app.services.scheme_service import SchemeService
        service = SchemeService()
        import asyncio
        result = asyncio.run(service.get_scheme_info("फसल बीमा कैसे करें"))
        assert "PMFBY" in result or "बीमा" in result

    def test_unknown_scheme(self):
        from app.services.scheme_service import SchemeService
        service = SchemeService()
        import asyncio
        result = asyncio.run(service.get_scheme_info("कुछ और"))
        assert "1800-180-1551" in result  # Should show helpline
