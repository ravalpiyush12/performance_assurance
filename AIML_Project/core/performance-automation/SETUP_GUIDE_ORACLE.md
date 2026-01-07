# Jenkins Scheduled Pipeline with Oracle Integration - Setup Guide

## 📋 Overview

This solution:
- ✅ Runs PC tests on a schedule (daily at 2 AM)
- ✅ Extracts transaction metrics from HTML reports
- ✅ Loads data into Oracle database
- ✅ No need to view HTML reports manually
- ✅ All data queryable in Oracle

---

## 🏗️ Architecture

```
Jenkins (Scheduled) 
    ↓
Trigger PC Test
    ↓
Download Report.zip
    ↓
Extract & Parse HTML Report
    ↓
Extract Transaction Metrics
    ↓
Load to Oracle Database
    ↓
Send Email Notification
```

---

## 📊 Oracle Database Schema

### Table 1: PC_TEST_RUNS
```sql
CREATE TABLE PC_TEST_RUNS (
    RUN_ID NUMBER PRIMARY KEY,
    TEST_ID NUMBER NOT NULL,
    BUILD_NUMBER VARCHAR2(50),
    RUN_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    TEST_STATUS VARCHAR2(50),
    TEST_DURATION NUMBER,
    PC_HOST VARCHAR2(255),
    PC_PROJECT VARCHAR2(255),
    CREATED_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Table 2: PC_TRANSACTIONS
```sql
CREATE TABLE PC_TRANSACTIONS (
    TRANSACTION_ID NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    RUN_ID NUMBER NOT NULL,
    TRANSACTION_NAME VARCHAR2(255) NOT NULL,
    AVG_RESPONSE_TIME NUMBER(10,2),
    MIN_RESPONSE_TIME NUMBER(10,2),
    MAX_RESPONSE_TIME NUMBER(10,2),
    PERCENTILE_90 NUMBER(10,2),
    PERCENTILE_95 NUMBER(10,2),
    ERROR_RATE NUMBER(5,2),
    TRANSACTION_COUNT NUMBER,
    CREATED_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_RUN FOREIGN KEY (RUN_ID) REFERENCES PC_TEST_RUNS(RUN_ID)
);

-- For Oracle < 12c without IDENTITY
CREATE SEQUENCE PC_TRANSACTIONS_SEQ START WITH 1;

ALTER TABLE PC_TRANSACTIONS MODIFY TRANSACTION_ID DEFAULT PC_TRANSACTIONS_SEQ.NEXTVAL;
```

---

## 🚀 Setup Steps

### Step 1: Create Oracle Tables

Connect to Oracle and run:
```sql
-- Create tables (run create_tables.sql from artifacts)
@create_tables.sql

-- Verify tables
SELECT * FROM user_tables WHERE table_name LIKE 'PC_%';

-- Grant permissions to Jenkins user
GRANT SELECT, INSERT, UPDATE ON PC_TEST_RUNS TO jenkins_user;
GRANT SELECT, INSERT, UPDATE ON PC_TRANSACTIONS TO jenkins_user;
```

### Step 2: Configure Jenkins Credentials

1. **PC Credentials:**
   ```
   Jenkins → Credentials → Add Credentials
   Kind: Username with password
   ID: pc-credentials
   Username: <PC username>
   Password: <PC password>
   ```

2. **Oracle Credentials:**
   ```
   Jenkins → Credentials → Add Credentials
   Kind: Username with password
   ID: oracle-credentials
   Username: <Oracle username>
   Password: <Oracle password>
   ```

### Step 3: Install Python Dependencies on Jenkins Agent

```bash
# SSH to Jenkins agent
ssh jenkins-agent

# Install Python packages
pip3 install --user beautifulsoup4 lxml cx_Oracle --break-system-packages

# Or system-wide (if you have sudo)
sudo pip3 install beautifulsoup4 lxml cx_Oracle

# Verify installation
python3 -c "import bs4, cx_Oracle; print('OK')"
```

### Step 4: Install Oracle Instant Client (Required for cx_Oracle)

```bash
# Download Oracle Instant Client
wget https://download.oracle.com/otn_software/linux/instantclient/instantclient-basic-linux.x64-19.10.0.0.0dbru.zip

