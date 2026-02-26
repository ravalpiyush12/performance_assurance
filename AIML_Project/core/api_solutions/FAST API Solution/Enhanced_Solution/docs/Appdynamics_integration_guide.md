# AppDynamics Monitoring Integration Guide

## 🎯 Overview

This guide shows how to integrate your existing AppDynamics code (Code 1, 2, 3) with the new API-based monitoring system.

---

## 📦 What's Included

### **1. API Endpoints (appdynamics_monitoring_api.py)**
- Health check management (Code 1)
- Configuration generation (Code 2)  
- Monitoring session management (Code 3)
- Thread pool monitoring
- Session status tracking

### **2. Beautiful UI (appdynamics_ui_tab.html)**
- Thread pool status dashboard
- Health check panel
- Start monitoring panel
- Active sessions view
- Real-time progress tracking

---

## 🔌 Integration Points

### **Code 1: Health Check / Discovery**

**Location in API:** `execute_healthcheck_task()` function

**Your Code Integration:**
```python
def execute_healthcheck_task(task_id: str, applications: List[str]):
    try:
        print(f"[Task {task_id}] Starting AppD health check...", flush=True)
        
        # ✅ TODO: Import and call your existing Code 1
        from your_appdynamics_module import discover_applications_and_nodes
        
        result = discover_applications_and_nodes(
            applications=applications if applications else None,
            calls_per_minute_threshold=10  # Your threshold
        )
        
        # result should contain:
        # {
        #     "discovered_applications": [...],
        #     "total_nodes_discovered": int,
        #     "total_tiers_discovered": int,
        #     "active_nodes": [...],
        #     "timestamp": datetime
        # }
        
        # ✅ Save to database
        save_discovery_to_database(result)
        
        return result
        
    except Exception as e:
        print(f"[Task {task_id}] Health check failed: {e}", flush=True)
        raise
```

### **Code 2: Generate Monitoring Configuration**

**Location in API:** `generate_monitoring_config()` endpoint

**Your Code Integration:**
```python
@appdynamics_router.post("/generate-config")
async def generate_monitoring_config(applications: List[str]):
    try:
        # ✅ TODO: Import and call your existing Code 2
        from your_appdynamics_module import generate_monitoring_json
        
        config = generate_monitoring_json(
            applications=applications,
            database_connection=your_db_connection
        )
        
        # config should return JSON structure with:
        # {
        #     "applications": [
        #         {
        #             "name": "AppName",
        #             "tiers": [
        #                 {
        #                     "name": "TierName",
        #                     "nodes": ["Node1", "Node2"]
        #                 }
        #             ]
        #         }
        #     ],
        #     "metrics": {...}
        # }
        
        return {
            "success": True,
            "configuration": config
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### **Code 3: Collect Metrics**

**Location in API:** `monitoring_worker()` function

**Your Code Integration:**
```python
def monitoring_worker(session_id: str, request: StartMonitoringRequest):
    while True:
        try:
            # ✅ TODO: Import and call your existing Code 3
            from your_appdynamics_module import collect_appd_metrics
            
            metrics = collect_appd_metrics(
                applications=request.applications,
                lob=request.lob,
                track=request.track,
                run_id=request.run_id,
                collect_application_metrics=True,
                collect_jvm_metrics=True,
                collect_server_metrics=True
            )
            
            # metrics should contain:
            # {
            #     "timestamp": datetime,
            #     "applications": [
            #         {
            #             "name": "AppName",
            #             "application_metrics": {
            #                 "calls_per_minute": int,
            #                 "response_time_ms": float,
            #                 "error_rate": float
            #             },
            #             "jvm_metrics": {
            #                 "heap_used_mb": int,
            #                 "gc_time_ms": int,
            #                 "thread_count": int
            #             },
            #             "server_metrics": {
            #                 "cpu_percent": float,
            #                 "memory_percent": float,
            #                 "disk_io_mbps": float
            #             }
            #         }
            #     ]
            # }
            
            # ✅ Save to database
            save_metrics_to_database(
                session_id=session_id,
                lob=request.lob,
                track=request.track,
                run_id=request.run_id,
                metrics=metrics
            )
            
            # Update session
            with thread_lock:
                if session_id in monitoring_sessions:
                    monitoring_sessions[session_id]["iterations_completed"] += 1
                    monitoring_sessions[session_id]["last_collection_time"] = datetime.now().isoformat()
            
        except Exception as e:
            print(f"[Session {session_id}] Error: {e}", flush=True)
        
        # Wait for next interval (e.g., 30 minutes)
        time.sleep(request.interval_seconds)
