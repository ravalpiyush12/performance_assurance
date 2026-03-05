# 🔧 Fix: Show Only Non-Completed Tests for Selected LOB

## 🎯 Problem

Register Test tab shows:
- ❌ Tests from ALL LOBs
- ❌ COMPLETED tests

**Should show only:**
- ✅ Tests from SELECTED LOB only
- ✅ Non-completed tests (INITIATED, RUNNING, ANALYZING)

---

## ✅ Solution: LOB-Based Filtering

### Strategy:
1. Track selected LOB
2. Filter tests by LOB when loading
3. Filter out COMPLETED/FAILED tests
4. Update when LOB changes

---

## 🔧 FIX #1: Add LOB Selector to Register Test Tab

**File:** `index.html`

**FIND the Register Test tab content section (near the top):**

```html
<div id="registertest" class="tab-content active">
    <h2>🎯 Register Performance Test Run</h2>
    <p style="color: #666; margin-bottom: 20px;">
        Register your Performance Center test run BEFORE starting any monitoring activities.
        This creates a master entry that links all monitoring solutions together.
    </p>
```

**ADD LOB SELECTOR BEFORE "Current Registration Status":**

```html
<div id="registertest" class="tab-content active">
    <h2>🎯 Register Performance Test Run</h2>
    <p style="color: #666; margin-bottom: 20px;">
        Register your Performance Center test run BEFORE starting any monitoring activities.
        This creates a master entry that links all monitoring solutions together.
    </p>
    
    <!-- LOB Selector for Filtering -->
    <div class="appd-section" style="background: #e3f2fd; border-left: 4px solid #2196f3;">
        <div style="display: flex; align-items: center; gap: 15px;">
            <div style="flex: 0 0 auto;">
                <strong style="color: #1976d2;">📍 Selected LOB:</strong>
            </div>
            <div style="flex: 1;">
                <select id="registerLobFilter" 
                        onchange="handleRegisterLOBChange()"
                        style="width: 100%; padding: 10px; border: 2px solid #2196f3; border-radius: 6px; font-size: 1em;">
                    <option value="">-- Select LOB --</option>
                </select>
            </div>
            <div style="flex: 0 0 auto;">
                <span id="registerLobTestCount" style="font-size: 0.9em; color: #1976d2; font-weight: 600;"></span>
            </div>
        </div>
        <p style="margin: 10px 0 0 0; font-size: 0.85em; color: #1565c0;">
            Active tests and recent registrations shown below are filtered for this LOB
        </p>
    </div>
    
    <!-- Rest of the tab content... -->
```

---

## 🔧 FIX #2: Update loadCurrentTestRun() to Filter by LOB

**File:** `index.html`

**FIND the `loadCurrentTestRun()` function and REPLACE with:**

