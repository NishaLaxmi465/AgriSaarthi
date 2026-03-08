"""
Message Processor - Smart context-aware WhatsApp bot.
Supports 7 languages: Hindi, Punjabi, Marathi, Telugu, Bengali, Gujarati, English
"""

import logging
from typing import Optional

from app.services.session_manager import SessionManager
from app.services.bedrock_service import BedrockService
from app.services.pest_detection_service import PestDetectionService
from app.services.weather_service import WeatherService
from app.services.mandi_service import MandiService
from app.services.scheme_service import SchemeService
from app.services.twilio_service import TwilioService

logger = logging.getLogger(__name__)

# ── Language Detection ────────────────────────────────────────────────────────
LANG_KEYWORDS = {
    "pa": ["ਸਤ","ਨਮਸਕਾਰ","ਕੀ","ਹਾਲ","ਪੰਜਾਬੀ","ਫਸਲ","ਮੌਸਮ","ਭਾਅ"],
    "mr": ["नमस्कार","मराठी","पीक","हवामान","काय","आहे"],
    "te": ["నమస్కారం","తెలుగు","పంట","వాతావరణం","ధర"],
    "bn": ["নমস্কার","বাংলা","ফসল","আবহাওয়া","দাম"],
    "gu": ["નમસ્તે","ગુજરાતી","પાક","હવામાન","ભાવ"],
    "en": ["english","in english","eng"],
}

CROPS = {
    "1":  ("wheat",     {"hi":"गेहूं",     "pa":"ਕਣਕ",    "mr":"गहू",    "te":"గోధుమ",       "bn":"গম",      "gu":"ઘઉં",    "en":"Wheat"}),
    "2":  ("rice",      {"hi":"धान/चावल",  "pa":"ਝੋਨਾ",   "mr":"भात",    "te":"వరి",          "bn":"ধান",     "gu":"ડાંગર",  "en":"Rice/Paddy"}),
    "3":  ("maize",     {"hi":"मक्का",     "pa":"ਮੱਕੀ",   "mr":"मका",    "te":"మొక్కజొన్న",  "bn":"ভুট্টা",  "gu":"મકાઈ",   "en":"Maize"}),
    "4":  ("sugarcane", {"hi":"गन्ना",     "pa":"ਗੰਨਾ",   "mr":"ऊस",     "te":"చెరకు",        "bn":"আখ",      "gu":"શેરડી",  "en":"Sugarcane"}),
    "5":  ("cotton",    {"hi":"कपास",      "pa":"ਕਪਾਹ",   "mr":"कापूस",  "te":"పత్తి",        "bn":"তুলা",    "gu":"કપાસ",   "en":"Cotton"}),
    "6":  ("soybean",   {"hi":"सोयाबीन",   "pa":"ਸੋਇਆਬੀਨ","mr":"सोयाबीन","te":"సోయాబీన్",    "bn":"সয়াবিন", "gu":"સોયાબીન","en":"Soybean"}),
    "7":  ("mustard",   {"hi":"सरसों",     "pa":"ਸਰ੍ਹੋਂ", "mr":"मोहरी",  "te":"ఆవాలు",        "bn":"সরিষা",   "gu":"સરસવ",   "en":"Mustard"}),
    "8":  ("tomato",    {"hi":"टमाटर",     "pa":"ਟਮਾਟਰ",  "mr":"टोमॅटो", "te":"టమాటా",        "bn":"টমেটো",   "gu":"ટામેટા", "en":"Tomato"}),
    "9":  ("onion",     {"hi":"प्याज",     "pa":"ਪਿਆਜ਼",  "mr":"कांदा",  "te":"ఉల్లిపాయ",     "bn":"পেঁয়াজ", "gu":"ડુંગળી", "en":"Onion"}),
    "10": ("potato",    {"hi":"आलू",       "pa":"ਆਲੂ",    "mr":"बटाटा",  "te":"బంగాళాదుంప",  "bn":"আলু",     "gu":"બટાકા",  "en":"Potato"}),
}