```

---

## 🗄️ Database Schema

### **Table 1: APPD_APPLICATIONS**
Stores discovered applications and nodes (from Code 1)

```sql
CREATE TABLE APPD_APPLICATIONS (
    APP_ID NUMBER PRIMARY KEY,
    APPLICATION_NAME VARCHAR2(200) NOT NULL,
    DISCOVERY_DATE DATE DEFAULT SYSDATE,
    TOTAL_NODES NUMBER,
    TOTAL_TIERS NUMBER,
    ACTIVE_NODES NUMBER,
    STATUS VARCHAR2(50),
    CREATED_DATE DATE DEFAULT SYSDATE,
    UPDATED_DATE DATE DEFAULT SYSDATE
);

CREATE SEQUENCE APPD_APPLICATIONS_SEQ START WITH 1;
```

### **Table 2: APPD_NODES**
Stores node details

```sql
CREATE TABLE APPD_NODES (
    NODE_ID NUMBER PRIMARY KEY,
    APP_ID NUMBER REFERENCES APPD_APPLICATIONS(APP_ID),
    NODE_NAME VARCHAR2(200) NOT NULL,
    TIER_NAME VARCHAR2(200),
    IS_ACTIVE VARCHAR2(1) DEFAULT 'Y',
    CALLS_PER_MINUTE NUMBER,
    LAST_SEEN_DATE DATE,
    CREATED_DATE DATE DEFAULT SYSDATE
);

CREATE SEQUENCE APPD_NODES_SEQ START WITH 1;
CREATE INDEX IDX_APPD_NODES_APP ON APPD_NODES(APP_ID);
```

### **Table 3: APPD_MONITORING_SESSIONS**
Stores monitoring sessions

```sql
CREATE TABLE APPD_MONITORING_SESSIONS (
    SESSION_ID VARCHAR2(100) PRIMARY KEY,
    LOB VARCHAR2(100) NOT NULL,
    TRACK VARCHAR2(100) NOT NULL,
    RUN_ID VARCHAR2(200) NOT NULL,
    APPLICATIONS CLOB,  -- JSON array of application names
    STATUS VARCHAR2(50),  -- running, stopped, completed, failed
    START_TIME TIMESTAMP,
    END_TIME TIMESTAMP,
    ITERATIONS_COMPLETED NUMBER DEFAULT 0,
    LAST_COLLECTION_TIME TIMESTAMP,
    ERROR_MESSAGE VARCHAR2(4000),
    CREATED_DATE DATE DEFAULT SYSDATE
);

CREATE INDEX IDX_APPD_SESSIONS_LOB ON APPD_MONITORING_SESSIONS(LOB, TRACK, RUN_ID);
```

### **Table 4: APPD_METRICS**
Stores collected metrics (from Code 3)

```sql
CREATE TABLE APPD_METRICS (
    METRIC_ID NUMBER PRIMARY KEY,
    SESSION_ID VARCHAR2(100) REFERENCES APPD_MONITORING_SESSIONS(SESSION_ID),
    LOB VARCHAR2(100),
    TRACK VARCHAR2(100),
    RUN_ID VARCHAR2(200),
    APPLICATION_NAME VARCHAR2(200),
    METRIC_TIMESTAMP TIMESTAMP,
    
    -- Application Metrics
    CALLS_PER_MINUTE NUMBER,
    RESPONSE_TIME_MS NUMBER,
    ERROR_RATE NUMBER,
    
    -- JVM Metrics
    HEAP_USED_MB NUMBER,
    GC_TIME_MS NUMBER,
    THREAD_COUNT NUMBER,
    
    -- Server Metrics
    CPU_PERCENT NUMBER,
    MEMORY_PERCENT NUMBER,
    DISK_IO_MBPS NUMBER,
    
    -- Additional data
    ADDITIONAL_DATA CLOB,  -- JSON for any extra metrics
    
    CREATED_DATE DATE DEFAULT SYSDATE
);

