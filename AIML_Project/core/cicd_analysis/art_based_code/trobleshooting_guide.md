# Troubleshooting FAQ & Common Issues

## 🔧 Quick Problem Solver

---

## Connection Issues

### ❌ **Problem: "Failed to connect to backend"**

**Symptoms:**
- Red "Disconnected" status in dashboard
- Error popup when loading page
- No data displayed

**Solutions:**

**1. Check if Python is running:**
```bash
# Look for the process
ps aux | grep python
# Or on Windows
tasklist | findstr python

# You should see: python app.py
```

**2. Test the backend directly:**
```bash
curl http://localhost:5000/api/health

# Expected response:
# {"status":"ok","message":"Backend is running",...}
```

**3. Check the port:**
```bash
# Linux/Mac
lsof -i :5000

# Windows
netstat -ano | findstr :5000
```

**4. Firewall blocking:**
```bash
# Linux - Allow port 5000
sudo ufw allow 5000

# Windows - Check Windows Firewall settings
```

**5. Wrong URL in HTML:**
```javascript
// In dashboard.html, check line ~580
const API_BASE = 'http://localhost:5000/api';

// If accessing from different machine, use IP:
const API_BASE = 'http://192.168.1.100:5000/api';
```

---

## Database Issues

### ❌ **Problem: "Database connection failed"**

**Check 1: Test Oracle connection separately**
```python
import cx_Oracle

try:
    conn = cx_Oracle.connect('user/password@host:1521/service')
    print("✓ Connected!")
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM DUAL")
    print("✓ Query works!")
    conn.close()
except cx_Oracle.DatabaseError as e:
    print(f"✗ Error: {e}")
```

**Check 2: Verify credentials**
```python
# In app.py, temporarily add debug:
DB_CONFIG = {
    'user': 'your_username',
    'password': 'your_password',
    'dsn': 'your_host:1521/your_service'
}
print(f"Connecting with user: {DB_CONFIG['user']}")
print(f"DSN: {DB_CONFIG['dsn']}")
```

**Check 3: Network connectivity**
```bash
# Can you reach the database server?
ping your_database_host

# Is port 1521 open?
telnet your_database_host 1521
# Or
nc -zv your_database_host 1521
```

**Check 4: Service name vs SID**
```python
# Try both formats:
# Service name (recommended):
dsn = 'host:1521/ORCL'

# SID format:
dsn = cx_Oracle.makedsn('host', 1521, sid='ORCL')
```

### ❌ **Problem: "cx_Oracle not found"**

**Install Oracle Instant Client:**

**Linux:**
```bash
# Download from Oracle
wget https://download.oracle.com/otn_software/linux/instantclient/instantclient-basic-linux.x64-21.1.0.0.0.zip
unzip instantclient-basic-linux.x64-21.1.0.0.0.zip
sudo mv instantclient_21_1 /opt/oracle/

# Set environment
export LD_LIBRARY_PATH=/opt/oracle/instantclient_21_1:$LD_LIBRARY_PATH
export ORACLE_HOME=/opt/oracle/instantclient_21_1

# Add to .bashrc for persistence
echo 'export LD_LIBRARY_PATH=/opt/oracle/instantclient_21_1:$LD_LIBRARY_PATH' >> ~/.bashrc
```

**Windows:**
```
1. Download Oracle Instant Client
2. Extract to C:\oracle\instantclient_21_1
3. Add to System PATH:
   - Control Panel → System → Advanced → Environment Variables
   - Edit PATH, add: C:\oracle\instantclient_21_1
4. Restart command prompt
```

**Mac:**
```bash
brew install instantclient-basic
```

---

## Prediction Issues

### ❌ **Problem: "Prediction shows 0% or 'Insufficient data'"**

**Reason 1: Not enough days of data**
```
Minimum required: 3 days
Current selection: 2 days
→ Change time range to 7+ days
```

**Reason 2: No data in database**
```sql
-- Check if data exists
SELECT COUNT(*), MIN(TEST_DATE), MAX(TEST_DATE)
FROM PTE_TABLE;

-- Should return records with date range
```

**Reason 3: All data is the same**
```sql
-- Check for variance
SELECT 
    STDDEV(FAILURES) as failure_variance,
    AVG(FAILURES) as avg_failures
FROM PTE_TABLE
WHERE TEST_DATE >= SYSDATE - 7;

-- If variance = 0, all values are identical
```

**Solution: Run sample data generator**
```sql
-- Use the sample_data_generator.sql script
-- It creates realistic test data with trends
@sample_data_generator.sql
```

### ❌ **Problem: "Predictions seem wrong"**

**Check confidence score:**
```
Confidence > 80%: Trust the prediction
Confidence 50-80%: Moderate trust
Confidence < 50%: Don't trust it
```

