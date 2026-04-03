# Autonomous Normalization & CRUD Engine Hybrid Database Framework

_(CS432 - Databases Assignment 2)_

This repository implements an intelligent, hybrid database framework that dynamically ingests, categorizes, normalizes, and routes JSON data across SQL (PostgreSQL) and NoSQL (MongoDB) databases. It completely orchestrates database schema creation, intelligent row/document structures, relational setups, and data mapping—without relying on static predefined schemas.

## Project Overview

The pipeline detects when data is highly recursive/nested and processes it accordingly:

- **SQL (PostgreSQL):** Resolves structured arrays and repeating entities into fully normalized tables, managing Primary and Foreign Keys automatically.
- **MongoDB:** Analyzes unstructured nested structures to intelligently decide if they should be embedded (smaller objects) or extracted into separate collections (frequently updated, large collections) and linked by references.
- **Query/CRUD Operations:** Exposes a unified API-like query runner that uses generated metadata to interact with both databases behind the scenes seamlessly.

## Project Structure

```text
CS432-a2/
│
├── data/              # Stores the temporary processing states (Buffer, Checkpoints, Metadata)
├── docs/              # Supplemental Architecture and Docker Guides
├── external/          # Contains mock external APIs (app.py) where data is fetched from
├── src/               # The Core Pipeline implementation
│   ├── phase_1_to_4/  # Data Profiling, Cleaning, Intelligent Classification & Metadata Gen
│   ├── phase_5/       # Storage Engine Execution (SQL generation, MongoDB collections)
│   ├── phase_6/       # The Database CRUD User Interface & Query Engine Execution
│   └── config.py      # Environment Constants
│
├── docker-compose.yml # Docker Services Definition (PostgreSQL, MongoDB)
├── main.py            # Main entrypoint to run the Database Pipeline Operations
├── requirements.txt   # Python Dependencies
└── starter.py         # Standalone utility to orchestrate Docker containers logic
```

## The Pipeline Architecture

The system completes its work in six distinct phases:

1. **Phase 1-2 (Ingestion & Schema Definition):** Fetches deeply nested JSON inputs from the mock API endpoint and cleans the datasets, stripping out missing or invalid structural issues.
2. **Phase 3 (Profiling & Analysis):** Recursively analyzes payload nodes tracking the density (datatypes vs lengths) and the complexity factor of each distinct array, string, and object entity.
3. **Phase 4 (Classification & Metadata):** Routes top-layer columns directly. Depending upon the structure, deeply nested complex entities are divided into relational tables (SQL) or documents/collections (MongoDB). It outputs an instruction manual (`metadata.json`) routing how properties will map locally. Unresolved anomalies wait in a pipeline `buffer`.
4. **Phase 5 (Database Engineering/Storage):** The respective SQL and MongoDB Engines deploy. Utilizing the metadata routing, tables are established holding strict normal forms and keys schemas. MongoDB stores complex fields via referential lookups or sub-document structures depending upon footprint rules.
5. **Phase 6 (Query Engine):** Handles user-supplied CRUD instructions (`query.json`) and translates properties using the Metadata map into raw parameterized queries sent asynchronously to Postgres and Mongo as required. Results are merged into a final coherent JSON response.

---

## How To Use The Repository

### 1. Clone the Repository

First, clone the repository to your local machine and navigate into the directory:

```powershell
git clone https://github.com/Acid-Trippers/CS432-a2
cd CS432-a2
```

### 2. Requirements Setup

Ensure you have the following installed on your machine:

- **Python 3.8+**
- **Docker Desktop**
- **Pip** dependencies:
  ```powershell
  pip install -r requirements.txt
  ```

### 3. Booting Up the Environment

Start the PostgreSQL, MongoDB instances, and network bridge using Docker Compose:

```powershell
docker-compose up -d
```

### 4. Running the Pipeline & Dashboard

The pipeline orchestration and CRUD operations are now hosted natively within a FastAPI backend dashboard. 

Start the dashboard server:

```powershell
python dashboard/run.py
```

This launches the dashboard on **[http://localhost:8080](http://localhost:8080)**.
_Port 8080 was chosen to avoid conflicts with existing services (8000 = data generator API, 5432 = PostgreSQL, 27017 = MongoDB)._

### 5. Orchestrating the Platform via the Dashboard

Navigate to the Web UI to interact with the databases. The backend exposes endpoints that previously ran as CLI scripts:

- **Initialise (`POST /api/pipeline/initialise`)**: Wipes databases, establishes normalized SQL tables, creates Mongo clusters, and ingests/routes fresh data (Phase 1-5).
- **Fetch (`POST /api/pipeline/fetch`)**: Incrementally ingests additional records, adapting dynamic schemas, updating intelligence, and routing appending data.
- **Query (`POST /api/query`)**: Run read, insert, update, or delete records globally across databases, directly from the Dashboard JSON Editor. The system matches properties with the generated `metadata.json` and routes sub-queries directly to the correct database layer concurrently.

### 7. Running the Dashboard

The web dashboard provides a browser-based interface for monitoring session status and running CRUD queries without using the CLI.

> **Prerequisite:** The Docker services must be running before starting the dashboard. You can initialize the database schema directly from the dashboard UI.

```powershell
python dashboard/run.py
```

This launches the dashboard on **[http://localhost:8080](http://localhost:8080)** via uvicorn.  
Port 8080 was chosen to avoid conflicts with existing services (8000 = data generator API, 5432 = PostgreSQL, 27017 = MongoDB).

The dashboard calls the same `query_runner()` logic used by the CLI — there is no separate query path.

---

## Documentation & Resources

For detailed insights into specific components of the framework, refer to the following guide documents available in the `docs/` folder:

- **[SQL Engine Architecture](docs/SQL_ENGINE_ARCHITECTURE.md)**: Details on the automated normalization techniques, key extraction, and repeating entity algorithms.
- **[Docker Setup & Usage Guide](docs/DOCKER_GUIDE.md)**: A complete technical breakdown for administrating the customized PostgreSQL and MongoDB containers.
- **[SQL Pipeline Guide](docs/sql_pipeline_guide.md)**: Learnings and rules backing the `src/phase_5/sql_pipeline.py`.
- **[Assignment 2 Guidelines](docs/assignment-2-guidelines.md)**: The original curriculum requirements from the IIT Gandhinagar course.

---

_Built incrementally mapping to Assignment Guidelines for Course Project CS 432._
