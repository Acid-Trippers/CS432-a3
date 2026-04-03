from fastapi import APIRouter, Depends
from pymongo import MongoClient
from pymongo.database import Database

from src.phase_5.sql_engine import SQLEngine
from src.phase_6.stats_service import get_stats_snapshot
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
    return get_stats_snapshot(sql_engine, mongo_client, mongo_db)
