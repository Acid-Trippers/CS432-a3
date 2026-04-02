# Project Guidelines

## Architecture
- This project is a hybrid SQL + Mongo pipeline exposed through a FastAPI dashboard.
- Keep layering clear:
  - Dashboard API/UI layer: dashboard/
  - Pipeline orchestration: pipeline/orchestrator.py
  - Data processing phases 1-4: src/phase_1_to_4/
  - Storage engines and schema logic: src/phase_5/
  - CRUD/query merge logic: src/phase_6/
- Assignment 3 requirement: present logical entities only. Do not expose SQL table names, Mongo collection names, or storage strategy details in user-facing dashboard responses.

## Build And Test
- Install dependencies: pip install -r requirements.txt
- Start infra: docker-compose up -d
- Start dashboard: python dashboard/run.py
- Basic checks:
  - python test.py
  - python test_db.py
- For dashboard/API changes, verify endpoints still behave as expected:
  - POST /api/pipeline/initialise
  - POST /api/pipeline/fetch
  - POST /api/query

## Conventions
- Use metadata-driven routing and query generation, not hardcoded backend mappings.
- Preserve the record_id cross-backend contract for joins/merge.
- Prefer minimal, targeted changes over broad rewrites because pipeline phases depend on shared JSON artifacts under data/.
- Use deferred imports in routers when needed to avoid circular import issues.
- Keep code comments brief and only for non-obvious logic.

## Docs
- System map and file-level behavior: docs/CODEBASE_REFERENCE.md
- SQL normalization details: docs/SQL_ENGINE_ARCHITECTURE.md
- Container setup and troubleshooting: docs/DOCKER_GUIDE.md
- Assignment requirements: docs/assignment-2-guidelines.md and docs/assignment-3-guidelines.md