# Extract
unzip instantclient-basic-linux.x64-19.10.0.0.0dbru.zip -d /opt/oracle

# Set environment variables
export LD_LIBRARY_PATH=/opt/oracle/instantclient_19_10:$LD_LIBRARY_PATH

# Add to Jenkins agent's .bashrc or Jenkins configuration
echo 'export LD_LIBRARY_PATH=/opt/oracle/instantclient_19_10:$LD_LIBRARY_PATH' >> ~/.bashrc
```

### Step 5: Create Jenkins Job

1. **New Item → Pipeline**
2. **Name:** PC-Automated-Daily-Tests
3. **Configure:**
   - Check "Do not allow concurrent builds"
   - Pipeline script from SCM (recommended) or paste Jenkinsfile

### Step 6: Configure Schedule

In Jenkinsfile, the `triggers` block sets the schedule:

```groovy
triggers {
    cron('0 2 * * *')  // Daily at 2 AM
}
```

**Cron Format:** `minute hour day month dayofweek`

**Examples:**
```
0 2 * * *         # Daily at 2 AM
0 2 * * 1-5       # Weekdays at 2 AM
0 */6 * * *       # Every 6 hours
H 2 * * *         # Daily at 2 AM (distributed hash)
0 2 * * 0         # Sundays at 2 AM
0 8,20 * * *      # Twice daily at 8 AM and 8 PM
```

---

## 🧪 Testing

### Test 1: Parse Report Locally

```bash
# Download report from previous run
wget http://jenkins-server/job/PC-Test/lastSuccessfulBuild/artifact/results/Report.zip

# Extract
unzip Report.zip -d test_report

# Run parser
python3 parse_pc_report.py test_report/index.html --output-json data.json --print-summary

# Check output
cat data.json
```

### Test 2: Test Oracle Connection

```python
import cx_Oracle

conn = cx_Oracle.connect(
    user='jenkins_user',
    password='password',
    dsn='oracle-server:1521/ORCL'
)

cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM PC_TEST_RUNS')
print(cursor.fetchone())

conn.close()
print("✓ Oracle connection works!")
```

### Test 3: Manual Load Test

```bash
# Load test data
python3 load_to_oracle.py \
    --json-file data.json \
    --oracle-user jenkins_user \
    --oracle-password password \
    --oracle-dsn oracle-server:1521/ORCL \
    --run-id 12345 \
    --test-id 1 \
    --build-number 100 \
    --test-status FINISHED \
    --create-tables

# Verify in Oracle
sqlplus jenkins_user/password@oracle-server:1521/ORCL
SQL> SELECT * FROM PC_TEST_RUNS WHERE RUN_ID = 12345;
SQL> SELECT COUNT(*) FROM PC_TRANSACTIONS WHERE RUN_ID = 12345;
```

---

## 📊 Querying Oracle Data

### Get Latest Test Results
```sql
SELECT 
    r.RUN_ID,
    r.BUILD_NUMBER,
    r.RUN_DATE,
    r.TEST_STATUS,
    COUNT(t.TRANSACTION_ID) as TRANSACTION_COUNT,
    AVG(t.AVG_RESPONSE_TIME) as OVERALL_AVG_RESPONSE
FROM PC_TEST_RUNS r
LEFT JOIN PC_TRANSACTIONS t ON r.RUN_ID = t.RUN_ID
WHERE r.RUN_DATE >= SYSDATE - 7  -- Last 7 days
GROUP BY r.RUN_ID, r.BUILD_NUMBER, r.RUN_DATE, r.TEST_STATUS
ORDER BY r.RUN_DATE DESC;
```

### Transaction Performance Trends
```sql
SELECT 
    t.TRANSACTION_NAME,
    r.RUN_DATE,
    t.AVG_RESPONSE_TIME,
    t.PERCENTILE_90,
    t.PERCENTILE_95,
    t.ERROR_RATE
FROM PC_TRANSACTIONS t
JOIN PC_TEST_RUNS r ON t.RUN_ID = r.RUN_ID
WHERE t.TRANSACTION_NAME = 'Login'
  AND r.RUN_DATE >= SYSDATE - 30
