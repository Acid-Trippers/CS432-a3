from typing import Dict
from fastapi import APIRouter, Depends
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ServerSelectionTimeoutError

from src.phase_5.sql_engine import SQLEngine
from dashboard.dependencies import get_sql_engine, get_mongo_client, get_mongo_db

router = APIRouter(prefix="/api/stats", tags=["Stats"])

@router.get("")
async def get_stats(
    sql_engine: SQLEngine | None = Depends(get_sql_engine),
    mongo_client: MongoClient = Depends(get_mongo_client),
    mongo_db: Database = Depends(get_mongo_db)
):
    """
    Return record counts and reachability status for PostgreSQL and MongoDB.
    """
    # --- PostgreSQL ---
    if sql_engine is None:
        sql_status = {
            "reachable": False,
            "tables": {},
            "total_records": 0,
        }
    else:
        try:
            table_counts: Dict[str, int] = sql_engine.get_database_stats()
            sql_status = {
                "reachable": True,
                "tables": table_counts,
                "total_records": sum(table_counts.values()),
            }
        except Exception as exc:
            sql_status = {
                "reachable": False,
                "tables": {},
                "total_records": 0,
                "error": str(exc),
            }

    # --- MongoDB ---
    try:
        mongo_client.admin.command("ping")  # fast liveness check
        collection_counts = {
            col: mongo_db[col].count_documents({})
            for col in mongo_db.list_collection_names()
        }
        mongo_status = {
            "reachable": True,
            "collections": collection_counts,
            "total_records": sum(collection_counts.values()),
        }
    except (ServerSelectionTimeoutError, Exception) as exc:
        mongo_status = {
            "reachable": False,
            "collections": {},
            "total_records": 0,
            "error": str(exc),
        }

    return {"postgresql": sql_status, "mongodb": mongo_status}
