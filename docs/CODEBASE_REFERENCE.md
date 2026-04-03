# Codebase Reference

## Global Facts

### File Paths
- `data/initial_schema.json`: User-defined structural rules for ingestion.
- `data/received_data.json`: Raw requested records from the fake API.
- `data/cleaned_data.json`: Validated/cleansed records ready for routing.
- `data/buffer.json`: Quarantine for fields not matching schemas during cleaning.
- `data/analyzed_schema.json`: Statistical profiles outputted by the analyzer.
- `data/metadata.json`: The core playbook mapping field names to locations (SQL/MONGO/UNKNOWN) and attributes.
- `data/sql_data.json`: Horizontally sharded payload destined for SQL.
- `data/mongo_data.json`: Payload sharded for MongoDB.
- `data/unknown_data.json`: Overflow storage for unstructured/sparse data without an engine.
- `data/data_till_now_sql.json`: Archived records successfully inserted into SQL.
- `data/query.json`: Saved user operations for CRUD queries.
- `data/query_output.json`: Output results from CRUD runs.
- `data/pipeline_checkpoint.json` / `data/checkpoint.json`: Tracks pipeline execution states.
- `data/counter.txt`: Persists the global record count for incremental runs.

### Environment Variables & Defaults
- `POSTGRES_URI`: `postgresql://admin:secret@localhost:5432/cs432_db`
- `MONGO_URI`: `mongodb://admin:secret@localhost:27017/`
- `MONGO_DB_NAME`: `cs432_db` (overridden in project_config.py to `hybrid_db` sometimes)
- `API_HOST`: `http://127.0.0.1:8000`

### Ports in Use
- **8000**: External FastAPI Generator
- **5433**: PostgreSQL (Host mapping -> 5432 container)
- **27017**: MongoDB

### Pipeline Entry Points (`pipeline/orchestrator.py` & Dashboard)
1. **`initialise` (`POST /api/pipeline/initialise`)**: Resets the environment by deleting all data files and dropping database schemas. Fetches an initial batch of records, runs the cleaner/analyzer, builds metadata, classifies fields, and executes data routing into SQL and MongoDB sequentially.
2. **`fetch` (`POST /api/pipeline/fetch`)**: Runs incrementally. Uses the existing metadata. Fetches raw data, processes it in memory, updates intelligence (metadata and classification via weighted evolution), routes the new batches, and upserts them into the respective databases without wiping existing tables.
3. **`query` (`POST /api/query`)**: Run natively from the Dashboard UI. Uses `CRUD_json_reader` to capture standard CRUD actions (as JSON) and hands them to `CRUD_runner` to execute read/write operations spanning the split backend.

### The `record_id` Contract
The `record_id` is an integer assigned sequentially. During pipeline runs, `cleaner.py` injects `record_id` based on offset tracking (via `counter.txt`). For `CREATE` queries, a new id is given from the counter.
This ID uniquely identifies an entity across shards: it becomes the Primary Key inside SQL tables, the `_id` field within MongoDB documents, and allows the `CRUD_operations.py` layer to execute distributed joins during `READ` commands.

### Query Flow (`query.json` -> `query_runner()` -> `CRUD_operations.py`)
1. **Input**: User creates or edits `query.json` comprising `operation`, `entity`, `filters`, and `payload`.
2. **Parsing**: `CRUD_json_reader.py` validates the query shape before execution.
3. **Analysis**: `CRUD_runner.py` cross-references the requested fields with `metadata.json` to map out which subset belongs to SQL, MongoDB, or the Unknown bucket.
4. **Execution (`CRUD_operations.py`)**:
    - **CREATE**: Distributes fields to backends. All backends receive the `record_id` to maintain synchronization, even if empty otherwise.
    - **READ / UPDATE / DELETE**: Executes in a Two-Phase approach. Phase 1 finds `record_id` lists matching the filter criteria per backend. Phase 2 fetches or mutates records using those aggregated ID matches, followed by a final merge phase utilizing `record_id` as the cross-engine join key.

### Engine Initialization & State
- **SQL Engine (`SQLEngine`)**: Operates functionally from state generated dynamically via `metadata.json`. It initiates the `SQLSchemaBuilder` up-front, reading root-level fields, arrays, and nested dictionaries destined for SQL. It procedurally crafts native SQLAlchemy ORM classes out of the metadata map, assigning a 1NF constraint by flattening objects.
- **MongoDB Engine (`mongo_engine.py`)**: Operates statelessly. Resolves documents using a recursive graph walking function that categorizes components as "embed" or "reference", saving references as linked sub-collections and the rest inside the `main_records` collection.

### Known Limitations/Gaps
- The SQL engine strictly relies on wiping tables during `initialise()`. Smooth schema evolution (e.g. `ALTER TABLE`) is bypassed for a drop/create pattern if schemas fundamentally shift.
- The `unknown` data sink is merely a JSON append operation to `data/unknown_data.json` instead of utilizing a legitimate triple-store or JSONB column for unmatched fields.
- `CRUD_operations.py` performs rudimentary filtering—if a filter applies to properties in a nested SQL array/table, the cross-backend `READ` join logic falls back on rudimentary logic that does not natively join deep SQL structures dynamically. 

---

## File By File Breakdown

### Root Directory 