ORDER BY r.RUN_DATE DESC;
```

### Find Slow Transactions
```sql
SELECT 
    r.RUN_ID,
    r.RUN_DATE,
    t.TRANSACTION_NAME,
    t.AVG_RESPONSE_TIME,
    t.MAX_RESPONSE_TIME,
    t.ERROR_RATE
FROM PC_TRANSACTIONS t
JOIN PC_TEST_RUNS r ON t.RUN_ID = r.RUN_ID
WHERE t.AVG_RESPONSE_TIME > 5000  -- Slower than 5 seconds
  AND r.RUN_DATE >= SYSDATE - 7
ORDER BY t.AVG_RESPONSE_TIME DESC;
```

### Error Rate Analysis
```sql
SELECT 
    t.TRANSACTION_NAME,
    AVG(t.ERROR_RATE) as AVG_ERROR_RATE,
    MAX(t.ERROR_RATE) as MAX_ERROR_RATE,
    COUNT(*) as RUN_COUNT
FROM PC_TRANSACTIONS t
JOIN PC_TEST_RUNS r ON t.RUN_ID = r.RUN_ID
WHERE r.RUN_DATE >= SYSDATE - 30
GROUP BY t.TRANSACTION_NAME
HAVING AVG(t.ERROR_RATE) > 0
ORDER BY AVG_ERROR_RATE DESC;
```

---

## 🔄 Workflow

### Daily Automated Run

```
02:00 AM - Jenkins trigger fires
02:00 AM - Authenticate with PC
02:01 AM - Trigger test (600 seconds = 10 min)
02:11 AM - Test completes
02:11 AM - Download Report.zip
02:11 AM - Extract and parse HTML
02:12 AM - Load 50 transactions to Oracle
02:12 AM - Send email notification
02:13 AM - Pipeline completes

Next Run: 02:00 AM tomorrow
```

### Manual Run

```
Anytime - Click "Build with Parameters"
- Adjust TEST_DURATION if needed
- Enable/disable LOAD_TO_ORACLE
- Run immediately
```

---

## 🎯 Benefits

### 1. No Manual Report Viewing
- Reports parsed automatically
- Data extracted to database
- Query anytime with SQL

### 2. Historical Analysis
- All runs stored in Oracle
- Trend analysis possible
- Compare across builds

### 3. Scheduled Execution
- Runs daily automatically
- No manual intervention
- Consistent test execution

### 4. Data Integration
- Export to BI tools
- Create dashboards
- Automated reporting

---

## 📂 Files Provided

1. **parse_pc_report.py** - HTML report parser
2. **load_to_oracle.py** - Oracle database loader
3. **Jenkinsfile-Scheduled-Oracle** - Complete pipeline
4. **create_tables.sql** - Oracle table creation script
5. **test_oracle_connection.py** - Connection test script

---

## 🆘 Troubleshooting

### Issue: cx_Oracle ImportError

```bash
# Check Oracle Instant Client
echo $LD_LIBRARY_PATH

# Should include /opt/oracle/instantclient_XX_X

# Add to Jenkins:
# Manage Jenkins → Configure System → Global properties
# Environment variables:
# Name: LD_LIBRARY_PATH
# Value: /opt/oracle/instantclient_19_10:$LD_LIBRARY_PATH
```

### Issue: No Transactions Parsed

```bash
# Check HTML report structure
unzip Report.zip
grep -i "transaction" index.html | head -20

# Run parser with debug
python3 parse_pc_report.py index.html --print-summary
```

### Issue: Oracle Connection Failed

```bash
# Test connection
tnsping oracle-server:1521/ORCL

# Test with sqlplus
sqlplus username/password@oracle-server:1521/ORCL

# Check firewall
telnet oracle-server 1521
```

---

## 📧 Email Notification Sample

The email will include:
- Test status
- Run ID and Build number
- Number of transactions loaded to Oracle
- Link to Jenkins artifacts
- SQL query to view results

---

## 🎉 Summary

**This solution provides:**
- ✅ Fully automated daily testing
- ✅ Automatic data extraction
- ✅ Oracle database integration
- ✅ No manual report viewing needed
- ✅ Historical data for analysis
- ✅ Scheduled execution (daily 2 AM)

**Data is always accessible via Oracle SQL queries!**
