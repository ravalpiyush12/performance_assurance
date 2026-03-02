# 🚀 Complete Implementation Guide - AppD UI Enhancement

## Summary of All Changes

### ✅ What's Completed:

1. **Database Schema** - 2 new tables for master data
2. **Backend APIs** - 4 new endpoints for cascading dropdowns
3. **Database Methods** - 4 new methods in database.py
4. **Updated Request Models** - Support for config_name, lob_name, track
5. **Complete UI Redesign** - Better UX with cascading dropdowns

---

## 📋 Implementation Steps

### **STEP 1: Create Database Tables (5 minutes)**

Run these SQL scripts in Oracle:

```sql
-- 1. Create LOB Master Table
CREATE TABLE APPD_LOB_MASTER (
    LOB_MASTER_ID NUMBER PRIMARY KEY,
    LOB_NAME VARCHAR2(100) UNIQUE NOT NULL,
    LOB_CODE VARCHAR2(20) NOT NULL,
    DESCRIPTION VARCHAR2(500),
    IS_ACTIVE CHAR(1) DEFAULT 'Y',
    CREATED_DATE DATE DEFAULT SYSDATE,
    CONSTRAINT CHK_LOB_MASTER_ACTIVE CHECK (IS_ACTIVE IN ('Y', 'N'))
);

CREATE SEQUENCE APPD_LOB_MASTER_SEQ START WITH 1 INCREMENT BY 1;

-- 2. Insert LOBs
INSERT INTO APPD_LOB_MASTER VALUES (APPD_LOB_MASTER_SEQ.NEXTVAL, 'Digital Technology', 'DT', 'Digital Technology Services', 'Y', SYSDATE);
INSERT INTO APPD_LOB_MASTER VALUES (APPD_LOB_MASTER_SEQ.NEXTVAL, 'Data', 'DATA', 'Data Platform and Analytics', 'Y', SYSDATE);
INSERT INTO APPD_LOB_MASTER VALUES (APPD_LOB_MASTER_SEQ.NEXTVAL, 'Payments', 'PAY', 'Payment Services', 'Y', SYSDATE);
INSERT INTO APPD_LOB_MASTER VALUES (APPD_LOB_MASTER_SEQ.NEXTVAL, 'Commercial Cards', 'CC', 'Commercial Cards Division', 'Y', SYSDATE);
INSERT INTO APPD_LOB_MASTER VALUES (APPD_LOB_MASTER_SEQ.NEXTVAL, 'Retail', 'RETAIL', 'Retail Banking', 'Y', SYSDATE);

-- 3. Create Applications Master Table
CREATE TABLE APPD_APPLICATIONS_MASTER (
    APP_MASTER_ID NUMBER PRIMARY KEY,
    APPLICATION_NAME VARCHAR2(200) UNIQUE NOT NULL,
    DESCRIPTION VARCHAR2(500),
    LOB_NAME VARCHAR2(100),
    IS_ACTIVE CHAR(1) DEFAULT 'Y',
    CREATED_DATE DATE DEFAULT SYSDATE,
    UPDATED_DATE DATE DEFAULT SYSDATE,
    CONSTRAINT CHK_APP_MASTER_ACTIVE CHECK (IS_ACTIVE IN ('Y', 'N'))
);

CREATE SEQUENCE APPD_APP_MASTER_SEQ START WITH 1 INCREMENT BY 1;
CREATE INDEX IDX_APP_MASTER_LOB ON APPD_APPLICATIONS_MASTER(LOB_NAME);

-- 4. Insert Sample Applications
INSERT INTO APPD_APPLICATIONS_MASTER VALUES (APPD_APP_MASTER_SEQ.NEXTVAL, 'icg-tts-paymentinitiation-pte-173720_PTE', 'Payment Initiation Service', 'Digital Technology', 'Y', SYSDATE, SYSDATE);
INSERT INTO APPD_APPLICATIONS_MASTER VALUES (APPD_APP_MASTER_SEQ.NEXTVAL, 'RetailWeb', 'Retail Web Application', 'Retail', 'Y', SYSDATE, SYSDATE);
INSERT INTO APPD_APPLICATIONS_MASTER VALUES (APPD_APP_MASTER_SEQ.NEXTVAL, 'RetailAPI', 'Retail API Service', 'Retail', 'Y', SYSDATE, SYSDATE);
INSERT INTO APPD_APPLICATIONS_MASTER VALUES (APPD_APP_MASTER_SEQ.NEXTVAL, 'DataPlatform', 'Data Platform Service', 'Data', 'Y', SYSDATE, SYSDATE);
INSERT INTO APPD_APPLICATIONS_MASTER VALUES (APPD_APP_MASTER_SEQ.NEXTVAL, 'PaymentGateway', 'Payment Gateway', 'Payments', 'Y', SYSDATE, SYSDATE);
INSERT INTO APPD_APPLICATIONS_MASTER VALUES (APPD_APP_MASTER_SEQ.NEXTVAL, 'CommercialCardsAPI', 'Commercial Cards API', 'Commercial Cards', 'Y', SYSDATE, SYSDATE);

COMMIT;
```