**`dashboard/run.py` & `pipeline/orchestrator.py`**
Orchestrates the entire hybrid database pipeline natively via a FastAPI web dashboard interface. It exposes endpoints to trigger `initialise`, `fetch`, and `query` operations without relying on a legacy CLI.
- **Key Functions (`orchestrator.py`)**: `process_in_memory()`, `clean_databases()`, `initialise()`, `fetch()`

**`project_config.py`** & **`src/config.py`**
Store all centralized URIs, hostnames, passwords, and file paths used during extraction and ingestion loops.

**`starter.py`**
Bootstrapping script for managing the Docker lifecycle (starts Docker if offline) to run Docker Compose smoothly and poll until all services are green.
- **Key Functions**: `wait_for_port()`, `start()`, `end()`

**`Dockerfile` / `docker-compose.yml`**
Containers setup: PostgreSQL, MongoDB, the Python API (`external/app.py`), and a master Python pipeline container sharing the `/data` volume.

**`external/app.py`**
A FastAPI application returning procedurally generated raw JSON user data using Faker. Evaluates randomized omission probabilities for nested strings to mimic hybrid schema variability.
- **Key Functions**: `get_nested_metadata()`, `generate_record()`
- **Endpoints**: `GET /` and `GET /record/{count}`

### Phase 1 to 4 (`src/phase_1_to_4/`)

**`00_schema_definition.py`**
Forces a user to validate or paste a boilerplate JSON topology rulebook to govern the system structure.
- **Key Functions**: `validate_structure()`, `get_pasted_json()`

**`01_ingestion.py`**
Asynchronously streams JSON payload datasets from the FastAPI endpoint into memory. Injects ingestion timestamps and persists a local global offset counter.
- **Key Functions**: `get_counter()`, `fetch_data()`

**`02_cleaner.py`**
Normalizes incoming semi-structured data by matching fuzzy keys against the schema template. Unmatched fields are saved into a buffer instead of dropping them, preventing data loss.
- **Key Functions/Classes**: `DataCleaner`, `DataCleaner.clean_recursive()`
- **Writes To**: `cleaned_data.json`, `buffer.json`

**`03_analyzer.py`**
Walks the cleaned data sequentially to discover properties: calculates sparsity, depth, array typing, format masks, and dominant value casting. Detects Primary Key candidates.
- **Key Functions/Classes**: `DataAnalyzer`, `DataAnalyzer._analyze_recursive()`, `run_data_analysis()`
- **Writes To**: `analyzed_schema.json`

**`04_metadata_builder.py`**
Merges user constraints with empirically collected metrics to generate a flat document outlining every encountered property constraint. Determines if a sparse unmapped field goes into probation ("discovered buffer").
- **Key Functions**: `merge_metadata()`
- **Writes To**: `metadata.json`

**`05_classifier.py`**
Runs two passes against `metadata.json` elements. Pass 1: checks metrics against type stability thresholds to choose SQL. Pass 2: Overrides classification if internal nesting levels break the 1NF pattern, exiling structures strictly to Mongo.
- **Key Functions/Classes**: `SchemaClassifier`, `SchemaClassifier.classify_statistically()`, `runPipeline()`

**`06_router.py`**
Reads the globally clean outputs and fragments individual fields inside the dictionary into the respective engine pipelines based strictly on the classified playbook instructions.
- **Key Functions**: `_build_field_routes()`, `route_data()`
- **Writes To**: `sql_data.json`, `mongo_data.json`, `unknown_data.json`

### Phase 5 (`src/phase_5/`)

**`sql_schema_definer.py`**
Interrogates the `metadata.json` elements tagged for SQL, dynamically constructing SQLAlchemy mappings. Normalizes objects and lists into distinct tables mapping foreign keys back to the main ID.
- **Key Functions/Classes**: `SchemaAnalyzer`, `SQLSchemaBuilder`, `SQLSchemaBuilder._create_models()`

**`sql_engine.py`**
Primary entry point for inserting into the crafted mapped tables via SQLAlchemy interactions. Flushes rows out of `sql_data.json`.
- **Key Functions/Classes**: `DataNormalizer`, `SQLEngine`, `SQLEngine.insert_record()`, `SQLEngine.bulk_insert_from_file()`

**`sql_pipeline.py`**
Wrapper linking initialization, insertion, and archiving together to orchestrate the entire SQL flow step cleanly and reporting states.
- **Key Functions**: `archive_processed_data()`, `run_sql_pipeline()`

**`mongo_engine.py`**
Ingests unstructured datasets directly using PyMongo. Uses recursion to determine dynamically matched "embed" versus "reference" strategies based on nested depth mapping metrics.
- **Key Functions**: `determineMongoStrategy()`, `processNode()`, `processMongoData()`

### Phase 6 (`src/phase_6/`)

**`CRUD_json_reader.py`**
An interactive gatekeeper ensuring a generated CRUD request properly maps entity, operation, filters, and payload. Saves results iteratively.
- **Key Functions**: `validate_structure()`, `store_query_to_json()`
- **Reads/Writes**: `query.json`

**`CRUD_runner.py`**
Evaluates what databases should be polled based on metadata field classifications and delegates it to the operations controller.
- **Key Functions**: `query_parser()`, `analyze_query_databases()`, `query_runner()`

**`CRUD_operations.py`**
Heavy algorithmic logic that implements isolated filtering, querying, and updating per persistence layer using a two-pass mechanism (collecting global ids matching conditions, then fetching records).
- **Key Functions**: `merge_results_by_record_id()`, `read_operation()`, `create_operation()`, `update_operation()`, `delete_operation()`
