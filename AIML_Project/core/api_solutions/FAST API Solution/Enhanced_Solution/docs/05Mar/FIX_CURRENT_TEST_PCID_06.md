# 🔧 Fix: currentTestRun.pc_run_id is Undefined

## 🎯 Problem

Frontend is sending `pc_run_id: undefined` to AWR upload endpoint.

**This means `currentTestRun` is either:**
1. Not set when test is registered
2. Lost when switching tabs
3. Not properly initialized on page load

---

## ✅ Solution: Ensure currentTestRun is Always Set

### Fix #1: Check Test Registration Sets currentTestRun Properly

**File:** `index.html`

**FIND the `registerTestRun()` function and verify this section:**

```javascript
async function registerTestRun() {
    // ... registration code ...
    
    if (data.success) {
        statusDiv.className = 'alert alert-success';
        statusDiv.innerHTML = `✓ Test registered successfully!`;
        
        // SET currentTestRun - THIS IS CRITICAL
        currentTestRun = {
            run_id: data.master_run_id,
            pc_run_id: data.pc_run_id,        // ← Make sure this exists
            lob_name: data.lob_name,
            track: data.track,
            test_name: data.test_name,
            test_status: 'INITIATED'
        };
        
        // Log to verify
        console.log('✓ currentTestRun set:', currentTestRun);
        
        selectedLOB = data.lob_name;
        
        // ... rest of code ...
    }
}
```

---

### Fix #2: Load currentTestRun on Page Load

**ADD this check to ensure currentTestRun is loaded when page starts:**

```javascript
window.addEventListener('DOMContentLoaded', function() {
    initializeTabs();
    loadEnvironmentInfo();
    loadDatabases();
    loadApiKeys();
    checkDatabaseStatus();
    loadLandingLOBs();
    loadRegisterLOBs();
    loadRegistrationLOBs();
    
    // Load current test and set currentTestRun
    loadCurrentTestRun();
    loadRecentRegistrations();
});
```

**MAKE SURE `loadCurrentTestRun()` sets `currentTestRun`:**

```javascript
async function loadCurrentTestRun() {
    try {
        const response = await fetch('/api/v1/pc/test-run/current');
        const data = await response.json();
        
        if (data.has_active_test) {
            const test = data.test_run;
            
            // Get selected LOB filter
            const selectedRegLob = document.getElementById('registerLobFilter')?.value;
            
            // Check if LOB matches
            if (selectedRegLob && test.lob_name !== selectedRegLob) {
                document.getElementById('currentTestStatus').style.display = 'none';
                document.getElementById('registrationForm').style.display = 'block';
                currentTestRun = null;
                return;
            }
            
            // Only show active tests
            if (test.test_status === 'COMPLETED' || test.test_status === 'FAILED') {
                document.getElementById('currentTestStatus').style.display = 'none';
                document.getElementById('registrationForm').style.display = 'block';
                currentTestRun = null;
            } else {
                // SET currentTestRun for active test
                currentTestRun = {
                    run_id: test.run_id,
                    pc_run_id: test.pc_run_id,  // ← Critical
                    lob_name: test.lob_name,
                    track: test.track,
                    test_name: test.test_name,
                    test_status: test.test_status
                };
                
                console.log('✓ Loaded currentTestRun:', currentTestRun);
                
                displayCurrentTest(test);
            }
        } else {
            document.getElementById('currentTestStatus').style.display = 'none';
            document.getElementById('registrationForm').style.display = 'block';
            currentTestRun = null;
        }
        
    } catch (error) {
        console.error('Error loading current test:', error);
        document.getElementById('currentTestStatus').style.display = 'none';
        document.getElementById('registrationForm').style.display = 'block';
        currentTestRun = null;
    }
}
```

---

### Fix #3: Add Validation to uploadAWRReport()

**UPDATE `uploadAWRReport()` with better validation and logging:**

```javascript
async function uploadAWRReport() {
    console.log('=== AWR Upload Started ===');
    console.log('currentTestRun:', currentTestRun);
    
    // Validation
    if (!currentTestRun) {
        alert('⚠️ No test registered!\n\nPlease go to "Register Test" tab and register your PC test first.');
        return;
    }
    
    if (!currentTestRun.pc_run_id) {
        console.error('ERROR: currentTestRun exists but pc_run_id is missing!');
        console.error('currentTestRun:', currentTestRun);
        alert('⚠️ Test data is incomplete. Please re-register your test.');
        return;
    }
    
    const dbName = document.getElementById('awrDatabaseName').value.trim();
    const testName = document.getElementById('awrTestName').value.trim();
    const fileInput = document.getElementById('awrFileInput');
    
    if (!dbName || !fileInput.files.length) {
        alert('Please fill in database name and select AWR file');
        return;
    }
    
    const statusDiv = document.getElementById('awrUploadStatus');
    statusDiv.style.display = 'block';
    statusDiv.className = 'alert alert-info';
    statusDiv.innerHTML = '⏳ Uploading and analyzing AWR report...';
    
    try {
        // Build form data
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('pc_run_id', currentTestRun.pc_run_id);
        formData.append('database_name', dbName);
        formData.append('lob_name', currentTestRun.lob_name || '');
        formData.append('track', currentTestRun.track || '');
        formData.append('test_name', testName || currentTestRun.test_name || '');
        
        // Debug log
        console.log('Sending to AWR upload:');
        console.log('  file:', fileInput.files[0].name);
        console.log('  pc_run_id:', currentTestRun.pc_run_id);
        console.log('  database_name:', dbName);
        console.log('  lob_name:', currentTestRun.lob_name);
        console.log('  track:', currentTestRun.track);
        console.log('  test_name:', testName || currentTestRun.test_name);
        
        const response = await fetch('/api/v1/monitoring/awr/upload', {
            method: 'POST',
            body: formData
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            const errorData = await response.json();
            console.error('Error response:', errorData);
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Success response:', data);
        
        if (data.success) {
            statusDiv.className = 'alert alert-success';
            statusDiv.innerHTML = `
                ✓ AWR Analysis Completed!<br>
                <strong>Run ID:</strong> ${data.run_id}<br>
                <strong>Database:</strong> ${data.database_name}<br>
                <strong>Concerns Found:</strong> ${data.total_concerns}
            `;
            
            // Clear form
            fileInput.value = '';
            document.getElementById('awrDatabaseName').value = '';
            document.getElementById('awrTestName').value = '';
            
        } else {
            statusDiv.className = 'alert alert-error';
            statusDiv.innerHTML = '✗ Error: ' + (data.message || 'Failed to analyze report');
        }
        
    } catch (error) {
        console.error('AWR Upload error:', error);
        statusDiv.className = 'alert alert-error';
        statusDiv.innerHTML = '✗ Error: ' + error.message;
    }
}
```

