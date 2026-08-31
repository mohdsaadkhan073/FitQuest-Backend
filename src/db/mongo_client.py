"""
FitQuest MongoDB Client Connection Manager
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load env variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "fitquest_db")

_client = None
_db = None
_is_connected = False


def init_mongo() -> bool:
    """Initialize MongoDB connection with short timeout fallback."""
    global _client, _db, _is_connected
    if _is_connected and _db is not None:
        return True

    try:
        import pymongo
        _client = pymongo.MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=2000,
            connectTimeoutMS=2000,
            socketTimeoutMS=2000
        )
        _db = _client[MONGO_DB_NAME]
        _is_connected = True
        return True
    except Exception as e:
        _is_connected = False
        _client = None
        _db = None
        print(f"[MongoDB] Notice: MongoDB not connected ({e}). Operating in resilient In-Memory mode.")
        return False


def get_db():
    """Get active MongoDB database or None if not connected."""
    global _db, _is_connected
    if not _is_connected and _db is None:
        init_mongo()
    return _db


def is_mongo_connected() -> bool:
    """Check if MongoDB is currently available."""
    global _is_connected
    return _is_connected
