"""
AgriSaarthi - AI-Powered Agricultural Advisory Chatbot
WhatsApp-based assistant for Indian farmers
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import logging
import os

from app.handlers.webhook_handler import router as webhook_router
from app.handlers.health_handler import router as health_router
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🌾 AgriSaarthi starting up...")
    yield
    logger.info("🌾 AgriSaarthi shutting down...")


app = FastAPI(
    title="AgriSaarthi API",
    description="AI-powered agricultural advisory for Indian farmers via WhatsApp",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(webhook_router, prefix="/api/v1")
app.include_router(health_router)


@app.get("/")
async def root():
    """Serve the frontend homepage."""
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return {
        "service": "AgriSaarthi",
        "version": "1.0.0",
        "description": "AI Agricultural Advisory for Indian Farmers",
        "status": "running",
    }
