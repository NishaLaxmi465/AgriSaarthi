# 🌾 AgriSaarthi — AI Agricultural Assistant for Bharat

> **WhatsApp-based AI chatbot empowering Indian farmers with crop advisory, pest detection, weather updates, mandi prices, and government scheme information — in 7 Indian languages.**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![AWS](https://img.shields.io/badge/AWS-DynamoDB%20%7C%20S3-orange.svg)](https://aws.amazon.com)
[![Anthropic](https://img.shields.io/badge/AI-Claude%203%20Haiku-purple.svg)](https://anthropic.com)
[![Twilio](https://img.shields.io/badge/WhatsApp-Twilio-red.svg)](https://twilio.com)

---

## 📱 Demo

Send `Hi` to **+1 415 523 8886** on WhatsApp with join code: `join respect-eventually`

---

## 🚀 Features

| Feature | Description |
|--------|-------------|
| 🌍 **7 Languages** | Hindi, Punjabi, Marathi, Telugu, Bengali, Gujarati, English |
| 🐛 **Pest & Disease Detection** | Upload crop photo → AI identifies disease + treatment |
| 🌤️ **Weather Advisory** | Hyperlocal weather with farming-specific alerts |
| 💰 **Mandi Prices** | Real-time market prices for 10 crops |
| 📋 **Government Schemes** | PM-KISAN, PMFBY, KCC, Soil Health Card, e-NAM |
| 🌾 **Crop Advisory** | AI-powered stage-wise crop management advice |
| 👤 **Smart Profiles** | Remembers returning users — no repeat questions |
| 🔄 **10 Crops Supported** | Wheat, Rice, Maize, Sugarcane, Cotton, Soybean, Mustard, Tomato, Onion, Potato |

---

## 🏗️ Architecture

```
WhatsApp Message
      ↓
   Twilio
      ↓
 FastAPI Webhook  (app/handlers/webhook_handler.py)
      ↓
Message Processor  (intent detection + language routing)
      ↓
┌─────────────────────────────────────────┐
│  Anthropic Claude 3    AWS DynamoDB     │
│  (Advisory + Vision)   (Sessions)       │
│                                         │
│  Weather Service       Mandi Service    │
│  (OpenWeather API)     (Agmarknet)      │
│                                         │
│  Scheme Service        AWS S3           │
│  (Knowledge Base)      (Crop Images)    │
└─────────────────────────────────────────┘
      ↓
  Twilio → WhatsApp Reply
```

---

## 🛠️ Tech Stack

- **Backend:** FastAPI (Python)
- **AI Model:** Anthropic Claude 3 Haiku (text) + Claude 3.5 Sonnet (vision)
- **Database:** AWS DynamoDB (session management)
- **Storage:** AWS S3 (crop images)
- **Messaging:** Twilio WhatsApp API
- **Weather:** OpenWeatherMap API
- **Deployment:** Render / AWS App Runner

---

## 📁 Project Structure

```
agrisaarthi/
├── app/
│   ├── main.py                        # FastAPI app entry point
│   ├── config.py                      # Environment settings
│   ├── handlers/
│   │   ├── webhook_handler.py         # POST /api/v1/webhook/whatsapp
│   │   └── health_handler.py          # GET /health
│   └── services/
│       ├── message_processor.py       # Core routing + intent detection
│       ├── bedrock_service.py         # Anthropic API (text + vision)
│       ├── pest_detection_service.py  # Crop disease detection
│       ├── weather_service.py         # Weather advisory
│       ├── mandi_service.py           # Market prices
│       ├── scheme_service.py          # Government schemes KB
│       ├── session_manager.py         # In-memory user sessions
│       └── twilio_service.py          # WhatsApp messaging
├── static/
│   └── index.html                     # Landing page + chat demo
├── requirements.txt
└── .env.example
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10+
- Twilio account (WhatsApp sandbox)
- Anthropic API key
- AWS account (DynamoDB + S3)

### 1. Clone the repository
```bash
git clone https://github.com/NishaLaxmi465/AgriSaarthi.git
cd AgriSaarthi
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
```
Edit `.env` with your credentials:
```env
# Anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxx

# Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxx
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# AWS
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=xxxxxxxxxx
AWS_SECRET_ACCESS_KEY=xxxxxxxxxx

# DynamoDB Tables
DYNAMODB_TABLE_USERS=agrisaarthi-users
DYNAMODB_TABLE_CONVERSATIONS=agrisaarthi-conversations
DYNAMODB_TABLE_PEST_DETECTIONS=agrisaarthi-pest-detections

# S3
S3_BUCKET_IMAGES=agrisaarthi-crop-images

# Optional
OPENWEATHER_API_KEY=xxxxxxxxxx
```

### 5. Run the server
```bash
uvicorn app.main:app --port 8000
```

### 6. Expose with ngrok (for local testing)
```bash
.\ngrok.exe http 8000
```
Copy the HTTPS URL and set it as your Twilio webhook:
```
https://your-ngrok-url.ngrok-free.app/api/v1/webhook/whatsapp
```

---

## 🌐 Deployment (Render)

1. Push code to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your GitHub repo
4. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port 8000`
5. Add all environment variables from `.env`
6. Deploy → get permanent URL
7. Update Twilio webhook to: `https://your-app.onrender.com/api/v1/webhook/whatsapp`

---

## 💬 Bot Flow

```
User: Hi
Bot:  🌾 Welcome! Choose language (1-7)

User: 7  (English)
Bot:  What is your name?

User: Ramesh
Bot:  Nice to meet you Ramesh! Which district?

User: Ludhiana
Bot:  Select your main crop (1-10)

User: 1  (Wheat)
Bot:  Sowing date? (or 0 to skip)

User: 0
Bot:  ✅ Profile created! Now ask:
      📸 Crop photo → pest/disease detection
      🌤️ Weather | 💰 Prices | 📋 Schemes | 🌾 Advisory

--- Returning User ---
User: Hi
Bot:  👋 Welcome back Ramesh! (Ludhiana | Wheat)
      → No questions asked again ✅
```

---

## 🗣️ Supported Languages

| # | Language | Script |
|---|----------|--------|
| 1 | हिंदी (Hindi) | Devanagari |
| 2 | ਪੰਜਾਬੀ (Punjabi) | Gurmukhi |
| 3 | मराठी (Marathi) | Devanagari |
| 4 | తెలుగు (Telugu) | Telugu |
| 5 | বাংলা (Bengali) | Bengali |
| 6 | ગુજરાતી (Gujarati) | Gujarati |
| 7 | English | Latin |

---

## 🌾 Supported Crops

Wheat · Rice/Paddy · Maize · Sugarcane · Cotton · Soybean · Mustard · Tomato · Onion · Potato

---

## 📋 Government Schemes Covered

| Scheme | Benefit |
|--------|---------|
| PM-KISAN | ₹6,000/year income support |
| PMFBY | Crop insurance at 2% premium |
| KCC | Loan up to ₹3 lakh at 4% interest |
| Soil Health Card | Free soil testing |
| e-NAM | Online marketplace for crops |

---

## 🔑 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/webhook/whatsapp` | Twilio webhook receiver |
| GET | `/health` | Health check |
| GET | `/` | Landing page |
| GET | `/docs` | Swagger API documentation |

---

## 👥 Team

Built for **Amazon AI for Bharat Hackathon**

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
