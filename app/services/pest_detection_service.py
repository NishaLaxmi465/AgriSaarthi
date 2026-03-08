"""
Pest Detection Service
Downloads image from Twilio with auth, compresses it, 
sends to Anthropic Vision for crop disease/pest analysis.
"""

import httpx
import base64
import logging
from io import BytesIO
from PIL import Image

from app.config import settings
from app.services.bedrock_service import BedrockService

logger = logging.getLogger(__name__)

CROP_NAMES = {
    "wheat":     {"hi":"गेहूं",    "en":"wheat"},
    "rice":      {"hi":"धान",      "en":"rice"},
    "maize":     {"hi":"मक्का",    "en":"maize"},
    "sugarcane": {"hi":"गन्ना",    "en":"sugarcane"},
    "cotton":    {"hi":"कपास",     "en":"cotton"},
    "soybean":   {"hi":"सोयाबीन",  "en":"soybean"},
    "mustard":   {"hi":"सरसों",    "en":"mustard"},
    "tomato":    {"hi":"टमाटर",    "en":"tomato"},
    "onion":     {"hi":"प्याज",    "en":"onion"},
    "potato":    {"hi":"आलू",      "en":"potato"},
}

PROMPTS = {
    "hi": """इस {crop} की फसल की फोटो देखें और बताएं:

🔍 *रोग/कीट का नाम* (हिंदी और अंग्रेजी में)
⚠️ *गंभीरता*: कम / मध्यम / अधिक
👁️ *लक्षण*: आप क्या देख रहे हैं
💊 *रासायनिक उपचार*: दवा का नाम और मात्रा
🌿 *जैविक उपचार*: प्राकृतिक उपाय
🛡️ *बचाव*: आगे कैसे बचें

अगर फसल स्वस्थ है तो बताएं।
अगर फोटो साफ नहीं है तो बेहतर फोटो मांगें।""",

    "pa": """ਇਸ {crop} ਦੀ ਫਸਲ ਦੀ ਫੋਟੋ ਦੇਖੋ ਅਤੇ ਦੱਸੋ:

🔍 *ਰੋਗ/ਕੀੜੇ ਦਾ ਨਾਮ*
⚠️ *ਗੰਭੀਰਤਾ*: ਘੱਟ / ਮੱਧਮ / ਜ਼ਿਆਦਾ
👁️ *ਲੱਛਣ*
💊 *ਰਸਾਇਣਕ ਇਲਾਜ*: ਦਵਾਈ ਦਾ ਨਾਮ
🌿 *ਕੁਦਰਤੀ ਇਲਾਜ*
🛡️ *ਬਚਾਅ*""",

    "mr": """या {crop} पिकाचा फोटो पाहा आणि सांगा:

🔍 *रोग/कीडीचे नाव*
⚠️ *तीव्रता*: कमी / मध्यम / जास्त
👁️ *लक्षणे*
💊 *रासायनिक उपचार*: औषध आणि प्रमाण
🌿 *जैविक उपचार*
🛡️ *प्रतिबंध*""",

    "te": """ఈ {crop} పంట ఫోటో చూసి చెప్పండి:

🔍 *వ్యాధి/చీడ పేరు*
⚠️ *తీవ్రత*: తక్కువ / మధ్యస్థం / ఎక్కువ
👁️ *లక్షణాలు*
💊 *రసాయన చికిత్స*: మందు పేరు మరియు మోతాదు
🌿 *సేంద్రీయ చికిత్స*
🛡️ *నివారణ*""",

    "bn": """এই {crop} ফসলের ছবি দেখুন এবং বলুন:

🔍 *রোগ/কীটের নাম*
⚠️ *তীব্রতা*: কম / মাঝারি / বেশি
👁️ *লক্ষণ*
💊 *রাসায়নিক চিকিৎসা*: ওষুধের নাম ও পরিমাণ
🌿 *জৈব চিকিৎসা*
🛡️ *প্রতিরোধ*""",

    "gu": """આ {crop} પાકનો ફોટો જુઓ અને જણાવો:

🔍 *રોગ/જીવાતનું નામ*
⚠️ *તીવ્રતા*: ઓછી / મધ્યમ / વધુ
👁️ *લક્ષણો*
💊 *રાસાયણિક સારવાર*: દવાનું નામ અને માત્રા
🌿 *કુદરતી સારવાર*
🛡️ *નિવારણ*""",

    "en": """Analyse this {crop} crop photo and tell me:

🔍 *Disease/Pest Name* (common and scientific)
⚠️ *Severity*: Low / Medium / High
👁️ *Symptoms*: What you can see
💊 *Chemical Treatment*: Medicine name and dosage
🌿 *Organic Treatment*: Natural remedies
🛡️ *Prevention*: How to avoid in future

If crop looks healthy, say so.
If photo is unclear, ask for a better one.""",
}

