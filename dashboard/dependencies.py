from fastapi import Request
from pymongo import MongoClient
from pymongo.database import Database
from src.phase_5.sql_engine import SQLEngine

def get_sql_engine(request: Request) -> SQLEngine | None:
    """Dependency to get the lifespan-initialized SQLEngine."""
    return request.app.state.sql_engine

def get_mongo_client(request: Request) -> MongoClient:
    """Dependency to get the MongoDB client."""
    return request.app.state.mongo_client

def get_mongo_db(request: Request) -> Database:
    """Dependency to get the MongoDB database directly."""
    client = request.app.state.mongo_client
    return client[request.app.state.mongo_db_name]
