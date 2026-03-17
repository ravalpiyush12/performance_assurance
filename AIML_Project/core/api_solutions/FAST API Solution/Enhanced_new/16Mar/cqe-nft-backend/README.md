# CQE NFT Platform — Backend Package

## What's in this package

```
cqe-nft-backend/
├── sql/
│   └── 01_nft_platform_tables.sql      ← Run this in Oracle SQL Developer first
├── app/
│   └── monitoring/
│       └── nft/
│           ├── __init__.py
│           ├── database.py             ← All DB operations for API_NFT_* tables
│           ├── models.py               ← Pydantic v1 request/response models
│           └── routes.py               ← FastAPI routes (39 endpoints)
└── MAIN_PY_ADDITIONS.py                ← Exact diff to apply to your main.py
```

---

## Step 1 — Run the SQL

Open `sql/01_nft_platform_tables.sql` in SQL Developer and run against **CQE_NFT** database.

**Tables created (10 new):**

| Table | Purpose |
|---|---|
| `API_NFT_USER_LOB_ACCESS` | Maps users to their accessible LOBs |
| `API_NFT_APPD_CONFIG` | AppDynamics controller config per LOB |
| `API_NFT_KIBANA_CONFIG` | Kibana dashboard configs per LOB/Track |
| `API_NFT_SPLUNK_CONFIG` | Splunk search/dashboard configs per LOB/Track |
| `API_NFT_MONGODB_CONFIG` | MongoDB collection configs per LOB/Track |
| `API_NFT_PC_CONFIG` | Performance Center project configs per LOB/Track |
| `API_NFT_DB_CONFIG` | Oracle DB configs per LOB (password via env var only) |
| `API_NFT_TRACK_TEMPLATE` | Maps all tool configs to a LOB/Track |
| `API_NFT_TEST_REGISTRATION` | Test registrations before monitoring starts |
| `API_NFT_RELEASE_REPORTS` | Final HTML reports stored as CLOB (12+ month retention) |

**Sequences created (9):**
`API_NFT_KIBANA_SEQ`, `API_NFT_SPLUNK_SEQ`, `API_NFT_MONGODB_SEQ`,
`API_NFT_PC_CONFIG_SEQ`, `API_NFT_DB_CONFIG_SEQ`, `API_NFT_TRACK_SEQ`,
`API_NFT_REPORT_SEQ`, `API_NFT_TEST_REG_SEQ`, `API_NFT_APPD_CFG_SEQ`

---

## Step 2 — Copy files

Copy the `nft/` folder into your existing structure:

```
Enhanced_Solution/app/monitoring/nft/   ← copy the entire nft/ folder here
```

---

## Step 3 — Update main.py

Open `MAIN_PY_ADDITIONS.py` — it has 4 clearly marked steps:

1. **Add import** — one line after existing `init_awr_routes` import
2. **Register router** — one `app.include_router()` call at prefix `/api/v1/nft`
3. **Initialize in startup** — one line `init_nft_routes(oracle_pool.pool)` inside existing try block
4. **Add health check** — one new `/api/health/nft` endpoint

Total changes to `main.py`: **~8 lines added, 0 lines changed.**

---

## Step 4 — Test

After starting the server, verify:

```bash
# Health check
curl http://localhost:8000/api/health/nft

# Register a test
curl -X POST http://localhost:8000/api/v1/nft/test-registration \
  -H "X-API-Key: your_key" \
  -H "Content-Type: application/json" \
  -d '{
    "pc_run_id": "65989",
    "lob_name": "Digital Technology",
    "track_name": "CDV3",
    "test_name": "Peak Load Test",
    "test_type": "LOAD",
    "release_name": "Release 2.5"
  }'

# View Swagger docs
open http://localhost:8000/api/docs
```

---

## Design decisions matching your codebase

| Decision | Why |
|---|---|
| `with self.pool.get_connection() as conn` | Matches `authentication_fixed.py` and `pc/database.py` exactly |
| `row[0], row[1]` indexed access | Matches your existing row mapping pattern |
| `dict(zip(columns, row))` | Matches your existing bulk row mapping |
| `CHAR(1) Y/N` flags | Matches `API_AUTH_USERS.IS_ACTIVE`, `API_LOB_MASTER.IS_ACTIVE` |
| `DEFAULT SYSDATE` on dates | Matches all existing tables |
| `API_NFT_CHK_*` constraint names | Matches `API_CHK_*` naming from Auth tables |
| Passwords via env var only | Matches `database_config.py` — `PASS_ENV_VAR` column stores env var name, never the actual password |
| Soft deletes via `IS_ACTIVE = 'N'` | Matches `delete_appd_config()` soft-delete pattern |
| `try/except HTTPException: raise` | Matches `appd/routes.py` exception re-raise pattern |
| `logger.error(..., exc_info=True)` | Matches `appd/routes.py` logging pattern |
| `Pydantic v1` with `schema_extra` | Matches existing models — `pydantic==1.10.18` |
| `oracledb 2.2.1` (not cx_Oracle) | Matches `requirements.txt` |

---

## Notes on test connection endpoints

The `test-connection` endpoints for Kibana, Splunk, MongoDB and PC currently return
simulated responses. The real implementations need:

- **Kibana**: Use `elasticsearch==8.11.0` client with the token from `os.environ[token_env_var]`
- **Splunk**: Use `requests` with the HEC token from `os.environ[token_env_var]`
- **MongoDB**: Use `pymongo==4.6.1` with URI from `os.environ[uri_env_var]`
- **PC**: Use existing `monitoring/pc/client.py` `PerformanceCenterClient`
- **Oracle DB**: Use `oracledb` with password from `os.environ[pass_env_var]`

The `contact_app_team: bool` field in test responses is `True` when connection
succeeds but no data is found — signals that data ingestion needs to be
verified with the application team, not infra.
