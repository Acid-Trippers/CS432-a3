**What we need to build — in order:**

**In order, here's what we need to complete for A3:**
1. Transaction Coordination first — this is the most critical change and affects existing code. Every CRUD operation needs to be wrapped in a logical transaction so if SQL succeeds but Mongo fails, SQL rolls back. This modifies CRUD_operations.py.
2. Dashboard backend second — dashboard_server.py with FastAPI endpoints that pull data from both databases and serve it. This needs transaction coordination to already be solid before building on top of it.
3. React frontend third — build the UI that talks to the dashboard backend. This is purely frontend work and depends on the backend endpoints being ready.
4. ACID experiments last — write test scripts that prove atomicity, consistency, isolation, durability. These test the transaction coordination we built in step 1.

**Stage 1 — Transaction Coordination** (modify existing CRUD)
- Wrap SQL + Mongo operations in a single logical transaction
- If SQL succeeds but Mongo fails → rollback SQL
- If Mongo succeeds but SQL fails → rollback Mongo
- This is a change to `CRUD_operations.py`

**Stage 2 — Dashboard**
- A web-based dashboard using FastAPI + React Frontend
- Shows: active session info, all records as logical entities, query submission form, query results
- No backend details exposed — just field names and values
- Lives in a new `dashboard/` folder

**Stage 3 — ACID Experiments**
- Python test scripts that simulate failures and prove ACID properties
- Lives in a new `tests/` folder

---

**Folder structure for a3:**
```
CS432-a3/
├── src/
│   ├── phase_1_to_4/     (unchanged from a2)
│   ├── phase_5/          (unchanged from a2)
│   ├── phase_6/          (CRUD_operations.py updated with transactions)
│   └── phase_7/          (NEW — dashboard)
│       ├── dashboard.py  (FastAPI dashboard server)
│       └── templates/    (HTML templates)
├── tests/                (NEW — ACID experiments)
│   ├── test_atomicity.py
│   ├── test_consistency.py
│   ├── test_isolation.py
│   └── test_durability.py
├── main.py               (add dashboard command)
├── starter.py            (unchanged)
└── requirements.txt      (add jinja2)

and some more stuff along with some changes.