# ── Intent Keywords ───────────────────────────────────────────────────────────
WEATHER_KW  = ["मौसम","ਮੌਸਮ","हवामान","వాతావరణం","আবহাওয়া","હવામાન","weather","rain","barish","mausam","temp","बारिश"]
MANDI_KW    = ["भाव","ਭਾਅ","बाजार","मंडी","ਮੰਡੀ","ధర","বাজার","ભाव","price","mandi","bhav","rate","market","दाम","कीमत"]
SCHEME_KW   = ["योजना","ਸਕੀਮ","పథకం","প্রকল্প","યોजना","pm-kisan","pmkisan","kcc","bima","insurance","scheme","yojana","6000","सरकार","government scheme"]
PEST_KW     = ["कीड़े","ਕੀੜੇ","కీడ","కీటకం","কীটপতঙ্গ","જіवात","pest","disease","keede","rog","bimari","insect","fungus","रोग","बीमारी"]
ADVISORY_KW = ["सलाह","ਸਲਾਹ","సలహా","পরামর্শ","સলাह","advice","advisory","fertilizer","khad","irrigation","sowing","खाद","पानी","सिंचाई","crop advice"]
MENU_KW     = ["menu","मेनू","ਮੀਨੂ","మెనూ","মেনু","મেнू","help","मदद","सहायता","options","what can you do"]
RESET_KW    = ["reset","restart","नया","ਨਵਾਂ","నొత్त","নতুন","change profile","profile change","new profile","start over"]
GREET_KW    = {"hi","hello","hey","नमस्ते","ਸਤ ਸ੍ਰੀ ਅਕਾਲ","नमस्कार","నమస్కారం","নমস্কার","નમસ્તે","start","शुरू","hii","helo","good morning","good afternoon","namaste"}

