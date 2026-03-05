# 🔧 Fix: Register Test Tab UI Issues

## 📋 Issues to Fix

1. **Page scrolls to bottom (test status section) on landing** ❌
   - Should stay at top (registration form)

2. **After registering test, shows "INITIATED" status and blocks new registration** ❌
   - Should allow immediate new test registration
   - Only show active (non-COMPLETED) tests

---

## ✅ FIX #1: Keep Page Scrolled to Top

### Issue:
When landing on Register Test tab, page scrolls down to "Recent Test Registrations" section automatically.

### Solution:
Remove auto-scroll behavior after loading test status.

**File:** `index.html`

**FIND the `loadCurrentTestRun()` function:**

```javascript
async function loadCurrentTestRun() {
    try {
        const response = await fetch('/api/v1/pc/test-run/current');
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
```

**REPLACE WITH (no changes needed, but ensure no scroll code exists):**

```javascript
async function loadCurrentTestRun() {
    try {
        const response = await fetch('/api/v1/pc/test-run/current');
        const data = await response.json();
        
        if (data.has_active_test) {
            currentTestRun = data.test_run;
            
            // Only show active tests (not COMPLETED or FAILED)
            if (currentTestRun.test_status === 'COMPLETED' || currentTestRun.test_status === 'FAILED') {
                // Test is done, hide status and show registration form
                document.getElementById('currentTestStatus').style.display = 'none';
                document.getElementById('registrationForm').style.display = 'block';
                currentTestRun = null; // Clear so user can register new test
            } else {
                // Test is active (INITIATED, RUNNING, ANALYZING)
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

## ✅ FIX #2: Allow Immediate New Registration After Test Registered

### Issue:
After registering a test, it shows "INITIATED" status and blocks form. User cannot register another test immediately.

### Solution:
After successful registration, clear the form and allow new registration without showing status section.

**File:** `index.html`

**FIND the `registerTestRun()` function:**

```javascript
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
        
        const response = await fetch('/api/v1/pc/test-run/register', {
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
```

**REPLACE WITH THIS NEW VERSION:**

```javascript
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
        
        const response = await fetch('/api/v1/pc/test-run/register', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            statusDiv.className = 'alert alert-success';
            statusDiv.innerHTML = `
                ✓ Test registered successfully!<br>
                <strong>Master Run ID:</strong> ${data.master_run_id}<br>
                <strong>PC Run ID:</strong> ${data.pc_run_id}<br>
                <strong>Test Name:</strong> ${data.test_name}<br>
                <strong>LOB:</strong> ${data.lob_name}<br>
                <br>
                ✓ You can now start monitoring or register another test
            `;
            
            // Set as current test for monitoring tabs to use
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
            
            // Clear the form to allow new registration immediately
            document.getElementById('regPcRunId').value = '';
            document.getElementById('regTestName').value = '';
            document.getElementById('regTrack').value = '';
            document.getElementById('regStartTime').value = '';
            // Don't clear LOB dropdown - user might register multiple tests for same LOB
            
            // Hide success message after 5 seconds
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 5000);
            
            // Reload recent registrations list
            loadRecentRegistrations();
            
            // DON'T show currentTestStatus section - keep form visible
            // DON'T call displayCurrentTest() - allows immediate new registration
            
        } else {
            statusDiv.className = 'alert alert-error';
            statusDiv.innerHTML = '✗ ' + data.message;
            
            // Hide error after 5 seconds
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 5000);
        }
        
    } catch (error) {
        statusDiv.className = 'alert alert-error';
        statusDiv.innerHTML = '✗ Error: ' + error.message;
        
        // Hide error after 5 seconds
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 5000);
    }
}
```

---

## ✅ FIX #3: Update displayCurrentTest() to Only Show Active Tests

**FIND the `displayCurrentTest()` function:**

```javascript
function displayCurrentTest(test) {
    // existing code...
}
```

**REPLACE WITH:**

```javascript
function displayCurrentTest(test) {
    // Only show if test is actually active (not completed/failed)
    if (test.test_status === 'COMPLETED' || test.test_status === 'FAILED') {
        // Don't show completed tests
        document.getElementById('currentTestStatus').style.display = 'none';
        document.getElementById('registrationForm').style.display = 'block';
        return;
    }
    
    // Show active test status
    document.getElementById('currentTestStatus').style.display = 'block';
    document.getElementById('registrationForm').style.display = 'none';
    
    document.getElementById('currentMasterRunId').textContent = test.run_id;
    document.getElementById('currentPcRunId').textContent = test.pc_run_id;
    document.getElementById('currentLob').textContent = test.lob_name;
    document.getElementById('currentTrack').textContent = test.track || 'N/A';
    document.getElementById('currentTestName').textContent = test.test_name;
    
    const statusElem = document.getElementById('currentTestStatus');
    statusElem.textContent = test.test_status;
    
    // Color coding
    if (test.test_status === 'RUNNING') {
        statusElem.style.color = '#ffc107'; // Orange
    } else if (test.test_status === 'ANALYZING') {
        statusElem.style.color = '#17a2b8'; // Blue
    } else {
        statusElem.style.color = '#28a745'; // Green for INITIATED
    }
}
```

---

## ✅ FIX #4: Ensure Page Stays at Top on Tab Load

Add scroll reset when switching to Register Test tab:

**FIND the `showTab()` function:**

```javascript
function showTab(evt, tabName) {
    // Hide all tab contents
    const tabContents = document.getElementsByClassName('tab-content');
    for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].style.display = 'none';
        tabContents[i].classList.remove('active');
    }
    
    // Remove active class from all tabs
    const tabs = document.getElementsByClassName('tab');
    for (let i = 0; i < tabs.length; i++) {
        tabs[i].classList.remove('active');
    }
    
    // Show selected tab
    document.getElementById(tabName).style.display = 'block';
    document.getElementById(tabName).classList.add('active');
    evt.currentTarget.classList.add('active');
    
    // Propagate LOB if applicable
    if (tabName !== 'oracle' && tabName !== 'registertest' && selectedLOB) {
        propagateLOBToAllTabs(selectedLOB);
    }
}
```

**ADD THIS CODE at the end of showTab():**

```javascript
function showTab(evt, tabName) {
    // ... existing code ...
    
    // Scroll to top when switching to Register Test tab
    if (tabName === 'registertest') {
        setTimeout(() => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }, 100);
    }
}
```

---

## 📝 Summary of Changes

### Fix #1: Page Scroll Position ✅
- **Before:** Page scrolls to bottom (recent registrations)
- **After:** Page stays at top (registration form)
- **Change:** Added scroll to top when switching to Register Test tab

### Fix #2: Immediate New Registration ✅
- **Before:** After registering, shows INITIATED status and blocks form
- **After:** After registering, clears form and allows immediate new registration
- **Changes:**
  - Don't call `displayCurrentTest()` after registration
  - Clear form fields immediately
  - Hide success message after 5 seconds
  - Keep registration form visible

### Fix #3: Only Show Active Tests ✅
- **Before:** Shows all tests including COMPLETED
- **After:** Only shows RUNNING, ANALYZING, INITIATED tests
- **Changes:**
  - `loadCurrentTestRun()` filters out COMPLETED/FAILED
  - `displayCurrentTest()` returns early for completed tests

### Fix #4: Scroll Reset ✅
- **Before:** Unknown scroll position on tab switch
- **After:** Always scrolls to top
- **Change:** Added scroll reset in `showTab()`

---

## 🧪 Testing Steps

### Test 1: Landing on Tab
1. Open application
2. Click "Register Test" tab
3. **Expected:** Page is scrolled to top, showing registration form

### Test 2: Register First Test
1. Fill in form (PC Run ID: 35678, Test Name: Test 1, LOB: Digital Tech)
2. Click "Register Test Run"
3. **Expected:** 
   - Success message shows
   - Form clears
   - Form stays visible (not hidden)
   - Success message disappears after 5 seconds
   - Can immediately fill form again

### Test 3: Register Second Test
1. Immediately fill form again (PC Run ID: 35679, Test Name: Test 2)
2. Click "Register Test Run"
3. **Expected:** Works without issues

### Test 4: Active Test Display
1. Register a test
2. Refresh page
3. **Expected:** 
   - If test is INITIATED/RUNNING/ANALYZING: Shows status, hides form
   - If test is COMPLETED/FAILED: Hides status, shows form

### Test 5: Switch to AppD Tab
1. Register a test
2. Switch to AppD tab
3. **Expected:** Can start monitoring (currentTestRun is set)

---

## ✅ Expected User Experience

### Workflow:
```
1. User lands on Register Test tab
   → Form visible at top
   
2. User registers Test 1 (PC_RUN_ID: 35678)
   → Success message shows
   → Form clears
   → Form stays visible
   
3. User immediately registers Test 2 (PC_RUN_ID: 35679)
   → Success message shows
   → Form clears
   → Form stays visible
   
4. User switches to AppD tab
   → Can start monitoring using Test 2 data
   
5. User switches back to Register Test tab
   → Form visible at top
   → Can register Test 3
```

---

## 🎯 Result

✅ **Page always at top when landing on Register Test tab**
✅ **Can register multiple tests immediately without blocking**
✅ **Only active tests shown in status section**
✅ **Clean, smooth user experience**

Apply these changes and the Register Test tab will work perfectly! 🚀