from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Request

# Defer heavy import to avoid circular loads / early crashes if deps are broken
from src.phase_6.CRUD_runner import query_runner

router = APIRouter(prefix="/api/query", tags=["Query"])

@router.post("")
async def run_query(request: Request):
    """
    Accept a CRUD query as a JSON body and execute it through the pipeline
    orchestrator.

    Expects:
        {
            "operation": "READ" | "CREATE" | "UPDATE" | "DELETE",
            "entity":    "<table/collection name>",
            "filters":   { ... },
            "payload":   { ... }
        }
    """
    try:
        body: Dict[str, Any] = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Request body must be valid JSON.")

    if not body:
        raise HTTPException(status_code=400, detail="Empty query body.")

    required_keys = {"operation", "entity"}
    missing = required_keys - body.keys()
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required query fields: {', '.join(sorted(missing))}",
        )

    try:
        result = query_runner(query_dict=body)
        return {"status": "ok", "result": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