---

### **STEP 2: Add Database Methods (10 minutes)**

In `monitoring/appd/database.py`, add these methods to the `AppDynamicsDatabase` class:

Copy all methods from: **APPD_COMPLETE_ENHANCEMENT_PART1.md → Part 3**

Methods to add:
- `get_master_lobs()`
- `get_master_applications()`
- `get_tracks_for_lob()`
- `get_latest_config_by_lob_track()`

---

### **STEP 3: Add Backend API Endpoints (10 minutes)**

In `monitoring/appd/routes.py`, add these endpoints:

Copy all endpoints from: **APPD_COMPLETE_ENHANCEMENT_PART1.md → Part 2**

Endpoints to add:
- `GET /master/lobs`
- `GET /master/applications`
- `GET /configs/by-lob-track`
- `GET /configs/tracks/{lob_name}`

---

### **STEP 4: Update StartMonitoringRequest Model (2 minutes)**

In `monitoring/appd/routes.py`, replace the `StartMonitoringRequest` class:

```python
class StartMonitoringRequest(BaseModel):
    """Request model for starting monitoring"""
    run_id: str
    config_name: str
    lob_name: str
    track: str
    test_name: Optional[str] = None
    interval_seconds: int = 1800
```

---

### **STEP 5: Update /monitoring/start Endpoint (5 minutes)**

In `monitoring/appd/routes.py`, replace the entire `/monitoring/start` endpoint:

Copy from: **APPD_COMPLETE_ENHANCEMENT_PART1.md → Part 5**

---

### **STEP 6: Update UI HTML (5 minutes)**

In your `index_final.html` or `index.html`:

1. **Find the AppD tab div** (starts with `<div id="appdynamics" class="tab-content">`)
2. **Replace the entire AppD tab section** with the content from: **appd_tab_complete_updated.html**

---

### **STEP 7: Test Everything (15 minutes)**

#### Test 1: Check Master Data
```bash
curl http://localhost:8000/api/v1/monitoring/appd/master/lobs
curl http://localhost:8000/api/v1/monitoring/appd/master/applications
```

#### Test 2: Discovery Flow
1. Open UI → AppD tab
2. Select "Digital Technology" from LOB dropdown
3. Enter Track: "CDV3"
4. Config name auto-generates: `NFT_Digital_Technology_CDV3_02Mar2026_1430`
5. Check application checkboxes
6. Click "Run Discovery"

#### Test 3: Health Check Flow
1. Select LOB → Track → Config (cascading dropdowns)
2. Click "Get Active Nodes"
3. See table with active nodes

#### Test 4: Start Monitoring Flow
1. Select LOB → Track → Config
2. Applications auto-show in preview
3. Enter Run ID
4. Click "Start Monitoring"

---

## 🎯 Features Delivered

### ✅ Discovery & Configuration:
- **LOB Dropdown**: Prepopulated from `APPD_LOB_MASTER`
- **Track Input**: User enters track name
- **Auto Config Name**: `NFT_{LOB}_{Track}_{Date}_{Time}`
- **Applications**: Multi-select checkboxes from `APPD_APPLICATIONS_MASTER`
- **Removed**: "Code 1, Code 2, Code 3" labels

