"""
FitQuest Database and Persistence Module
"""

from backend.src.db.mongo_client import get_db, is_mongo_connected, init_mongo

__all__ = ["get_db", "is_mongo_connected", "init_mongo"]