MESSAGES = {
    "welcome_new": {
        "hi": "🌾 *AgriSaarthi में आपका स्वागत है!*\n\nनमस्ते! मैं आपका AI कृषि सहायक हूं। फसल सलाह, मौसम, मंडी भाव और सरकारी योजनाओं की जानकारी दे सकता हूं।\n\n*अपनी भाषा चुनें:*\n1️⃣ हिंदी\n2️⃣ ਪੰਜਾਬੀ\n3️⃣ मराठी\n4️⃣ తెలుగు\n5️⃣ বাংলা\n6️⃣ ગુજરાતી\n7️⃣ English",
    },
    "welcome_back": {
        "hi": "👋 *{name} जी, फिर से स्वागत है!*\n\n📍 {district} | 🌾 {crop}\n\n🌤️ *मौसम* | 💰 *भाव* | 📋 *योजना* | 🌾 *सलाह*\n\n_(प्रोफाइल बदलने के लिए 'reset' टाइप करें)_",
        "pa": "👋 *{name} ਜੀ, ਜੀ ਆਇਆਂ!*\n\n📍 {district} | 🌾 {crop}\n\n🌤️ *ਮੌਸਮ* | 💰 *ਭਾਅ* | 📋 *ਸਕੀਮ* | 🌾 *ਸਲਾਹ*",
        "mr": "👋 *{name} जी, स्वागत आहे!*\n\n📍 {district} | 🌾 {crop}\n\n🌤️ *हवामान* | 💰 *भाव* | 📋 *योजना* | 🌾 *सल्ला*",
        "te": "👋 *{name} గారు, స్వాగతం!*\n\n📍 {district} | 🌾 {crop}\n\n🌤️ *వాతావరణం* | 💰 *ధర* | 📋 *పథకం* | 🌾 *సలహా*",
        "bn": "👋 *{name} জি, স্বাগতম!*\n\n📍 {district} | 🌾 {crop}\n\n🌤️ *আবহাওয়া* | 💰 *দাম* | 📋 *প্রকল্প* | 🌾 *পরামর্শ*",
        "gu": "👋 *{name} જી, સ્વાગત છે!*\n\n📍 {district} | 🌾 {crop}\n\n🌤️ *હવামาન* | 💰 *ભाव* | 📋 *યোजना* | 🌾 *સलाह*",
        "en": "👋 *Welcome back, {name}!*\n\n📍 {district} | 🌾 {crop}\n\n🌤️ *Weather* | 💰 *Prices* | 📋 *Schemes* | 🌾 *Advisory*\n\n_(Type 'reset' to update your profile)_",
    },
    "ask_name": {
        "hi": "आपका नाम क्या है? 😊",
        "pa": "ਤੁਹਾਡਾ ਨਾਮ ਕੀ ਹੈ? 😊",
        "mr": "तुमचे नाव काय आहे? 😊",
        "te": "మీ పేరు ఏమిటి? 😊",
        "bn": "আপনার নাম কী? 😊",
        "gu": "તમારું નામ શું છે? 😊",
        "en": "What is your name? 😊",
    },
    "ask_district": {
        "hi": "आप किस जिले में रहते हैं?\n_(जैसे: लुधियाना, पुणे, हैदराबाद)_",
        "pa": "ਤੁਸੀਂ ਕਿਸ ਜ਼ਿਲ੍ਹੇ ਵਿੱਚ ਰਹਿੰਦੇ ਹੋ?\n_(ਜਿਵੇਂ: ਲੁਧਿਆਣਾ, ਅੰਮ੍ਰਿਤਸਰ)_",
        "mr": "तुम्ही कोणत्या जिल्ह्यात राहता?\n_(जसे: पुणे, नाशिक)_",
        "te": "మీరు ఏ జిల్లాలో ఉన్నారు?\n_(ఉదా: హైదరాబాద్, వరంగల్)_",
        "bn": "আপনি কোন জেলায় থাকেন?\n_(যেমন: মুর্শিদাবাদ, বর্ধমান)_",
        "gu": "તમે કયા જિલ્લામાં રહો છો?\n_(જેમ કે: આણંદ, સુરત)_",
        "en": "Which district do you live in?\n_(e.g. Ludhiana, Pune, Hyderabad)_",
    },
    "ask_crop": {
        "hi": "आपकी मुख्य फसल:\n\n1️⃣ गेहूं  2️⃣ धान  3️⃣ मक्का  4️⃣ गन्ना\n5️⃣ कपास  6️⃣ सोयाबीन  7️⃣ सरसों\n8️⃣ टमाटर  9️⃣ प्याज  🔟 आलू\n\n_नंबर दबाएं_",
        "pa": "ਆਪਣੀ ਮੁੱਖ ਫਸਲ:\n\n1️⃣ ਕਣਕ  2️⃣ ਝੋਨਾ  3️⃣ ਮੱਕੀ  4️⃣ ਗੰਨਾ\n5️⃣ ਕਪਾਹ  6️⃣ ਸੋਇਆਬੀਨ  7️⃣ ਸਰ੍ਹੋਂ\n8️⃣ ਟਮਾਟਰ  9️⃣ ਪਿਆਜ਼  🔟 ਆਲੂ",
        "mr": "तुमचे मुख्य पीक:\n\n1️⃣ गहू  2️⃣ भात  3️⃣ मका  4️⃣ ऊस\n5️⃣ कापूस  6️⃣ सोयाबीन  7️⃣ मोहरी\n8️⃣ टोमॅटो  9️⃣ कांदा  🔟 बटाटा",
        "te": "మీ ప్రధాన పంట:\n\n1️⃣ గోధుమ  2️⃣ వరి  3️⃣ మొక్కజొన్న  4️⃣ చెరకు\n5️⃣ పత్తి  6️⃣ సోయాబీన్  7️⃣ ఆవాలు\n8️⃣ టమాటా  9️⃣ ఉల్లిపాయ  🔟 బంగాళాదుంప",
        "bn": "আপনার প্রধান ফসল:\n\n1️⃣ গম  2️⃣ ধান  3️⃣ ভুট্টা  4️⃣ আখ\n5️⃣ তুলা  6️⃣ সয়াবিন  7️⃣ সরিষা\n8️⃣ টমেটো  9️⃣ পেঁয়াজ  🔟 আলু",
        "gu": "તમારો મુખ્ય પাક:\n\n1️⃣ ઘઉં  2️⃣ ડાંગર  3️⃣ મકાઈ  4️⃣ શેરડી\n5️⃣ ક�าส  6️⃣ સوยाबین  7️⃣ সরসব\n8️⃣ ટामेटा  9️⃣ ડুंगळी  🔟 बटाका",
        "en": "Select your main crop:\n\n1️⃣ Wheat  2️⃣ Rice  3️⃣ Maize  4️⃣ Sugarcane\n5️⃣ Cotton  6️⃣ Soybean  7️⃣ Mustard\n8️⃣ Tomato  9️⃣ Onion  🔟 Potato\n\n_Press a number (1-10)_",
    },
    "ask_sowing": {
        "hi": "बुवाई की तारीख? (DD/MM/YYYY)\n_जैसे: 15/11/2024_\n\n_(नहीं पता? '0' दबाएं)_",
        "pa": "ਬਿਜਾਈ ਦੀ ਤਾਰੀਖ? (DD/MM/YYYY)\n_(ਨਹੀਂ ਪਤਾ? '0' ਦਬਾਓ)_",
        "mr": "पेरणीची तारीख? (DD/MM/YYYY)\n_(माहीत नसल्यास '0' दाबा)_",
        "te": "విత్తన తేదీ? (DD/MM/YYYY)\n_(తెలియకపోతే '0' నొక్కండి)_",
        "bn": "বপনের তারিখ? (DD/MM/YYYY)\n_(জানা না থাকলে '0' চাপুন)_",
        "gu": "વावणी তারীখ? (DD/MM/YYYY)\n_(ખبर ন হোय তো '0' দবাво)_",
        "en": "What is your sowing date? (DD/MM/YYYY)\n_e.g. 15/11/2024_\n\n_(Don't know? Press '0')_",
    },
    "onboard_done": {
        "hi": "✅ *प्रोफाइल तैयार!*\n\n👤 {name} | 📍 {district} | 🌾 {crop}\n\nअब पूछें:\n📸 *फसल की फोटो* → कीट/रोग पहचान\n🌤️ मौसम | 💰 भाव | 📋 योजना | 🌾 सलाह\n\n_मेनू के लिए 'menu' टाइप करें_",
        "pa": "✅ *ਪ੍ਰੋਫਾਈਲ ਤਿਆਰ!*\n\n👤 {name} | 📍 {district} | 🌾 {crop}\n\nਹੁਣ ਪੁੱਛੋ:\n📸 *ਫਸਲ ਦੀ ਫੋਟੋ* → ਕੀੜੇ/ਰੋਗ ਪਛਾਣ\n🌤️ ਮੌਸਮ | 💰 ਭਾਅ | 📋 ਸਕੀਮ | 🌾 ਸਲਾਹ",
        "mr": "✅ *प्रोफाइल तयार!*\n\n👤 {name} | 📍 {district} | 🌾 {crop}\n\nआता विचारा:\n📸 *पीकाचा फोटो* → कीड/रोग ओळख\n🌤️ हवामान | 💰 भाव | 📋 योजना | 🌾 सल्ला",
        "te": "✅ *ప్రొఫైల్ సిద్ధం!*\n\n👤 {name} | 📍 {district} | 🌾 {crop}\n\nఇప్పుడు అడగండి:\n📸 *పంట ఫోటో* → చీడ/వ్యాధి గుర్తింపు\n🌤️ వాతావరణం | 💰 ధర | 📋 పథకం | 🌾 సలహా",
        "bn": "✅ *প্রোফাইল তৈরি!*\n\n👤 {name} | 📍 {district} | 🌾 {crop}\n\nএখন জিজ্ঞেস করুন:\n📸 *ফসলের ছবি* → কীট/রোগ শনাক্ত\n🌤️ আবহাওয়া | 💰 দাম | 📋 প্রকল্প | 🌾 পরামর্শ",
        "gu": "✅ *પ્રোফাઇل তৈयার!*\n\n👤 {name} | 📍 {district} | 🌾 {crop}\n\nহवे पूछो:\n📸 *পাकनো ফোটো* → কীড/রোগ ওળখ\n🌤️ হवामान | 💰 ভাব | 📋 যোজনা | 🌾 সলাহ",
        "en": "✅ *Profile Created!*\n\n👤 {name} | 📍 {district} | 🌾 {crop}\n\nYou can now ask:\n📸 *Send crop photo* → Pest/disease detection\n🌤️ Weather | 💰 Prices | 📋 Schemes | 🌾 Advisory\n\n_Type 'menu' anytime for options_",
    },
    "menu": {
        "hi": "📋 *AgriSaarthi मेनू*\n\n1️⃣ 🌤️ मौसम\n2️⃣ 💰 मंडी भाव\n3️⃣ 🌾 फसल सलाह\n4️⃣ 📋 सरकारी योजनाएं\n5️⃣ 📸 कीट/रोग पहचान\n6️⃣ 🔄 प्रोफाइल बदलें\n\n_नंबर दबाएं या सीधे सवाल पूछें_",
        "pa": "📋 *AgriSaarthi ਮੀਨੂ*\n\n1️⃣ 🌤️ ਮੌਸਮ\n2️⃣ 💰 ਮੰਡੀ ਭਾਅ\n3️⃣ 🌾 ਫਸਲ ਸਲਾਹ\n4️⃣ 📋 ਸਰਕਾਰੀ ਸਕੀਮਾਂ\n5️⃣ 📸 ਕੀੜੇ/ਰੋਗ ਪਛਾਣ\n6️⃣ 🔄 ਪ੍ਰੋਫਾਈਲ ਬਦਲੋ",
        "mr": "📋 *AgriSaarthi मेनू*\n\n1️⃣ 🌤️ हवामान\n2️⃣ 💰 बाजार भाव\n3️⃣ 🌾 पीक सल्ला\n4️⃣ 📋 सरकारी योजना\n5️⃣ 📸 कीड/रोग ओळख\n6️⃣ 🔄 प्रोफाइल बदला",
        "te": "📋 *AgriSaarthi మెనూ*\n\n1️⃣ 🌤️ వాతావరణం\n2️⃣ 💰 మార్కెట్ ధరలు\n3️⃣ 🌾 పంట సలహా\n4️⃣ 📋 ప్రభుత్వ పథకాలు\n5️⃣ 📸 చీడ/వ్యాధి గుర్తింపు\n6️⃣ 🔄 ప్రొఫైల్ మార్చండి",
        "bn": "📋 *AgriSaarthi মেনু*\n\n1️⃣ 🌤️ আবহাওয়া\n2️⃣ 💰 বাজার দর\n3️⃣ 🌾 ফসলের পরামর্শ\n4️⃣ 📋 সরকারি প্রকল্প\n5️⃣ 📸 কীট/রোগ শনাক্ত\n6️⃣ 🔄 প্রোফাইল পরিবর্তন",
        "gu": "📋 *AgriSaarthi মেনূ*\n\n1️⃣ 🌤️ হवামান\n2️⃣ 💰 বাজার ভাব\n3️⃣ 🌾 পাক সলাহ\n4️⃣ 📋 সরকারী যোজনা\n5️⃣ 📸 জীবাত/রোগ ওळখ\n6️⃣ 🔄 প্রোফাইল বदलো",
        "en": "📋 *AgriSaarthi Menu*\n\n1️⃣ 🌤️ Weather Update\n2️⃣ 💰 Market Prices\n3️⃣ 🌾 Crop Advisory\n4️⃣ 📋 Government Schemes\n5️⃣ 📸 Pest/Disease Detection\n6️⃣ 🔄 Change Profile\n\n_Press a number or ask anything directly_",
    },
    "send_photo": {
        "hi": "📸 अपनी फसल की फोटो भेजें।\nAI कीट/रोग की पहचान करेगा और इलाज बताएगा। 🔍",
        "pa": "📸 ਆਪਣੀ ਫਸਲ ਦੀ ਫੋਟੋ ਭੇਜੋ।\nAI ਕੀੜੇ/ਰੋਗ ਦੀ ਪਛਾਣ ਕਰੇਗਾ। 🔍",
        "mr": "📸 तुमच्या पीकाचा फोटो पाठवा.\nAI कीड/रोग ओळखेल आणि उपाय सांगेल. 🔍",
        "te": "📸 మీ పంట ఫోటో పంపండి.\nAI చీడ/వ్యాధి గుర్తించి చికిత్స చెప్తుంది. 🔍",
        "bn": "📸 আপনার ফসলের ছবি পাঠান.\nAI কীট/রোগ শনাক্ত করে চিকিৎসা জানাবে. 🔍",
        "gu": "📸 તমারা पाकनो फोटो मोक्लो.\nAI जीवात/रोग पछानशे. 🔍",
        "en": "📸 Send a clear photo of your crop.\nAI will identify the pest/disease and suggest treatment. 🔍",
    },
    "register_first": {
        "hi": "👋 AgriSaarthi में रजिस्टर करने के लिए 'Hi' टाइप करें। 🌾",
        "pa": "👋 AgriSaarthi ਵਿੱਚ ਰਜਿਸਟਰ ਕਰਨ ਲਈ 'Hi' ਟਾਈਪ ਕਰੋ। 🌾",
        "mr": "👋 AgriSaarthi मध्ये नोंदणी करण्यासाठी 'Hi' टाइप करा. 🌾",
        "te": "👋 AgriSaarthi లో నమోదు చేయడానికి 'Hi' అని టైప్ చేయండి. 🌾",
        "bn": "👋 AgriSaarthi তে নিবন্ধন করতে 'Hi' টাইপ করুন. 🌾",
        "gu": "👋 AgriSaarthi माँ नोंधणी करवा 'Hi' टाईप करो. 🌾",
        "en": "👋 Type 'Hi' to register with AgriSaarthi and get started. 🌾",
    },
    "error": {
        "hi": "⚠️ क्षमा करें, कुछ समस्या आई। कृपया दोबारा कोशिश करें।",
        "pa": "⚠️ ਮਾਫ਼ ਕਰੋ, ਕੁਝ ਸਮੱਸਿਆ ਆਈ। ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।",
        "mr": "⚠️ क्षमा करा, समस्या आली. पुन्हा प्रयत्न करा.",
        "te": "⚠️ క్షమించండి, సమస్య వచ్చింది. మళ్ళీ ప్రయత్నించండి.",
        "bn": "⚠️ দুঃখিত, সমস্যা হয়েছে. আবার চেষ্টা করুন.",
        "gu": "⚠️ माफ करो, समस्या आवी. फरी प्रयास करो.",
        "en": "⚠️ Sorry, something went wrong. Please try again.",
    },
}


