# 📊 AppDynamics Tab - Complete Workflow Guide

## 🎯 Overview

The AppD tab enables you to:
1. **Discovery** - Find and classify active/inactive nodes
2. **Health Check** - View active nodes for monitoring
3. **Start Monitoring** - Collect metrics during performance tests
4. **View Sessions** - Monitor active collection sessions

---

## 🔄 Complete Workflow - Step by Step

### **PHASE 1: Discovery (Code 1)**
*Purpose: Find all applications, tiers, nodes and classify them as active/inactive*

#### **Step 1: User Fills Discovery Form**

```
UI Form Fields:
┌─────────────────────────────────────┐
│ Config Name: Retail_Q1_2026        │ (Unique identifier)
│ LOB Name: Retail                   │ (Line of Business)
│ Track: Q1_2026                     │ (Release/Track)
│ AppD Applications: RetailWeb,      │ (Comma-separated)
│                    RetailAPI        │
│                                    │
│ [🔍 Run Discovery & Save Config]  │
└─────────────────────────────────────┘
```

#### **Step 2: UI Calls Backend**

```javascript
// JavaScript in index_final.html
async function runDiscovery() {
    const configName = document.getElementById('configName').value;
    const lob = document.getElementById('discoveryLob').value;
    const track = document.getElementById('discoveryTrack').value;
    const apps = document.getElementById('discoveryApps').value;
    
    // First: Save config
    await fetch('/api/v1/monitoring/appd/config/save', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            config_name: configName,
            lob_name: lob,
            track: track,
            applications: apps.split(',').map(a => a.trim())
        })
    });
    
    // Second: Run discovery
    await fetch('/api/v1/monitoring/appd/discovery/run', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            config_name: configName,
            lob_name: lob,
            applications: apps.split(',').map(a => a.trim())
        })
    });
}
```

#### **Step 3: Backend Saves Config**

```python
# routes.py - /config/save endpoint
@router.post("/config/save")
async def save_appd_config(request: ConfigSaveRequest):
    config_data = {
        "config_name": "Retail_Q1_2026",
        "lob_name": "Retail",
        "track": "Q1_2026",
        "applications": ["RetailWeb", "RetailAPI"],
        "is_active": "Y"
    }
    appd_db.save_config(config_data)
```

```sql
-- database.py - Saves to APPD_LOB_CONFIG table
INSERT INTO APPD_LOB_CONFIG (
    LOB_ID, CONFIG_NAME, LOB_NAME, TRACK, APPLICATION_NAMES
) VALUES (
    1, 'Retail_Q1_2026', 'Retail', 'Q1_2026', 
    '["RetailWeb", "RetailAPI"]'
);
```

**Database State After Step 3:**
```
APPD_LOB_CONFIG Table:
┌────────┬─────────────────┬──────────┬─────────┬────────────────────────────┐
│ LOB_ID │ CONFIG_NAME     │ LOB_NAME │ TRACK   │ APPLICATION_NAMES          │
├────────┼─────────────────┼──────────┼─────────┼────────────────────────────┤
│ 1      │ Retail_Q1_2026  │ Retail   │ Q1_2026 │ ["RetailWeb","RetailAPI"]  │
└────────┴─────────────────┴──────────┴─────────┴────────────────────────────┘
```

#### **Step 4: Backend Runs Discovery**

```python
# routes.py - /discovery/run endpoint
@router.post("/discovery/run")
async def run_discovery(request: DiscoveryRequest):
    # Calls discovery_service.run_discovery_for_lob()
    # This connects to AppDynamics REST API
```

```python
# discovery.py - Discovery logic
class AppDynamicsDiscoveryService:
    def run_discovery_for_lob(self, lob_name):
        # 1. Get config from database
        # 2. For each application in config:
        #    - Get all tiers from AppD API
        #    - For each tier, get all nodes
        #    - Calculate CPM (Calls Per Minute) for each node
        #    - Classify: CPM >= 10 → Active, CPM < 10 → Inactive
        # 3. Save to database
```

#### **Step 5: Discovery Process Details**

