# 🔧 Fixes for UI Issues - Registration Tab & AppD Integration

## 📋 Issues to Fix

1. **Register Test tab shows Oracle API content on first landing**
2. **Completed test still shows, cannot register new test**
3. **AppD monitoring not linked with PC_RUN_ID (null in database)**

---

## 🔧 FIX #1: Register Test Tab - Hide Oracle Content & Set as Default

### Issue:
Register Test tab shows Oracle SQL API content on first load.

### Solution:
Make Register Test the active tab by default and hide Oracle tab content.

**File:** `index.html`

**FIND THIS (in tabs section):**
```html
<div class="tabs" id="mainTabs">
    <button class="tab active" onclick="showTab(event, 'oracle')">Oracle SQL APIs</button>
    <button class="tab" onclick="showTab(event, 'registertest')">🎯 Register Test</button>
    ...
</div>
```

**CHANGE TO:**
```html
<div class="tabs" id="mainTabs">
    <button class="tab" onclick="showTab(event, 'registertest')">🎯 Register Test</button>
    <button class="tab" onclick="showTab(event, 'oracle')">Oracle SQL APIs</button>
    <button class="tab" onclick="showTab(event, 'appdynamics')">📊 AppDynamics</button>
    <button class="tab" onclick="showTab(event, 'awr')">AWR Analysis</button>
    <button class="tab" onclick="showTab(event, 'loadrunner')">LR Test Results</button>
    <button class="tab" onclick="showTab(event, 'mongodb')">MongoDB APIs</button>
    <button class="tab" onclick="showTab(event, 'splunk')">Splunk APIs</button>
</div>
```

**FIND THIS (in tab content section):**
```html
<div id="registertest" class="tab-content">
```

**CHANGE TO:**
```html
<div id="registertest" class="tab-content active">
```

**FIND THIS (Oracle tab content):**
```html
<div id="oracle" class="tab-content active">
```

**CHANGE TO:**
```html
<div id="oracle" class="tab-content">
```

---

## 🔧 FIX #2: Allow New Test Registration After Completion

### Issue:
Completed test status stays on screen, blocking new test registration.

### Solution:
Update the UI logic to allow new registration when test is COMPLETED.

**File:** `index.html`

**FIND THIS FUNCTION:**
```javascript
function displayCurrentTest(test) {
    document.getElementById('currentTestStatus').style.display = 'block';
    document.getElementById('registrationForm').style.display = 'none';
    
    document.getElementById('currentMasterRunId').textContent = test.run_id;
    document.getElementById('currentPcRunId').textContent = test.pc_run_id;
    document.getElementById('currentLob').textContent = test.lob_name;
    document.getElementById('currentTrack').textContent = test.track || 'N/A';
    document.getElementById('currentTestName').textContent = test.test_name;
    
    const statusElem = document.getElementById('currentTestStatus');
    statusElem.textContent = test.test_status;
    statusElem.style.color = test.test_status === 'COMPLETED' ? '#28a745' : '#ffc107';
}
```

**REPLACE WITH:**
```javascript
function displayCurrentTest(test) {
    // If test is COMPLETED, allow new registration
    if (test.test_status === 'COMPLETED' || test.test_status === 'FAILED') {
        document.getElementById('currentTestStatus').style.display = 'block';
        document.getElementById('registrationForm').style.display = 'block'; // Show both
        
        // Update the status message
        const statusDiv = document.getElementById('currentTestStatus');
        statusDiv.style.background = '#f0f0f0';
        statusDiv.style.borderLeftColor = '#6c757d';
        
        // Update title
        statusDiv.querySelector('h3').textContent = '✓ Previous Test (Completed)';
        statusDiv.querySelector('h3').style.color = '#6c757d';
    } else {
        // Test is active (INITIATED, RUNNING, ANALYZING)
        document.getElementById('currentTestStatus').style.display = 'block';
        document.getElementById('registrationForm').style.display = 'none';
    }
    
    document.getElementById('currentMasterRunId').textContent = test.run_id;
    document.getElementById('currentPcRunId').textContent = test.pc_run_id;
    document.getElementById('currentLob').textContent = test.lob_name;
    document.getElementById('currentTrack').textContent = test.track || 'N/A';
    document.getElementById('currentTestName').textContent = test.test_name;
    
    const statusElem = document.getElementById('currentTestStatus');
    statusElem.textContent = test.test_status;
    
    // Color coding based on status
    if (test.test_status === 'COMPLETED') {
        statusElem.style.color = '#28a745';
    } else if (test.test_status === 'FAILED') {
        statusElem.style.color = '#dc3545';
    } else {
        statusElem.style.color = '#ffc107';
    }
}
```