**Check for outliers:**
```sql
-- Find anomalies in your data
SELECT 
    TEST_DATE,
    FAILURES,
    CASE 
        WHEN FAILURES > AVG(FAILURES) OVER () + 2*STDDEV(FAILURES) OVER ()
        THEN 'OUTLIER'
        ELSE 'NORMAL'
    END AS STATUS
FROM PTE_TABLE
WHERE TEST_DATE >= SYSDATE - 7
ORDER BY TEST_DATE;
```

---

## Chart Issues

### ❌ **Problem: "Charts not displaying"**

**Check 1: Chart.js loaded?**
```html
<!-- In dashboard.html, verify this line exists -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0"></script>
```

**Check 2: Canvas elements exist?**
```javascript
// Open browser console (F12)
console.log(document.getElementById('failureChart'));
// Should NOT be null
```

**Check 3: Data format correct?**
```javascript
// In browser console:
fetch('http://localhost:5000/api/dashboard?days=7')
  .then(r => r.json())
  .then(d => console.log(d));

// Should return valid JSON with daily_metrics array
```

**Check 4: JavaScript errors?**
```
- Open browser console (F12)
- Look for red error messages
- Common: "Cannot read property 'map' of undefined"
- Means: Data didn't load properly
```

---

## Performance Issues

### ❌ **Problem: "Dashboard loads very slowly"**

**Optimization 1: Add database indexes**
```sql
-- Check if indexes exist
SELECT index_name, table_name, column_name
FROM user_ind_columns
WHERE table_name = 'PTE_TABLE';

-- Create if missing
CREATE INDEX idx_pte_date ON PTE_TABLE(TEST_DATE);
CREATE INDEX idx_pte_api ON PTE_TABLE(API);
CREATE INDEX idx_pte_art ON PTE_TABLE(ART);
```

**Optimization 2: Limit data**
```python
# In app.py, add row limit for development:
query = """
SELECT * FROM (
    SELECT 
        ART, API, PASS_COUNT, FAILURES, 
        P95_RESPONSE_TIME, TEST_DATE, EXECUTION_TIME
    FROM PTE_TABLE
    WHERE TEST_DATE >= SYSDATE - :days
    ORDER BY TEST_DATE DESC
) WHERE ROWNUM <= 5000
"""
```

**Optimization 3: Check database performance**
```sql
-- Find slow queries
SELECT 
    sql_text,
    elapsed_time/1000000 as elapsed_seconds,
    executions
FROM v$sql
WHERE sql_text LIKE '%PTE_TABLE%'
ORDER BY elapsed_time DESC;
```

### ❌ **Problem: "High memory usage"**

**Check memory:**
```bash
# Linux
free -h
ps aux | grep python | awk '{print $6}'

# Windows
tasklist /FI "IMAGENAME eq python.exe"
```

**Reduce memory:**
```python
# In app.py, clear dataframe after use:
def get_dashboard_data():
    # ... existing code
    result = jsonify({...})
    
    # Clear memory
    analyzer.df = None
    import gc
    gc.collect()
    
    return result
```

---

## Tab & UI Issues

### ❌ **Problem: "ART Specific tab not showing data"**

**Check 1: ARTs loaded?**
```javascript
// In browser console:
fetch('http://localhost:5000/api/arts')
  .then(r => r.json())
  .then(d => console.log(d));

// Should return list of ARTs
```

**Check 2: Selector populated?**
```javascript
// In browser console:
const selector = document.getElementById('artSelector');
console.log(selector.options.length);
// Should be > 1 (first option is "-- Select ART --")
```

**Check 3: Data format correct?**
```sql
-- Verify ART names don't have weird characters
SELECT DISTINCT ART, LENGTH(ART) as name_length
FROM PTE_TABLE;

-- ART names should be clean strings
```

### ❌ **Problem: "Tab switching doesn't work"**

**Check JavaScript errors:**
```
1. Press F12 (browser console)
2. Click on ART Specific View tab
3. Look for errors in Console tab
4. Common issues:
   - "switchTab is not defined" → JavaScript not loaded
   - "Cannot read property..." → Missing DOM element
```

**Verify function exists:**
```javascript
// In browser console:
console.log(typeof switchTab);
// Should output: "function"
```

---

## Data Quality Issues

### ❌ **Problem: "Metrics don't make sense"**

**Validate data:**
```sql
-- Check for data anomalies
SELECT 
    TEST_DATE,
    PASS_COUNT,
    FAILURES,
    CASE 
        WHEN PASS_COUNT < 0 THEN 'NEGATIVE PASSES'
        WHEN FAILURES < 0 THEN 'NEGATIVE FAILURES'
        WHEN PASS_COUNT + FAILURES = 0 THEN 'NO TESTS'
        WHEN P95_RESPONSE_TIME <= 0 THEN 'INVALID P95'
        ELSE 'OK'
    END as validation_status
FROM PTE_TABLE
WHERE TEST_DATE >= SYSDATE - 7
ORDER BY TEST_DATE DESC;
```