```
For Application "RetailWeb":
┌─────────────────────────────────────────────────────────┐
│ 1. Call AppD API: GET /applications/RetailWeb/tiers    │
│    Response: ["WebTier", "ServiceTier"]                 │
│                                                          │
│ 2. For "WebTier":                                       │
│    Call AppD API: GET /tiers/WebTier/nodes             │
│    Response: [                                          │
│      {name: "Node1", id: 123, ...},                    │
│      {name: "Node2", id: 124, ...}                     │
│    ]                                                    │
│                                                          │
│ 3. For each node, get CPM metric:                      │
│    Call AppD API: GET /nodes/123/metrics?name=Calls... │
│    Response: {value: 150}  ← 150 calls/minute          │
│                                                          │
│ 4. Classify:                                            │
│    Node1: CPM=150 → 150 >= 10 → ACTIVE ✅              │
│    Node2: CPM=2   → 2 < 10    → INACTIVE ❌            │
│                                                          │
│ 5. Save to database                                     │
└─────────────────────────────────────────────────────────┘
```

#### **Step 6: Save Discovery Results**

```sql
-- APPD_APPLICATIONS table
INSERT INTO APPD_APPLICATIONS (APP_ID, LOB_ID, APPLICATION_NAME, TOTAL_NODES, ACTIVE_NODES)
VALUES (1, 1, 'RetailWeb', 10, 7);  -- 7 out of 10 active

-- APPD_TIERS table
INSERT INTO APPD_TIERS (TIER_ID, APP_ID, TIER_NAME, TOTAL_NODES, ACTIVE_NODES)
VALUES (1, 1, 'WebTier', 5, 4);  -- 4 out of 5 active

-- APPD_NODES table (with CPM-based classification)
INSERT INTO APPD_NODES (NODE_ID, TIER_ID, NODE_NAME, CALLS_PER_MINUTE, IS_ACTIVE)
VALUES (1, 1, 'WebNode1', 150, 'Y');  -- Active: CPM >= 10

INSERT INTO APPD_NODES (NODE_ID, TIER_ID, NODE_NAME, CALLS_PER_MINUTE, IS_ACTIVE)
VALUES (2, 1, 'WebNode2', 2, 'N');    -- Inactive: CPM < 10
```

**Database State After Discovery:**
```
APPD_NODES Table (simplified):
┌─────────┬──────────┬───────────┬──────────────────┬───────────┐
│ NODE_ID │ TIER_ID  │ NODE_NAME │ CALLS_PER_MINUTE │ IS_ACTIVE │
├─────────┼──────────┼───────────┼──────────────────┼───────────┤
│ 1       │ 1        │ WebNode1  │ 150.5            │ Y         │ ✅ Active
│ 2       │ 1        │ WebNode2  │ 2.3              │ N         │ ❌ Inactive
│ 3       │ 1        │ WebNode3  │ 85.7             │ Y         │ ✅ Active
│ 4       │ 2        │ APINode1  │ 220.0            │ Y         │ ✅ Active
│ 5       │ 2        │ APINode2  │ 0.1              │ N         │ ❌ Inactive
└─────────┴──────────┴───────────┴──────────────────┴───────────┘
```

---

### **PHASE 2: Health Check**
*Purpose: View active nodes before starting monitoring*

#### **Step 1: User Selects Config in UI**

```
UI:
┌─────────────────────────────────────┐
│ Select Config: [Retail_Q1_2026 ▼]  │
│                                     │
│ [🏥 Get Active Nodes]              │
└─────────────────────────────────────┘
```

#### **Step 2: UI Calls Health Check API**

```javascript
async function runHealthCheck() {
    const config = document.getElementById('healthCheckConfig').value;
    
    const response = await fetch(
        `/api/v1/monitoring/appd/health/${config}`
    );
    const data = await response.json();
    
    // Display results
    displayActiveNodes(data);
}
```

#### **Step 3: Backend Queries Database**

```python
# routes.py
@router.get("/health/{config_name}")
async def get_lob_health(config_name: str):
    # Query database for active nodes
    active_nodes = appd_db.get_active_nodes_for_config(config_name)
    return {"total_active_nodes": len(active_nodes), ...}
```

```sql
-- database.py - Query only active nodes
SELECT 
    a.APPLICATION_NAME,
    t.TIER_NAME,
    n.NODE_NAME,
    n.CALLS_PER_MINUTE
FROM APPD_LOB_CONFIG lob
JOIN APPD_APPLICATIONS a ON lob.LOB_ID = a.LOB_ID
JOIN APPD_TIERS t ON a.APP_ID = t.APP_ID
JOIN APPD_NODES n ON t.TIER_ID = n.TIER_ID
WHERE lob.CONFIG_NAME = 'Retail_Q1_2026'
  AND n.IS_ACTIVE = 'Y'  -- Only active nodes!
ORDER BY a.APPLICATION_NAME, t.TIER_NAME, n.NODE_NAME;
```

#### **Step 4: UI Displays Results**