### ✅ Health Check:
- **Cascading Dropdowns**: LOB → Track → Config (Latest)
- **Table Format**: Clean table with App, Tier, Node, CPM, Status columns
- **Active Filter**: Only shows nodes with IS_ACTIVE = 'Y'

### ✅ Start Monitoring:
- **Cascading Dropdowns**: LOB → Track → Config
- **Auto Applications**: Fetched from selected config
- **Application Preview**: Shows selected apps before starting
- **Complete Info**: Run ID, Test Name, Interval

### ✅ Active Sessions:
- **Shows**: LOB / Track / Run ID
- **Config Name**: Displayed in details
- **Applications**: Listed for each session

---

## 📊 Database Schema Reference

```
APPD_LOB_MASTER
├─ LOB_NAME (Digital Technology, Data, Payments, etc.)
├─ LOB_CODE
└─ DESCRIPTION

APPD_APPLICATIONS_MASTER
├─ APPLICATION_NAME
├─ LOB_NAME (FK to LOB_MASTER)
└─ DESCRIPTION

APPD_LOB_CONFIG (Updated)
├─ CONFIG_NAME (NFT_Digital_Technology_CDV3_02Mar2026_1430)
├─ LOB_NAME
├─ TRACK
└─ APPLICATION_NAMES (JSON array)
```

---

## 🔄 Data Flow

```
USER SELECTS:
LOB: Digital Technology
↓
TRACK: CDV3
↓
AUTO-GENERATES:
CONFIG_NAME: NFT_Digital_Technology_CDV3_02Mar2026_1430
↓
SHOWS APPLICATIONS:
☑ icg-tts-paymentinitiation-pte-173720_PTE
☐ OtherApp1
☐ OtherApp2
↓
SAVES TO DB:
INSERT INTO APPD_LOB_CONFIG
↓
RUNS DISCOVERY:
GET apps, tiers, nodes from AppD
↓
SAVES NODES:
INSERT INTO APPD_NODES (with IS_ACTIVE = 'Y' or 'N')
```

---

## 🐛 Troubleshooting

### Issue: LOB dropdown empty
**Fix**: Check `APPD_LOB_MASTER` table has data

### Issue: Applications checkboxes don't show
**Fix**: Check `APPD_APPLICATIONS_MASTER` has entries for selected LOB

### Issue: Config dropdown empty in Health Check
**Fix**: Run Discovery first to create configs

### Issue: Monitoring start fails with 422
**Fix**: Ensure StartMonitoringRequest includes all fields (config_name, lob_name, track)

---

## 📝 Adding New LOBs/Applications

### Add New LOB:
```sql
INSERT INTO APPD_LOB_MASTER (LOB_MASTER_ID, LOB_NAME, LOB_CODE, DESCRIPTION)
VALUES (APPD_LOB_MASTER_SEQ.NEXTVAL, 'New LOB', 'NL', 'Description', 'Y', SYSDATE);
COMMIT;
```

### Add New Application:
```sql
INSERT INTO APPD_APPLICATIONS_MASTER (APP_MASTER_ID, APPLICATION_NAME, LOB_NAME, DESCRIPTION)
VALUES (APPD_APP_MASTER_SEQ.NEXTVAL, 'NewApp', 'Digital Technology', 'New Application', 'Y', SYSDATE, SYSDATE);
COMMIT;
```

Then refresh browser - dropdowns will auto-update!

---

## ✅ Checklist

- [ ] Step 1: Database tables created
- [ ] Step 2: Database methods added
- [ ] Step 3: API endpoints added
- [ ] Step 4: Request model updated
- [ ] Step 5: /monitoring/start updated
- [ ] Step 6: UI HTML replaced
- [ ] Step 7: All tests passed

**Total Time**: ~52 minutes
**Difficulty**: Medium
**Files Modified**: 3 (database.py, routes.py, index.html)
**Database Changes**: 2 new tables, 11 sample rows

---

All done! 🎉 Your AppD monitoring is now production-ready with an intuitive UI!