CREATE SEQUENCE APPD_METRICS_SEQ START WITH 1;
CREATE INDEX IDX_APPD_METRICS_SESSION ON APPD_METRICS(SESSION_ID);
CREATE INDEX IDX_APPD_METRICS_RUN ON APPD_METRICS(LOB, TRACK, RUN_ID);
CREATE INDEX IDX_APPD_METRICS_TIME ON APPD_METRICS(METRIC_TIMESTAMP);
```

---

## 🔧 Implementation Steps

### **Step 1: Add API Router to main.py**

```python
# Add import
from appdynamics_monitoring_api import appdynamics_router

# Include router
app.include_router(appdynamics_router)
```

### **Step 2: Update index.html**

Replace the AppDynamics tab content with the new UI from `appdynamics_ui_tab.html`:

```html
<!-- Find this in index.html: -->
<div id="appdynamics" class="tab-content">
    <!-- Replace entire content with appdynamics_ui_tab.html -->
</div>
```

### **Step 3: Create Database Tables**

Run the SQL scripts above in your Oracle database (CQE_NFT or dedicated monitoring DB).

### **Step 4: Integrate Your Existing Code**

1. **Code 1 Integration:**
   - Update `execute_healthcheck_task()` 
   - Import your discovery function
   - Save results to `APPD_APPLICATIONS` and `APPD_NODES`

2. **Code 2 Integration:**
   - Update `generate_monitoring_config()`
   - Import your JSON generation function
   - Query from `APPD_APPLICATIONS` and `APPD_NODES`

3. **Code 3 Integration:**
   - Update `monitoring_worker()`
   - Import your metrics collection function
   - Save to `APPD_METRICS` table

---

## 📊 Workflow

### **Daily Health Check (Automated)**

```python
# Schedule this to run daily
@app.post("/api/v1/monitoring/appdynamics/healthcheck")
# Runs Code 1
# Discovers applications
# Identifies active nodes
# Updates database
```

### **Performance Test Workflow**

**1. User starts performance test in LoadRunner**

**2. User opens AppDynamics tab:**
   - Sees thread pool status
   - Clicks "Run Health Check" (optional, to verify current state)

**3. User fills Start Monitoring form:**
   ```
   LOB: Retail
   Track: Q4_2026
   Run ID: RUN_20260225_001
   Applications: RetailWeb, RetailAPI
   Interval: 30 minutes
   ```

**4. Clicks "Start Monitoring":**
   - Background thread starts
   - Collects metrics every 30 minutes
   - Saves to database with LOB/Track/Run ID

**5. Monitor progress:**
   - View active sessions
   - See iterations completed
   - Check last collection time

**6. Test completes:**
   - Click "Stop" button
   - Session marked as completed

**7. Later - RCA Portal (future):**
   - Query by LOB/Track/Run ID
   - Retrieve all AppD metrics
   - Combine with LoadRunner data
   - Generate automated RCA

---

## 🎨 UI Features

### **Thread Pool Status**
Shows real-time monitoring capacity:
- Active monitors
- Available slots
- Utilization percentage

### **Health Check Panel**
- Input: Applications (optional)
- Action: Run discovery
- Output: Task ID and status

### **Start Monitoring Panel**
- Inputs: LOB, Track, Run ID, Applications, Interval
- Action: Start background monitoring
- Output: Session ID

### **Active Sessions**
- Live view of all sessions
- Status indicators (running/stopped/failed)
- Progress bars for running sessions
- Stop and View Details buttons
- Auto-refresh every 10 seconds

---

## 🔍 API Reference

### **POST /api/v1/monitoring/appdynamics/healthcheck**
Run Code 1 - Discover applications

### **POST /api/v1/monitoring/appdynamics/generate-config**
Run Code 2 - Generate monitoring JSON

### **POST /api/v1/monitoring/appdynamics/start**
Start Code 3 - Begin metrics collection

### **POST /api/v1/monitoring/appdynamics/stop/{session_id}**
Stop monitoring session

### **GET /api/v1/monitoring/appdynamics/sessions**
List all sessions

### **GET /api/v1/monitoring/appdynamics/thread-pool/status**
Get thread pool capacity and utilization

### **GET /api/v1/monitoring/appdynamics/metrics**
Query collected metrics by LOB/Track/Run ID

---

## 🚀 Next Steps

1. ✅ Copy API file to `app/monitoring/appdynamics.py`
2. ✅ Update index.html with new UI tab
3. ✅ Create database tables
4. ✅ Integrate your Code 1, 2, 3
5. ✅ Test health check
6. ✅ Test monitoring session
7. ✅ Verify data in database

---

## 📝 Sample Database Integration

```python
import oracledb

