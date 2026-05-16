from motor.motor_asyncio import AsyncIOMotorClient
import os

_client: AsyncIOMotorClient = None
_db = None


async def connect_db():
    global _client, _db
    url = os.getenv("MONGO_URI") or os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    db_name = os.getenv("DATABASE_NAME", "memphis_meat_scout")
    _client = AsyncIOMotorClient(url, serverSelectionTimeoutMS=5000)
    _db = _client[db_name]
    try:
        await _db.command("ping")
        print(f"✓ Connected to MongoDB at {url}")
    except Exception as e:
        print(f"⚠ MongoDB not reachable at {url}: {e}")
        print("  Start MongoDB and restart the server.")


async def close_db():
    global _client
    if _client:
        _client.close()


def get_db():
    return _db
