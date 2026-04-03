# Docker Setup & SQL Pipeline Guide

## Prerequisites
- Docker Desktop installed and running
- Python 3.11+ with dependencies installed (`pip install -r requirements.txt`)

---

## Step 1 — Start Docker Containers

Ensure that the environment is running.

```powershell
docker compose up -d
```

This starts all 4 containers:
| Container | Role | Port |
|---|---|---|
| `cs432_postgres` | PostgreSQL database | 5432 |
| `cs432_mongo` | MongoDB database | 27017 |
| `cs432_api` | Faker data API | 8000 |
| `cs432_pipeline` | Python pipeline runner | — |

## Step 2 — Run the Initialisation Pipeline

Instead of running separate local scripts and CLI commands inside Docker, initialization is now entirely automated via the web Dashboard.

1. Ensure the Dashboard is running: `python dashboard/run.py`
2. Navigate to `http://localhost:8080/`
3. Enter your desired record count in the pipeline controls and click **Initialise Pipeline**.

This will automatically drop existing schemas, fetch data from the API, perform data analysis, and execute the SQL Pipeline to bulk insert the records effortlessly.

---

## Step 3 — Verify Data in PostgreSQL

### Connect to psql
```powershell
docker compose exec postgres psql -U admin -d cs432_db
```

### Useful commands (run one at a time inside psql)

List all tables:
```sql
\dt
```

View table schema:
```sql
\d main_records
```

Count total records:
```sql
SELECT COUNT(*) FROM main_records;
```

View first 5 records:
```sql
SELECT * FROM main_records LIMIT 5;
```

View specific columns:
```sql
SELECT record_id, username, city, subscription FROM main_records LIMIT 10;
```

Exit psql:
```sql
\q
```

---

## Step 5 — Check Pipeline Status

```powershell
docker compose exec pipeline python -m src.sql_pipeline status
```

---

## Fetching More Records

To ingest additional records into the existing database smoothly without wiping it, simply use the **Fetch Records** functionality natively in the Dashboard UI.

```http
POST http://localhost:8080/api/pipeline/fetch?count=500
```

The system will ingest the data, automatically run the classifier, and inject the records efficiently into PostgreSQL.

---

## Clearing All Records

### Option 1 — Wipe database only (keeps containers running)
```powershell
docker compose exec postgres psql -U admin -d cs432_db -c "TRUNCATE main_records CASCADE;"
```

### Option 2 — Full reset (wipes database volume and restarts everything)
```powershell
docker compose down -v
docker compose up -d
```

After a full reset, re-run Step 3 to re-insert data.

---

## Stopping Containers

Stop containers but keep data:
```powershell
docker compose down
```

Stop containers and wipe all data:
```powershell
docker compose down -v
```