**Check for nulls:**
```sql
SELECT 
    COUNT(*) as total,
    COUNT(ART) as has_art,
    COUNT(API) as has_api,
    COUNT(PASS_COUNT) as has_passes,
    COUNT(FAILURES) as has_failures,
    COUNT(P95_RESPONSE_TIME) as has_p95
FROM PTE_TABLE
WHERE TEST_DATE >= SYSDATE - 7;

-- All counts should be equal
```

---

## Browser-Specific Issues

### ❌ **Problem: "Works in Chrome but not Safari/Firefox"**

**CORS issue:**
```python
# In app.py, update CORS:
from flask_cors import CORS

CORS(app, resources={
    r"/api/*": {
        "origins": "*",  # Allow all origins (development only!)
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": False
    }
})
```

**Cache issue:**
```
1. Hard refresh: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)
2. Clear browser cache
3. Try incognito/private mode
```

---

## Common Error Messages & Solutions

### **"TypeError: Cannot read property 'map' of undefined"**
```
Cause: Data didn't load from API
Solution: 
1. Check backend is running
2. Verify API endpoint returns data
3. Check browser console for network errors
```

### **"ORA-12154: TNS:could not resolve the connect identifier"**
```
Cause: Oracle can't find the database
Solution: 
1. Check DSN format: 'host:1521/service_name'
2. Verify tnsnames.ora if using it
3. Try IP address instead of hostname
```

### **"ORA-01017: invalid username/password"**
```
Cause: Wrong credentials
Solution:
1. Test login with SQL*Plus or SQL Developer
2. Check for typos in username/password
3. Verify account is not locked
```

### **"Address already in use: Port 5000"**
```
Cause: Another process using port 5000
Solution:
# Find and kill the process:
# Linux/Mac:
lsof -ti:5000 | xargs kill -9

# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Or use different port in app.py:
app.run(port=5001)
```

---

## Debug Mode Tips

### **Enable detailed logging:**

```python
# In app.py, add at the top:
import logging
logging.basicConfig(level=logging.DEBUG)

# Add debug prints:
@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    days = int(request.args.get('days', 7))
    print(f"DEBUG: Requested {days} days of data")
    
    try:
        data = analyzer.fetch_test_results(days)
        print(f"DEBUG: Fetched {len(data)} records")
        # ... rest of code
```

### **Test individual components:**

```python
# test_components.py
from app import CICDAnalyzer

analyzer = CICDAnalyzer()

# Test 1: Connection
print("Testing connection...")
if analyzer.connect_db():
    print("✓ Connected")
else:
    print("✗ Connection failed")
    exit(1)

# Test 2: Data fetch
print("\nTesting data fetch...")
df = analyzer.fetch_test_results(7)
print(f"✓ Fetched {len(df)} records")

# Test 3: Predictions
print("\nTesting predictions...")
pred = analyzer.predict_failure_rate()
print(f"✓ Prediction: {pred}")

# Test 4: API analysis
print("\nTesting API analysis...")
apis = analyzer.analyze_api_failures()
print(f"✓ Found {len(apis)} APIs")
```

---

## Getting Help

### **Information to provide when asking for help:**

1. **Environment:**
   - OS: Windows/Linux/Mac?
   - Python version: `python --version`
   - Package versions: `pip list`

2. **Error Details:**
   - Full error message
   - When does it occur?
   - What were you trying to do?

3. **Configuration:**
   - Are you using sample data or real data?
   - How many days of data do you have?
   - What time range are you selecting?

4. **Logs:**
   ```bash
   # Python backend logs
   python app.py > output.log 2>&1
   
   # Browser console logs
   # Press F12, copy errors from Console tab
   ```

### **Self-diagnostic script:**

```python
# diagnose.py
print("CI/CD Analytics Diagnostic")
print("="*50)

# Check Python version
import sys
print(f"Python version: {sys.version}")

# Check packages
try:
    import cx_Oracle
    print("✓ cx_Oracle installed")
except:
    print("✗ cx_Oracle not installed")

try:
    import pandas
    print("✓ pandas installed")
except:
    print("✗ pandas not installed")

try:
    import flask
    print("✓ Flask installed")
except:
    print("✗ Flask not installed")

try:
    import sklearn
    print("✓ scikit-learn installed")
except:
    print("✗ scikit-learn not installed")

# Check Oracle client
try:
    print(f"\nOracle client version: {cx_Oracle.clientversion()}")
except:
    print("✗ Oracle Instant Client not found")

print("\n" + "="*50)
print("Run this and share output when asking for help")
```

---

## Still Having Issues?

**Checklist:**
- [ ] Python 3.8+ installed?
- [ ] All dependencies installed? (`pip install -r requirements.txt`)
- [ ] Oracle Instant Client installed?
- [ ] Backend running? (`python app.py`)
- [ ] Database accessible?
- [ ] At least 3 days of test data?
- [ ] Browser console shows no errors?
- [ ] Tried the sample data generator?

If you've checked everything above and still have issues, run the diagnostic script and provide the output! 🔍