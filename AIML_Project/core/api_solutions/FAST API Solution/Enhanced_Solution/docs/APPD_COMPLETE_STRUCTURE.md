# AppDynamics Complete Project Structure

```
API-Solutions/
└── Phase1_Enhanced/
    └── app/
        ├── appd_monitoring/          # NEW: AppDynamics module
        │   ├── __init__.py
        │   ├── config.py             # AppD configuration
        │   ├── discovery/
        │   │   ├── __init__.py
        │   │   ├── appd_client.py    # AppD REST API client
        │   │   └── discovery_service.py  # Code 1: Discovery & Load to DB
        │   ├── database/
        │   │   ├── __init__.py
        │   │   └── appd_db.py        # Database operations
        │   ├── monitoring/
        │   │   ├── __init__.py
        │   │   ├── collectors/
        │   │   │   ├── __init__.py
        │   │   │   ├── server_collector.py   # CPU, Memory, Disk, Network
        │   │   │   ├── jvm_collector.py      # Heap, GC, Threads
        │   │   │   └── app_collector.py      # CPM, Response Time
        │   │   ├── orchestrator.py   # Code 3: Monitoring orchestration
        │   │   └── thread_manager.py # Multi-threaded collection
        │   └── api/
        │       ├── __init__.py
        │       └── routes.py         # FastAPI routes
        │
        ├── config/
        │   ├── __init__.py
        │   ├── settings.py
        │   └── database_config.py
        │
        ├── database/
        │   ├── __init__.py
        │   ├── connection_manager.py
        │   └── oracle_handler.py
        │
        └── main.py                   # Updated main with AppD routes
```

## File Purposes

### 1. Discovery Module (Code 1)
- `appd_client.py` - REST API calls to AppDynamics
- `discovery_service.py` - Discovers apps, tiers, nodes and loads to DB

### 2. Database Module
- `appd_db.py` - All database operations for 9 tables

### 3. Monitoring Module (Code 3)
- `server_collector.py` - Collects CPU, Memory, Network, Disk
- `jvm_collector.py` - Collects Heap, GC, Threads, Exceptions
- `app_collector.py` - Collects CPM, Response Time, Errors
- `orchestrator.py` - Coordinates all collectors
- `thread_manager.py` - Manages parallel collection per tier

### 4. API Module
- `routes.py` - FastAPI endpoints for UI integration

## Integration Points

### main.py
```python
from appd_monitoring.api.routes import appd_router
app.include_router(appd_router)
```

### Environment Variables (.env.local)
```bash
# AppDynamics Configuration
APPD_CONTROLLER_HOST=controller.appdynamics.com
APPD_CONTROLLER_PORT=443
APPD_ACCOUNT_NAME=customer1
APPD_USERNAME=admin@customer1
APPD_PASSWORD=your_password
APPD_USE_SSL=true

# Thresholds
APPD_ACTIVE_NODE_CPM_THRESHOLD=10
APPD_DISCOVERY_SCHEDULE=DAILY
```

## Key Features

1. ✅ **Daily Discovery** - Runs once per day per LOB
2. ✅ **Health Check API** - Returns active nodes by LOB from DB
3. ✅ **Multi-threaded Monitoring** - Parallel collection per tier
4. ✅ **3 Metrics Tables** - Server, JVM, Application
5. ✅ **Run ID Primary Key** - Links all metrics
6. ✅ **LOB-based Organization** - Separate monitoring per LOB
7. ✅ **Complete UI Integration** - Visible tabs and controls

## Database Tables (9 total)

1. `APPD_LOB_CONFIG` - LOB configuration
2. `APPD_APPLICATIONS` - Discovered applications
3. `APPD_TIERS` - Application tiers
4. `APPD_NODES` - Nodes (active/inactive based on CPM)
5. `APPD_MONITORING_RUNS` - Monitoring sessions
6. `APPD_SERVER_METRICS` - CPU, Memory, Network, Disk
7. `APPD_JVM_METRICS` - Heap, GC, Threads, Exceptions
8. `APPD_APPLICATION_METRICS` - CPM, Response Time, Errors
9. `APPD_DISCOVERY_LOG` - Discovery audit trail

## API Endpoints

### Discovery
- `POST /api/v1/appd/discovery/run` - Run discovery for LOB(s)
- `GET /api/v1/appd/discovery/status/{log_id}` - Check discovery status

### Health Check
- `GET /api/v1/appd/health/{lob_name}` - Get active nodes for LOB
- `GET /api/v1/appd/health/summary` - Get all LOBs summary

### Monitoring
- `POST /api/v1/appd/monitoring/start` - Start monitoring session
- `POST /api/v1/appd/monitoring/stop/{run_id}` - Stop monitoring
- `GET /api/v1/appd/monitoring/sessions` - List all sessions
- `GET /api/v1/appd/monitoring/metrics/{run_id}` - Get metrics

### Thread Pool
- `GET /api/v1/appd/monitoring/thread-pool/status` - Thread pool status

## Files to Generate Next

Due to character limits, I'll generate these files in parts:

1. ✅ Database Schema (appd_database_schema.sql)
2. ⏳ AppD Client (appd_client.py)
3. ⏳ Discovery Service (discovery_service.py)
4. ⏳ Database Operations (appd_db.py)
5. ⏳ Collectors (server, jvm, app)
6. ⏳ Orchestrator (orchestrator.py)
7. ⏳ Thread Manager (thread_manager.py)
8. ⏳ API Routes (routes.py)
9. ⏳ Updated main.py
10. ⏳ Updated index.html

Let me know which files you want generated next!