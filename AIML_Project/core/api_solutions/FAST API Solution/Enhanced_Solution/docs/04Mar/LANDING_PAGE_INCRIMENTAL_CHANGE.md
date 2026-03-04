# 🚀 Landing Page Implementation - Incremental Changes

## 📋 Overview

Transform your index.html to have a landing page with LOB selection that shows Health Status, Audit Details, and API Details before accessing the monitoring dashboard.

---

## 🎯 UI Flow

```
┌─────────────────────────────────────────────┐
│  Landing Page                                │
│  ┌─────────────────────────────────────┐   │
│  │ Select LOB: [Digital Technology ▼] │   │
│  └─────────────────────────────────────┘   │
│                                              │
│  ┌───────┐  ┌───────┐  ┌───────┐          │
│  │Health │  │Audit  │  │ API   │          │
│  │Status │  │Details│  │ Keys  │          │
│  └───────┘  └───────┘  └───────┘          │
│                                              │
│  [Continue to Monitoring Dashboard →]       │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Digital Technology - Monitoring Dashboard   │
│  ← Change LOB                                │
├─────────────────────────────────────────────┤
│  [Oracle SQL] [AppD] [MongoDB] [Splunk]...  │
└─────────────────────────────────────────────┘
```

---

## 📝 INCREMENTAL CHANGES

### ✅ CHANGE #1: Add Global LOB Variable

**File:** `index.html`  
**Location:** Inside `<script>` tag, at the very top (before any existing variables or functions)

**ACTION:** ADD THIS CODE

```javascript
// ==========================================
// Global LOB Selection
// ==========================================
let selectedLOB = null;
let showLandingPage = true;
```

**Purpose:** Store the selected LOB globally so it's available across all tabs without re-selection.

---

### ✅ CHANGE #2: Add Landing Page HTML

**File:** `index.html`  
**Location:** Right after the opening `<div class="container">` tag

**FIND THIS:**
```html
<div class="container">
    <div class="header">
```

**REPLACE WITH:**
```html
<div class="container">
    
    <!-- ========================================== -->
    <!-- Landing Page -->
    <!-- ========================================== -->
    <div id="landingPage" style="display: block;">
        <div class="landing-header">
            <h1>🗄️ CQE NFT Monitoring Platform</h1>
            <p>Select your Line of Business to begin</p>
        </div>
        
        <div class="landing-content">
            <!-- LOB Selection Card -->
            <div class="lob-selection-card">
                <h3>Select Line of Business</h3>
                <select id="landingLobSelect" onchange="onLandingLobChange()" class="lob-select-large">
                    <option value="">-- Select LOB --</option>
                </select>
            </div>
            
            <!-- Dashboard Cards (Hidden until LOB selected) -->
            <div id="landingDashboard" style="display: none;">
                <div class="dashboard-cards">
                    <!-- Health Status Card -->
                    <div class="dashboard-card">
                        <div class="card-icon">❤️</div>
                        <h3>Health Status</h3>
                        <p id="healthStatusSummary">Loading...</p>
                    </div>
                    
                    <!-- Audit Details Card -->
                    <div class="dashboard-card">
                        <div class="card-icon">📊</div>
                        <h3>Audit Details</h3>
                        <p id="auditSummary">Loading...</p>
                    </div>
                    
                    <!-- API Details Card -->
                    <div class="dashboard-card">
                        <div class="card-icon">🔑</div>
                        <h3>API Keys</h3>
                        <p id="apiKeysSummary">Loading...</p>
                    </div>
                </div>
                
                <!-- Continue Button -->
                <div style="text-align: center; margin-top: 30px;">
                    <button class="btn btn-success" onclick="proceedToMonitoring()" style="font-size: 1.2em; padding: 15px 50px;">
                        Continue to Monitoring Dashboard →
                    </button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- ========================================== -->
    <!-- Main Dashboard (Hidden initially) -->
    <!-- ========================================== -->
    <div id="mainDashboard" style="display: none;">
    
    <div class="header">
```

**Purpose:** Creates the landing page with LOB selector and dashboard cards.

---

### ✅ CHANGE #3: Add CSS Styles for Landing Page

