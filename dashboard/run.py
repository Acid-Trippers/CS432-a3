"""
dashboard/run.py
================
Entry point for the hybrid-DB web dashboard.

Usage
-----
    python dashboard/run.py

The dashboard is served on port 8080 so it does not conflict with any
existing services in the pipeline:
    - 8000  →  External FastAPI Generator (external/app.py)
    - 5432  →  PostgreSQL
    - 27017 →  MongoDB
"""

import os
import sys
import uvicorn

if __name__ == "__main__":
    # Ensure the root project directory is on the python path for uvicorn workers
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
        
    os.environ["PYTHONPATH"] = root_dir + os.pathsep + os.environ.get("PYTHONPATH", "")

    uvicorn.run(
        "dashboard.app:app",   # FastAPI instance inside dashboard/app.py
        host="0.0.0.0",
        port=8080,
        reload=True,           # Convenient during development
    )
