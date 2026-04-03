"""
pipeline/orchestrator.py
========================
Pure Python module containing the core orchestration logic for the hybrid database pipeline.
This replaces the old CLI-based `main.py` script. It exposes `initialise()` and `fetch()`
as callable functions that can be invoked natively from FastAPI endpoints or any other
Python code.

Dependencies:
    - src.phase_1_to_4.* (cleaning, analysis, metadata, routing)
    - src.phase_5.* (SQL & Mongo engines)
"""

import os
import json
import time
import shutil
import asyncio
import logging

from src.config import *

# Suppress noisy logs from SQLAlchemy and pymongo
logging.getLogger('sqlalchemy').setLevel(logging.CRITICAL)
logging.getLogger('pymongo').setLevel(logging.CRITICAL)
logging.getLogger('src.phase_5.sql_engine').setLevel(logging.CRITICAL)

import importlib

schema_definition = importlib.import_module("src.phase_1_to_4.00_schema_definition")
ingestion = importlib.import_module("src.phase_1_to_4.01_ingestion")
cleaner_mod = importlib.import_module("src.phase_1_to_4.02_cleaner")
analyzer_mod = importlib.import_module("src.phase_1_to_4.03_analyzer")
metadata_builder = importlib.import_module("src.phase_1_to_4.04_metadata_builder")
classifier = importlib.import_module("src.phase_1_to_4.05_classifier")
data_router = importlib.import_module("src.phase_1_to_4.06_router")
import src.phase_5.sql_schema_definer as sql_schema_definer
import src.phase_5.sql_engine as sql_engine
import src.phase_5.sql_pipeline as sql_pipeline
import src.phase_5.mongo_engine as mongo_engine


def save_checkpoint(filepath: str, data: list | dict, append: bool = False):
    """Saves data to a JSON checkpoint, optionally appending to existing lists."""
    if append and os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                content = f.read().strip()
                existing = json.loads(content) if content else []
        except (json.JSONDecodeError, IOError):
            existing = []
            
        if isinstance(existing, list) and isinstance(data, list):
            data = existing + data
            
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)


def process_in_memory(raw_records: list, is_fetch: bool = False) -> list:
    """Handles the sequential processing of data records in memory."""
    print("[*] Cleaning Data...")
    
    # helper to get offset
    offset = 0
    if os.path.exists(COUNTER_FILE):
        try:
            with open(COUNTER_FILE, 'r') as f:
                offset = int(f.read().strip() or 0) - len(raw_records)
        except Exception:
            pass

    cleaner = cleaner_mod.DataCleaner()
    cleaned_records = []
    
    for i, record in enumerate(raw_records):
        ref_id = record.get("id", record.get("_id", f"idx_{time.time()}_{i}"))
        cleaned_node = cleaner.clean_recursive(record, cleaner.schema, ref_id)
        cleaned_node["record_id"] = offset + i 
        cleaned_records.append(cleaned_node)
    
    # Save the cleaned data
    save_checkpoint(CLEANED_DATA_FILE, cleaned_records, append=is_fetch)
    save_checkpoint(BUFFER_FILE, cleaner.buffer, append=is_fetch)

    # Flush raw ingestion file after successful cleaning
    if raw_records:
        with open(RECEIVED_DATA_FILE, 'w') as f:
            json.dump([], f)
        print("[*] Received_data flushed.")

    print("[*] Profiling Data...")
    analyzer = analyzer_mod.DataAnalyzer()
    analyzer.analyze_records(cleaned_records)
    analyzer.save_analysis(ANALYZED_SCHEMA_FILE)
    
    new_total = offset + len(raw_records)
    with open(COUNTER_FILE, 'w') as f:
        f.write(str(new_total))
        
    return cleaned_records