def _msg(key: str, lang: str) -> str:
    return MESSAGES.get(key, {}).get(lang) or MESSAGES.get(key, {}).get("hi", "")


def _detect_lang(text: str) -> Optional[str]:
    t = text.lower()
    for lang, keywords in LANG_KEYWORDS.items():
        if any(kw in t for kw in keywords):
            return lang
    return None


def _crop_name(crop_key: str, lang: str) -> str:
    for num, (key, names) in CROPS.items():
        if key == crop_key:
            return names.get(lang, names.get("hi", crop_key))
    return crop_key


class MessageProcessor:
    def __init__(self):
        self.sessions = SessionManager()
        self.bedrock = BedrockService()
        self.pest = PestDetectionService()
        self.weather = WeatherService()
        self.mandi = MandiService()
        self.schemes = SchemeService()
        self.twilio = TwilioService()

    async def process_incoming_message(self, webhook_data: dict):
        phone = webhook_data["from_number"]
        body  = webhook_data.get("body", "").strip()
        num_media  = webhook_data.get("num_media", 0)
        media_url  = webhook_data.get("media_url")
        media_type = webhook_data.get("media_content_type", "")

        try:
            session = await self.sessions.get_session(phone)
            lang = (session or {}).get("lang", "hi")
            response = await self._route(phone, body, num_media, media_url, media_type, session, lang)
            await self.twilio.send_message(phone, response)
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            session = await self.sessions.get_session(phone)
            lang = (session or {}).get("lang", "hi")
            await self.twilio.send_message(phone, _msg("error", lang))

    async def _route(self, phone, body, num_media, media_url, media_type, session, lang) -> str:
        t = body.lower().strip()

        # ── Image ─────────────────────────────────────────────────────────────
        if num_media > 0 and media_type.startswith("image/"):
            if not session or not session.get("onboarding_complete"):
                return _msg("register_first", lang)
            return await self.pest.detect_disease(media_url, session.get("crop", "wheat"), lang)

        # ── Reset profile ──────────────────────────────────────────────────────
        if any(kw in t for kw in RESET_KW):
            await self.sessions.clear_session(phone)
            return MESSAGES["welcome_new"]["hi"]

        # ── Greeting ───────────────────────────────────────────────────────────
        if t in GREET_KW:
            if session and session.get("onboarding_complete"):
                # Returning user — personalised welcome, no questions
                crop = _crop_name(session.get("crop", "wheat"), lang)
                return _msg("welcome_back", lang).format(
                    name=session.get("name", "किसान"),
                    district=session.get("district", ""),
                    crop=crop,
                )
            elif not session:
                # Brand new user
                await self.sessions.create_session(phone, {
                    "onboarding_complete": False,
                    "onboarding_step": 0,
                    "lang": "hi",
                })
                return MESSAGES["welcome_new"]["hi"]
            else:
                # Mid-onboarding — continue where they left off
                return await self._onboard(phone, body, session)

        # ── Onboarding in progress ─────────────────────────────────────────────
        if session and not session.get("onboarding_complete"):
            return await self._onboard(phone, body, session)

        # ── Registered user ────────────────────────────────────────────────────
        if session and session.get("onboarding_complete"):
            return await self._handle_command(phone, body, t, session, lang)

        # ── Unknown user, random message ───────────────────────────────────────
        return _msg("register_first", "hi")

    async def _onboard(self, phone: str, body: str, session: dict) -> str:
        step = session.get("onboarding_step", 0)
        lang = session.get("lang", "hi")

        # Step 0: language selection
        if step == 0:
            lang_map = {"1":"hi","2":"pa","3":"mr","4":"te","5":"bn","6":"gu","7":"en"}
            detected = _detect_lang(body)
            chosen = lang_map.get(body.strip()) or detected or "hi"
            await self.sessions.update_session(phone, {**session, "lang": chosen, "onboarding_step": 1})
            return _msg("ask_name", chosen)

        # Step 1: name
        elif step == 1:
            name = body.strip()
            if len(name) < 2:
                return _msg("ask_name", lang)
            await self.sessions.update_session(phone, {**session, "name": name, "onboarding_step": 2})
            greets = {
                "hi": f"नमस्ते *{name}* जी! 🙏\n\n",
                "pa": f"ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ *{name}* ਜੀ! 🙏\n\n",
                "mr": f"नमस्कार *{name}* जी! 🙏\n\n",
                "te": f"నమస్కారం *{name}* గారు! 🙏\n\n",
                "bn": f"নমস্কার *{name}* জি! 🙏\n\n",
                "gu": f"નমস્તে *{name}* জি! 🙏\n\n",
                "en": f"Nice to meet you, *{name}*! 🙏\n\n",
            }
            return greets.get(lang, f"Hello *{name}*! 🙏\n\n") + _msg("ask_district", lang)

        # Step 2: district
        elif step == 2:
            district = body.strip()
            if len(district) < 2:
                return _msg("ask_district", lang)
            await self.sessions.update_session(phone, {**session, "district": district, "onboarding_step": 3})
            return _msg("ask_crop", lang)

        # Step 3: crop
        elif step == 3:
            crop_data = CROPS.get(body.strip())
            if not crop_data:
                # Try matching typed crop name in any language
                for num, (key, names) in CROPS.items():
                    if body.strip().lower() in [n.lower() for n in names.values()]:
                        crop_data = (key, names)
                        break
            if not crop_data:
                invalid_msg = {
                    "hi": "⚠️ 1 से 10 के बीच नंबर दबाएं",
                    "pa": "⚠️ 1 ਤੋਂ 10 ਦੇ ਵਿਚਕਾਰ ਨੰਬਰ ਦਬਾਓ",
                    "mr": "⚠️ 1 ते 10 मधील नंबर दाबा",
                    "te": "⚠️ 1 నుండి 10 మధ్య నంబర్ నొక్కండి",
                    "bn": "⚠️ 1 থেকে 10 এর মধ্যে নম্বর চাপুন",
                    "gu": "⚠️ 1 थी 10 वच्चे नंबर दबावो",
                    "en": "⚠️ Please press a number between 1 and 10",
                }.get(lang, "⚠️ Press 1-10")
                return _msg("ask_crop", lang) + "\n\n" + invalid_msg
            crop_key = crop_data[0]
            await self.sessions.update_session(phone, {**session, "crop": crop_key, "onboarding_step": 4})
            return _msg("ask_sowing", lang)

        # Step 4: sowing date → complete onboarding
        elif step == 4:
            sowing = None if body.strip() == "0" else body.strip()
            await self.sessions.update_session(phone, {
                **session,
                "sowing_date": sowing,
                "onboarding_complete": True,
            })
            crop = _crop_name(session.get("crop", "wheat"), lang)
            return _msg("onboard_done", lang).format(
                name=session.get("name", "Farmer"),
                district=session.get("district", ""),
                crop=crop,
            )

        return _msg("menu", lang)

    async def _handle_command(self, phone: str, body: str, t: str, session: dict, lang: str) -> str:
        district = session.get("district", "Delhi")
        crop     = session.get("crop", "wheat")

        # Detect mid-conversation language switch
        detected = _detect_lang(body)
        if detected and detected != lang:
            lang = detected
            await self.sessions.update_session(phone, {**session, "lang": lang})

        # Menu
        if any(kw in t for kw in MENU_KW) or t == "0":
            return _msg("menu", lang)

        # Number shortcuts
        if t == "1": return await self.weather.get_weather_advisory(district)
        if t == "2": return await self.mandi.get_prices(district, crop)
        if t == "3": return await self.bedrock.get_crop_advisory(crop, session.get("sowing_date"), district, lang)
        if t == "4": return await self.schemes.get_scheme_info(body, lang)
        if t == "5": return _msg("send_photo", lang)
        if t == "6":
            await self.sessions.clear_session(phone)
            return MESSAGES["welcome_new"]["hi"]

        # Intent keywords
        if any(kw in t for kw in WEATHER_KW):
            return await self.weather.get_weather_advisory(district)

        if any(kw in t for kw in MANDI_KW):
            return await self.mandi.get_prices(district, crop)

        if any(kw in t for kw in SCHEME_KW):
            return await self.schemes.get_scheme_info(body, lang)

        if any(kw in t for kw in PEST_KW):
            return _msg("send_photo", lang)

        if any(kw in t for kw in ADVISORY_KW):
            return await self.bedrock.get_crop_advisory(crop, session.get("sowing_date"), district, lang)

        # Anything else → Bedrock AI answers intelligently
        return await self.bedrock.get_general_response(body, session, lang)
