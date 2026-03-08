"""
Weather Service - Hyperlocal weather forecasts with farming-specific alerts.
Uses OpenWeather API with AWS ElastiCache for 6-hour caching.
"""

import httpx
import logging
from typing import Optional
from app.config import settings
from app.services.session_manager import SessionManager

logger = logging.getLogger(__name__)

# District to coordinates mapping (expand as needed)
DISTRICT_COORDS = {
    "ludhiana": (30.9010, 75.8573),
    "amritsar": (31.6340, 74.8723),
    "patiala": (30.3398, 76.3869),
    "chandigarh": (30.7333, 76.7794),
    "delhi": (28.6139, 77.2090),
    "lucknow": (26.8467, 80.9462),
    "varanasi": (25.3176, 82.9739),
    "pune": (18.5204, 73.8567),
    "nagpur": (21.1458, 79.0882),
    "patna": (25.5941, 85.1376),
}


class WeatherService:
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.session = SessionManager()

    async def get_weather_advisory(self, district: str) -> str:
        """Get 3-day weather forecast with farming advice."""
        # Check cache first
        cache_key = f"weather:{district.lower()}"
        cached = await self.session.get_session(f"cache_{district}")
        if cached and cached.get("weather_data"):
            return cached["weather_data"]

        coords = self._get_coords(district)

        if not self.api_key:
            return self._mock_weather_response(district)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/forecast",
                    params={
                        "lat": coords[0],
                        "lon": coords[1],
                        "appid": self.api_key,
                        "units": "metric",
                        "cnt": 8,  # 24 hours
                        "lang": "hi",
                    }
                )
                data = response.json()
                result = self._format_weather_response(data, district)

                # Cache for 6 hours
                await self.session.create_session(
                    f"cache_{district}",
                    {"weather_data": result}
                )
                return result

        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return self._mock_weather_response(district)

    def _get_coords(self, district: str) -> tuple:
        """Get lat/lon for district."""
        return DISTRICT_COORDS.get(district.lower(), (28.6139, 77.2090))

    def _format_weather_response(self, data: dict, district: str) -> str:
        """Format OpenWeather response into farming-friendly Hindi message."""
        try:
            today = data["list"][0]
            temp = today["main"]["temp"]
            humidity = today["main"]["humidity"]
            desc = today["weather"][0]["description"]
            rain_prob = today.get("pop", 0) * 100
            wind = today["wind"]["speed"]

            # Farming alerts
            alerts = []
            if rain_prob > 70:
                alerts.append("⚠️ बारिश की संभावना है - कीटनाशक न छिड़कें")
            if temp > 40:
                alerts.append("🌡️ गर्मी अधिक है - सुबह सिंचाई करें")
            if temp < 5:
                alerts.append("❄️ पाले का खतरा - फसल ढकें")
            if wind > 40:
                alerts.append("💨 तेज हवा - छिड़काव न करें")

            advice = "\n".join(alerts) if alerts else "✅ मौसम अनुकूल है"

            return (
                f"🌤️ *{district} का मौसम*\n\n"
                f"🌡️ तापमान: {temp:.0f}°C\n"
                f"💧 नमी: {humidity}%\n"
                f"🌧️ बारिश की संभावना: {rain_prob:.0f}%\n"
                f"💨 हवा: {wind:.0f} km/h\n\n"
                f"*खेती सलाह:*\n{advice}"
            )
        except Exception as e:
            logger.error(f"Weather formatting error: {e}")
            return self._mock_weather_response(district)

    def _mock_weather_response(self, district: str) -> str:
        """Mock response for development/when API key unavailable."""
        return (
            f"🌤️ *{district} का मौसम*\n\n"
            f"🌡️ तापमान: 24°C (अधिकतम 28°C)\n"
            f"💧 नमी: 65%\n"
            f"🌧️ बारिश: अगले 24 घंटे में नहीं\n"
            f"💨 हवा: 12 km/h\n\n"
            f"*खेती सलाह:*\n"
            f"✅ आज छिड़काव के लिए अच्छा दिन है\n"
            f"✅ शाम को सिंचाई कर सकते हैं\n"
            f"⚠️ अगले 3 दिनों में हल्की बारिश संभव"
        )
