"""
Anthropic API Service - replaces AWS Bedrock.
Drop-in replacement - all method signatures stay the same.
"""

import anthropic
import base64
import logging
import asyncio
from typing import Optional
from datetime import datetime
from functools import partial

from app.config import settings

logger = logging.getLogger(__name__)

LANG_NAMES = {
    "hi": "Hindi (हिंदी)",
    "pa": "Punjabi (ਪੰਜਾਬੀ)",
    "mr": "Marathi (मराठी)",
    "te": "Telugu (తెలుగు)",
    "bn": "Bengali (বাংলা)",
    "gu": "Gujarati (ગુજराती)",
    "en": "English",
}

CROP_NAMES = {
    "wheat":     {"hi":"गेहूं",    "pa":"ਕਣਕ",    "mr":"गहू",    "te":"గోధుమ",       "bn":"গম",      "gu":"ઘઉં",    "en":"Wheat"},
    "rice":      {"hi":"धान",      "pa":"ਝੋਨਾ",   "mr":"भात",    "te":"వరి",          "bn":"ধান",     "gu":"ડાંગર",  "en":"Rice"},
    "maize":     {"hi":"मक्का",    "pa":"ਮੱਕੀ",   "mr":"मका",    "te":"మొక్కజొన్న",  "bn":"ভুট্টা",  "gu":"મકાઈ",   "en":"Maize"},
    "sugarcane": {"hi":"गन्ना",    "pa":"ਗੰਨਾ",   "mr":"ऊस",     "te":"చెరకు",        "bn":"আখ",      "gu":"શેરડી",  "en":"Sugarcane"},
    "cotton":    {"hi":"कपास",     "pa":"ਕਪਾਹ",   "mr":"कापूस",  "te":"పత్తి",        "bn":"তুলা",    "gu":"કપાસ",   "en":"Cotton"},
    "soybean":   {"hi":"सोयाबीन",  "pa":"ਸੋਇਆਬੀਨ","mr":"सोयाबीन","te":"సోయాబీన్",    "bn":"সয়াবিন", "gu":"સોयाबीन","en":"Soybean"},
    "mustard":   {"hi":"सरसों",    "pa":"ਸਰ੍ਹੋਂ", "mr":"मोहरी",  "te":"ఆవాలు",        "bn":"সরিষা",   "gu":"સरसव",   "en":"Mustard"},
    "tomato":    {"hi":"टमाटर",    "pa":"ਟਮਾਟਰ",  "mr":"टोमॅटो", "te":"టమాటా",        "bn":"টমেটো",   "gu":"ટામेटा", "en":"Tomato"},
    "onion":     {"hi":"प्याज",    "pa":"ਪਿਆਜ਼",  "mr":"कांदा",  "te":"ఉల్లిపాయ",     "bn":"পেঁয়াজ", "gu":"ડુંगళी", "en":"Onion"},
    "potato":    {"hi":"आलू",      "pa":"ਆਲੂ",    "mr":"बटाटा",  "te":"బంగాళాదుంప",  "bn":"আলু",     "gu":"બटाका",  "en":"Potato"},
}

ERROR_MSGS = {
    "hi": "⚠️ क्षमा करें, सेवा अभी उपलब्ध नहीं। थोड़ी देर बाद कोशिश करें।",
    "pa": "⚠️ ਮਾਫ਼ ਕਰੋ, ਸੇਵਾ ਹੁਣ ਉਪਲਬਧ ਨਹੀਂ।",
    "mr": "⚠️ क्षमा करा, सेवा सध्या उपलब्ध नाही.",
    "te": "⚠️ క్షమించండి, సేవ అందుబాటులో లేదు.",
    "bn": "⚠️ দুঃখিত, সেবা এখন পাওয়া যাচ্ছে না.",
    "gu": "⚠️ માફ કरो, સेवा हाल उपलब्ध नथी.",
    "en": "⚠️ Sorry, the service is temporarily unavailable. Please try again shortly.",
}


