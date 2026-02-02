🎯 What's Updated
1. Oracle Schema - New Column Added ✓
sqlALTER TABLE PC_TEST_RUNS ADD SCENARIO_NAME VARCHAR2(255);
2. Jenkins Pipeline - New Stage Added ✓
groovystage('Get Scenario Name')  // Added after "Trigger Test"
- Fetches run details from PC
- Extracts scenario/test name from XML
- Saves to scenario_name.txt
- Tries multiple XML field names
3. Oracle Loader - Updated to Include Scenario ✓
pythonINSERT INTO PC_TEST_RUNS (
    RUN_ID, TEST_ID, SCENARIO_NAME, BUILD_NUMBER, ...
)

📊 Updated Oracle Schema
PC_TEST_RUNS Table:
sqlRUN_ID          NUMBER          Primary Key
TEST_ID         NUMBER          Test ID
SCENARIO_NAME   VARCHAR2(255)   ⭐ NEW - Scenario/Test Name
BUILD_NUMBER    VARCHAR2(50)    Jenkins Build #
RUN_DATE        TIMESTAMP       When test ran
TEST_STATUS     VARCHAR2(50)    FINISHED/FAILED
TEST_DURATION   NUMBER          Duration in seconds
PC_HOST         VARCHAR2(255)   PC Server
PC_PROJECT      VARCHAR2(255)   PC Project

🚀 Implementation Steps
Step 1: Update Oracle Table
sql-- Run this on your Oracle database
sqlplus your_user/your_password@your_database

@add_scenario_column.sql

-- Verify column added
DESC PC_TEST_RUNS;
Step 2: Update Jenkinsfile
Add two new stages to your Jenkinsfile:
A. After "Trigger Test" stage:
groovy// Copy content from jenkinsfile_scenario_stage.groovy
stage('Get Scenario Name') {
    // Captures scenario name from PC
}
B. Replace "Load to Oracle Database" stage:
groovy// Copy content from jenkinsfile_oracle_load_stage.groovy
stage('Load to Oracle Database') {
    // Updated to include scenario_name parameter
}
Step 3: Test the Integration
bash# Test locally first
python3 load_to_oracle.py \
    --json-file data.json \
    --oracle-user user \
    --oracle-password pass \
    --oracle-dsn host:1521/service \
    --run-id 12345 \
    --test-id 1 \
    --scenario-name "Login_Scenario" \
    --build-number 100 \
    --test-status FINISHED

# Verify in Oracle
SELECT RUN_ID, SCENARIO_NAME, TEST_ID, BUILD_NUMBER 
FROM PC_TEST_RUNS 
ORDER BY RUN_DATE DESC;

🔍 How Scenario Name is Captured
Method 1: From Run Details
bashGET /LoadTest/rest/domains/{domain}/projects/{project}/Runs/{runId}

# Tries to extract from XML tags:
<TestName>Login_Scenario</TestName>
<ScenarioName>Login_Scenario</ScenarioName>
<n>Login_Scenario</n>
Method 2: From Test Details (Fallback)
bashGET /LoadTest/rest/domains/{domain}/projects/{project}/Tests/{testId}

# Extracts test name as fallback
<n>Login_Performance_Test</n>
```

### Method 3: Default (Last Resort)
```
If no name found: "Test_{TEST_ID}"
Example: "Test_1"

📊 Sample Queries with Scenario Name
Query 1: Latest Results by Scenario
sqlSELECT 
    SCENARIO_NAME,
    RUN_ID,
    RUN_DATE,
    TEST_STATUS,
    COUNT(t.TRANSACTION_ID) as TRANSACTIONS
FROM PC_TEST_RUNS r
LEFT JOIN PC_TRANSACTIONS t ON r.RUN_ID = t.RUN_ID
WHERE RUN_DATE >= SYSDATE - 7
GROUP BY SCENARIO_NAME, RUN_ID, RUN_DATE, TEST_STATUS
ORDER BY RUN_DATE DESC;
Query 2: Compare Scenarios
sqlSELECT 
    SCENARIO_NAME,
    COUNT(DISTINCT RUN_ID) as TOTAL_RUNS,
    AVG(TEST_DURATION) as AVG_DURATION,
    MAX(RUN_DATE) as LAST_RUN
