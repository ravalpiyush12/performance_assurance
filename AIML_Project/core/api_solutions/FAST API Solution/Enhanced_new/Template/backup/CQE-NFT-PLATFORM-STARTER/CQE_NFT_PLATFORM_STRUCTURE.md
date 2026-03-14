# 🏗️ CQE NFT PLATFORM - COMPLETE STRUCTURE

## 📁 FILE STRUCTURE

```
cqe-nft-platform/
├── css/
│   └── global.css                          ✅ CREATED
│
├── js/
│   ├── config.js                          📝 TODO: Add your API base URL
│   ├── auth.js                            📝 TODO: Add your authentication logic
│   └── api.js                             📝 TODO: Add your API call functions
│
├── pages/
│   ├── landing.html                       ✅ CREATED (Main entry with 2 buttons)
│   │
│   ├── analysis/
│   │   ├── test-selection.html            ✅ CREATED (LOB → Release → Tests)
│   │   └── test-report.html               📝 TODO: Comprehensive report with graphs
│   │
│   ├── monitoring/
│   │   ├── pre-login.html                 📝 TODO: LOB & Track selection before login
│   │   ├── login.html                     📝 TODO: Role-based login (Admin/PE)
│   │   ├── start-monitoring.html          📝 TODO: Performance Engineer landing
│   │   └── upload-reports.html            📝 TODO: AWR & PC upload section
│   │
│   └── admin/
│       ├── dashboard.html                 📝 TODO: Admin landing with Test Management
│       ├── test-management.html           📝 TODO: Delete faulty data by PC Run ID
│       ├── track-management.html          📝 TODO: Configure track templates
│       ├── user-management.html           📝 TODO: Create/View users
│       ├── audit-logs.html                📝 TODO: Audit trail
│       ├── api-docs.html                  📝 TODO: API documentation
│       └── [other admin pages]            📝 TODO: DB console, etc.
│
└── README.md                              📝 Creating comprehensive guide
```

---

## 🎯 KEY PAGES BREAKDOWN

### **1. LANDING PAGE** ✅
- **File:** `pages/landing.html`
- **Access:** Public (no login)
- **Features:**
  - Two large cards: "Test Result Analysis" & "Test Monitoring Activity"
  - Clear visual distinction
  - No login required badge vs Login required badge

### **2. TEST RESULT ANALYSIS PATH** (No Login)

#### **A. Test Selection** ✅
- **File:** `pages/analysis/test-selection.html`
- **Flow:**
  1. Select LOB → Loads releases
  2. Select Release → Shows all tests for that release
  3. Click test → Goes to detailed report

#### **B. Test Report** 📝 NEED TO CREATE
- **File:** `pages/analysis/test-report.html`
- **Shows:**
  - Performance Center results (graphs + tables)
  - AppDynamics metrics (response time, errors, CPM)
  - Oracle AWR analysis (top SQL, CPU, I/O)
  - Kibana logs (error counts, severity)
  - Splunk events (timeline, critical events)
  - MongoDB metrics (ops/sec, query performance)
  - Database query results

### **3. TEST MONITORING PATH** (Login Required)

#### **A. Pre-Login Selection** 📝
- **File:** `pages/monitoring/pre-login.html`
- **Features:**
  - Select LOB
  - Select Track
  - Button: "Continue to Login"
  - Stores selections for after login

#### **B. Login** 📝
- **File:** `pages/monitoring/login.html`
- **Features:**
  - Username, Password, TOTP
  - Role selection: Admin OR Performance Engineer
  - Redirects based on role

#### **C. Admin Dashboard** 📝
- **File:** `pages/admin/dashboard.html`
- **Features:**
  - Top nav: [API Docs] [Audit Logs] [Logout]
  - **NEW: Test Management** tile
  - Track Management tile (configure templates)
  - All other admin tiles

#### **D. Performance Engineer - Start Monitoring** 📝
- **File:** `pages/monitoring/start-monitoring.html`
- **Features:**
  - Top nav: [API Docs] [Audit Logs] [Upload Reports] [Logout]
  - Shows pre-selected LOB & Track
  - Auto-loads track configuration (read-only)
  - Fields: PC Run ID, Test Name, Release Name, Duration
  - Start → Progress bars → Stop → Data summary

#### **E. Upload Reports** 📝
- **File:** `pages/monitoring/upload-reports.html`
- **Features:**
  - Select: Track, Release, PC Run ID
  - Upload: AWR HTML, PC ZIP
  - Process → Show storage summary

---

## 🔗 NAVIGATION FLOW

