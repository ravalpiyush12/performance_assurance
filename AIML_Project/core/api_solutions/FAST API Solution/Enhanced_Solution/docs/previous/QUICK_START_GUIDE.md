# AppDynamics Monitoring - Quick Start Guide

## ✅ All Files Generated - Ready to Deploy!

### **12 Production-Ready Files:**

1. ✅ **appd_database_schema.sql** - Complete database schema
2. ✅ **appd_config.py** - Configuration management
3. ✅ **appd_client.py** - REST API client (450+ lines)
4. ✅ **appd_db.py** - Database operations (550+ lines)
5. ✅ **appd_discovery.py** - Discovery service (Code 1)
6. ✅ **appd_collectors.py** - Metrics collectors
7. ✅ **appd_orchestrator.py** - Orchestration (Code 3)
8. ✅ **appd_routes.py** - FastAPI endpoints
9. ✅ **main_py_UPDATED.py** - Integration guide
10. ✅ **monitoring__init__.py** - Module init
11. ✅ **monitoring_appd__init__.py** - AppD module init
12. ✅ **env.local.TEMPLATE** - Configuration template

---

## 🚀 Installation Steps (5 Minutes)

### **Step 1: Create Project Structure**

```bash
cd your-project/app

# Create monitoring module
mkdir -p monitoring/appd

# Copy all AppD files
cp /path/to/appd_config.py monitoring/appd/config.py
cp /path/to/appd_client.py monitoring/appd/client.py
cp /path/to/appd_db.py monitoring/appd/database.py
cp /path/to/appd_discovery.py monitoring/appd/discovery.py
cp /path/to/appd_collectors.py monitoring/appd/collectors.py
cp /path/to/appd_orchestrator.py monitoring/appd/orchestrator.py
cp /path/to/appd_routes.py monitoring/appd/routes.py

# Copy init files
cp /path/to/monitoring__init__.py monitoring/__init__.py
cp /path/to/monitoring_appd__init__.py monitoring/appd/__init__.py
```

### **Step 2: Create Database**

```bash
# Connect to Oracle
sqlplus user/password@database

# Run schema
@appd_database_schema.sql

# Verify tables created
SELECT table_name FROM user_tables WHERE table_name LIKE 'APPD%';
```

**Expected output:** 9 tables
- APPD_LOB_CONFIG
- APPD_APPLICATIONS
- APPD_TIERS
- APPD_NODES
- APPD_MONITORING_RUNS
- APPD_SERVER_METRICS
- APPD_JVM_METRICS
- APPD_APPLICATION_METRICS
- APPD_DISCOVERY_LOG

### **Step 3: Configure Environment**

```bash
# Copy template
cp env.local.TEMPLATE .env.local

# Edit with your values
nano .env.local
```

**Update these values:**
```bash
APPD_CONTROLLER_HOST=your-controller.appdynamics.com
APPD_ACCOUNT_NAME=your_account
APPD_USERNAME=your_username@your_account
APPD_PASSWORD=your_password
```

### **Step 4: Insert LOB Data**

```sql
-- Insert your LOBs
INSERT INTO APPD_LOB_CONFIG (
    LOB_ID, LOB_NAME, LOB_DESCRIPTION, APPLICATION_NAMES, IS_ACTIVE
) VALUES (
    APPD_LOB_CONFIG_SEQ.NEXTVAL,
    'Retail',
    'Retail Line of Business',
    '["RetailWeb", "RetailAPI", "RetailMobile"]',
    'Y'
);

INSERT INTO APPD_LOB_CONFIG (
    LOB_ID, LOB_NAME, LOB_DESCRIPTION, APPLICATION_NAMES, IS_ACTIVE
) VALUES (
    APPD_LOB_CONFIG_SEQ.NEXTVAL,
    'Banking',
    'Banking Line of Business', 
    '["BankingWeb", "BankingCore", "BankingMobile"]',
    'Y'
);

COMMIT;
```

### **Step 5: Update main.py**

Add these lines to your `app/main.py`:

```python
# At top with other imports
from monitoring.appd.routes import router as appd_router, initialize_appd_components

# In startup event (after Oracle pool creation)
@app.on_event("startup")
async def startup_event():
    # ... existing code ...
    
    # Initialize AppD
    try:
        oracle_pool = app.state.connection_manager.pools.get('CQE_NFT')
        if oracle_pool:
            initialize_appd_components(oracle_pool.pool)
            print("[Startup] AppD initialized", flush=True)
    except Exception as e:
        print(f"[Startup] AppD init failed: {e}", flush=True)

# After other router includes
app.include_router(
    appd_router,
    prefix="/api/v1/monitoring/appd",
    tags=["AppDynamics Monitoring"]
)
```

### **Step 6: Install Dependencies**

```bash
# If not already in requirements.txt
pip install requests
```

### **Step 7: Start Application**

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🧪 Testing

### **Test 1: Check Initialization**

```bash
# Check logs for:
# [AppD] Initializing components...
# [AppD] Initialized successfully
```

### **Test 2: Run Discovery**

```bash
# API call
curl -X POST "http://localhost:8000/api/v1/monitoring/appd/discovery/run" \
  -H "Content-Type: application/json" \
  -d '{"lob_names": ["Retail"]}'

# Expected response:
# {
#   "task_id": "...",
#   "status": "initiated",
#   "lob_names": ["Retail"]
# }
```

**Check database:**
```sql
SELECT * FROM APPD_APPLICATIONS;
SELECT * FROM APPD_NODES WHERE IS_ACTIVE = 'Y';
```

### **Test 3: Health Check**

