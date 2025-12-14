# CI/CD NFT Test Analysis System - Setup Guide

## 📋 Requirements

### Python Dependencies (requirements.txt)
```
cx_Oracle==8.3.0
pandas==2.1.3
numpy==1.24.3
flask==3.0.0
flask-cors==4.0.0
scikit-learn==1.3.2
```

### System Requirements
- Python 3.8+
- Oracle Instant Client (for cx_Oracle)
- Oracle Database with PTE table

## 🗄️ Oracle Database Schema

Your PTE table should have the following structure:

```sql
CREATE TABLE PTE_TABLE (
    TEST_ID NUMBER PRIMARY KEY,
    ART VARCHAR2(100),              -- Application/Feature name
    API VARCHAR2(200),               -- API endpoint
    PASS_COUNT NUMBER,               -- Number of passed tests
    FAILURES NUMBER,                 -- Number of failed tests
    P95_RESPONSE_TIME NUMBER,        -- 95th percentile response time (ms)
    TEST_DATE DATE,                  -- Date of test execution
    EXECUTION_TIME NUMBER            -- Total execution time (seconds)
);

-- Create index for better query performance
CREATE INDEX idx_pte_date ON PTE_TABLE(TEST_DATE);
CREATE INDEX idx_pte_api ON PTE_TABLE(API);
CREATE INDEX idx_pte_art ON PTE_TABLE(ART);
```

## 🚀 Installation Steps

### 1. Install Oracle Instant Client

#### For Linux:
```bash
# Download Oracle Instant Client
wget https://download.oracle.com/otn_software/linux/instantclient/instantclient-basic-linux.x64-21.1.0.0.0.zip

# Unzip
unzip instantclient-basic-linux.x64-21.1.0.0.0.zip

# Set environment variables
export LD_LIBRARY_PATH=/path/to/instantclient_21_1:$LD_LIBRARY_PATH
export ORACLE_HOME=/path/to/instantclient_21_1
```

#### For Windows:
1. Download Oracle Instant Client from Oracle website
2. Extract to `C:\oracle\instantclient_21_1`
3. Add to PATH: `C:\oracle\instantclient_21_1`

#### For macOS:
```bash
brew tap InstantClientTap/instantclient
brew install instantclient-basic
```

### 2. Install Python Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Database Connection

Edit the `DB_CONFIG` section in the Python code:

```python
DB_CONFIG = {
    'user': 'your_oracle_username',
    'password': 'your_oracle_password',
    'dsn': 'hostname:1521/servicename'  # Example: 'localhost:1521/ORCL'
}
```

### 4. Create Project Structure

```
cicd-analysis/
├── app.py                 # Python backend (provided)
├── templates/
│   └── dashboard.html     # HTML frontend (provided)
├── requirements.txt       # Dependencies
├── config.py             # Configuration file (optional)
└── README.md             # Documentation
```

## 🏃 Running the Application

### 1. Start the Python Backend

```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run the Flask application
python app.py
```

The server will start on `http://localhost:5000`

### 2. Access the Dashboard

Open your web browser and navigate to:
```
http://localhost:5000
```

## 📊 Sample Data Population (for testing)

If you need to populate sample data for testing:

```sql
-- Sample data insertion script
BEGIN
    FOR i IN 1..30 LOOP
        FOR j IN 1..5 LOOP
            INSERT INTO PTE_TABLE (
                TEST_ID,
                ART,
                API,
                PASS_COUNT,
                FAILURES,
                P95_RESPONSE_TIME,
                TEST_DATE,
                EXECUTION_TIME
            ) VALUES (
                SEQ_PTE.NEXTVAL,  -- Assuming sequence exists
                CASE MOD(j, 3)
                    WHEN 0 THEN 'Authentication'
                    WHEN 1 THEN 'Payment Gateway'
                    ELSE 'User Management'
                END,
                '/api/v1/endpoint' || j,
                ROUND(DBMS_RANDOM.VALUE(400, 500)),
                ROUND(DBMS_RANDOM.VALUE(5, 50)),
                ROUND(DBMS_RANDOM.VALUE(100, 500)),
                SYSDATE - (30 - i),
                ROUND(DBMS_RANDOM.VALUE(300, 600))
            );
        END LOOP;
    END LOOP;
    COMMIT;
END;
/
```

