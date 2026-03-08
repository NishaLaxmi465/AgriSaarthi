# 🌾 AgriSaarthi

> **AI-powered agricultural advisory chatbot for Indian farmers via WhatsApp**
> Built on AWS (Bedrock + DynamoDB + S3 + Lambda) | 5 Languages | Zero app install

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green)](https://fastapi.tiangolo.com)
[![AWS](https://img.shields.io/badge/AWS-Bedrock%20%7C%20DynamoDB%20%7C%20S3-orange)](https://aws.amazon.com)
[![WhatsApp](https://img.shields.io/badge/Interface-WhatsApp-25D366)](https://whatsapp.com)

---

## 🎯 Problem
India has 146 million farmers, 86% are small/marginal (<2 hectares). They face:
- ❌ No real-time crop disease detection
- ❌ No market price visibility
- ❌ Unaware of government schemes worth ₹2.8 lakh crore
- ❌ Can't afford private agronomists (₹500-1000/visit)

## ✅ Solution
WhatsApp bot + Web App that provides expert advice in Hindi, Punjabi, Marathi, Telugu & English.

---

## 🏗️ Architecture

```
Farmer (WhatsApp)  ←→  Twilio  ←→  FastAPI (AWS)
                                         │
                          ┌──────────────┼──────────────┐
                          ▼              ▼              ▼
                    AWS Bedrock     DynamoDB        S3 (images)
                    Claude 3        (users,         7-day TTL
                    (LLM+Vision)    sessions)
```

## 🛠️ AWS Services
| Service | Purpose |
|---|---|
| **Amazon Bedrock** | Claude 3 Haiku (text) + Claude 3 Sonnet (pest detection vision) |
| **Amazon DynamoDB** | User profiles, conversation history |
| **Amazon S3** | Crop image storage (7-day lifecycle) |
| **AWS Lambda / App Runner** | Serverless hosting |
| **Amazon ElastiCache** | Session management + API caching |

---

## 🚀 Quick Start

```bash
git clone https://github.com/your-org/agrisaarthi.git
cd agrisaarthi
pip install -r requirements.txt
cp .env.example .env
# Add your AWS keys to .env
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000 → see the full web interface!
Open http://localhost:8000/docs → interactive API explorer

---

## 📁 Project Structure

```
agrisaarthi/
├── app/
│   ├── main.py                        # FastAPI app + frontend serving
│   ├── config.py                      # AWS & app settings
│   ├── handlers/
│   │   ├── webhook_handler.py         # WhatsApp webhook
│   │   └── health_handler.py          # Health checks
│   ├── services/
│   │   ├── message_processor.py       # Core routing logic
│   │   ├── bedrock_service.py         # AWS Bedrock (Claude 3)
│   │   ├── pest_detection_service.py  # Image analysis + S3
│   │   ├── session_manager.py         # ElastiCache sessions
│   │   ├── weather_service.py         # Weather + caching
│   │   ├── mandi_service.py           # Market prices
│   │   ├── scheme_service.py          # Govt schemes KB
│   │   └── twilio_service.py          # WhatsApp messaging
│   └── utils/
│       ├── hindi_responses.py         # Response templates
│       ├── twilio_validator.py        # Webhook security
│       └── logger.py                  # Structured logging
├── static/
│   └── index.html                     # Frontend (landing + chat demo)
├── infra/
│   └── cdk_stack.py                   # AWS CDK infrastructure
├── tests/
│   └── test_api.py                    # Test suite
├── .github/workflows/ci.yml           # CI/CD pipeline
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## 🌐 Languages Supported
- 🇮🇳 Hindi (हिंदी)
- 🇮🇳 Punjabi (ਪੰਜਾਬੀ)
- 🇮🇳 Marathi (मराठी)
- 🇮🇳 Telugu (తెలుగు)
- 🇬🇧 English

---

## 📄 License
MIT — free for farmers and agricultural organizations.