FROM PC_TEST_RUNS
WHERE RUN_DATE >= SYSDATE - 30
GROUP BY SCENARIO_NAME
ORDER BY LAST_RUN DESC;
Query 3: Scenario Performance Trend
sqlSELECT 
    r.SCENARIO_NAME,
    TRUNC(r.RUN_DATE) as RUN_DAY,
    AVG(t.AVG_RESPONSE_TIME) as AVG_RESPONSE
FROM PC_TEST_RUNS r
JOIN PC_TRANSACTIONS t ON r.RUN_ID = t.RUN_ID
WHERE r.RUN_DATE >= SYSDATE - 30
GROUP BY r.SCENARIO_NAME, TRUNC(r.RUN_DATE)
ORDER BY RUN_DAY DESC, SCENARIO_NAME;
```

---

## 📂 Files Delivered

### 1. **add_scenario_column.sql**
- Adds SCENARIO_NAME column to existing table
- Includes null check
- Updates existing records (optional)
- Shows verification queries

### 2. **oracle_queries_with_scenario.sql**
- 11 sample queries using scenario name
- Latest results by scenario
- Scenario comparisons
- Performance trends
- Export formats

### 3. **jenkinsfile_scenario_stage.groovy**
- Complete stage to capture scenario name
- Multiple extraction methods
- Fallback strategies
- Saves to file for later use

### 4. **jenkinsfile_oracle_load_stage.groovy**
- Updated Oracle load stage
- Includes scenario_name parameter
- Inline Python script
- Proper error handling

### 5. **load_to_oracle.py** (Updated)
- Updated schema with SCENARIO_NAME
- Updated INSERT statement
- Updated command-line arguments
- UPDATE on duplicate (if run exists)

---

## 🎯 Console Output Example
```
==========================================
Getting Scenario Details
==========================================

Run details XML received (length: 2456)
Scenario Name: Login_Performance_Test

Fetching test metadata for Test ID: 1
Test Name from Test Details: Login_Performance_Test

✓ Scenario Name captured: Login_Performance_Test

==========================================
Loading Data to Oracle
==========================================

Run ID: 12345
Scenario Name: Login_Performance_Test
Status: FINISHED

Connecting to Oracle: oracle-server:1521/ORCL
✓ Connected to Oracle
✓ Inserted run 12345 - Scenario: Login_Performance_Test
✓ Loaded 25 transactions to Oracle

✓ Data loaded to Oracle successfully
  - Run ID: 12345
  - Scenario: Login_Performance_Test
  - Transactions loaded
```

---

## 🔄 Complete Workflow
```
1. Authenticate with PC ✓
2. Trigger Test ✓
3. Get Scenario Name ⭐ NEW
   ├── Fetch run details XML
   ├── Extract scenario name
   └── Save to file
4. Monitor Test ✓
5. Download Report ✓
6. Parse Transactions ✓
7. Load to Oracle ⭐ UPDATED
   ├── Include scenario_name
   ├── Link with RUN_ID
   └── Store in database
8. Query Data ⭐ NEW QUERIES
   ├── Filter by scenario
   ├── Compare scenarios
   └── Track trends

✅ Benefits
1. Scenario Identification

Know which test scenario ran
Filter results by scenario
Compare different scenarios

2. Better Reporting
sql-- Weekly report by scenario
SELECT 
    SCENARIO_NAME,
    COUNT(*) as RUNS,
    AVG(response) as AVG_RESPONSE
FROM ...
GROUP BY SCENARIO_NAME;
3. Historical Analysis
sql-- Track scenario performance over time
SELECT 
    SCENARIO_NAME,
    RUN_DATE,
    AVG_RESPONSE_TIME
FROM ...
WHERE SCENARIO_NAME = 'Login_Test'
ORDER BY RUN_DATE;
4. Dashboard Ready

Group by scenario
Compare scenarios side-by-side
Track scenario-specific SLAs


🧪 Testing Checklist

 Add SCENARIO_NAME column to Oracle
 Verify column with DESC PC_TEST_RUNS
 Add "Get Scenario Name" stage to Jenkinsfile
 Update "Load to Oracle" stage
 Run test pipeline
 Check console for scenario name
 Verify in Oracle: SELECT * FROM PC_TEST_RUNS
 Test sample queries


🎉 Summary
Now capturing:

✅ Run ID
✅ Test ID
✅ Scenario Name ⭐ NEW
✅ Transaction metrics
✅ Response times
✅ Error rates

Stored in Oracle with:

RUN_ID as primary key
SCENARIO_NAME for filtering
Full transaction details
Queryable anytime!