**File:** `index.html`  
**Location:** Inside `<style>` tag, at the end before `</style>`

**ACTION:** ADD THIS CODE AT THE END OF YOUR STYLES

```css
/* ========================================== */
/* Landing Page Styles */
/* ========================================== */

.landing-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 60px 30px;
    text-align: center;
    border-radius: 12px 12px 0 0;
}

.landing-header h1 {
    font-size: 3em;
    margin-bottom: 10px;
}

.landing-header p {
    font-size: 1.3em;
    opacity: 0.95;
}

.landing-content {
    padding: 40px;
    min-height: 400px;
    background: white;
}

.lob-selection-card {
    max-width: 600px;
    margin: 0 auto 40px;
    background: #f8f9fa;
    padding: 30px;
    border-radius: 12px;
    text-align: center;
    border: 2px solid #e0e0e0;
}

.lob-selection-card h3 {
    color: #667eea;
    margin-bottom: 20px;
    font-size: 1.5em;
}

.lob-select-large {
    width: 100%;
    padding: 15px;
    font-size: 1.2em;
    border: 2px solid #667eea;
    border-radius: 8px;
    background: white;
    cursor: pointer;
    transition: all 0.3s;
}

.lob-select-large:focus {
    outline: none;
    border-color: #764ba2;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.lob-select-large:hover {
    border-color: #764ba2;
}

.dashboard-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 25px;
    margin-bottom: 30px;
}

.dashboard-card {
    background: white;
    padding: 30px;
    border-radius: 12px;
    border: 2px solid #e0e0e0;
    text-align: center;
    transition: all 0.3s;
    cursor: pointer;
}

.dashboard-card:hover {
    border-color: #667eea;
    box-shadow: 0 5px 20px rgba(102, 126, 234, 0.2);
    transform: translateY(-5px);
}

.dashboard-card .card-icon {
    font-size: 3em;
    margin-bottom: 15px;
}

.dashboard-card h3 {
    color: #333;
    margin-bottom: 10px;
    font-size: 1.3em;
}

.dashboard-card p {
    color: #666;
    font-size: 0.95em;
    line-height: 1.5;
}

/* ========================================== */
/* LOB Badge in Main Dashboard Header */
/* ========================================== */

.lob-badge {
    display: inline-block;
    background: rgba(255, 255, 255, 0.2);
    padding: 8px 20px;
    border-radius: 20px;
    font-size: 0.9em;
    margin-left: 15px;
    font-weight: 600;
}

.back-to-landing {
    background: rgba(255, 255, 255, 0.2);
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.3);
    padding: 8px 20px;
    border-radius: 20px;
    cursor: pointer;
    font-size: 0.9em;
    transition: all 0.3s;
}

.back-to-landing:hover {
    background: rgba(255, 255, 255, 0.3);
    border-color: rgba(255, 255, 255, 0.5);
}

/* ========================================== */
/* Responsive Design for Landing Page */
/* ========================================== */

@media (max-width: 768px) {
    .landing-header h1 {
        font-size: 2em;
    }
    
    .landing-header p {
        font-size: 1em;
    }
    
    .dashboard-cards {
        grid-template-columns: 1fr;
    }
    
    .lob-select-large {
        font-size: 1em;
        padding: 12px;
    }
}
```

**Purpose:** Styles the landing page to look professional and modern.

---

### ✅ CHANGE #4: Update Header with LOB Badge

**File:** `index.html`  
**Location:** Find the existing `<div class="header">` section

**FIND THIS:**
```html
<div class="header">
    <h1>🗄️ CQE NFT Monitoring API Solutions</h1>
    <p>Multi-Database Management Platform with Integrated Monitoring</p>
    <p style="font-size: 0.9em; margin-top: 10px;">
        Environment: <span id="headerEnvironment">Loading...</span> | 
        Version: <span id="headerVersion">Loading...</span>
    </p>
```