---

### Fix #4: Declare currentTestRun Globally

**Make sure `currentTestRun` is declared at the top of your JavaScript:**

```javascript
<script>
// ==========================================
// Global Variables
// ==========================================
let selectedLOB = null;
let currentTestRun = null;  // ← Make sure this exists

// Rest of your code...
</script>
```

---

### Fix #5: Add Debug Panel to Check currentTestRun

**Add this temporary debug panel to your page to see currentTestRun value:**

```html
<!-- Debug Panel - Remove after fixing -->
<div style="position: fixed; bottom: 10px; right: 10px; background: #fff; border: 2px solid #2196f3; padding: 15px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.2); max-width: 300px; z-index: 9999;">
    <h4 style="margin: 0 0 10px 0; color: #2196f3;">🔍 Debug: currentTestRun</h4>
    <div id="debugCurrentTestRun" style="font-size: 0.85em; font-family: monospace;">
        Not set
    </div>
    <button onclick="updateDebugPanel()" style="margin-top: 10px; padding: 5px 10px; background: #2196f3; color: white; border: none; border-radius: 4px; cursor: pointer;">
        Refresh
    </button>
</div>

<script>
function updateDebugPanel() {
    const debugDiv = document.getElementById('debugCurrentTestRun');
    if (currentTestRun) {
        debugDiv.innerHTML = `
            <div style="color: green; font-weight: bold;">✓ Test Registered</div>
            <div>run_id: ${currentTestRun.run_id || 'missing'}</div>
            <div>pc_run_id: <strong>${currentTestRun.pc_run_id || 'MISSING!'}</strong></div>
            <div>lob_name: ${currentTestRun.lob_name || 'missing'}</div>
            <div>test_name: ${currentTestRun.test_name || 'missing'}</div>
            <div>status: ${currentTestRun.test_status || 'missing'}</div>
        `;
    } else {
        debugDiv.innerHTML = '<div style="color: red; font-weight: bold;">✗ Not Set</div>';
    }
}

// Auto-update every 2 seconds
setInterval(updateDebugPanel, 2000);
updateDebugPanel();
</script>
```

---

## 🧪 Testing Steps

### Step 1: Check if currentTestRun is Set After Registration

1. Go to Register Test tab
2. Register a test (PC_RUN_ID: 12345)
3. Open console (F12)
4. Check for: `✓ currentTestRun set: {pc_run_id: "12345", ...}`
5. If you see this, currentTestRun is set correctly ✓

### Step 2: Check if currentTestRun Persists

1. Switch to AWR tab
2. In console, type: `console.log(currentTestRun)`
3. Should show: `{pc_run_id: "12345", ...}`
4. If it shows `null` or `undefined`, it's being lost ✗

### Step 3: Check Debug Panel

1. Look at bottom-right debug panel
2. Should show:
   ```
   ✓ Test Registered
   pc_run_id: 12345
   ```
3. If it shows "Not Set" or "MISSING!", there's an issue

### Step 4: Try AWR Upload

1. Select AWR file
2. Enter database name
3. Check console for logs
4. Should show: `pc_run_id: 12345` (not undefined)

---

## 🔍 Quick Debug Commands

Open browser console and run these:

```javascript
// Check if variable exists
console.log('currentTestRun:', currentTestRun);

// Check if it has pc_run_id
console.log('pc_run_id:', currentTestRun?.pc_run_id);

// Force set it for testing
currentTestRun = {
    run_id: 'RUNID_12345_05Mar2026_001',
    pc_run_id: '12345',
    lob_name: 'Test LOB',
    test_name: 'Test',
    test_status: 'INITIATED'
};
console.log('✓ Manually set currentTestRun');

// Try upload again
uploadAWRReport();
```

---

## ✅ Most Likely Issues

1. **Not declared globally** ✗
   ```javascript
   let currentTestRun = null;  // ← Add at top
   ```

2. **Not set after registration** ✗
   ```javascript
   currentTestRun = {
       pc_run_id: data.pc_run_id,  // ← Make sure this line exists
       ...
   };
   ```

3. **Lost on page load** ✗
   ```javascript
   loadCurrentTestRun() {
       currentTestRun = test;  // ← Make sure this sets it
   }
   ```

4. **Backend doesn't return pc_run_id** ✗
   ```python
   return {
       "pc_run_id": pc_run_id,  # ← Make sure backend returns this
       ...
   }
   ```

---

**Add the debug panel and check the console logs - they will tell you exactly where currentTestRun is getting lost!** 🚀

Once you see the logs, we can pinpoint the exact issue!