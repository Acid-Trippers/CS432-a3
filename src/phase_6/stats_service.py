from typing import Dict, Any

from src.phase_5.sql_engine import SQLEngine


def get_stats_snapshot(
    sql_engine: SQLEngine | None,
    mongo_client: Any,
    mongo_db: Any,
) -> Dict[str, Any]:
    """Build a read-only backend health and counts snapshot for dashboard stats."""
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

    try:
        mongo_client.admin.command("ping")
        collection_counts = {
            col: mongo_db[col].count_documents({})
            for col in mongo_db.list_collection_names()
        }
        mongo_status = {
            "reachable": True,
            "collections": collection_counts,
            "total_records": sum(collection_counts.values()),
        }
    except Exception as exc:
        mongo_status = {
            "reachable": False,
            "collections": {},
            "total_records": 0,
            "error": str(exc),
        }

    return {"postgresql": sql_status, "mongodb": mongo_status}