**REPLACE WITH:**
```html
<div class="header">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
        <div>
            <h1>
                🗄️ CQE NFT Monitoring
                <span class="lob-badge" id="lobBadge" style="display: none;"></span>
            </h1>
            <p>Multi-Database Management Platform with Integrated Monitoring</p>
            <p style="font-size: 0.9em; margin-top: 10px;">
                Environment: <span id="headerEnvironment">Loading...</span> | 
                Version: <span id="headerVersion">Loading...</span>
            </p>
        </div>
        <button class="back-to-landing" id="backToLanding" onclick="backToLandingPage()" style="display: none;">
            ← Change LOB
        </button>
    </div>
```

**Purpose:** Shows the selected LOB in the header and provides a back button.

---

### ✅ CHANGE #5: Update Tabs with New Tabs

**File:** `index.html`  
**Location:** Find the `<div class="tabs">` section

**FIND THIS:**
```html
<div class="tabs">
    <button class="tab active" onclick="showTab(event, 'oracle')">Oracle SQL</button>
    <button class="tab" onclick="showTab(event, 'apikeys')">📋 API Keys</button>
    <button class="tab" onclick="showTab(event, 'appdynamics')">📊 AppDynamics</button>
    <button class="tab" onclick="showTab(event, 'kibana')">Kibana</button>
    <button class="tab" onclick="showTab(event, 'splunk')">Splunk</button>
    <button class="tab" onclick="showTab(event, 'mongodb')">MongoDB</button>
</div>
```

**REPLACE WITH:**
```html
<div class="tabs" id="mainTabs">
    <button class="tab active" onclick="showTab(event, 'oracle')">Oracle SQL APIs</button>
    <button class="tab" onclick="showTab(event, 'appdynamics')">📊 AppDynamics</button>
    <button class="tab" onclick="showTab(event, 'mongodb')">MongoDB APIs</button>
    <button class="tab" onclick="showTab(event, 'splunk')">Splunk APIs</button>
    <button class="tab" onclick="showTab(event, 'awr')">AWR Analysis</button>
    <button class="tab" onclick="showTab(event, 'loadrunner')">LR Test Results</button>
    <button class="tab" onclick="showTab(event, 'apikeys')">📋 API Keys</button>
</div>
```

**Purpose:** Adds new tabs for AWR Analysis and LoadRunner Test Results.

---

### ✅ CHANGE #6: Add Placeholder Tabs

**File:** `index.html`  
**Location:** After the last existing tab content (after MongoDB tab), before closing container div

**FIND THIS:**
```html
<div id="mongodb" class="tab-content">
    <h2>MongoDB Analysis</h2>
    <div class="api-doc">
        <h3>🍃 Available Endpoints</h3>
        <ul style="list-style: none; padding-left: 0;">
            <li style="margin-bottom: 10px;"><code>GET /api/v1/monitoring/mongodb/collections</code> - List collections</li>
        </ul>
    </div>
</div>
```

**ADD AFTER IT:**
```html

<!-- AWR Analysis Tab -->
<div id="awr" class="tab-content">
    <h2>AWR Analysis</h2>
    <p style="color: #666; margin-bottom: 20px;">
        Automatic Workload Repository Analysis for <span id="awrLobName" style="font-weight: bold; color: #667eea;"></span>
    </p>
    <div class="api-doc">
        <h3>📊 AWR Report Generation</h3>
        <p>Generate and analyze AWR reports for database performance monitoring.</p>
        <ul style="list-style: none; padding-left: 0;">
            <li style="margin-bottom: 10px;"><code>GET /api/v1/awr/snapshots</code> - List available snapshots</li>
            <li style="margin-bottom: 10px;"><code>POST /api/v1/awr/generate-report</code> - Generate AWR report</li>
        </ul>
    </div>
</div>

<!-- LoadRunner Test Results Tab -->
<div id="loadrunner" class="tab-content">
    <h2>LoadRunner Test Results</h2>
    <p style="color: #666; margin-bottom: 20px;">
        Fetch and analyze LoadRunner performance test results for <span id="lrLobName" style="font-weight: bold; color: #667eea;"></span>
    </p>
    <div class="api-doc">
        <h3>🧪 Test Results API</h3>
        <p>Retrieve LoadRunner test execution results and performance metrics.</p>
        <ul style="list-style: none; padding-left: 0;">
            <li style="margin-bottom: 10px;"><code>GET /api/v1/loadrunner/tests</code> - List test runs</li>
            <li style="margin-bottom: 10px;"><code>GET /api/v1/loadrunner/results/{test_id}</code> - Get test results</li>
            <li style="margin-bottom: 10px;"><code>POST /api/v1/loadrunner/fetch</code> - Fetch results from LR server</li>
        </ul>
    </div>
</div>
```

