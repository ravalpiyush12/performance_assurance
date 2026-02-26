# Complete Project Structure - Production Ready

## 📁 Recommended Folder Structure

```
your-project/
├── .env.local                      # Environment variables
├── requirements.txt                # Python dependencies
├── gunicorn.conf.py               # Gunicorn configuration
│
├── app/
│   ├── __init__.py
│   ├── main.py                    # Main FastAPI app (UPDATED)
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py            # Main settings (Oracle SQL API)
│   │   └── database_config.py     # DB configuration
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py            # API key validation
│   │   └── sql_validator.py      # SQL validation
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection_manager.py  # Oracle connection pool
│   │   ├── oracle_handler.py      # Oracle handler (python-oracledb)
│   │   └── sql_executor.py        # SQL execution
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── audit.py               # Audit logging
│   │   └── cyberark.py            # CyberArk integration
│   │
│   ├── monitoring/                # NEW: Monitoring Module
│   │   ├── __init__.py
│   │   │
│   │   ├── appd/                  # AppDynamics Monitoring
│   │   │   ├── __init__.py
│   │   │   ├── config.py          # ✅ AppD configuration
│   │   │   ├── client.py          # ✅ REST API client
│   │   │   ├── database.py        # ✅ Database operations
│   │   │   ├── discovery.py       # ⏳ Code 1: Discovery service
│   │   │   ├── collectors.py      # ⏳ All collectors (server/jvm/app)
│   │   │   ├── orchestrator.py    # ⏳ Code 3: Orchestration
│   │   │   ├── thread_manager.py  # ⏳ Multi-threading
│   │   │   └── routes.py          # ⏳ FastAPI routes
│   │   │
│   │   ├── kibana/                # Kibana Monitoring (Future)
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── client.py
│   │   │   ├── database.py
│   │   │   ├── collectors.py
│   │   │   └── routes.py
│   │   │
│   │   └── mongodb/               # MongoDB Monitoring (Future)
│   │       ├── __init__.py
│   │       ├── config.py
│   │       ├── client.py
│   │       ├── database.py
│   │       ├── collectors.py
│   │       └── routes.py
│   │
│   └── [existing Oracle SQL API files...]
│
├── templates/
│   └── index.html                 # UPDATED: With AppD/Kibana/MongoDB tabs
│
├── logs/
│   └── audit/                     # Audit logs
│
└── docs/
    ├── appd_database_schema.sql   # ✅ AppD DB schema
    ├── kibana_database_schema.sql # ⏳ Kibana DB schema
    └── mongodb_database_schema.sql # ⏳ MongoDB DB schema
```

## 🎯 Modular Design Benefits

### 1. **Separation of Concerns**
Each monitoring system (AppD, Kibana, MongoDB) is isolated in its own module.

### 2. **Reusable Pattern**
Same structure for all monitoring systems:
- `config.py` - Configuration
- `client.py` - API client
- `database.py` - Database operations
- `collectors.py` - Metrics collectors
- `orchestrator.py` - Orchestration logic
- `routes.py` - FastAPI routes

### 3. **Easy to Extend**
Adding new monitoring systems follows the same pattern.

### 4. **Independent Development**
Teams can work on AppD, Kibana, MongoDB simultaneously.

## 📝 File Organization Strategy

### **Core Files (Shared)**
- `app/main.py` - Includes all routers
- `app/config/settings.py` - Global settings
- `app/database/connection_manager.py` - Oracle connection pool

### **Monitoring Module Structure**
Each monitoring system (`appd/`, `kibana/`, `mongodb/`) contains:

1. **config.py** - System-specific configuration
2. **client.py** - REST API / SDK client
3. **database.py** - Database CRUD operations
4. **discovery.py** - Service discovery (if applicable)
5. **collectors.py** - All metric collectors in one file
6. **orchestrator.py** - Collection orchestration
7. **thread_manager.py** - Threading (if needed)
8. **routes.py** - FastAPI routes

## 🔌 Integration in main.py

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Existing imports
from config.settings import get_settings
from database.connection_manager import ConnectionManager
# ... other existing imports

# NEW: Monitoring routers
from monitoring.appd.routes import router as appd_router
from monitoring.kibana.routes import router as kibana_router  # Future
from monitoring.mongodb.routes import router as mongodb_router  # Future

app = FastAPI(title="CQE NFT Monitoring API Solutions")

# Include existing routers
# ... existing router includes ...

