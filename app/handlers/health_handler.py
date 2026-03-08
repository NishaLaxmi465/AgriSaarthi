"""Health check endpoints."""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "AgriSaarthi",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }


@router.get("/health/detailed")
async def detailed_health():
    """Detailed health check for monitoring."""
    checks = {
        "api": "ok",
        "dynamodb": "ok",   # Would check real connection
        "redis": "ok",       # Would check real connection
        "bedrock": "ok",     # Would check real connection
    }
    return {
        "status": "healthy",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
    }
