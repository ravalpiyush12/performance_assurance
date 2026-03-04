# 🎯 PC Run ID Registration - Complete Solution

## 📋 The Problem

**Current Flow (Won't Work):**
```
User starts PC test manually in LoadRunner → Gets PC_RUN_ID = 35678
User goes to AppD tab → Tries to start monitoring
❌ ERROR: No master RUN_ID exists yet!
❌ System doesn't know about PC_RUN_ID = 35678
```

**What We Need:**
```
User starts PC test manually → Gets PC_RUN_ID = 35678
User registers PC_RUN_ID in system FIRST → Creates master entry
User can now start any monitoring (AppD, AWR, etc.) → All link to master
✅ All monitoring activities link to registered PC_RUN_ID
```

---

## 🎯 Solution: Add "Register Test Run" Feature

### Option 1: Dedicated Tab (RECOMMENDED)
### Option 2: Modal Popup on Landing Page
### Option 3: Add to Each Monitoring Tab

I'll provide **Option 1** (most user-friendly):

---

## 📝 INCREMENTAL CHANGE #1: Add "Register Test" Tab

**File:** `index.html`  
**Location:** Update the tabs section

**FIND THIS:**
```html
<div class="tabs" id="mainTabs">
    <button class="tab active" onclick="showTab(event, 'oracle')">Oracle SQL APIs</button>
    <button class="tab" onclick="showTab(event, 'appdynamics')">📊 AppDynamics</button>
    ...
</div>
```

**REPLACE WITH:**
```html
<div class="tabs" id="mainTabs">
    <button class="tab active" onclick="showTab(event, 'registertest')">🎯 Register Test</button>
    <button class="tab" onclick="showTab(event, 'oracle')">Oracle SQL APIs</button>
    <button class="tab" onclick="showTab(event, 'appdynamics')">📊 AppDynamics</button>
    <button class="tab" onclick="showTab(event, 'awr')">AWR Analysis</button>
    <button class="tab" onclick="showTab(event, 'loadrunner')">LR Test Results</button>
    <button class="tab" onclick="showTab(event, 'mongodb')">MongoDB APIs</button>
    <button class="tab" onclick="showTab(event, 'splunk')">Splunk APIs</button>
</div>
```

---

## 📝 INCREMENTAL CHANGE #2: Add Register Test Tab Content

**File:** `index.html`  
**Location:** Add as the FIRST tab content (before Oracle SQL tab)

**ADD THIS TAB:**
```html
<!-- Register Test Run Tab -->
<div id="registertest" class="tab-content active">
    <h2>🎯 Register Performance Test Run</h2>
    <p style="color: #666; margin-bottom: 20px;">
        Register your Performance Center test run BEFORE starting any monitoring activities.
        This creates a master entry that links all monitoring solutions together.
    </p>
    
    <!-- Current Registration Status -->
    <div class="appd-section" id="currentTestStatus" style="display: none; background: #e3f2fd; border-left: 4px solid #2196f3;">
        <h3 style="color: #1976d2;">✅ Active Test Registration</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
            <div>
                <div style="font-size: 0.85em; color: #666;">Master Run ID</div>
                <div style="font-weight: bold; font-size: 1.1em; color: #1976d2;" id="currentMasterRunId">--</div>
            </div>
            <div>
                <div style="font-size: 0.85em; color: #666;">PC Run ID</div>
                <div style="font-weight: bold; font-size: 1.1em; color: #1976d2;" id="currentPcRunId">--</div>
            </div>
            <div>
                <div style="font-size: 0.85em; color: #666;">LOB</div>
                <div style="font-weight: bold; font-size: 1.1em; color: #1976d2;" id="currentLob">--</div>
            </div>
            <div>
                <div style="font-size: 0.85em; color: #666;">Track</div>
                <div style="font-weight: bold; font-size: 1.1em; color: #1976d2;" id="currentTrack">--</div>
            </div>
            <div>
                <div style="font-size: 0.85em; color: #666;">Test Name</div>
                <div style="font-weight: bold; font-size: 1.1em; color: #1976d2;" id="currentTestName">--</div>
            </div>
            <div>
                <div style="font-size: 0.85em; color: #666;">Status</div>
                <div style="font-weight: bold; font-size: 1.1em;" id="currentTestStatus">--</div>
            </div>
        </div>
        <div style="margin-top: 15px; text-align: center;">
            <button class="btn" style="background: #28a745;" onclick="continueWithCurrentTest()">
                ✓ Continue with This Test
            </button>
            <button class="btn" style="background: #dc3545; margin-left: 10px;" onclick="clearCurrentTest()">
                🔄 Register New Test
            </button>
        </div>
    </div>
    
    <!-- Registration Form -->
    <div class="appd-section" id="registrationForm">
        <h3>📝 Register New Test Run</h3>
        <p style="color: #666; margin-bottom: 15px;">
            Fill in the details of your Performance Center test run
        </p>
        
        <div class="form-group">
            <label>Performance Center Run ID: *</label>
            <input type="text" id="regPcRunId" placeholder="e.g., 35678" required>
            <small style="color: #666;">
                The run ID from LoadRunner Performance Center (you get this when you start the test)
            </small>
        </div>
        
        <div class="form-group">
            <label>Test Name: *</label>
            <input type="text" id="regTestName" placeholder="e.g., Peak Load Test - Q1 2026" required>
            <small style="color: #666;">
                Descriptive name for this test run
            </small>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
            <div class="form-group">
                <label>LOB: *</label>
                <select id="regLob" required>
                    <option value="">-- Select LOB --</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>Track:</label>
                <input type="text" id="regTrack" placeholder="e.g., CDV3">
            </div>
        </div>
        
        <div class="form-group">
            <label>Test Start Time (Optional):</label>
            <input type="datetime-local" id="regStartTime">
            <small style="color: #666;">
                When did you start the Performance Center test? (Leave blank to use current time)
            </small>
        </div>
        
        <div class="form-group">
            <label>Notes (Optional):</label>
            <textarea id="regNotes" rows="3" placeholder="Any additional notes about this test run..."></textarea>
        </div>
        
        <button class="btn btn-success" onclick="registerTestRun()" style="font-size: 1.1em; padding: 15px 40px;">
            🎯 Register Test Run
        </button>
        
        <div id="registrationStatus" style="display: none; margin-top: 15px;"></div>
    </div>
    
    <!-- How to Use -->
    <div class="appd-section" style="background: #fff9e6; border-left: 4px solid #ffc107;">
        <h3 style="color: #856404;">💡 How to Use</h3>
        <ol style="color: #666; line-height: 1.8;">
            <li><strong>Start your Performance Center test</strong> - You'll get a Run ID (e.g., 35678)</li>
            <li><strong>Come here and register it</strong> - Fill in the form above with PC Run ID and test details</li>
            <li><strong>Start monitoring</strong> - Go to AppD, AWR, or any other monitoring tab</li>
            <li><strong>All monitoring will link to this test</strong> - Everything connects automatically!</li>
        </ol>
        <p style="margin-top: 15px; padding: 12px; background: white; border-radius: 6px; color: #856404;">
            <strong>⚠️ Important:</strong> You MUST register the test run BEFORE starting any monitoring activities. 
            Otherwise, monitoring data won't be properly linked.
        </p>
    </div>
    
    <!-- Recent Registrations -->
    <div class="appd-section">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <h3 style="margin: 0;">📋 Recent Test Registrations</h3>
            <button class="btn-refresh" onclick="loadRecentRegistrations()">🔄 Refresh</button>
        </div>
        
        <div id="recentRegistrations">
            <p style="text-align: center; color: #999;">Loading...</p>
        </div>
    </div>
</div>
```

---

## 📝 INCREMENTAL CHANGE #3: Add Backend API Endpoint

**File:** `monitoring/routes.py`  
**Location:** Add this endpoint to the unified routes file

**ADD THIS ENDPOINT:**
```python
@router.post("/test-run/register")
async def register_test_run(
    pc_run_id: str = Form(..., description="Performance Center run ID"),
    lob_name: str = Form(..., description="Line of Business"),
    test_name: str = Form(..., description="Test name"),
    track: Optional[str] = Form(None),
    test_start_time: Optional[str] = Form(None),
    created_by: Optional[str] = Form(None)
):
    """
    Register a Performance Center test run
    Creates master RUN_ID that all monitoring solutions will link to
    """
    if not monitoring_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        # Generate master run ID
        sequence = monitoring_db.get_next_sequence_for_pc_run(pc_run_id)
        master_run_id = RunIDGenerator.generate_master_run_id(pc_run_id, sequence)
        
        logger.info(f"Registering test run: {master_run_id}")
        
        # Parse start time if provided
        start_time = None
        if test_start_time:
            from datetime import datetime
            start_time = datetime.fromisoformat(test_start_time)
        
        # Create master entry
        success = monitoring_db.create_master_run(
            run_id=master_run_id,
            pc_run_id=pc_run_id,
            lob_name=lob_name,
            track=track,
            test_name=test_name,
            created_by=created_by
        )
        
        if success:
            # Update start time if provided
            if start_time:
                monitoring_db.update_run_start_time(master_run_id, start_time)
            
            return {
                "success": True,
                "master_run_id": master_run_id,
                "pc_run_id": pc_run_id,
                "lob_name": lob_name,
                "track": track,
                "test_name": test_name,
                "message": f"Test run registered successfully! Master Run ID: {master_run_id}"
            }
        else:
            # Run already exists
            return {
                "success": False,
                "message": f"Test run with PC_RUN_ID {pc_run_id} is already registered today"
            }
            
    except Exception as e:
        logger.error(f"Error registering test run: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-run/current")
async def get_current_test_run():
    """Get the most recently registered test run"""
    if not monitoring_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        run = monitoring_db.get_latest_test_run()
        
        if run:
            return {
                "success": True,
                "has_active_test": True,
                "test_run": run
            }
        else:
            return {
                "success": True,
                "has_active_test": False,
                "message": "No active test run found"
            }
            
    except Exception as e:
        logger.error(f"Error getting current test run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-run/recent")
async def get_recent_test_runs(limit: int = 10):
    """Get recent test run registrations"""
    if not monitoring_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        runs = monitoring_db.get_recent_test_runs(limit)
        
        return {
            "success": True,
            "count": len(runs),
            "test_runs": runs
        }
            
    except Exception as e:
        logger.error(f"Error getting recent test runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 📝 INCREMENTAL CHANGE #4: Add Database Methods

**File:** `monitoring/database.py`  
**Location:** Add these methods to the MonitoringDatabase class

**ADD THESE METHODS:**
```python
def get_next_sequence_for_pc_run(self, pc_run_id: str) -> int:
    """Get next sequence number for today's runs with same PC_RUN_ID"""
    conn = self.pool.acquire()
    cursor = conn.cursor()
    
    try:
        from datetime import date
        today = date.today()
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM RUN_MASTER 
            WHERE PC_RUN_ID = :pc_run_id 
              AND TRUNC(CREATED_DATE) = :today
        """, {'pc_run_id': pc_run_id, 'today': today})
        
        count = cursor.fetchone()[0]
        return count + 1
        
    finally:
        cursor.close()
        conn.close()

def update_run_start_time(self, run_id: str, start_time: datetime):
    """Update test start time"""
    conn = self.pool.acquire()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE RUN_MASTER
            SET TEST_START_TIME = :start_time,
                UPDATED_DATE = SYSDATE
            WHERE RUN_ID = :run_id
        """, {
            'start_time': start_time,
            'run_id': run_id
        })
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating start time: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def get_latest_test_run(self) -> Optional[Dict]:
    """Get the most recently created test run"""
    conn = self.pool.acquire()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                RUN_ID, PC_RUN_ID, LOB_NAME, TRACK, TEST_NAME,
                TEST_STATUS, TEST_START_TIME, CREATED_DATE
            FROM RUN_MASTER
            ORDER BY CREATED_DATE DESC
            FETCH FIRST 1 ROW ONLY
        """)
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return {
            'run_id': row[0],
            'pc_run_id': row[1],
            'lob_name': row[2],
            'track': row[3],
            'test_name': row[4],
            'test_status': row[5],
            'test_start_time': row[6].isoformat() if row[6] else None,
            'created_date': row[7].isoformat() if row[7] else None
        }
        
    finally:
        cursor.close()
        conn.close()

def get_recent_test_runs(self, limit: int = 10) -> List[Dict]:
    """Get recent test run registrations"""
    conn = self.pool.acquire()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                RUN_ID, PC_RUN_ID, LOB_NAME, TRACK, TEST_NAME,
                TEST_STATUS, TEST_START_TIME, CREATED_DATE
            FROM RUN_MASTER
            ORDER BY CREATED_DATE DESC
            FETCH FIRST :limit ROWS ONLY
        """, {'limit': limit})
        
        runs = []
        for row in cursor.fetchall():
            runs.append({
                'run_id': row[0],
                'pc_run_id': row[1],
                'lob_name': row[2],
                'track': row[3],
                'test_name': row[4],
                'test_status': row[5],
                'test_start_time': row[6].isoformat() if row[6] else None,
                'created_date': row[7].isoformat() if row[7] else None
            })
        
        return runs
        
    finally:
        cursor.close()
        conn.close()