## 🔧 Configuration Options

### Scheduled Execution (12PM - 2PM EST)

Add a cron job (Linux/Mac) or Task Scheduler (Windows) to run data collection:

#### Linux/Mac (crontab):
```bash
# Run at 12 PM EST daily
0 12 * * * cd /path/to/cicd-analysis && /path/to/venv/bin/python collect_data.py

# Run at 2 PM EST daily
0 14 * * * cd /path/to/cicd-analysis && /path/to/venv/bin/python collect_data.py
```

#### Windows Task Scheduler:
Create a task that runs at 12 PM and 2 PM EST daily

### Auto-refresh Dashboard

The dashboard auto-refreshes every 5 minutes. To change this, modify in `dashboard.html`:

```javascript
// Change 300000 (5 minutes) to desired interval in milliseconds
setInterval(refreshData, 300000);
```

## 📈 API Endpoints

The backend provides these REST API endpoints:

- `GET /` - Dashboard home page
- `POST /api/init` - Initialize database connection
- `GET /api/dashboard?days=30` - Get all dashboard data
- `GET /api/metrics/daily` - Get daily metrics
- `GET /api/predictions` - Get failure predictions
- `GET /api/analysis/api` - Get API-level analysis
- `GET /api/analysis/art` - Get ART-level analysis
- `GET /api/performance` - Get performance analysis
- `GET /api/instability` - Get instability hotspots
- `GET /api/alerts` - Get current alerts
- `GET /api/recommendations` - Get AI recommendations

## 🔍 Troubleshooting

### Database Connection Issues

```python
# Test connection separately
import cx_Oracle

try:
    conn = cx_Oracle.connect('user/password@hostname:1521/servicename')
    print("Connection successful!")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
```

### Port Already in Use

```bash
# Change port in app.py
app.run(host='0.0.0.0', port=5001, debug=True)  # Use different port
```

### CORS Issues

If accessing from different domain, update CORS settings:

```python
CORS(app, resources={r"/api/*": {"origins": "http://yourdomain.com"}})
```

## 🎯 Key Features Explained

### 1. **Predictive Analytics**
- Uses Linear Regression to predict failure rates
- Provides 24-hour and 7-day forecasts
- Calculates confidence scores

### 2. **Trend Analysis**
- Identifies increasing/decreasing/stable trends
- Analyzes patterns across APIs and ARTs
- Tracks performance degradation

### 3. **Instability Detection**
- Calculates instability scores using:
  - Failure rate variance (50%)
  - Average failures (30%)
  - Failure trend (20%)

### 4. **Early Warning System**
- Generates alerts when thresholds are exceeded
- Prioritizes by severity (critical/high/medium/low)
- Provides actionable recommendations

## 📧 Support

For issues or questions:
1. Check Oracle connection and credentials
2. Verify table structure matches schema
3. Ensure all dependencies are installed
4. Check Python and Oracle Instant Client versions

## 🔒 Security Recommendations

1. **Never commit credentials** - Use environment variables:
```python
import os
DB_CONFIG = {
    'user': os.getenv('ORACLE_USER'),
    'password': os.getenv('ORACLE_PASS'),
    'dsn': os.getenv('ORACLE_DSN')
}
```

2. **Use connection pooling** for production
3. **Enable HTTPS** for production deployments
4. **Implement authentication** for dashboard access

## 🚀 Production Deployment

For production, consider:
- Using Gunicorn/uWSGI instead of Flask dev server
- Setting up nginx as reverse proxy
- Implementing Redis for caching
- Using environment-based configuration
- Setting up monitoring and logging
