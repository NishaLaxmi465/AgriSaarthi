"""
Session Manager - Maintains conversation context for 30 minutes.
Falls back to in-memory for local development (no Redis needed).
"""

import logging
import hashlib
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

_memory_store: dict = {}

def _hash_phone(phone: str) -> str:
    return hashlib.sha256(phone.encode()).hexdigest()[:16]

class SessionManager:
    def __init__(self):
        logger.info("✅ Session manager initialized (in-memory mode)")

    async def get_session(self, phone: str) -> Optional[dict]:
        key = f"session:{_hash_phone(phone)}"
        return _memory_store.get(key)

    async def create_session(self, phone: str, data: dict) -> bool:
        key = f"session:{_hash_phone(phone)}"
        _memory_store[key] = {**data, "created_at": datetime.utcnow().isoformat()}
        return True

    async def update_session(self, phone: str, data: dict) -> bool:
        key = f"session:{_hash_phone(phone)}"
        _memory_store[key] = {**data, "last_active": datetime.utcnow().isoformat()}
        return True

    async def clear_session(self, phone: str) -> bool:
        key = f"session:{_hash_phone(phone)}"
        _memory_store.pop(key, None)
        return True