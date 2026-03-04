# 🎯 RUN_ID Architecture - Complete Explanation

## 📋 The Problem We're Solving

### Without Master RUN_ID (Current Problem):
```
Performance Test Run #35678 in LoadRunner

AppD monitoring stores:     RUN_ID = "AppD_35678_001"
AWR analysis stores:        ANALYSIS_ID = 1234
MongoDB stores:             SESSION_ID = "mongo_5678"
Splunk stores:              SEARCH_ID = "splunk_abc"

❌ Problem: No way to link all monitoring data from the SAME test run!
❌ Can't correlate AppD metrics with AWR database issues
❌ Can't match LoadRunner slow transactions with database waits
❌ Each monitoring tool is isolated
```

### With Master RUN_ID (Solution):
```
Performance Test Run #35678 in LoadRunner

Master Table:    RUN_ID = "RUNID_35678_04Mar2026_001"
                    ↓
         ┌──────────┼──────────┬──────────┐
         ↓          ↓          ↓          ↓
AppD:    AppD_...   AWR:...    PC:...     Mongo:...
         35678      35678      35678      35678

✅ All monitoring solutions link to ONE master RUN_ID
✅ Easy to find all data for test run #35678
✅ Can correlate issues across all tools
✅ Generate unified reports
```

---

## 🗄️ Database Structure Explanation

### Master Table: RUN_MASTER

**Purpose:** Central registry for ALL test runs

```sql
CREATE TABLE RUN_MASTER (
    RUN_ID VARCHAR2(100) PRIMARY KEY,        -- RUNID_35678_04Mar2026_001
    PC_RUN_ID VARCHAR2(50) NOT NULL,         -- 35678 (from LoadRunner)
    LOB_NAME VARCHAR2(100) NOT NULL,         -- Digital Technology
    TRACK VARCHAR2(50),                      -- CDV3
    TEST_NAME VARCHAR2(200),                 -- Peak Load Test
    TEST_STATUS VARCHAR2(20),                -- RUNNING, COMPLETED, FAILED
    TEST_START_TIME TIMESTAMP,
    TEST_END_TIME TIMESTAMP,
    CREATED_DATE DATE DEFAULT SYSDATE
);
```

**What it stores:**
- One entry per test run
- Links to Performance Center run ID
- Test metadata (LOB, Track, Test Name)
- Test status and timing

---

## 🔗 How the Linking Works

### Example Scenario:

**Step 1: User Starts Performance Test**
```
LoadRunner generates:  PC_RUN_ID = 35678
User knows:           LOB = Digital Technology
                      Track = CDV3
```

**Step 2: System Creates Master Entry**
```sql
INSERT INTO RUN_MASTER (
    RUN_ID,                      -- RUNID_35678_04Mar2026_001
    PC_RUN_ID,                   -- 35678
    LOB_NAME,                    -- Digital Technology
    TRACK,                       -- CDV3
    TEST_NAME,                   -- Peak Load Test
    TEST_STATUS                  -- INITIATED
) VALUES (
    'RUNID_35678_04Mar2026_001',
    '35678',
    'Digital Technology',
    'CDV3',
    'Peak Load Test',
    'INITIATED'
);
```

**Step 3: User Starts AppD Monitoring**
```sql
-- AppD creates its own run ID
AppD_RUN_ID = 'AppD_Run_04Mar2026_001_35678'

INSERT INTO APPD_MONITORING_RUNS (
    APPD_RUN_ID,                           -- AppD_Run_04Mar2026_001_35678
    RUN_ID,                                -- RUNID_35678_04Mar2026_001 (FK)
    PC_RUN_ID,                             -- 35678
    LOB_NAME,                              -- Digital Technology
    CONFIG_NAME,
    APPLICATIONS,
    STATUS
) VALUES (
    'AppD_Run_04Mar2026_001_35678',
    'RUNID_35678_04Mar2026_001',           -- ← Links to master!
    '35678',
    'Digital Technology',
    'NFT_Digital_Technology_CDV3_...',
    '["RetailWeb", "RetailAPI"]',
    'RUNNING'
);
```

