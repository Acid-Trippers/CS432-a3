from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel

import pipeline.orchestrator as orchestrator
from src.config import DATABASE_URL
from src.phase_5.sql_engine import SQLEngine

router = APIRouter(prefix="/api/pipeline", tags=["Pipeline"])

class InitialiseResponse(BaseModel):
    status: str
    message: str

class FetchResponse(BaseModel):
    status: str
    message: str

@router.post("/initialise", response_model=InitialiseResponse)
def trigger_initialise(request: Request, count: int = 1000):
    """
    Resets the database environment, fetches initial records, builds intelligence schemas,
    and runs the data routing pipeline from a fresh state.
    """
    try:
        # Close global DB connection to prevent DROP SCHEMA from hanging
        if getattr(request.app.state, "sql_engine", None):
            request.app.state.sql_engine.close()
            request.app.state.sql_engine = None

        # Calls the synchronous orchestrator method natively
        result = orchestrator.initialise(count)

        # Re-initialize the engine since we recreate the schema
        sql_engine = SQLEngine(database_url=DATABASE_URL)
        if sql_engine.initialize():
            request.app.state.sql_engine = sql_engine

        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.post("/fetch", response_model=FetchResponse)
def trigger_fetch(count: int = 100):
    """
    Incrementally fetches more records, adapts dynamic schemas, and routes data.
    Requires metadata.json from a prior initialise run.
    """
    try:
        result = orchestrator.fetch(count)
        return result
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