```bash
curl "http://localhost:8000/api/v1/monitoring/appd/health/Retail"

# Expected: List of active nodes grouped by app/tier
```

### **Test 4: Start Monitoring**

```bash
curl -X POST "http://localhost:8000/api/v1/monitoring/appd/monitoring/start" \
  -H "Content-Type: application/json" \
  -d '{
    "run_id": "TEST_RUN_001",
    "lob_name": "Retail",
    "track": "Q1_2026",
    "applications": ["RetailWeb"],
    "interval_seconds": 300
  }'

# Expected:
# {
#   "success": true,
#   "run_id": "TEST_RUN_001",
#   "message": "Monitoring started"
# }
```

**Check database:**
```sql
SELECT * FROM APPD_MONITORING_RUNS WHERE RUN_ID = 'TEST_RUN_001';

-- Wait 5 minutes, then check metrics
SELECT COUNT(*) FROM APPD_SERVER_METRICS WHERE RUN_ID = 'TEST_RUN_001';
SELECT COUNT(*) FROM APPD_JVM_METRICS WHERE RUN_ID = 'TEST_RUN_001';
SELECT COUNT(*) FROM APPD_APPLICATION_METRICS WHERE RUN_ID = 'TEST_RUN_001';
```

### **Test 5: Check Thread Pool**

```bash
curl "http://localhost:8000/api/v1/monitoring/appd/monitoring/thread-pool/status"

# Expected:
# {
#   "max_concurrent_monitors": 10,
#   "active_monitors": 1,
#   "available_slots": 9,
#   "utilization_percent": 10.0
# }
```

### **Test 6: Stop Monitoring**

```bash
curl -X POST "http://localhost:8000/api/v1/monitoring/appd/monitoring/stop/TEST_RUN_001"

# Expected:
# {
#   "success": true,
#   "run_id": "TEST_RUN_001"
# }
```

---

## 📊 API Endpoints Reference

### **Discovery**
- `POST /api/v1/monitoring/appd/discovery/run` - Run discovery

### **Health Check**
- `GET /api/v1/monitoring/appd/health/{lob_name}` - Get active nodes

### **Monitoring**
- `POST /api/v1/monitoring/appd/monitoring/start` - Start monitoring
- `POST /api/v1/monitoring/appd/monitoring/stop/{run_id}` - Stop
- `GET /api/v1/monitoring/appd/monitoring/sessions` - List sessions
- `GET /api/v1/monitoring/appd/monitoring/thread-pool/status` - Thread status

---

## 🎯 Typical Workflow

### **Daily Discovery (Scheduled)**
```python
# Schedule this to run daily via cron/scheduler
POST /api/v1/monitoring/appd/discovery/run
{"lob_names": ["Retail", "Banking"]}
```

### **Performance Test Flow**

1. **Start LoadRunner test**
2. **Check active nodes:**
   ```bash
   GET /api/v1/monitoring/appd/health/Retail
   ```
3. **Start AppD monitoring:**
   ```bash
   POST /api/v1/monitoring/appd/monitoring/start
   {
     "run_id": "RUN_20260226_001",
     "lob_name": "Retail",
     "track": "Q1_2026",
     "test_name": "Peak Load Test",
     "applications": ["RetailWeb", "RetailAPI"],
     "interval_seconds": 1800
   }
   ```
4. **Monitor progress:**
   ```bash
   GET /api/v1/monitoring/appd/monitoring/sessions
   ```
5. **Stop when test completes:**
   ```bash
   POST /api/v1/monitoring/appd/monitoring/stop/RUN_20260226_001
   ```

---

## 🔍 Troubleshooting

### **Issue: "Service not initialized"**
**Solution:** Check startup logs for AppD initialization errors

### **Issue: No nodes discovered**
**Solution:** 
- Verify AppD credentials in .env.local
- Check CPM threshold (default: 10)
- Verify application names in LOB_CONFIG

### **Issue: Monitoring not collecting metrics**
**Solution:**
- Check thread pool status
- Verify nodes are marked as active in database
- Check AppD API credentials

### **Issue: Database connection errors**
**Solution:**
- Verify Oracle pool is passed to initialize_appd_components()
- Check CQE_NFT database credentials

---

## ✅ Success Checklist

- [ ] All 9 tables created in Oracle
- [ ] LOB data inserted
- [ ] .env.local configured
- [ ] main.py updated with AppD router
- [ ] Application starts without errors
- [ ] Discovery runs successfully
- [ ] Health check returns active nodes
- [ ] Monitoring starts and collects metrics
- [ ] Metrics appear in database tables

---

## 📞 Support

**Common Issues:**
1. AppD credentials - Check controller URL and account name
2. CPM threshold - Adjust APPD_ACTIVE_NODE_CPM_THRESHOLD if needed
3. Thread pool - Increase APPD_MAX_CONCURRENT_MONITORS for more parallel sessions

**Database Queries:**
```sql
-- Check discovery status
SELECT * FROM APPD_DISCOVERY_LOG ORDER BY DISCOVERY_START_TIME DESC;

-- Check active nodes by LOB
SELECT * FROM VW_APPD_ACTIVE_NODES_BY_LOB;

-- Check LOB summary
SELECT * FROM VW_APPD_LOB_SUMMARY;

-- Check recent metrics
SELECT COUNT(*), RUN_ID FROM APPD_SERVER_METRICS 
GROUP BY RUN_ID ORDER BY MAX(CREATED_DATE) DESC;
```

---

## 🚀 Next Steps

After AppD is working:
1. Add UI tab (index.html)
2. Schedule daily discovery
3. Replicate structure for Kibana
4. Replicate structure for MongoDB

**You now have a complete, production-ready AppDynamics monitoring system!** 🎉