def clean_databases():
    """Drops all SQL tables and the MongoDB database for a fresh start."""
    print("[*] Clearing databases for a clean slate...")
    
    # 1. Clear MongoDB
    try:
        from pymongo import MongoClient
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        client.server_info()
        client.drop_database(MONGO_DB_NAME)
        print(f"[+] MongoDB '{MONGO_DB_NAME}' database dropped.")
    except Exception as e:
        print(f"[!] Warning: MongoDB not reachable, skipping: {e}")

    # 2. Clear SQL
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 2})
        with engine.connect() as conn:
            conn.execute(text("SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = current_database() AND pid <> pg_backend_pid();"))
            conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
            conn.commit()
        print("[+] SQL database tables dropped.")
    except Exception as e:
        print(f"[!] Warning: PostgreSQL not reachable, skipping: {e}")


def initialise(count: int = 1000) -> dict:
    """
    Resets the environment, fetches initial records, builds intelligence, and routes them.
    """
    files_to_clean = [
        COUNTER_FILE, RECEIVED_DATA_FILE, CLEANED_DATA_FILE, 
        BUFFER_FILE, ANALYZED_SCHEMA_FILE, METADATA_FILE, 
        SQL_DATA_FILE, MONGO_DATA_FILE, QUERY_FILE, CHECKPOINT_FILE
    ]
    
    for f in files_to_clean:
        if os.path.exists(f):
            if os.path.isfile(f):
                os.remove(f)
            else:
                shutil.rmtree(f)
                
    with open(COUNTER_FILE, 'w') as f:
        f.write("0")
        
    print("\n[!] Environment reset.")
    clean_databases()

    print("[*] Running Schema Definition...")
    schema_definition.main()
    
    print(f"[*] Fetching Data ({count} records)...")
    raw_records = asyncio.run(ingestion.fetch_data(count))
    save_checkpoint(RECEIVED_DATA_FILE, raw_records, append=False)

    print("[*] Processed In-Memory. (Cleaning + Profiling)")
    process_in_memory(raw_records, is_fetch=False)

    print("[*] Building Metadata...")
    metadata_builder.merge_metadata()

    print("[*] Classifying Schema...")
    classifier.run_classification(verbose=True)
    
    print("[*] Routing Data...")
    data_router.route_data()
    
    print("[*] SQL Pipeline...")
    engine_sqll = sql_engine.SQLEngine()
    sql_pipeline.run_sql_pipeline(engine_sqll)

    print("[*] MongoDB Pipeline...")
    mongo_engine.runMongoEngine()
    
    return {"status": "success", "message": f"Initialised {count} records."}


def fetch(count: int = 100) -> dict:
    """
    Incrementally fetches more records, adapts intelligence, and routes data.
    """
    if not os.path.exists(METADATA_FILE):
        raise FileNotFoundError("No metadata found. Run `initialise` first.")

    batch_size = 100
    remaining = count
    total_processed = 0
    
    print(f"[*] Starting Batch-Fetch for {count} records...")

    while remaining > 0:
        current_batch = min(remaining, batch_size)
        
        n_old = 0
        if os.path.exists(COUNTER_FILE):
            try:
                with open(COUNTER_FILE, 'r') as f:
                    n_old = int(f.read().strip() or 0)
            except Exception:
                pass

        print(f"[*] Fetching chunk of {current_batch}...")
        raw_records = asyncio.run(ingestion.fetch_data(current_batch))
        
        # Clean data into memory, update counter/schemas
        process_in_memory(raw_records, is_fetch=True)
        
        # Update intelligence
        metadata_builder.merge_metadata(is_update=True, n_old=n_old, n_new=len(raw_records))
        classifier.run_classification(verbose=False)

        print("[*] Routing Data...")
        batch_stats = data_router.route_data()
        if batch_stats:
            print(f"    >>> Batch Success: {batch_stats['sql']} records to SQL, {batch_stats['mongo']} to Mongo.")
        
        print("[*] SQL Pipeline...")
        engine_sqll = sql_engine.SQLEngine()
        sql_pipeline.run_sql_pipeline(engine_sqll)

        print("[*] MongoDB Pipeline...")
        mongo_engine.runMongoEngine()

        remaining -= current_batch
        total_processed += current_batch
        print(f"[+] Chunk processed. Total global records: {n_old + current_batch}")

    return {"status": "success", "message": f"Fetched {total_processed} new records."}