```
Health Check Results:
┌──────────────────────────────────────────────────┐
│ ✅ Active Nodes: 3                               │
│                                                  │
│ RetailWeb / WebTier:                            │
│   • WebNode1 (CPM: 150.5)                       │
│   • WebNode3 (CPM: 85.7)                        │
│                                                  │
│ RetailAPI / APITier:                            │
│   • APINode1 (CPM: 220.0)                       │
└──────────────────────────────────────────────────┘
```

---

### **PHASE 3: Start Monitoring (Code 3)**
*Purpose: Collect metrics during performance test*

#### **Step 1: User Fills Monitoring Form**

```
UI:
┌─────────────────────────────────────┐
│ Run ID: RUN_20260227_001           │ (Unique test ID)
│ Config: [Retail_Q1_2026 ▼]         │ (Pre-saved config)
│ Test Name: Peak Load Test          │ (Optional)
│ Interval: [30 minutes ▼]           │ (Collection frequency)
│                                     │
│ [▶️ Start Monitoring]              │
└─────────────────────────────────────┘
```

#### **Step 2: UI Calls Start Monitoring API**

```javascript
async function startMonitoring() {
    const runId = document.getElementById('monitorRunId').value;
    const config = document.getElementById('monitorConfig').value;
    const testName = document.getElementById('monitorTestName').value;
    const interval = parseInt(document.getElementById('monitorInterval').value);
    
    await fetch('/api/v1/monitoring/appd/monitoring/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            run_id: runId,
            config_name: config,
            test_name: testName,
            interval_seconds: interval
        })
    });
}
```

#### **Step 3: Backend Creates Monitoring Session**

```python
# routes.py
@router.post("/monitoring/start")
async def start_monitoring(request: StartMonitoringRequest):
    # 1. Validate run_id is unique
    # 2. Check thread pool capacity
    # 3. Create monitoring run in database
    # 4. Start background thread
    
    orchestrator.start_monitoring(
        run_id="RUN_20260227_001",
        config_name="Retail_Q1_2026",
        applications=["RetailWeb", "RetailAPI"]
    )
    
    # Launch background worker thread
    thread = threading.Thread(
        target=monitoring_worker,
        args=(run_id, interval_seconds)
    )
    thread.start()
```

#### **Step 4: Create Monitoring Run Record**

```sql
-- database.py - Create run record
INSERT INTO APPD_MONITORING_RUNS (
    RUN_ID, LOB_ID, LOB_NAME, TRACK, TEST_NAME,
    START_TIME, STATUS, COLLECTION_INTERVAL_SECONDS,
    APPLICATIONS
) VALUES (
    'RUN_20260227_001', 
    1, 
    'Retail', 
    'Q1_2026', 
    'Peak Load Test',
    SYSTIMESTAMP, 
    'RUNNING', 
    1800,  -- 30 minutes
    '["RetailWeb", "RetailAPI"]'
);
```

**Database State:**
```
APPD_MONITORING_RUNS Table:
┌──────────────────┬────────┬──────────┬─────────┬─────────────────┬──────────┬──────────┐
│ RUN_ID           │ LOB_ID │ LOB_NAME │ TRACK   │ TEST_NAME       │ STATUS   │ INTERVAL │
├──────────────────┼────────┼──────────┼─────────┼─────────────────┼──────────┼──────────┤
│ RUN_20260227_001 │ 1      │ Retail   │ Q1_2026 │ Peak Load Test  │ RUNNING  │ 1800     │
└──────────────────┴────────┴──────────┴─────────┴─────────────────┴──────────┴──────────┘
```

#### **Step 5: Background Worker Collects Metrics**

```python
# routes.py - Background worker thread
def monitoring_worker(run_id: str, interval_seconds: int):
    """
    This runs in background, collecting metrics every N seconds
    """
    while True:
        try:
            # 1. Check if still running
            status = orchestrator.get_session_status(run_id)
            if status != 'RUNNING':
                break
            
            # 2. Collect metrics for all active nodes
            orchestrator.collect_metrics_once(run_id)
            
            # 3. Sleep until next collection
            time.sleep(interval_seconds)  # 1800 seconds = 30 minutes
            
        except Exception as e:
            log_error(e)
            time.sleep(60)  # Wait 1 minute on error
```

#### **Step 6: Metrics Collection Process**