class BedrockService:
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY,
        )
        self.model = "claude-3-haiku-20240307"
        self.vision_model = "claude-3-5-sonnet-20241022"

    def _get_crop_name(self, crop: str, lang: str) -> str:
        return CROP_NAMES.get(crop, {}).get(lang) or CROP_NAMES.get(crop, {}).get("en", crop)

    def _call_api(self, model, system, messages, max_tokens):
        """Synchronous API call — run in thread to avoid blocking."""
        return self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )

    async def invoke_model(self, prompt: str, lang: str = "hi", max_tokens: int = 512) -> str:
        lang_name = LANG_NAMES.get(lang, "English")
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                partial(
                    self._call_api,
                    self.model,
                    (
                        f"You are AgriSaarthi, an AI agricultural advisor for Indian farmers. "
                        f"ALWAYS respond ONLY in {lang_name}. "
                        f"Keep responses under 200 words. Use emojis for clarity. "
                        f"Give practical, actionable advice. Format nicely for WhatsApp."
                    ),
                    [{"role": "user", "content": prompt}],
                    max_tokens,
                )
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {e}", exc_info=True)
            return ERROR_MSGS.get(lang, ERROR_MSGS["en"])

    async def invoke_vision_model(self, prompt: str, image_base64: str,
                                   media_type: str = "image/jpeg", lang: str = "hi") -> str:
        lang_name = LANG_NAMES.get(lang, "English")
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                partial(
                    self._call_api,
                    self.vision_model,
                    (
                        f"You are AgriSaarthi, an expert in Indian crop diseases and pests. "
                        f"Respond ONLY in {lang_name}. "
                        f"Be precise and give actionable treatment advice with product names."
                    ),
                    [{
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_base64,
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }],
                    1024,
                )
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic vision error: {e}", exc_info=True)
            vision_errors = {
                "hi": "⚠️ फोटो विश्लेषण में समस्या आई। कृपया दोबारा भेजें।",
                "en": "⚠️ Could not analyse the photo. Please send it again.",
            }
            return vision_errors.get(lang, vision_errors["en"])

    async def get_crop_advisory(self, crop: str, sowing_date: Optional[str],
                                 district: str, lang: str = "hi") -> str:
        crop_name = self._get_crop_name(crop, lang)
        days = 0
        if sowing_date and sowing_date != "0":
            try:
                sow = datetime.strptime(sowing_date, "%d/%m/%Y")
                days = (datetime.now() - sow).days
            except Exception:
                pass

        prompts = {
            "hi": (
                f"फसल: {crop_name} | जिला: {district}"
                + (f" | बुवाई के {days} दिन बाद" if days else "") +
                f"\n\nअभी क्या करें? सिंचाई, खाद, कीट निगरानी और अगला काम बताएं। 150 शब्दों में, बिंदुओं में।"
            ),
            "pa": (
                f"ਫਸਲ: {crop_name} | ਜ਼ਿਲ੍ਹਾ: {district}"
                + (f" | ਬਿਜਾਈ ਦੇ {days} ਦਿਨ ਬਾਅਦ" if days else "") +
                f"\n\nਹੁਣ ਕੀ ਕਰਨਾ ਚਾਹੀਦਾ ਹੈ? ਸਿੰਚਾਈ, ਖਾਦ, ਕੀੜੇ ਅਤੇ ਅਗਲਾ ਕੰਮ ਦੱਸੋ।"
            ),
            "mr": (
                f"पीक: {crop_name} | जिल्हा: {district}"
                + (f" | पेरणीनंतर {days} दिवस" if days else "") +
                f"\n\nआत्ता काय करावे? सिंचन, खत, कीड आणि पुढचे काम सांगा."
            ),
            "te": (
                f"పంట: {crop_name} | జిల్లా: {district}"
                + (f" | విత్తిన {days} రోజులు" if days else "") +
                f"\n\nఇప్పుడు ఏమి చేయాలి? నీటిపారుదల, ఎరువు, చీడ నిర్వహణ చెప్పండి."
            ),
            "bn": (
                f"ফসল: {crop_name} | জেলা: {district}"
                + (f" | বপনের {days} দিন পর" if days else "") +
                f"\n\nএখন কী করবেন? সেচ, সার, কীটপতঙ্গ ব্যবস্থাপনা বলুন."
            ),
            "gu": (
                f"પાક: {crop_name} | જિલ્લો: {district}"
                + (f" | વાવણી પછી {days} દિવસ" if days else "") +
                f"\n\nહવે શું કરવું? સિંચાઈ, ખાદ, કીડ નિયંત્રણ બતાવો."
            ),
            "en": (
                f"Crop: {crop_name} | District: {district}"
                + (f" | {days} days since sowing" if days else "") +
                f"\n\nWhat should the farmer do right now? "
                f"Cover: irrigation schedule, fertilizer application, pest monitoring, and next key task. "
                f"Keep it under 150 words, use bullet points."
            ),
        }

        prompt = prompts.get(lang) or prompts["en"]
        return await self.invoke_model(prompt, lang, max_tokens=400)

    async def get_general_response(self, query: str, session: dict, lang: str = "hi") -> str:
        crop = session.get("crop", "wheat")
        district = session.get("district", "")
        crop_name = self._get_crop_name(crop, lang)

        prompts = {
            "hi": f"किसान का सवाल: {query}\nसंदर्भ: {district} में {crop_name} की खेती\nसरल हिंदी में जवाब दें (100 शब्द)।",
            "pa": f"ਕਿਸਾਨ ਦਾ ਸਵਾਲ: {query}\nਸੰਦਰਭ: {district} ਵਿੱਚ {crop_name} ਦੀ ਖੇਤੀ\nਸਰਲ ਪੰਜਾਬੀ ਵਿੱਚ ਜਵਾਬ ਦਿਓ।",
            "mr": f"शेतकऱ्याचा प्रश्न: {query}\nसंदर्भ: {district} मध्ये {crop_name} शेती\nसोप्या मराठीत उत्तर द्या.",
            "te": f"రైతు ప్రశ్న: {query}\nసందర్భం: {district}లో {crop_name} సాగు\nసరళమైన తెలుగులో సమాధానం చెప్పండి.",
            "bn": f"কৃষকের প্রশ্ন: {query}\nপ্রসঙ্গ: {district}তে {crop_name} চাষ\nসহজ বাংলায় উত্তর দিন.",
            "gu": f"ખેડૂતનો સવાલ: {query}\nસંदर्भ: {district}માં {crop_name} ખेتী\nসরল ভাষায় জবাব দো.",
            "en": f"Farmer's question: {query}\nContext: Growing {crop_name} in {district}\nAnswer in simple English in under 100 words. Be practical and specific.",
        }

        prompt = prompts.get(lang) or prompts["en"]
        return await self.invoke_model(prompt, lang, max_tokens=300)