```javascript
async function loadCurrentTestRun() {
    try {
        const response = await fetch('/api/v1/pc/test-run/current');
        const data = await response.json();
        
        if (data.has_active_test) {
            const test = data.test_run;
            
            // Check if test belongs to currently selected LOB
            const selectedRegLob = document.getElementById('registerLobFilter')?.value;
            
            // If LOB is selected and test doesn't match, don't show it
            if (selectedRegLob && test.lob_name !== selectedRegLob) {
                document.getElementById('currentTestStatus').style.display = 'none';
                document.getElementById('registrationForm').style.display = 'block';
                currentTestRun = null;
                return;
            }
            
            // Only show active tests (not COMPLETED or FAILED)
            if (test.test_status === 'COMPLETED' || test.test_status === 'FAILED') {
                // Test is done, hide status and show registration form
                document.getElementById('currentTestStatus').style.display = 'none';
                document.getElementById('registrationForm').style.display = 'block';
                currentTestRun = null;
            } else {
                // Test is active (INITIATED, RUNNING, ANALYZING)
                currentTestRun = test;
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

## 🔧 FIX #3: Update loadRecentRegistrations() to Filter by LOB

**FIND the `loadRecentRegistrations()` function and REPLACE with:**

```javascript
async function loadRecentRegistrations() {
    const container = document.getElementById('recentRegistrations');
    container.innerHTML = '<p style="text-align: center; color: #999;">Loading...</p>';
    
    try {
        // Get selected LOB
        const selectedRegLob = document.getElementById('registerLobFilter')?.value;
        
        // Fetch more tests to ensure we have enough after filtering
        const response = await fetch('/api/v1/pc/test-run/recent?limit=50');
        const data = await response.json();
        
        if (data.count === 0) {
            container.innerHTML = '<p style="text-align: center; color: #999;">No tests found</p>';
            updateRegisterLobTestCount(0);
            return;
        }
        
        // Filter tests
        let filteredTests = data.test_runs.filter(run => {
            // Filter 1: Only non-completed tests
            const isActive = run.test_status !== 'COMPLETED' && run.test_status !== 'FAILED';
            
            // Filter 2: Match selected LOB (if LOB is selected)
            const matchesLob = !selectedRegLob || run.lob_name === selectedRegLob;
            
            return isActive && matchesLob;
        });
        
        // Update count badge
        updateRegisterLobTestCount(filteredTests.length);
        
        // Show top 5 tests
        const displayTests = filteredTests.slice(0, 5);
        
        if (displayTests.length === 0) {
            const message = selectedRegLob 
                ? `No active tests found for <strong>${selectedRegLob}</strong>`
                : 'No active tests found';
            container.innerHTML = `<p style="text-align: center; color: #999;">${message}</p>`;
            return;
        }
        
        let html = '<div style="display: flex; flex-direction: column; gap: 12px;">';
        
        displayTests.forEach(run => {
            const createdDate = new Date(run.created_date).toLocaleString();
            
            // Color coding for active statuses
            let statusColor = '#ffc107'; // Default yellow
            if (run.test_status === 'RUNNING') {
                statusColor = '#17a2b8'; // Blue
            } else if (run.test_status === 'ANALYZING') {
                statusColor = '#6f42c1'; // Purple
            } else if (run.test_status === 'INITIATED') {
                statusColor = '#28a745'; // Green
            }
            
            html += `
                <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid ${statusColor};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <strong style="font-size: 1.1em;">${run.test_name}</strong>
                        <span style="background: white; padding: 4px 12px; border-radius: 12px; font-size: 0.85em; color: ${statusColor}; font-weight: 600;">
                            🔄 ${run.test_status}
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
        
        // Add count info
        if (filteredTests.length > 5) {
            html += `
                <div style="text-align: center; margin-top: 15px; padding: 10px; background: #e3f2fd; border-radius: 6px; font-size: 0.9em; color: #1976d2;">
                    📊 Showing 5 of ${filteredTests.length} active test${filteredTests.length !== 1 ? 's' : ''}
                    ${selectedRegLob ? ` for ${selectedRegLob}` : ''}
                </div>
            `;
        }
        
        container.innerHTML = html;
        
    } catch (error) {
        container.innerHTML = '<p style="text-align: center; color: #dc3545;">Error loading registrations</p>';
        console.error('Error loading recent registrations:', error);
        updateRegisterLobTestCount(0);
    }
}
```

---

## 🔧 FIX #4: Add Helper Functions

**ADD these NEW functions in your JavaScript section:**

```javascript
// ==========================================
// Register Test Tab - LOB Filtering
// ==========================================

function handleRegisterLOBChange() {
    const selectedLob = document.getElementById('registerLobFilter').value;
    
    console.log('Register LOB changed to:', selectedLob);
    
    // Update selected LOB in registration form dropdown if it exists
    const regLobDropdown = document.getElementById('regLob');
    if (regLobDropdown && selectedLob) {
        regLobDropdown.value = selectedLob;
    }
    
    // Reload current test and recent registrations with LOB filter
    loadCurrentTestRun();
    loadRecentRegistrations();
}

function updateRegisterLobTestCount(count) {
    const countBadge = document.getElementById('registerLobTestCount');
    if (countBadge) {
        if (count > 0) {
            countBadge.textContent = `${count} active test${count !== 1 ? 's' : ''}`;
            countBadge.style.display = 'inline';
        } else {
            countBadge.textContent = 'No active tests';
            countBadge.style.display = 'inline';
        }
    }
}

async function loadRegisterLOBs() {
    try {
        // Reuse the same LOB list from AppD master config
        const response = await fetch('/api/v1/monitoring/appd/master/lobs');
        const data = await response.json();
        
        const select = document.getElementById('registerLobFilter');
        if (!select) return;
        
        select.innerHTML = '<option value="">-- All LOBs --</option>';
        
        data.lobs.forEach(lob => {
            const option = document.createElement('option');
            option.value = lob.lob_name;
            option.textContent = lob.lob_name;
            select.appendChild(option);
        });
        
        // If global selectedLOB is set, select it
        if (selectedLOB) {
            select.value = selectedLOB;
            handleRegisterLOBChange();
        }
        
    } catch (error) {
        console.error('Error loading register LOBs:', error);
    }
}
```

---

## 🔧 FIX #5: Initialize LOB Selector on Page Load

**FIND the `window.addEventListener('DOMContentLoaded'` section:**

```javascript
window.addEventListener('DOMContentLoaded', function() {
    initializeTabs();
    loadEnvironmentInfo();
    loadDatabases();
    loadApiKeys();
    checkDatabaseStatus();
    loadLandingLOBs();
    loadCurrentTestRun();
    loadRecentRegistrations();
    loadRegistrationLOBs();
});
```

**UPDATE TO:**

```javascript
window.addEventListener('DOMContentLoaded', function() {
    initializeTabs();
    loadEnvironmentInfo();
    loadDatabases();
    loadApiKeys();
    checkDatabaseStatus();
    loadLandingLOBs();
    
    // Load LOBs for register tab filter
    loadRegisterLOBs();
    
    // Load LOBs for registration form dropdown
    loadRegistrationLOBs();
    
    // Load current test and recent registrations
    loadCurrentTestRun();
    loadRecentRegistrations();
});
```

---

## 🔧 FIX #6: Sync LOB Selection with Landing Page

When user selects LOB on landing page, sync to Register Test tab:

**FIND the `selectLOB()` function (from landing page):**

```javascript
function selectLOB(lobName) {
    selectedLOB = lobName;
    
    // ... existing code ...
    
    // Show tabs
    document.getElementById('mainTabs').style.display = 'flex';
    document.getElementById('tabsContainer').style.display = 'block';
    
    propagateLOBToAllTabs(lobName);
}
```

**UPDATE propagateLOBToAllTabs() to include Register Test:**

```javascript
function propagateLOBToAllTabs(lob) {
    console.log('📍 Propagating LOB to all tabs:', lob);
    
    // ... existing code for other tabs ...
    
    // Register Test tab - set LOB filter
    const registerLobFilter = document.getElementById('registerLobFilter');
    if (registerLobFilter) {
        registerLobFilter.value = lob;
        handleRegisterLOBChange(); // Reload with filter
    }
    
    // Register Test form - pre-select LOB
    const regLobDropdown = document.getElementById('regLob');
    if (regLobDropdown) {
        regLobDropdown.value = lob;
    }
}
```

---

## 🧪 Testing Steps

### Test 1: LOB Filtering
```
1. Select "Digital Technology" from landing page
2. Go to Register Test tab
3. ✓ LOB filter shows "Digital Technology"
4. ✓ Only shows tests for Digital Technology
5. Change filter to "Retail Banking"
6. ✓ Shows only Retail Banking tests
```

### Test 2: Register Test with LOB
```
1. Select "Digital Technology" LOB
2. Register Test 1 (PC_RUN_ID: 35678)
3. ✓ Test appears in "Active Test Runs" section
4. ✓ LOB shows "Digital Technology"
5. Change filter to "Retail Banking"
6. ✓ Test 1 disappears (not shown)
7. Change filter back to "Digital Technology"
8. ✓ Test 1 reappears
```

### Test 3: Multiple LOBs
```
1. Register Test A for "Digital Technology"
2. Register Test B for "Retail Banking"
3. Filter by "Digital Technology"
   ✓ Shows only Test A
4. Filter by "Retail Banking"
   ✓ Shows only Test B
5. Filter by "All LOBs"
   ✓ Shows both Test A and Test B
```

### Test 4: Completed Tests Not Shown
```
1. Register Test 1 for "Digital Technology" (INITIATED)
2. ✓ Test 1 shows in active tests
3. Mark Test 1 as COMPLETED in database
4. Refresh page
5. ✓ Test 1 does NOT show
6. Register Test 2 for "Digital Technology" (INITIATED)
7. ✓ Test 2 shows, Test 1 still hidden
```

---

## 📊 Summary

### Filters Applied:

1. **LOB Filter:**
   - Shows only tests for selected LOB
   - "All LOBs" option shows tests from all LOBs

2. **Status Filter:**
   - Shows only: INITIATED, RUNNING, ANALYZING
   - Hides: COMPLETED, FAILED

### UI Components Added:

1. **LOB Selector** at top of Register Test tab
2. **Test Count Badge** showing number of active tests
3. **Info Text** explaining filtering
4. **Sync with Landing Page** LOB selection

### Result:

✅ **Shows only non-completed tests**
✅ **Filtered by selected LOB**
✅ **Clear indication of filtering**
✅ **Synced with landing page LOB selection**
✅ **Count badge shows active test count**

---

## 🎯 Expected Behavior

```
Landing Page: User selects "Digital Technology"
   ↓
Register Test Tab:
   ✓ LOB filter auto-set to "Digital Technology"
   ✓ Current test shown (if exists for Digital Tech)
   ✓ Recent tests shown (only Digital Tech, only active)
   ✓ Badge shows: "3 active tests"
   ↓
User changes filter to "Retail Banking"
   ✓ Current test updates (if exists)
   ✓ Recent tests update (only Retail Banking, only active)
   ✓ Badge shows: "1 active test"
```

**Apply all 6 fixes and your Register Test tab will be perfectly filtered!** 🚀