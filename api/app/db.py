"""MongoDB connection (async via motor)."""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

_client: AsyncIOMotorClient | None = None


def get_db() -> AsyncIOMotorDatabase:
    """Return a singleton Motor database handle."""
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongo_uri)
    return _client[settings.mongo_db]