**Step 4: User Uploads AWR Report**
```sql
-- AWR creates its own run ID
AWR_RUN_ID = 'AWR_Run_04Mar2026_001_35678'

INSERT INTO AWR_ANALYSIS_RESULTS (
    ANALYSIS_ID,                           -- 1 (auto-generated)
    AWR_RUN_ID,                            -- AWR_Run_04Mar2026_001_35678
    RUN_ID,                                -- RUNID_35678_04Mar2026_001 (FK)
    DATABASE_NAME,                         -- PRODDB
    SNAPSHOT_BEGIN,
    SNAPSHOT_END,
    TOTAL_CONCERNS,                        -- 8
    CRITICAL_CONCERNS                      -- 2
) VALUES (
    1,
    'AWR_Run_04Mar2026_001_35678',
    'RUNID_35678_04Mar2026_001',           -- ← Links to master!
    'PRODDB',
    12345,
    12346,
    8,
    2
);
```

**Step 5: User Fetches PC Results**
```sql
-- PC creates its own run ID (same format)
PC_RUN_ID_FULL = 'PC_Run_04Mar2026_001_35678'

INSERT INTO PC_TEST_RUNS (
    PC_TEST_ID,                            -- 1 (auto-generated)
    RUN_ID,                                -- RUNID_35678_04Mar2026_001 (FK)
    PC_RUN_ID,                             -- 35678
    TEST_STATUS,                           -- Finished
    COLLATION_STATUS                       -- Collated
) VALUES (
    1,
    'RUNID_35678_04Mar2026_001',           -- ← Links to master!
    '35678',
    'Finished',
    'Collated'
);

INSERT INTO LR_TRANSACTION_RESULTS (
    TRANSACTION_ID,
    RUN_ID,                                -- RUNID_35678_04Mar2026_001 (FK)
    PC_RUN_ID,                             -- 35678
    TRANSACTION_NAME,                      -- Login
    AVERAGE_TIME,                          -- 2.5 seconds
    PASS_PERCENTAGE                        -- 98.5%
) VALUES (
    1,
    'RUNID_35678_04Mar2026_001',           -- ← Links to master!
    '35678',
    'Login',
    2.5,
    98.5
);
```

---

## 🔍 Querying Linked Data

### Query 1: Get All Monitoring Data for One Test Run

```sql
-- Get master test info
SELECT * FROM RUN_MASTER 
WHERE PC_RUN_ID = '35678';

-- Output:
RUN_ID                       | PC_RUN_ID | LOB_NAME            | TRACK | TEST_STATUS
RUNID_35678_04Mar2026_001    | 35678     | Digital Technology  | CDV3  | COMPLETED

-- Get AppD monitoring data
SELECT * FROM APPD_MONITORING_RUNS 
WHERE RUN_ID = 'RUNID_35678_04Mar2026_001';

-- Output:
APPD_RUN_ID                      | RUN_ID                    | APPLICATIONS
AppD_Run_04Mar2026_001_35678     | RUNID_35678_04Mar2026_001 | ["RetailWeb", "RetailAPI"]

-- Get AWR analysis
SELECT * FROM AWR_ANALYSIS_RESULTS 
WHERE RUN_ID = 'RUNID_35678_04Mar2026_001';

-- Output:
AWR_RUN_ID                       | RUN_ID                    | DATABASE_NAME | CRITICAL_CONCERNS
AWR_Run_04Mar2026_001_35678      | RUNID_35678_04Mar2026_001 | PRODDB        | 2

-- Get LoadRunner transactions
SELECT * FROM LR_TRANSACTION_RESULTS 
WHERE RUN_ID = 'RUNID_35678_04Mar2026_001';

-- Output:
TRANSACTION_NAME | AVERAGE_TIME | PASS_PERCENTAGE
Login            | 2.5          | 98.5%
Browse Products  | 3.2          | 95.0%
Checkout         | 5.8          | 92.0%
```

### Query 2: Unified Report - All Data Together