```python
# orchestrator.py - Collect metrics
def collect_metrics_once(self, run_id):
    """
    For each active node in the monitoring run:
    1. Collect Server Metrics (CPU, Memory, Disk, Network)
    2. Collect JVM Metrics (Heap, GC, Threads)
    3. Collect Application Metrics (Response Time, Errors, Throughput)
    """
    
    # Get all active nodes for this run
    nodes = self.get_active_nodes_for_run(run_id)
    
    for node in nodes:
        # Server metrics
        server_metrics = self.collectors.collect_server_metrics(
            node['application_id'],
            node['tier_id'],
            node['node_id']
        )
        self.db.insert_server_metrics(run_id, node['node_id'], server_metrics)
        
        # JVM metrics
        jvm_metrics = self.collectors.collect_jvm_metrics(
            node['application_id'],
            node['node_id']
        )
        self.db.insert_jvm_metrics(run_id, node['node_id'], jvm_metrics)
        
        # Application metrics
        app_metrics = self.collectors.collect_app_metrics(
            node['application_id'],
            node['tier_id'],
            node['node_id']
        )
        self.db.insert_application_metrics(
            run_id, node['node_id'], node['tier_id'], 
            node['app_id'], app_metrics
        )
```

#### **Step 7: Metrics Saved to Database**

```sql
-- Server Metrics (every 30 minutes)
INSERT INTO APPD_SERVER_METRICS (
    METRIC_ID, RUN_ID, NODE_ID, COLLECTION_TIME,
    CPU_BUSY_PERCENT, MEMORY_USED_PERCENT, DISK_USED_PERCENT
) VALUES (
    1, 'RUN_20260227_001', 1, SYSTIMESTAMP,
    45.5, 72.3, 68.9
);

-- JVM Metrics (every 30 minutes)
INSERT INTO APPD_JVM_METRICS (
    METRIC_ID, RUN_ID, NODE_ID, COLLECTION_TIME,
    HEAP_USED_MB, GC_TIME_MS, THREAD_COUNT
) VALUES (
    1, 'RUN_20260227_001', 1, SYSTIMESTAMP,
    2048, 150, 125
);

-- Application Metrics (every 30 minutes)
INSERT INTO APPD_APPLICATION_METRICS (
    METRIC_ID, RUN_ID, NODE_ID, TIER_ID, APP_ID, COLLECTION_TIME,
    CALLS_PER_MINUTE, RESPONSE_TIME_AVG_MS, ERROR_RATE_PERCENT
) VALUES (
    1, 'RUN_20260227_001', 1, 1, 1, SYSTIMESTAMP,
    150.5, 250.0, 0.5
);
```

**Timeline of Metrics Collection:**
```
00:00 - Start Monitoring
00:30 - First Collection  → 3 metrics inserted per node
01:00 - Second Collection → 3 metrics inserted per node
01:30 - Third Collection  → 3 metrics inserted per node
02:00 - Fourth Collection → 3 metrics inserted per node
...
```

---

### **PHASE 4: View Active Sessions**
*Purpose: Monitor running collection sessions*

#### **Step 1: Auto-Refresh Sessions in UI**

```javascript
// Auto-refresh every 10 seconds
setInterval(() => {
    refreshSessions();
}, 10000);

async function refreshSessions() {
    const response = await fetch('/api/v1/monitoring/appd/monitoring/sessions');
    const data = await response.json();
    
    displaySessions(data.sessions);
}
```

#### **Step 2: Backend Returns All Sessions**

```python
# routes.py
@router.get("/monitoring/sessions")
async def list_sessions():
    sessions = orchestrator.get_all_sessions()
    return {"total_sessions": len(sessions), "sessions": sessions}
```

```sql
-- Query all monitoring runs
SELECT 
    RUN_ID, LOB_NAME, TRACK, TEST_NAME, STATUS,
    START_TIME, END_TIME,
    TOTAL_COLLECTIONS, SUCCESSFUL_COLLECTIONS, FAILED_COLLECTIONS
FROM APPD_MONITORING_RUNS
ORDER BY START_TIME DESC;
```

#### **Step 3: UI Displays Session Cards**

```
Active Monitoring Sessions:
┌─────────────────────────────────────────────────────┐
│ 🟢 Retail / Q1_2026 / RUN_20260227_001            │
│ Status: RUNNING                                     │
│ Applications: RetailWeb, RetailAPI                  │
│ Iterations: 4                                       │
│ Started: 2026-02-27 10:00:00                       │
│                                                     │
│ [⏹️ Stop] [👁️ View Details]                       │
├─────────────────────────────────────────────────────┤
│ Progress: [████████░░░░░░░░░░] Collecting...       │
└─────────────────────────────────────────────────────┘
```