```
LANDING PAGE
    |
    ├─→ Test Result Analysis (No Login)
    │   ├─→ Select LOB & Release
    │   └─→ View Test Report (all data sources)
    │
    └─→ Test Monitoring Activity (Login Required)
        ├─→ Select LOB & Track (pre-login)
        ├─→ Login (Admin OR Performance Engineer)
        │
        ├─→ [If Admin]
        │   └─→ Admin Dashboard
        │       ├─→ Test Management (delete data)
        │       ├─→ Track Management (templates)
        │       ├─→ User Management
        │       └─→ Other admin features
        │
        └─→ [If Performance Engineer]
            └─→ Start Monitoring
                ├─→ See track config (auto-loaded)
                ├─→ Fill PC Run ID, Test Name, Release
                ├─→ Start → Progress → Stop
                └─→ Upload Reports (sidebar/separate)
```

---

## 📊 DATA FLOW

### **Track Template (Configured by Admin):**
```json
{
  "track_name": "CDV3",
  "lob": "Digital Technology",
  "appd_applications": [
    "icg-tts-cirp-ng-173720_PTE",
    "CDV3_NFT_Digital_Technology"
  ],
  "kibana_dashboard": "Performance_Monitoring_CDV3",
  "splunk_dashboard": "Application_Logs_CDV3",
  "mongodb_collections": ["metrics_cdv3", "logs_cdv3"]
}
```

### **Monitoring Session:**
```json
{
  "pc_run_id": "65989",
  "test_name": "Peak Load Test",
  "release_name": "Release 2.5",
  "lob": "Digital Technology",
  "track": "CDV3",
  "duration": 1800,
  "config": {
    "appd_apps": ["..."],
    "kibana_dashboard": "...",
    "splunk_dashboard": "...",
    "mongodb_collections": ["..."]
  }
}
```

---

## 🎨 UI REQUIREMENTS

### **Charts/Graphs Needed for Test Report:**
1. **Performance Center:**
   - Response time line chart
   - Throughput bar chart
   - Transaction summary table

2. **AppDynamics:**
   - Response time per app (multi-line chart)
   - Error rate line chart
   - Calls per minute line chart
   - Business transactions table

3. **AWR:**
   - Top SQL table
   - CPU usage line chart
   - I/O statistics bar chart

4. **Kibana:**
   - Error count timeline
   - Log severity pie chart
   - Top errors table

5. **Splunk:**
   - Event timeline
   - Critical events table

6. **MongoDB:**
   - Operations per second line chart
   - Query performance table

7. **Database:**
   - Custom query results table

---

## 🔌 API ENDPOINTS NEEDED

### **Test Result Analysis:**
```
GET /api/v1/analysis/releases?lob={lob}
GET /api/v1/analysis/tests?lob={lob}&release={release}
GET /api/v1/analysis/report/{pc_run_id}
  → Returns all data from all sources
```

### **Monitoring - Track Config:**
```
GET /api/v1/monitoring/tracks?lob={lob}
GET /api/v1/monitoring/track/config?track={track}
  → Returns template configuration
```

### **Monitoring - Start/Stop:**
```
POST /api/v1/monitoring/start
  Body: {pc_run_id, test_name, release, lob, track, duration}
POST /api/v1/monitoring/stop
  Body: {session_id}
  → Returns data summary
```

### **Upload Reports:**
```
POST /api/v1/reports/upload/awr
  Body: FormData with file + metadata
POST /api/v1/reports/upload/pc
  Body: FormData with file + metadata
```

### **Admin - Test Management:**
```
DELETE /api/v1/admin/test-data/{pc_run_id}
  → Deletes from all tables
```

### **Admin - Track Management:**
```
GET /api/v1/admin/tracks
POST /api/v1/admin/tracks/create
PUT /api/v1/admin/tracks/{track_id}
```

---

## ✅ COMPLETED
- ✅ Directory structure
- ✅ Global CSS
- ✅ Landing page
- ✅ Test selection page

## 📝 NEXT STEPS
1. Create test report page with dummy graphs
2. Create monitoring flow pages
3. Create admin pages with test management
4. Connect all pages with navigation
5. Add JavaScript for interactions
6. Integrate with your real APIs

---

## 🚀 READY FOR YOUR CODE SHARING

**Once you share screenshots of your existing working code**, I will:
1. Extract all API endpoints
2. Complete all remaining pages
3. Wire everything with real backend calls
4. Provide production-ready code

**Share your JS files first - that's where all the API magic is!** 📸