```sql
SELECT 
    rm.RUN_ID,
    rm.PC_RUN_ID,
    rm.LOB_NAME,
    rm.TRACK,
    rm.TEST_NAME,
    rm.TEST_STATUS,
    
    -- AppD metrics
    COUNT(DISTINCT am.NODE_ID) as APPD_NODES_MONITORED,
    COUNT(DISTINCT am.APPLICATION_NAME) as APPD_APPS_MONITORED,
    
    -- AWR metrics
    awr.DATABASE_NAME,
    awr.TOTAL_CONCERNS as AWR_CONCERNS,
    awr.CRITICAL_CONCERNS as AWR_CRITICAL,
    
    -- LoadRunner metrics
    COUNT(lr.TRANSACTION_ID) as LR_TOTAL_TRANSACTIONS,
    AVG(lr.PASS_PERCENTAGE) as LR_AVG_PASS_RATE,
    AVG(lr.AVERAGE_TIME) as LR_AVG_RESPONSE_TIME

FROM RUN_MASTER rm

LEFT JOIN APPD_MONITORING_RUNS amr ON rm.RUN_ID = amr.RUN_ID
LEFT JOIN APPD_METRICS am ON amr.MONITORING_RUN_ID = am.MONITORING_RUN_ID

LEFT JOIN AWR_ANALYSIS_RESULTS awr ON rm.RUN_ID = awr.RUN_ID

LEFT JOIN LR_TRANSACTION_RESULTS lr ON rm.RUN_ID = lr.RUN_ID

WHERE rm.PC_RUN_ID = '35678'

GROUP BY 
    rm.RUN_ID, rm.PC_RUN_ID, rm.LOB_NAME, rm.TRACK, rm.TEST_NAME, 
    rm.TEST_STATUS, awr.DATABASE_NAME, awr.TOTAL_CONCERNS, awr.CRITICAL_CONCERNS;
```

**Result:**
```
RUN_ID                    | PC_RUN_ID | TEST_NAME      | APPD_NODES | AWR_CRITICAL | LR_PASS_RATE | LR_AVG_TIME
RUNID_35678_04Mar2026_001 | 35678     | Peak Load Test | 12         | 2            | 95.2%        | 3.8s
```

---

## 🎯 Real-World Use Case

### Scenario: Investigating Slow Performance

**User Question:** "Why was test run #35678 slow?"

**Step 1: Check Master Status**
```sql
SELECT * FROM RUN_MASTER WHERE PC_RUN_ID = '35678';
```
Found: Test completed, ran for 60 minutes

**Step 2: Check LoadRunner Transactions**
```sql
SELECT 
    TRANSACTION_NAME, 
    AVERAGE_TIME, 
    PASS_PERCENTAGE 
FROM LR_TRANSACTION_RESULTS 
WHERE RUN_ID = 'RUNID_35678_04Mar2026_001'
ORDER BY AVERAGE_TIME DESC;
```
Found: "Checkout" transaction averaged 5.8 seconds (slow!)

**Step 3: Check AppD Metrics**
```sql
SELECT 
    APPLICATION_NAME,
    TIER_NAME,
    AVG(RESPONSE_TIME_MS) as AVG_RESPONSE
FROM APPD_METRICS 
WHERE RUN_ID = 'RUNID_35678_04Mar2026_001'
  AND TRANSACTION_NAME LIKE '%Checkout%'
GROUP BY APPLICATION_NAME, TIER_NAME
ORDER BY AVG_RESPONSE DESC;
```
Found: PaymentAPI tier had 4500ms average response time

**Step 4: Check AWR Concerns**
```sql
SELECT 
    CONCERN_TITLE,
    CONCERN_DESCRIPTION,
    SEVERITY,
    RECOMMENDATION
FROM AWR_CONCERNS 
WHERE RUN_ID = 'RUNID_35678_04Mar2026_001'
  AND SEVERITY = 'CRITICAL';
```
Found: 
- "Slow SQL Statement: abc123xyz" - SQL took 3200ms per execution
- "High Wait Event: db file sequential read" - 45% of DB time

**Conclusion:**
✅ Checkout transaction slow (5.8s)
✅ Caused by PaymentAPI tier (4500ms response)
✅ Root cause: Slow SQL in database (3200ms)
✅ Specific issue: High disk I/O waits

**All discovered by linking data through the master RUN_ID!**

---

## 📊 RUN_ID Naming Convention

### Master RUN_ID Format:
```
RUNID_{PC_RUN_ID}_{DATE}_{SEQUENCE}

Example: RUNID_35678_04Mar2026_001

Components:
- RUNID      = Prefix indicating master ID
- 35678      = Performance Center run ID
- 04Mar2026  = Date test was initiated
- 001        = Sequence (if multiple tests same day)
```