**ALSO UPDATE loadCurrentTestRun() FUNCTION:**
```javascript
async function loadCurrentTestRun() {
    try {
        const response = await fetch('/api/v1/pc/test-run/current');
        const data = await response.json();
        
        if (data.has_active_test) {
            currentTestRun = data.test_run;
            
            // Only show as "active" if test is not completed
            if (currentTestRun.test_status === 'COMPLETED' || currentTestRun.test_status === 'FAILED') {
                // Show completed test but allow new registration
                displayCurrentTest(currentTestRun);
                
                // Clear currentTestRun so user can register new test
                // But keep it visible for reference
                console.log('Last test completed. Ready for new registration.');
            } else {
                // Test is still active
                displayCurrentTest(currentTestRun);
            }
        } else {
            document.getElementById('currentTestStatus').style.display = 'none';
            document.getElementById('registrationForm').style.display = 'block';
        }
        
    } catch (error) {
        console.error('Error loading current test:', error);
        // On error, show registration form
        document.getElementById('currentTestStatus').style.display = 'none';
        document.getElementById('registrationForm').style.display = 'block';
    }
}
```

---

## 🔧 FIX #3: Link AppD Monitoring with PC_RUN_ID

### Issue:
AppD monitoring runs have PC_RUN_ID = NULL in database.

### Solution:
Update AppD monitoring start functions to include PC_RUN_ID from registered test.

**File:** `index.html`

**FIND THIS FUNCTION:**
```javascript
async function startMonitoring() {
    // Check if test is registered
    if (!currentTestRun) {
        alert('⚠️ Please register your Performance Center test run first!\n\nGo to "Register Test" tab and enter your PC Run ID.');
        return;
    }
    
    // ... existing code ...
}
```

**UPDATE TO INCLUDE PC_RUN_ID:**
```javascript
async function startMonitoring() {
    // Check if test is registered
    if (!currentTestRun) {
        alert('⚠️ Please register your Performance Center test run first!\n\nGo to "Register Test" tab and enter your PC Run ID.');
        return;
    }
    
    const configName = document.getElementById('configSelect').value;
    const duration = parseInt(document.getElementById('duration').value);
    const interval = parseInt(document.getElementById('interval').value);
    
    if (!configName) {
        alert('Please select a configuration');
        return;
    }
    
    const statusDiv = document.getElementById('monitoringStatus');
    statusDiv.style.display = 'block';
    statusDiv.className = 'alert alert-info';
    statusDiv.innerHTML = '⏳ Starting AppDynamics monitoring...';
    
    try {
        const requestBody = {
            config_name: configName,
            duration_minutes: duration,
            interval_seconds: interval,
            run_id: currentTestRun.run_id,           // ← ADD THIS
            pc_run_id: currentTestRun.pc_run_id,    // ← ADD THIS
            lob_name: currentTestRun.lob_name,       // ← ADD THIS
            track: currentTestRun.track              // ← ADD THIS
        };
        
        const response = await fetch('/api/v1/monitoring/appd/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        const data = await response.json();
        
        if (data.success) {
            statusDiv.className = 'alert alert-success';
            statusDiv.innerHTML = `
                ✓ Monitoring started successfully!<br>
                <strong>Session ID:</strong> ${data.monitoring_run_id}<br>
                <strong>Run ID:</strong> ${data.run_id}<br>
                <strong>PC Run ID:</strong> ${data.pc_run_id}<br>
                <strong>Applications:</strong> ${data.applications.length}<br>
                <strong>Duration:</strong> ${duration} minutes
            `;
            
            // Refresh monitoring sessions
            setTimeout(() => {
                loadMonitoringSessions();
            }, 1000);
        } else {
            statusDiv.className = 'alert alert-error';
            statusDiv.innerHTML = '✗ Error: ' + data.message;
        }
        
    } catch (error) {
        statusDiv.className = 'alert alert-error';
        statusDiv.innerHTML = '✗ Error: ' + error.message;
    }
}
```

---

## 🔧 BACKEND FIX: AppD Routes - Accept PC_RUN_ID

**File:** `monitoring/appd/routes.py` (or wherever your AppD start endpoint is)

**FIND THIS:**
```python
@router.post("/start")
async def start_monitoring(
    config_name: str,
    duration_minutes: int,
    interval_seconds: int = 60
):
```

**UPDATE TO:**
```python
@router.post("/start")
async def start_monitoring(
    config_name: str,
    duration_minutes: int,
    interval_seconds: int = 60,
    run_id: Optional[str] = None,
    pc_run_id: Optional[str] = None,
    lob_name: Optional[str] = None,
    track: Optional[str] = None
):
```

