"""
dashboard/app.py
================
FastAPI web dashboard for the hybrid database pipeline.

Run from project root:
    python dashboard/run.py

Endpoints:
    GET  /                 — renders the main dashboard page
    GET  /api/stats        — DB reachability and counts (dashboard/routers/stats.py)
    POST /api/query        — execute CRUD operations (dashboard/routers/query.py)
    POST /api/pipeline/... — trigger initialise/fetch (dashboard/routers/pipeline.py)
"""

import sys
import os
from contextlib import asynccontextmanager

# Ensure the project root is on sys.path so src.* imports work
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient

from src.config import DATABASE_URL, MONGO_URI, MONGO_DB_NAME
from src.phase_5.sql_engine import SQLEngine

# Import Modular Routers
from dashboard.routers import stats, query, pipeline

# ---------------------------------------------------------------------------
# Lifespan: initialize heavy resources once at startup, tear down on shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Start-up:
    - Attempt to initialize SQLEngine. On failure, store None.
    - Create MongoClient (lazy).

    Shutdown:
    - Close SQL session and Mongo client cleanly.
    """
    # --- SQL ---
    sql_engine = None
    try:
        sql_engine = SQLEngine(database_url=DATABASE_URL)
        initialized = sql_engine.initialize()
        if not initialized:
            sql_engine = None  # None = unreachable
    except Exception as exc:
        print(f"[dashboard] SQL Engine init failed: {exc}")
        sql_engine = None

    # --- MongoDB ---
    mongo_client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=2000,
        connectTimeoutMS=2000,
    )

    app.state.sql_engine = sql_engine
    app.state.mongo_client = mongo_client
    app.state.mongo_db_name = MONGO_DB_NAME

    yield  # application runs here

    # Shutdown
    if sql_engine is not None:
        sql_engine.close()
    mongo_client.close()


# ---------------------------------------------------------------------------
# App Configuration & Templates
# ---------------------------------------------------------------------------

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

app = FastAPI(title="Hybrid DB Pipeline Dashboard", lifespan=lifespan)

# Register Sub-Routers
app.include_router(stats.router)
app.include_router(query.router)
app.include_router(pipeline.router)


# ---------------------------------------------------------------------------
# Base Route
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main dashboard HTML page."""
    return templates.TemplateResponse("index.html", {"request": request})