### Solution-Specific RUN_ID Format:
```
{SOLUTION}_Run_{DATE}_{SEQUENCE}_{PC_RUN_ID}

Examples:
- AppD_Run_04Mar2026_001_35678
- AWR_Run_04Mar2026_001_35678
- PC_Run_04Mar2026_001_35678
- Mongo_Run_04Mar2026_001_35678

Components:
- AppD/AWR/PC = Solution identifier
- Run         = Standard separator
- 04Mar2026   = Date
- 001         = Sequence
- 35678       = PC_RUN_ID (ALWAYS at the end)
```

### Why This Format?

**Easy to Extract PC_RUN_ID:**
```python
def extract_pc_run_id(run_id: str) -> str:
    # From any format, PC_RUN_ID is always the last part
    parts = run_id.split('_')
    return parts[-1]

# Works for all:
extract_pc_run_id('AppD_Run_04Mar2026_001_35678')    # → 35678
extract_pc_run_id('AWR_Run_04Mar2026_001_35678')     # → 35678
extract_pc_run_id('RUNID_35678_04Mar2026_001')       # → 001 (need different logic)
```

**Human Readable:**
- Can tell which solution: AppD, AWR, PC
- Can see the date: 04Mar2026
- Can identify the PC test: 35678

---

## 🔄 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│  User Starts Performance Test in LoadRunner            │
│  PC_RUN_ID = 35678                                      │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  CREATE MASTER ENTRY                                    │
│  RUN_MASTER                                             │
│  ┌────────────────────────────────────────────────┐    │
│  │ RUN_ID: RUNID_35678_04Mar2026_001              │    │
│  │ PC_RUN_ID: 35678                               │    │
│  │ LOB_NAME: Digital Technology                   │    │
│  │ TRACK: CDV3                                    │    │
│  │ STATUS: INITIATED                              │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                        ↓
        ┌───────────────┼───────────────┬───────────────┐
        ↓               ↓               ↓               ↓
┌───────────────┐ ┌─────────────┐ ┌────────────┐ ┌────────────┐
│ AppD Monitor  │ │ AWR Upload  │ │ PC Fetch   │ │ MongoDB    │
│               │ │             │ │            │ │            │
│ AppD_Run_...  │ │ AWR_Run_... │ │ PC_Run_... │ │ Mongo_...  │
│ _35678        │ │ _35678      │ │ _35678     │ │ _35678     │
│               │ │             │ │            │ │            │
│ FOREIGN KEY → │ │ FK →        │ │ FK →       │ │ FK →       │
│ RUN_MASTER    │ │ RUN_MASTER  │ │ RUN_MASTER │ │ RUN_MASTER │
└───────────────┘ └─────────────┘ └────────────┘ └────────────┘
        ↓               ↓               ↓               ↓
┌────────────────────────────────────────────────────────────┐
│  ALL DATA LINKED TO MASTER RUN_ID                         │
│  Query by PC_RUN_ID = 35678 returns everything!           │
└────────────────────────────────────────────────────────────┘
```

---

## ✅ Benefits Summary

### 1. **Unified Reporting**
Get complete test picture in one query

### 2. **Root Cause Analysis**
Correlate issues across all monitoring tools

### 3. **Traceability**
Know exactly which test run generated which data

### 4. **Data Integrity**
Foreign keys ensure all data links to valid test runs

### 5. **Scalability**
Easy to add new monitoring solutions - just add FK to RUN_MASTER

### 6. **Historical Analysis**
Compare test runs over time by PC_RUN_ID

---

## 🎯 Key Takeaway

**RUN_MASTER is the "hub"** - all monitoring solutions are "spokes"

```
              RUN_MASTER (Hub)
                    │
        ┌───────────┼───────────┬───────────┐
        ↓           ↓           ↓           ↓
      AppD        AWR         PC        MongoDB
    (Spoke)     (Spoke)    (Spoke)     (Spoke)
```

**Every monitoring solution:**
1. Creates its own specific RUN_ID (e.g., AppD_Run_...)
2. Links to master via FOREIGN KEY to RUN_MASTER.RUN_ID
3. Stores PC_RUN_ID for easy querying

**Result:**
All data for test run #35678 can be found by querying RUN_MASTER where PC_RUN_ID = '35678', then following foreign keys to get all related monitoring data!

---

**Is this clear now?** 🎯