def save_discovery_to_database(result):
    """Save Code 1 discovery results"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    for app in result['discovered_applications']:
        cursor.execute("""
            INSERT INTO APPD_APPLICATIONS 
            (APP_ID, APPLICATION_NAME, TOTAL_NODES, TOTAL_TIERS, ACTIVE_NODES, STATUS)
            VALUES 
            (APPD_APPLICATIONS_SEQ.NEXTVAL, :name, :total_nodes, :total_tiers, :active_nodes, 'ACTIVE')
        """, {
            'name': app['name'],
            'total_nodes': app['total_nodes'],
            'total_tiers': app['total_tiers'],
            'active_nodes': app['active_nodes']
        })
    
    connection.commit()
    cursor.close()
    connection.close()


def save_metrics_to_database(session_id, lob, track, run_id, metrics):
    """Save Code 3 metrics"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    for app_metrics in metrics['applications']:
        cursor.execute("""
            INSERT INTO APPD_METRICS (
                METRIC_ID, SESSION_ID, LOB, TRACK, RUN_ID, APPLICATION_NAME,
                METRIC_TIMESTAMP, CALLS_PER_MINUTE, RESPONSE_TIME_MS, ERROR_RATE,
                HEAP_USED_MB, GC_TIME_MS, THREAD_COUNT,
                CPU_PERCENT, MEMORY_PERCENT, DISK_IO_MBPS
            ) VALUES (
                APPD_METRICS_SEQ.NEXTVAL, :session_id, :lob, :track, :run_id, :app_name,
                :timestamp, :cpm, :response_time, :error_rate,
                :heap, :gc_time, :threads,
                :cpu, :memory, :disk_io
            )
        """, {
            'session_id': session_id,
            'lob': lob,
            'track': track,
            'run_id': run_id,
            'app_name': app_metrics['name'],
            'timestamp': metrics['timestamp'],
            'cpm': app_metrics['application_metrics']['calls_per_minute'],
            'response_time': app_metrics['application_metrics']['response_time_ms'],
            'error_rate': app_metrics['application_metrics']['error_rate'],
            'heap': app_metrics['jvm_metrics']['heap_used_mb'],
            'gc_time': app_metrics['jvm_metrics']['gc_time_ms'],
            'threads': app_metrics['jvm_metrics']['thread_count'],
            'cpu': app_metrics['server_metrics']['cpu_percent'],
            'memory': app_metrics['server_metrics']['memory_percent'],
            'disk_io': app_metrics['server_metrics']['disk_io_mbps']
        })
    
    connection.commit()
    cursor.close()
    connection.close()
```

---

**Your AppDynamics monitoring is now API-enabled with a beautiful UI!** 🎉