# Include monitoring routers
app.include_router(appd_router, prefix="/api/v1/monitoring/appd", tags=["AppDynamics"])
app.include_router(kibana_router, prefix="/api/v1/monitoring/kibana", tags=["Kibana"])
app.include_router(mongodb_router, prefix="/api/v1/monitoring/mongodb", tags=["MongoDB"])

# ... rest of main.py
```

## 🗄️ Database Organization

### **Oracle Schemas**
All monitoring data in same Oracle database:

```sql
-- AppDynamics Tables (9 tables)
APPD_LOB_CONFIG
APPD_APPLICATIONS
APPD_TIERS
APPD_NODES
APPD_MONITORING_RUNS
APPD_SERVER_METRICS
APPD_JVM_METRICS
APPD_APPLICATION_METRICS
APPD_DISCOVERY_LOG

-- Kibana Tables (Future)
KIBANA_CONFIG
KIBANA_INDICES
KIBANA_LOGS
...

-- MongoDB Tables (Future)
MONGO_CONFIG
MONGO_COLLECTIONS
MONGO_METRICS
...
```

## 🌐 UI Organization

### **index.html Structure**
```html
<div class="tabs">
    <!-- Core -->
    <button class="tab">Oracle SQL</button>
    <button class="tab">API Keys</button>
    
    <!-- Monitoring -->
    <button class="tab">AppDynamics</button>
    <button class="tab">Kibana</button>
    <button class="tab">Splunk</button>
    <button class="tab">MongoDB</button>
</div>

<div id="appdynamics" class="tab-content">
    <!-- AppD monitoring UI -->
</div>

<div id="kibana" class="tab-content">
    <!-- Kibana monitoring UI -->
</div>

<div id="mongodb" class="tab-content">
    <!-- MongoDB monitoring UI -->
</div>
```

## 📋 Consistent Patterns

### **1. Configuration Pattern**
```python
# monitoring/appd/config.py
# monitoring/kibana/config.py
# monitoring/mongodb/config.py

class MonitoringConfig(BaseSettings):
    # System-specific settings
    HOST: str
    PORT: int
    USERNAME: str
    PASSWORD: str
    # ... etc
```

### **2. Client Pattern**
```python
# monitoring/appd/client.py
# monitoring/kibana/client.py
# monitoring/mongodb/client.py

class MonitoringClient:
    def __init__(self, config):
        # Initialize client
        
    def get_metrics(self, ...):
        # Fetch metrics
```

### **3. Database Pattern**
```python
# monitoring/appd/database.py
# monitoring/kibana/database.py
# monitoring/mongodb/database.py

class MonitoringDatabase:
    def insert_metrics(self, ...):
        # Save metrics
        
    def get_active_nodes(self, ...):
        # Query data
```

### **4. Routes Pattern**
```python
# monitoring/appd/routes.py
# monitoring/kibana/routes.py
# monitoring/mongodb/routes.py

router = APIRouter()

@router.post("/discovery/run")
async def run_discovery(...):
    # Discovery endpoint
    
@router.post("/monitoring/start")
async def start_monitoring(...):
    # Start monitoring
```

## ✅ Benefits of This Structure

1. **Scalability** - Easy to add new monitoring systems
2. **Maintainability** - Clear separation, easy to find code
3. **Testability** - Each module can be tested independently
4. **Reusability** - Same patterns across all monitoring systems
5. **Team Collaboration** - Multiple developers can work simultaneously
6. **Documentation** - Self-documenting structure

## 🚀 Development Workflow

### **Phase 1: AppDynamics** ✅
1. ✅ Database schema
2. ✅ Config, Client, Database
3. ⏳ Discovery, Collectors, Orchestrator
4. ⏳ Routes, UI integration

### **Phase 2: Kibana** 🔄
1. Copy AppD structure
2. Customize for Kibana/Elasticsearch
3. Different metrics (logs, errors, response times)
4. Integration

### **Phase 3: MongoDB** 🔄
1. Copy AppD structure
2. Customize for MongoDB
3. Collection stats, operation metrics
4. Integration

## 📦 Dependencies Management

### **requirements.txt**
```txt
# Core
fastapi==0.88.0
uvicorn[standard]==0.27.0
pydantic==1.10.18
oracledb==2.0.0

# Monitoring - AppDynamics
requests==2.31.0

# Monitoring - Kibana (Future)
elasticsearch==8.11.0

# Monitoring - MongoDB (Future)
pymongo==4.6.1

# ... other dependencies
```

This structure ensures:
- Clean code organization
- Easy onboarding for new team members
- Consistent patterns across monitoring systems
- Future-proof for additional monitoring tools