DOWNLOAD_ERROR = {
    "hi": "📸 फोटो डाउनलोड नहीं हो सकी।\n\nकृपया:\n• फोटो दोबारा भेजें\n• अच्छी रोशनी में लें\n• पत्ती/तना करीब से दिखाएं",
    "pa": "📸 ਫੋਟੋ ਡਾਊਨਲੋਡ ਨਹੀਂ ਹੋ ਸਕੀ। ਕਿਰਪਾ ਕਰਕੇ ਦੁਬਾਰਾ ਭੇਜੋ।",
    "mr": "📸 फोटो डाउनलोड होऊ शकला नाही. कृपया पुन्हा पाठवा.",
    "te": "📸 ఫోటో డౌన్లోడ్ కాలేదు. దయచేసి మళ్ళీ పంపండి.",
    "bn": "📸 ছবি ডাউনলোড হয়নি। অনুগ্রহ করে আবার পাঠান.",
    "gu": "📸 ફોટો ડાઉનલોડ થઈ શક્યો નહીં. કૃপા કરી ફરી મોકલો.",
    "en": "📸 Could not download the photo.\n\nPlease:\n• Send the photo again\n• Take it in good lighting\n• Show the leaf/stem clearly",
}

ANALYSIS_ERROR = {
    "hi": "🔍 फोटो विश्लेषण में समस्या आई।\n\nकृपया:\n• अच्छी रोशनी में फोटो लें\n• पत्ती/तना करीब से दिखाएं\n• दोबारा भेजें",
    "pa": "🔍 ਫੋਟੋ ਵਿਸ਼ਲੇਸ਼ਣ ਵਿੱਚ ਸਮੱਸਿਆ ਆਈ। ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।",
    "mr": "🔍 फोटो विश्लेषणात समस्या आली. पुन्हा प्रयत्न करा.",
    "te": "🔍 ఫోటో విశ్లేషణలో సమస్య వచ్చింది. మళ్ళీ పంపండి.",
    "bn": "🔍 ছবি বিশ্লেষণে সমস্যা হয়েছে। আবার পাঠান.",
    "gu": "🔍 ફોટો વિশ્લેષણમાં સમસ્યા આવી. ફરી મોકલો.",
    "en": "🔍 Could not analyse the photo.\n\nPlease:\n• Take photo in good lighting\n• Show leaf/stem up close\n• Send it again",
}


class PestDetectionService:
    def __init__(self):
        self.bedrock = BedrockService()

    async def detect_disease(self, image_url: str, crop: str, lang: str = "hi") -> str:
        try:
            logger.info(f"🔍 Pest detection | crop={crop} | lang={lang}")

            # Step 1: Download image from Twilio with authentication
            image_bytes, media_type = await self._download_image(image_url)
            if not image_bytes:
                return DOWNLOAD_ERROR.get(lang, DOWNLOAD_ERROR["en"])

            # Step 2: Compress image
            compressed, final_media_type = self._compress_image(image_bytes)

            # Step 3: Try S3 upload (non-critical, skip if fails)
            await self._try_upload_s3(compressed, crop)

            # Step 4: Build prompt in user's language
            crop_info = CROP_NAMES.get(crop, {"hi": crop, "en": crop})
            crop_display = crop_info.get(lang, crop_info.get("en", crop))
            prompt_template = PROMPTS.get(lang, PROMPTS["en"])
            prompt = prompt_template.format(crop=crop_display)

            # Step 5: Send to Anthropic Vision
            image_b64 = base64.b64encode(compressed).decode("utf-8")
            result = await self.bedrock.invoke_vision_model(
                prompt, image_b64, final_media_type, lang
            )

            return result

        except Exception as e:
            logger.error(f"Pest detection error: {e}", exc_info=True)
            return ANALYSIS_ERROR.get(lang, ANALYSIS_ERROR["en"])

    async def _download_image(self, url: str):
        """Download image from Twilio URL with proper auth."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Twilio requires Basic Auth to download media
                auth = None
                if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
                    auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

                response = await client.get(url, auth=auth, follow_redirects=True)

                if response.status_code == 200:
                    content_type = response.headers.get("content-type", "image/jpeg")
                    # Clean content type (remove charset etc.)
                    media_type = content_type.split(";")[0].strip()
                    if media_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
                        media_type = "image/jpeg"
                    logger.info(f"✅ Image downloaded: {len(response.content)} bytes | {media_type}")
                    return response.content, media_type
                else:
                    logger.error(f"Image download failed: HTTP {response.status_code}")
                    return None, None

        except httpx.TimeoutException:
            logger.error("Image download timed out")
            return None, None
        except Exception as e:
            logger.error(f"Image download error: {e}")
            return None, None

    def _compress_image(self, image_bytes: bytes):
        """Resize and compress image to reduce API costs."""
        try:
            img = Image.open(BytesIO(image_bytes)).convert("RGB")
            # Resize if larger than 800x800
            img.thumbnail((800, 800), Image.Resampling.LANCZOS)
            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=85, optimize=True)
            compressed = buffer.getvalue()
            logger.info(f"Image compressed: {len(image_bytes)} → {len(compressed)} bytes")
            return compressed, "image/jpeg"
        except Exception as e:
            logger.warning(f"Compression failed, using original: {e}")
            return image_bytes, "image/jpeg"

    async def _try_upload_s3(self, image_bytes: bytes, crop: str):
        """Upload to S3 for audit - non-critical, silently skip if fails."""
        try:
            import boto3
            from datetime import datetime
            s3 = boto3.client(
                "s3",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
            key = f"pest-images/{crop}/{datetime.utcnow().strftime('%Y/%m/%d/%H%M%S')}.jpg"
            s3.put_object(
                Bucket=settings.S3_BUCKET_IMAGES,
                Key=key,
                Body=image_bytes,
                ContentType="image/jpeg",
            )
            logger.info(f"Image saved to S3: {key}")
        except Exception as e:
            logger.warning(f"S3 upload skipped: {e}")