def get_master_run_by_pc_id(self, pc_run_id: str) -> Optional[Dict]:
    """Get master run by PC Run ID"""
    conn = self.pool.acquire()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                RUN_ID, PC_RUN_ID, LOB_NAME, TRACK, TEST_NAME,
                TEST_STATUS, TEST_START_TIME, CREATED_DATE
            FROM RUN_MASTER
            WHERE PC_RUN_ID = :pc_run_id
            ORDER BY CREATED_DATE DESC
            FETCH FIRST 1 ROW ONLY
        """, {'pc_run_id': pc_run_id})
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return {
            'run_id': row[0],
            'pc_run_id': row[1],
            'lob_name': row[2],
            'track': row[3],
            'test_name': row[4],
            'test_status': row[5],
            'test_start_time': row[6].isoformat() if row[6] else None,
            'created_date': row[7].isoformat() if row[7] else None
        }
        
    finally:
        cursor.close()
        conn.close()
```

---

## 📝 INCREMENTAL CHANGE #5: Add JavaScript Functions

**File:** `index.html`  
**Location:** Inside `<script>` tag

**ADD THESE FUNCTIONS:**
```javascript
// ==========================================
// Test Registration Functions
// ==========================================

let currentTestRun = null;

async function loadCurrentTestRun() {
    try {
        const response = await fetch('/api/v1/monitoring/test-run/current');
        const data = await response.json();
        
        if (data.has_active_test) {
            currentTestRun = data.test_run;
            displayCurrentTest(currentTestRun);
        } else {
            document.getElementById('currentTestStatus').style.display = 'none';
            document.getElementById('registrationForm').style.display = 'block';
        }
        
    } catch (error) {
        console.error('Error loading current test:', error);
    }
}

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

function continueWithCurrentTest() {
    if (currentTestRun) {
        // Set global LOB if not already set
        if (!selectedLOB) {
            selectedLOB = currentTestRun.lob_name;
        }
        
        alert(`✓ Continuing with test:\n\nPC Run ID: ${currentTestRun.pc_run_id}\nTest: ${currentTestRun.test_name}\n\nYou can now use any monitoring tab!`);
        
        // Switch to AppD tab or whichever tab user wants
        showTab({currentTarget: document.querySelector('[onclick*="appdynamics"]')}, 'appdynamics');
    }
}

function clearCurrentTest() {
    if (confirm('Are you sure you want to register a new test? This will hide the current test registration.')) {
        currentTestRun = null;
        document.getElementById('currentTestStatus').style.display = 'none';
        document.getElementById('registrationForm').style.display = 'block';
        
        // Clear form
        document.getElementById('regPcRunId').value = '';
        document.getElementById('regTestName').value = '';
        document.getElementById('regTrack').value = '';
        document.getElementById('regStartTime').value = '';
        document.getElementById('regNotes').value = '';
    }
}

async function registerTestRun() {
    const pcRunId = document.getElementById('regPcRunId').value.trim();
    const testName = document.getElementById('regTestName').value.trim();
    const lob = document.getElementById('regLob').value;
    const track = document.getElementById('regTrack').value.trim();
    const startTime = document.getElementById('regStartTime').value;
    
    if (!pcRunId || !testName || !lob) {
        alert('Please fill in all required fields (*)');
        return;
    }
    
    const statusDiv = document.getElementById('registrationStatus');
    statusDiv.style.display = 'block';
    statusDiv.className = 'alert alert-info';
    statusDiv.innerHTML = '⏳ Registering test run...';
    
    try {
        const formData = new FormData();
        formData.append('pc_run_id', pcRunId);
        formData.append('test_name', testName);
        formData.append('lob_name', lob);
        if (track) formData.append('track', track);
        if (startTime) formData.append('test_start_time', startTime);
        
        const response = await fetch('/api/v1/monitoring/test-run/register', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            statusDiv.className = 'alert alert-success';
            statusDiv.innerHTML = `
                ✓ ${data.message}<br>
                <strong>Master Run ID:</strong> ${data.master_run_id}<br>
                <strong>PC Run ID:</strong> ${data.pc_run_id}<br>
                <strong>LOB:</strong> ${data.lob_name}<br>
                <br>
                <strong>🎯 You can now start monitoring activities!</strong>
            `;
            
            // Set as current test
            currentTestRun = {
                run_id: data.master_run_id,
                pc_run_id: data.pc_run_id,
                lob_name: data.lob_name,
                track: data.track,
                test_name: data.test_name,
                test_status: 'INITIATED'
            };
            
            // Set global LOB
            selectedLOB = data.lob_name;
            
            // Reload current test display
            setTimeout(() => {
                displayCurrentTest(currentTestRun);
                loadRecentRegistrations();
            }, 2000);
            
        } else {
            statusDiv.className = 'alert alert-error';
            statusDiv.innerHTML = '✗ ' + data.message;
        }
        
    } catch (error) {
        statusDiv.className = 'alert alert-error';
        statusDiv.innerHTML = '✗ Error: ' + error.message;
    }
}

async function loadRecentRegistrations() {
    const container = document.getElementById('recentRegistrations');
    container.innerHTML = '<p style="text-align: center; color: #999;">Loading...</p>';
    
    try {
        const response = await fetch('/api/v1/monitoring/test-run/recent?limit=5');
        const data = await response.json();
        
        if (data.count === 0) {
            container.innerHTML = '<p style="text-align: center; color: #999;">No registrations found</p>';
            return;
        }
        
        let html = '<div style="display: flex; flex-direction: column; gap: 12px;">';
        
        data.test_runs.forEach(run => {
            const createdDate = new Date(run.created_date).toLocaleString();
            const statusColor = run.test_status === 'COMPLETED' ? '#28a745' : 
                               run.test_status === 'FAILED' ? '#dc3545' : '#ffc107';
            
            html += `
                <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid ${statusColor};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <strong style="font-size: 1.1em;">${run.test_name}</strong>
                        <span style="background: white; padding: 4px 12px; border-radius: 12px; font-size: 0.85em; color: ${statusColor}; font-weight: 600;">
                            ${run.test_status}
                        </span>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 8px; font-size: 0.9em; color: #666;">
                        <div><strong>PC Run ID:</strong> ${run.pc_run_id}</div>
                        <div><strong>LOB:</strong> ${run.lob_name}</div>
                        ${run.track ? `<div><strong>Track:</strong> ${run.track}</div>` : ''}
                        <div><strong>Created:</strong> ${createdDate}</div>
                    </div>
                    <div style="margin-top: 8px; font-size: 0.85em; color: #999;">
                        Master Run ID: ${run.run_id}
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        container.innerHTML = html;
        
    } catch (error) {
        container.innerHTML = '<p style="text-align: center; color: #dc3545;">Error loading registrations</p>';
        console.error('Error loading recent registrations:', error);
    }
}

// Load LOBs for registration form
async function loadRegistrationLOBs() {
    try {
        const response = await fetch('/api/v1/monitoring/appd/master/lobs');
        const data = await response.json();
        
        const select = document.getElementById('regLob');
        select.innerHTML = '<option value="">-- Select LOB --</option>';
        
        data.lobs.forEach(lob => {
            const option = document.createElement('option');
            option.value = lob.lob_name;
            option.textContent = lob.lob_name;
            select.appendChild(option);
        });
        
    } catch (error) {
        console.error('Error loading registration LOBs:', error);
    }
}
```

---

## 📝 INCREMENTAL CHANGE #6: Update Page Load

**File:** `index.html`  
**Location:** Find `window.addEventListener('DOMContentLoaded'`

**ADD THESE LINES:**
```javascript
window.addEventListener('DOMContentLoaded', function() {
    loadEnvironmentInfo();
    loadDatabases();
    loadApiKeys();
    checkDatabaseStatus();
    loadLandingLOBs();
    
    // ADD THESE NEW LINES:
    loadCurrentTestRun();           // Load current test registration
    loadRecentRegistrations();      // Load recent registrations
    loadRegistrationLOBs();         // Load LOBs for registration form
});
```

---

## 📝 INCREMENTAL CHANGE #7: Update Other Monitoring Tabs

**File:** `index.html`  
**Location:** In AppD, AWR, PC tabs - add validation

**ADD AT START OF MONITORING FUNCTIONS:**
```javascript
async function startMonitoring() {
    // Check if test is registered
    if (!currentTestRun) {
        alert('⚠️ Please register your Performance Center test run first!\n\nGo to "Register Test" tab and enter your PC Run ID.');
        return;
    }
    
    // ... rest of function
}

async function uploadAWRReport() {
    // Check if test is registered
    if (!currentTestRun) {
        alert('⚠️ Please register your Performance Center test run first!\n\nGo to "Register Test" tab and enter your PC Run ID.');
        return;
    }
    
    // Auto-fill PC Run ID
    document.getElementById('awrPcRunId').value = currentTestRun.pc_run_id;
    
    // ... rest of function
}

async function fetchPCResults() {
    // Check if test is registered
    if (!currentTestRun) {
        alert('⚠️ Please register your Performance Center test run first!\n\nGo to "Register Test" tab and enter your PC Run ID.');
        return;
    }
    
    // Auto-fill PC Run ID
    document.getElementById('pcRunId').value = currentTestRun.pc_run_id;
    
    // ... rest of function
}
```

---

## 🎯 Complete User Flow

```
Step 1: User starts LoadRunner test
   ↓
   PC generates Run ID: 35678
   ↓
Step 2: User goes to your app → "Register Test" tab
   ↓
   Fills in:
   - PC Run ID: 35678
   - Test Name: Peak Load Test
   - LOB: Digital Technology
   - Track: CDV3
   ↓
   Clicks "Register Test Run"
   ↓
   System creates:
   - Master Run ID: RUNID_35678_04Mar2026_001
   - Entry in RUN_MASTER table
   ↓
Step 3: User starts AppD monitoring
   ↓
   System creates:
   - AppD Run ID: AppD_Run_04Mar2026_001_35678
   - Links to RUN_MASTER via FK
   ↓
Step 4: User uploads AWR report
   ↓
   System creates:
   - AWR Run ID: AWR_Run_04Mar2026_001_35678
   - Links to RUN_MASTER via FK
   ↓
Step 5: User fetches PC results
   ↓
   System creates:
   - PC transactions linked to RUN_MASTER
   ↓
ALL MONITORING DATA LINKED! ✅
```

---

## ✅ Summary

**What this solves:**
- ✅ Forces users to register PC Run ID FIRST
- ✅ Creates master RUN_MASTER entry
- ✅ Shows current active test
- ✅ Auto-fills PC Run ID in other tabs
- ✅ Validates before allowing monitoring
- ✅ Shows recent registrations

**User experience:**
1. Start PC test manually
2. Register in "Register Test" tab
3. Use any monitoring tab
4. All data links automatically!

**Is this clear now?** 🚀