---

### **PHASE 5: Stop Monitoring**

#### **Step 1: User Clicks Stop**

```javascript
async function stopMonitoring(runId) {
    if (!confirm('Stop monitoring?')) return;
    
    await fetch(`/api/v1/monitoring/appd/monitoring/stop/${runId}`, {
        method: 'POST'
    });
    
    refreshSessions();  // Refresh UI
}
```

#### **Step 2: Backend Stops Session**

```python
# routes.py
@router.post("/monitoring/stop/{run_id}")
async def stop_monitoring(run_id: str):
    orchestrator.stop_monitoring(run_id)
    return {"success": True}
```

```sql
-- Update monitoring run
UPDATE APPD_MONITORING_RUNS
SET STATUS = 'STOPPED',
    END_TIME = SYSTIMESTAMP
WHERE RUN_ID = 'RUN_20260227_001';
```

#### **Step 3: Background Thread Exits**

```python
def monitoring_worker(run_id, interval_seconds):
    while True:
        status = orchestrator.get_session_status(run_id)
        if status != 'RUNNING':  # ← Status changed to STOPPED
            break  # Exit loop, thread terminates
        ...
```

---

## 📊 Complete Data Flow Summary

```
USER INPUT
    ↓
┌──────────────────────┐
│ 1. Discovery Form    │ → Config: Retail_Q1_2026
│    (UI)              │   LOB: Retail, Track: Q1_2026
└──────────────────────┘   Apps: RetailWeb, RetailAPI
    ↓
┌──────────────────────┐
│ 2. Save Config       │ → APPD_LOB_CONFIG table
│    (Backend)         │   INSERT config record
└──────────────────────┘
    ↓
┌──────────────────────┐
│ 3. Run Discovery     │ → Connect to AppD REST API
│    (Backend)         │   Get: Apps → Tiers → Nodes → CPM
└──────────────────────┘   Classify: CPM >= 10 = Active
    ↓
┌──────────────────────┐
│ 4. Save Discovery    │ → APPD_APPLICATIONS
│    (Database)        │   APPD_TIERS
└──────────────────────┘   APPD_NODES (with IS_ACTIVE)
    ↓
┌──────────────────────┐
│ 5. Health Check      │ → Query: WHERE IS_ACTIVE = 'Y'
│    (UI Request)      │   Return: 3 active nodes
└──────────────────────┘
    ↓
┌──────────────────────┐
│ 6. Start Monitoring  │ → APPD_MONITORING_RUNS
│    (User Action)     │   CREATE run record
└──────────────────────┘   START background thread
    ↓
┌──────────────────────┐
│ 7. Collect Metrics   │ → Every 30 minutes:
│    (Background)      │   - APPD_SERVER_METRICS
└──────────────────────┘   - APPD_JVM_METRICS
    ↓                      - APPD_APPLICATION_METRICS
┌──────────────────────┐
│ 8. View Sessions     │ → Query APPD_MONITORING_RUNS
│    (UI Auto-refresh) │   Display status cards
└──────────────────────┘
    ↓
┌──────────────────────┐
│ 9. Stop Monitoring   │ → UPDATE STATUS = 'STOPPED'
│    (User Action)     │   Thread exits gracefully
└──────────────────────┘
```

---

## 🎯 Key Logic Points

### **1. Active Node Classification**
```python
# CPM (Calls Per Minute) threshold = 10
if node.calls_per_minute >= 10:
    node.is_active = 'Y'  # ✅ Active - receiving traffic
else:
    node.is_active = 'N'  # ❌ Inactive - no traffic
```

### **2. Config-Based Organization**
```
Config = Unique identifier for a discovery run
├── LOB (Line of Business)
├── Track (Release/Version)
└── Applications (List of AppD apps)

Example:
- Retail_Q1_2026 → Retail → Q1_2026 → [RetailWeb, RetailAPI]
- Banking_R2_2026 → Banking → R2_2026 → [BankingWeb, BankingCore]
```

### **3. Monitoring Run Structure**
```
Run ID = Unique identifier for a performance test
├── Links to Config
├── Has Start/End Time
├── Collects metrics every N seconds
└── Stores metrics in 3 tables (Server, JVM, Application)
```

### **4. Background Thread Pattern**
```python
# One thread per monitoring run
# Runs until STATUS != 'RUNNING'
# Sleeps between collections (interval_seconds)
# Auto-terminates when stopped
```

---

This is the complete workflow! Each phase builds on the previous one, creating a comprehensive monitoring solution. 🚀