**Purpose:** Creates placeholder tabs for AWR and LoadRunner (you'll add functionality later).

---

### ✅ CHANGE #7: Close Main Dashboard Div

**File:** `index.html`  
**Location:** At the very end, before the closing `</div>` for container

**FIND THIS (at the very end of your HTML):**
```html
    </div> <!-- End of last tab content -->
</div> <!-- End of container -->
</body>
</html>
```

**REPLACE WITH:**
```html
    </div> <!-- End of last tab content -->
    
    </div> <!-- End of mainDashboard -->
</div> <!-- End of container -->
</body>
</html>
```

**Purpose:** Properly closes the mainDashboard div that was opened in Change #2.

---

### ✅ CHANGE #8: Add Landing Page JavaScript Functions

**File:** `index.html`  
**Location:** Inside `<script>` tag, at the end before the closing `</script>`

**ACTION:** ADD THESE FUNCTIONS

```javascript
// ==========================================
// Landing Page Functions
// ==========================================

function onLandingLobChange() {
    const lob = document.getElementById('landingLobSelect').value;
    
    if (!lob) {
        document.getElementById('landingDashboard').style.display = 'none';
        return;
    }
    
    // Store selected LOB globally
    selectedLOB = lob;
    
    // Show dashboard cards
    document.getElementById('landingDashboard').style.display = 'block';
    
    // Load summary data for cards
    loadHealthStatusSummary(lob);
    loadAuditSummary(lob);
    loadAPIKeysSummary(lob);
}

async function loadHealthStatusSummary(lob) {
    const elem = document.getElementById('healthStatusSummary');
    elem.innerHTML = '⏳ Loading...';
    
    try {
        const response = await fetch('/health');
        const data = await response.json();
        
        const databases = data.databases || {};
        const dbCount = Object.keys(databases).length;
        const healthyCount = Object.values(databases).filter(db => db.status === 'healthy').length;
        
        elem.innerHTML = `
            <strong style="color: #28a745; font-size: 1.2em;">${healthyCount}/${dbCount}</strong><br>
            <span style="color: #666;">Databases Healthy</span><br>
            <small style="color: ${data.status === 'healthy' ? '#28a745' : '#ffc107'};">
                System: ${data.status === 'healthy' ? '✅ Operational' : '⚠️ Degraded'}
            </small>
        `;
    } catch (error) {
        elem.innerHTML = '<span style="color: #dc3545;">❌ Unable to load</span>';
        console.error('Health status error:', error);
    }
}

async function loadAuditSummary(lob) {
    const elem = document.getElementById('auditSummary');
    elem.innerHTML = `
        <strong style="color: #667eea; font-size: 1.2em;">Active</strong><br>
        <span style="color: #666;">Audit Logging</span><br>
        <small style="color: #666;">LOB: ${lob}</small><br>
        <small style="color: #667eea;">View detailed logs in dashboard</small>
    `;
}

async function loadAPIKeysSummary(lob) {
    const elem = document.getElementById('apiKeysSummary');
    elem.innerHTML = '⏳ Loading...';
    
    try {
        const response = await fetch('/api/v1/config/api-keys');
        const data = await response.json();
        
        const apiKeys = data.api_keys || {};
        const keyCount = Object.keys(apiKeys).reduce((sum, db) => {
            return sum + (apiKeys[db]?.length || 0);
        }, 0);
        
        const dbCount = Object.keys(apiKeys).length;
        
        elem.innerHTML = `
            <strong style="color: #667eea; font-size: 1.2em;">${keyCount}</strong><br>
            <span style="color: #666;">API Keys Available</span><br>
            <small style="color: #666;">Across ${dbCount} databases</small>
        `;
    } catch (error) {
        elem.innerHTML = '<span style="color: #dc3545;">❌ Unable to load</span>';
        console.error('API keys error:', error);
    }
}

function proceedToMonitoring() {
    if (!selectedLOB) {
        alert('⚠️ Please select a LOB first');
        return;
    }
    
    // Hide landing page
    document.getElementById('landingPage').style.display = 'none';
    
    // Show main dashboard
    document.getElementById('mainDashboard').style.display = 'block';
    
    // Update header with selected LOB
    document.getElementById('lobBadge').textContent = selectedLOB;
    document.getElementById('lobBadge').style.display = 'inline-block';
    document.getElementById('backToLanding').style.display = 'inline-block';
    
    // Pre-populate LOB across all tabs
    propagateLOBToAllTabs(selectedLOB);
}

function backToLandingPage() {
    // Show landing page
    document.getElementById('landingPage').style.display = 'block';
    
    // Hide main dashboard
    document.getElementById('mainDashboard').style.display = 'none';
    
    // Hide LOB badge and back button
    document.getElementById('lobBadge').style.display = 'none';
    document.getElementById('backToLanding').style.display = 'none';
    
    // Keep selectedLOB value for user convenience (don't clear it)
}

function propagateLOBToAllTabs(lob) {
    console.log('📍 Propagating LOB to all tabs:', lob);
    
    // AppDynamics tab - Discovery section
    const discoveryLob = document.getElementById('discoveryLob');
    if (discoveryLob) {
        discoveryLob.value = lob;
        // Trigger change event to load tracks
        if (typeof onDiscoveryLobSelected === 'function') {
            onDiscoveryLobSelected();
        }
    }
    
    // AppDynamics tab - Health Check section
    const healthLob = document.getElementById('healthLob');
    if (healthLob) {
        healthLob.value = lob;
        // Trigger change event to load tracks
        if (typeof onHealthLobChange === 'function') {
            onHealthLobChange();
        }
    }
    
    // AppDynamics tab - Start Monitoring section
    const monitorLob = document.getElementById('monitorLob');
    if (monitorLob) {
        monitorLob.value = lob;
        // Trigger change event to load tracks
        if (typeof onMonitorLobChange === 'function') {
            onMonitorLobChange();
        }
    }
    
    // AWR Analysis tab
    const awrLobName = document.getElementById('awrLobName');
    if (awrLobName) {
        awrLobName.textContent = lob;
    }
    
    // LoadRunner tab
    const lrLobName = document.getElementById('lrLobName');
    if (lrLobName) {
        lrLobName.textContent = lob;
    }
    
    // You can add more tab-specific LOB propagation here as you build them
}
```

**Purpose:** Handles landing page interactions, loads summary data, and propagates LOB to all tabs.

---

### ✅ CHANGE #9: Load LOBs on Page Load

**File:** `index.html`  
**Location:** Find `window.addEventListener('DOMContentLoaded'` function

**FIND THIS:**
```javascript
window.addEventListener('DOMContentLoaded', function() {
    loadEnvironmentInfo();
    loadDatabases();
    loadApiKeys();
    checkDatabaseStatus();
});
```

**REPLACE WITH:**
```javascript
window.addEventListener('DOMContentLoaded', function() {
    loadEnvironmentInfo();
    loadDatabases();
    loadApiKeys();
    checkDatabaseStatus();
    loadLandingLOBs();  // ← ADD THIS LINE
});
```

**THEN ADD THIS NEW FUNCTION** (anywhere in the script section):

```javascript
async function loadLandingLOBs() {
    try {
        const response = await fetch('/api/v1/monitoring/appd/master/lobs');
        const data = await response.json();
        
        const select = document.getElementById('landingLobSelect');
        if (!select) {
            console.error('Landing LOB select not found');
            return;
        }
        
        select.innerHTML = '<option value="">-- Select LOB --</option>';
        
        const lobs = data.lobs || [];
        lobs.forEach(lob => {
            const option = document.createElement('option');
            option.value = lob.lob_name;
            option.textContent = lob.lob_name;
            select.appendChild(option);
        });
        
        console.log(`✅ Loaded ${lobs.length} LOBs for landing page`);
    } catch (error) {
        console.error('❌ Failed to load LOBs for landing page:', error);
    }
}
```

**Purpose:** Loads LOB options from the database when page loads.

---

## 🧪 Testing Steps

### Step 1: Apply All Changes
Go through changes #1 through #9 in order.

### Step 2: Save and Refresh
Save `index.html` and refresh your browser.

### Step 3: Verify Landing Page
You should see:
- ✅ Purple gradient header "CQE NFT Monitoring Platform"
- ✅ LOB dropdown with options (Digital Technology, Data, Payments, etc.)
- ✅ No dashboard cards yet (they appear after selecting LOB)

### Step 4: Select a LOB
Select "Digital Technology" from dropdown.
- ✅ Three cards appear (Health Status, Audit Details, API Keys)
- ✅ Cards show loading, then display data
- ✅ "Continue to Monitoring Dashboard →" button appears

### Step 5: Click Continue
Click the green "Continue" button.
- ✅ Landing page disappears
- ✅ Main dashboard appears
- ✅ Header shows "Digital Technology" badge
- ✅ "← Change LOB" button appears in header
- ✅ All tabs are visible

### Step 6: Verify LOB Propagation
Click on "AppDynamics" tab.
- ✅ Discovery section should have "Digital Technology" pre-selected
- ✅ Health Check section should have "Digital Technology" pre-selected
- ✅ Start Monitoring section should have "Digital Technology" pre-selected

### Step 7: Test Back Button
Click "← Change LOB" in header.
- ✅ Returns to landing page
- ✅ Previously selected LOB is still selected
- ✅ Dashboard cards are still visible

---

## 🐛 Troubleshooting

### Issue: Landing page doesn't show
**Fix:** Check that Change #2 was applied correctly. Make sure `<div id="landingPage">` has `display: block;`

### Issue: LOB dropdown is empty
**Fix:** Check browser console for errors. Verify the API endpoint `/api/v1/monitoring/appd/master/lobs` is working.

### Issue: Cards don't appear after selecting LOB
**Fix:** Check Change #8 was applied. Open browser console and look for JavaScript errors.

### Issue: Main dashboard doesn't show after clicking Continue
**Fix:** Verify Change #7 was applied correctly. The closing `</div>` for mainDashboard must be in the right place.

### Issue: LOB doesn't propagate to AppD tabs
**Fix:** Make sure your AppD tab has elements with IDs: `discoveryLob`, `healthLob`, `monitorLob`.

---

## 📊 Summary

| Change | File | Lines | Difficulty |
|--------|------|-------|------------|
| #1 - Global variables | index.html | 2 | Easy |
| #2 - Landing HTML | index.html | ~60 | Medium |
| #3 - CSS styles | index.html | ~100 | Easy |
| #4 - Header update | index.html | ~15 | Easy |
| #5 - Tabs update | index.html | ~10 | Easy |
| #6 - New tab placeholders | index.html | ~40 | Easy |
| #7 - Close div | index.html | 2 | Easy |
| #8 - JavaScript functions | index.html | ~120 | Medium |
| #9 - Load LOBs | index.html | ~20 | Easy |

**Total:** ~369 lines added/modified

---

## ✅ Checklist

- [ ] Change #1: Global variables added
- [ ] Change #2: Landing page HTML added
- [ ] Change #3: CSS styles added
- [ ] Change #4: Header updated with LOB badge
- [ ] Change #5: Tabs updated with new tabs
- [ ] Change #6: AWR and LR tab placeholders added
- [ ] Change #7: mainDashboard div closed properly
- [ ] Change #8: JavaScript functions added
- [ ] Change #9: LOB loading on page load added
- [ ] Tested: Landing page shows
- [ ] Tested: LOB selection works
- [ ] Tested: Dashboard cards appear
- [ ] Tested: Continue button works
- [ ] Tested: LOB propagates to AppD tabs
- [ ] Tested: Back button works

---

## 🚀 Next Steps

Once this is working, we can add:
1. **AWR Analysis functionality** - Backend API + UI forms
2. **LoadRunner Test Results** - Backend API + results viewer
3. **Enhanced health status** - Real-time monitoring per LOB
4. **Audit log viewer** - Show recent API calls per LOB
5. **LOB-specific API key management** - Filter keys by LOB

**Ready to proceed?** Let me know if you encounter any issues! 🎉