**THEN IN THE FUNCTION, WHEN CREATING MONITORING RUN:**
```python
# Generate AppD-specific run ID if master run_id provided
appd_run_id = None
if pc_run_id:
    from common.run_id_generator import RunIDGenerator
    appd_run_id = RunIDGenerator.generate_solution_run_id("AppD", pc_run_id, 1)

# When inserting into APPD_MONITORING_RUNS table:
cursor.execute("""
    INSERT INTO APPD_MONITORING_RUNS (
        MONITORING_RUN_ID, CONFIG_NAME, LOB_NAME, TRACK,
        APPD_RUN_ID, RUN_ID, PC_RUN_ID,
        STATUS, START_TIME, DURATION_MINUTES, INTERVAL_SECONDS
    ) VALUES (
        APPD_MONITORING_SEQ.NEXTVAL, :config_name, :lob_name, :track,
        :appd_run_id, :run_id, :pc_run_id,
        'RUNNING', SYSTIMESTAMP, :duration, :interval
    ) RETURNING MONITORING_RUN_ID INTO :mon_run_id
""", {
    'config_name': config_name,
    'lob_name': lob_name,
    'track': track,
    'appd_run_id': appd_run_id,
    'run_id': run_id,
    'pc_run_id': pc_run_id,
    'duration': duration_minutes,
    'interval': interval_seconds,
    'mon_run_id': cursor.var(cx_Oracle.NUMBER)
})
```

---

## 📝 ALTERNATIVE FIX #3: If AppD Table Doesn't Have PC_RUN_ID Column

If your APPD_MONITORING_RUNS table doesn't have PC_RUN_ID column yet:

**SQL to add columns:**
```sql
-- Add PC_RUN_ID and other columns to APPD_MONITORING_RUNS
ALTER TABLE APPD_MONITORING_RUNS ADD RUN_ID VARCHAR2(100);
ALTER TABLE APPD_MONITORING_RUNS ADD PC_RUN_ID VARCHAR2(50);
ALTER TABLE APPD_MONITORING_RUNS ADD APPD_RUN_ID VARCHAR2(150);

-- Add foreign key to RUN_MASTER
ALTER TABLE APPD_MONITORING_RUNS 
ADD CONSTRAINT FK_APPD_RUN_MASTER 
FOREIGN KEY (RUN_ID) REFERENCES RUN_MASTER(RUN_ID) ON DELETE CASCADE;

-- Add indexes
CREATE INDEX IDX_APPD_RUN_ID ON APPD_MONITORING_RUNS(RUN_ID);
CREATE INDEX IDX_APPD_PC_RUN_ID ON APPD_MONITORING_RUNS(PC_RUN_ID);

-- Add comments
COMMENT ON COLUMN APPD_MONITORING_RUNS.RUN_ID IS 'Links to central RUN_MASTER table';
COMMENT ON COLUMN APPD_MONITORING_RUNS.PC_RUN_ID IS 'Performance Center run ID';
COMMENT ON COLUMN APPD_MONITORING_RUNS.APPD_RUN_ID IS 'AppD-specific run ID: AppD_Run_DDMMMYYYY_SEQ_PCRUNID';
```

---

## ✅ Summary of Changes

### Fix #1: Registration Tab Default
- ✅ Make "Register Test" the first/active tab
- ✅ Remove "active" class from Oracle tab

### Fix #2: Allow New Registration
- ✅ Show form even when previous test is COMPLETED
- ✅ Display completed test as reference (grayed out)
- ✅ Allow user to register new test

### Fix #3: Link AppD with PC_RUN_ID
- ✅ Pass currentTestRun data to AppD start
- ✅ Include RUN_ID, PC_RUN_ID in request
- ✅ Update backend to save PC_RUN_ID
- ✅ Add database columns if missing

---

## 🧪 Testing

### Test Fix #1:
1. Clear browser cache
2. Open application
3. **Expected:** Register Test tab is active, shows registration form
4. Click Oracle tab
5. **Expected:** Oracle content shows

### Test Fix #2:
1. Register a test
2. Mark test as COMPLETED (in DB or via API)
3. Refresh page
4. **Expected:** 
   - Previous test shows (grayed out)
   - Registration form ALSO shows below
   - Can register new test

### Test Fix #3:
1. Register a test (PC_RUN_ID = 35678)
2. Go to AppD tab
3. Start monitoring
4. Check database:
```sql
SELECT RUN_ID, PC_RUN_ID, APPD_RUN_ID, CONFIG_NAME
FROM APPD_MONITORING_RUNS
ORDER BY START_TIME DESC
FETCH FIRST 1 ROW ONLY;
```
5. **Expected:** 
   - RUN_ID = RUNID_35678_04Mar2026_001
   - PC_RUN_ID = 35678
   - APPD_RUN_ID = AppD_Run_04Mar2026_001_35678

---

## 🎯 Result After Fixes

✅ **Register Test tab shows first**
✅ **Completed tests don't block new registration**
✅ **AppD monitoring properly linked with PC_RUN_ID**
✅ **All monitoring solutions linked via master RUN_ID**

Let me know if you need any clarification on these fixes! 🚀