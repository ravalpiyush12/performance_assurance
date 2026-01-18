performance-monitoring/
├── config/
│   ├── __init__.py
│   └── config.py
├── fetchers/
│   ├── __init__.py
│   ├── appdynamics_fetcher.py
│   └── kibana_fetcher.py
├── database/
│   ├── __init__.py
│   └── db_handler.py
├── orchestrator/
│   ├── __init__.py
│   └── monitoring_orchestrator.py
├── utils/
│   ├── __init__.py
│   └── logger.py
├── generate_appd_config.py
├── generate_kibana_config.py
├── monitoring_main.py
├── generate_report_main.py
├── test_appd_discovery.py
├── test_kibana.py
├── requirements.txt
└── README.md


Complete Workflow
Step 1: Generate AppDynamics Config
bashpython3 generate_appd_config.py \
    --controller "http://controller:8090" \
    --account "customer1" \
    --username "monitor@customer1" \
    --password "password" \
    --app-names "App1,App2,App3" \
    --output appd_config.json
Step 2: Generate Kibana Config
bashpython3 generate_kibana_config.py \
    --kibana-url "http://kibana:5601" \
    --kibana-user "admin" \
    --kibana-pass "password" \
    --output kibana_config.json
Step 3: Run Monitoring
bashpython3 monitoring_main.py \
    --run-id "PERF_TEST_001" \
    --test-name "Production Load Test" \
    --duration 60 \
    --appd-controller "http://controller:8090" \
    --appd-account "customer1" \
    --appd-user "monitor@customer1" \
    --appd-pass "password" \
    --appd-config "appd_config.json" \
    --kibana-url "http://kibana:5601" \
    --kibana-user "admin" \
    --kibana-pass "password" \
    --kibana-config "kibana_config.json" \
    --kibana-index "your-api-logs-*" \
    --kibana-api-field "api_name.keyword" \
    --kibana-status-field "status" \
    --kibana-response-field "response_time" \
    --db-user "monitoring_user" \
    --db-pass "password" \
    --db-dsn "dbhost:1521/ORCL"
Oracle Tables Created:

TEST_RUNS - Test execution metadata
APPD_SERVER_METRICS - CPU, Memory, Disk, Network metrics
APPD_JVM_METRICS - Heap, GC, Thread metrics
APPD_APPLICATION_METRICS - Calls, Response Time, Errors, Exceptions, Stalls
KIBANA_API_METRICS - API calls, Pass/Fail counts, P90/P95 response times

All metrics are collected every 5 minutes and stored with test_run_id for correlation!


```

## Jenkins Configuration Setup

### 1. Create Jenkins Credentials

In Jenkins → Manage Jenkins → Credentials, create these credentials:

**Performance Center:**
- `pc-url` - String
- `pc-username` - String  
- `pc-password` - Secret text
- `pc-domain` - String
- `pc-project` - String

**AppDynamics:**
- `appd-controller-url` - String
- `appd-account-name` - String
- `appd-username` - String
- `appd-password` - Secret text

**Kibana:**
- `kibana-url` - String
- `kibana-username` - String
- `kibana-password` - Secret text

**Oracle Database:**
- `oracle-username` - String
- `oracle-password` - Secret text
- `oracle-dsn` - String (format: `hostname:1521/ORCL`)

**Email:**
- `email-recipients` - String (comma-separated emails)

### 2. Jenkins Pipeline Setup

1. **Create New Pipeline Job:**
   - New Item → Pipeline
   - Name: `Performance-Test-With-Monitoring`

2. **Configure Pipeline:**
   - Check "This project is parameterized"
   - Parameters will be defined in Jenkinsfile

3. **Pipeline Definition:**
   - Pipeline script from SCM
   - Or paste the Jenkinsfile directly

### 3. Folder Structure in Repository
```
your-repo/
├── Jenkinsfile                          # Main pipeline
├── monitoring/                          # Monitoring scripts
│   ├── config/
│   ├── fetchers/
│   ├── database/
│   ├── orchestrator/
│   ├── utils/
│   ├── generate_appd_config.py
│   ├── generate_kibana_config.py
│   ├── monitoring_main.py
│   ├── generate_report_main.py
│   └── requirements.txt
└── pc_automation.py                     # Your existing PC script


Trigger Pipeline Manually:

Go to Jenkins job
Click "Build with Parameters"
Fill in parameters:

PC_TEST_ID: Your PC test ID
TEST_DURATION: 60
TEST_NAME: Production Load Test
APPD_APP_NAMES: App1,App2,App3
KIBANA_INDEX_PATTERN: api-logs-*



Trigger via Jenkins API:
bashcurl -X POST "http://jenkins-url/job/Performance-Test-With-Monitoring/buildWithParameters" \
  --user "username:token" \
  --data-urlencode "PC_TEST_ID=123" \
  --data-urlencode "TEST_DURATION=60" \
  --data-urlencode "TEST_NAME=Load Test" \
  --data-urlencode "APPD_APP_NAMES=App1,App2"
Pipeline Features:
✅ Parallel Execution - PC test and monitoring run simultaneously
✅ Auto Configuration - Generates AppD and Kibana configs automatically
✅ Error Handling - Pipeline continues even if one component fails
✅ Artifact Archiving - Saves all configs, logs, and reports
✅ Email Notifications - Detailed HTML email with links
✅ Database Storage - All metrics stored with TEST_RUN_ID
✅ Report Generation - Consolidated HTML reports
✅ Flexible Parameters - Easy to customize per test run



# .env file for local development only
# DO NOT commit this file to git!

# AppDynamics Configuration
APPD_CONTROLLER=http://your-controller:8090
APPD_ACCOUNT=customer1
APPD_USERNAME=monitor@customer1
APPD_PASSWORD=your_password

# Kibana Configuration
KIBANA_URL=http://your-kibana:5601
KIBANA_USERNAME=admin
KIBANA_PASSWORD=your_password

# Oracle Database Configuration
ORACLE_USER=monitoring_user
ORACLE_PASSWORD=your_password
ORACLE_DSN=dbhost:1521/ORCL

# Performance Center (if testing PC scripts locally)
PC_URL=http://your-pc-server:8080
PC_USERNAME=pc_user
PC_PASSWORD=your_password
PC_DOMAIN=DEFAULT
PC_PROJECT=MyProject

# Email (optional for local testing)
EMAIL_RECIPIENTS=your-email@company.com


Add to .gitignore:
bash# .gitignore
.env
*.env
.env.*
config/*.json
reports/
logs/
*.log
__pycache__/
*.pyc
Update Python scripts to support .env (Optional):
If you want to support both Jenkins and local .env file, update the scripts:
python# Add to top of monitoring_main.py, generate_appd_config.py, etc.

import os
from pathlib import Path

# Try to load .env file if it exists (for local development)
def load_env_file():
    """Load environment variables from .env file if present"""
    env_file = Path('.env')
    if env_file.exists():
        print("Loading .env file for local development...")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        return True
    return False

# Call at the start of main()
if __name__ == '__main__':
    load_env_file()  # Load .env if running locally
    sys.exit(main())
Option 3: Hybrid Approach (Both Jenkins and Local)
If your team needs both Jenkins and local development, use this structure:
python# utils/config_loader.py
import os
from pathlib import Path

class ConfigLoader:
    """Load configuration from environment or .env file"""
    
    @staticmethod
    def load():
        """Load .env file if it exists (for local dev)"""
        env_file = Path('.env')
        if env_file.exists():
            print("📄 Loading .env file...")
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
    
    @staticmethod
    def get(key, default=None, required=False):
        """Get configuration value from environment"""
        value = os.environ.get(key, default)
        if required and not value:
            raise ValueError(f"Required configuration '{key}' not found!")
        return value
Then in your scripts:
python# monitoring_main.py
from utils.config_loader import ConfigLoader

def parse_arguments():
    parser = argparse.ArgumentParser()
    
    # Load .env if running locally
    ConfigLoader.load()
    
    # Arguments with defaults from environment
    parser.add_argument('--appd-controller', 
                       default=os.environ.get('APPD_CONTROLLER'),
                       help='AppDynamics controller URL')
    # ... rest of arguments
```

## **My Recommendation:**

### **For Your Use Case:**

Since you're using **Jenkins**, you **DON'T need a .env file** at all. Just:

1. ✅ Configure Jenkins Credentials (as shown in previous response)
2. ✅ Use the Jenkinsfile as provided
3. ✅ All scripts will receive credentials via command-line arguments from Jenkins

### **Optional - For Local Testing Only:**

If developers want to test scripts locally before committing:

1. Create `.env` file (only on local machine)
2. Add `.env` to `.gitignore`
3. Add the optional `load_env_file()` function to scripts
4. Test locally: `python3 monitoring_main.py --run-id TEST_001 --duration 5`

## Quick Setup Decision Tree:
```
Do you only run scripts via Jenkins?
│
├─ YES → No .env needed! ✅
│         Use Jenkins Credentials only
│
└─ NO → Do developers need to test locally?
    │
    ├─ YES → Create .env for local testing
    │         (but still use Jenkins Credentials in CI/CD)
    │
    └─ NO → No .env needed! ✅






# Performance Monitoring System

Automated monitoring system for collecting AppDynamics and Kibana metrics during performance tests.

## Features

- **AppDynamics Monitoring**: Server, JVM, and Application metrics
- **Kibana Monitoring**: API metrics including pass/fail counts and response times
- **Oracle Database**: Stores all metrics with test run correlation
- **Jenkins Integration**: Automated execution in CI/CD pipeline
- **Parallel Execution**: Monitors alongside Performance Center tests

## Project Structure
```
performance-monitoring/
├── config/              # Configuration classes
├── fetchers/           # Data collection modules
├── database/           # Oracle database handlers
├── orchestrator/       # Monitoring orchestration
├── utils/              # Utility functions (logging, etc.)
├── generate_appd_config.py      # Generate AppD config
├── generate_kibana_config.py    # Generate Kibana config
├── monitoring_main.py           # Main monitoring script
├── generate_report_main.py      # Report generation
├── test_appd_discovery.py       # AppD testing utility
├── test_kibana.py              # Kibana testing utility
└── requirements.txt            # Python dependencies
```

## Installation

### Prerequisites

- Python 3.7+
- Oracle Instant Client (for cx_Oracle)
- Access to AppDynamics Controller
- Access to Kibana
- Oracle Database

### Setup

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Install Oracle Instant Client:**

For Linux:
```bash
# Download from Oracle website
wget https://download.oracle.com/otn_software/linux/instantclient/...
unzip instantclient-basic-linux.x64-21.1.0.0.0.zip
sudo mv instantclient_21_1 /opt/oracle/
export LD_LIBRARY_PATH=/opt/oracle/instantclient_21_1:$LD_LIBRARY_PATH
```

For Windows:
- Download and extract Oracle Instant Client
- Add to PATH environment variable

3. **Configure Jenkins Credentials:**
- Add all required credentials in Jenkins Credentials Manager
- See Jenkinsfile for required credential IDs

## Usage

### 1. Generate Configurations

**AppDynamics:**
```bash
python3 generate_appd_config.py \
    --controller "http://controller:8090" \
    --account "customer1" \
    --username "user@customer1" \
    --password "password" \
    --app-names "App1,App2" \
    --output appd_config.json
```

**Kibana:**
```bash
python3 generate_kibana_config.py \
    --kibana-url "http://kibana:5601" \
    --kibana-user "admin" \
    --kibana-pass "password" \
    --output kibana_config.json
```

### 2. Run Monitoring
```bash
python3 monitoring_main.py \
    --run-id "TEST_001" \
    --test-name "Load Test" \
    --duration 60 \
    --appd-controller "http://controller:8090" \
    --appd-account "customer1" \
    --appd-user "user@customer1" \
    --appd-pass "password" \
    --appd-config "appd_config.json" \
    --kibana-url "http://kibana:5601" \
    --kibana-user "admin" \
    --kibana-pass "password" \
    --kibana-config "kibana_config.json" \
    --kibana-index "api-logs-*" \
    --db-user "monitoring" \
    --db-pass "password" \
    --db-dsn "dbhost:1521/ORCL"
```

### 3. Testing

**Test AppDynamics Connection:**
```bash
python3 test_appd_discovery.py \
    --controller "http://controller:8090" \
    --account "customer1" \
    --username "user@customer1" \
    --password "password" \
    --app-name "MyApp" \
    --tier-name "WebTier" \
    --node-name "Node1" \
    --test-metrics
```

**Test Kibana Connection:**
```bash
python3 test_kibana.py \
    --kibana-url "http://kibana:5601" \
    --kibana-user "admin" \
    --kibana-pass "password" \
    --test-connection \
    --list-dashboards
```

## Jenkins Integration

The system is designed to run in Jenkins pipelines. See `Jenkinsfile` for complete integration.

### Key Features:
- Parallel execution with Performance Center tests
- Automatic configuration generation
- Artifact archiving
- Email notifications
- HTML report generation

### Jenkins Parameters:
- `PC_TEST_ID`: Performance Center test ID
- `TEST_DURATION`: Test duration in minutes
- `APPD_APP_NAMES`: Comma-separated AppD application names
- `KIBANA_INDEX_PATTERN`: Kibana index pattern

## Database Schema

### Tables Created:

1. **TEST_RUNS** - Test execution metadata
2. **APPD_SERVER_METRICS** - Server metrics (CPU, Memory, Disk, Network)
3. **APPD_JVM_METRICS** - JVM metrics (Heap, GC, Threads)
4. **APPD_APPLICATION_METRICS** - Application metrics (Calls, Response Time, Errors)
5. **KIBANA_API_METRICS** - API metrics (Pass/Fail counts, Response times)

### Query Examples:
```sql
-- Get test run information
SELECT * FROM TEST_RUNS WHERE TEST_RUN_ID = 'TEST_001';

-- Get AppDynamics JVM metrics
SELECT * FROM APPD_JVM_METRICS 
WHERE TEST_RUN_ID = 'TEST_001' 
AND NODE_NAME = 'WebNode1'
ORDER BY TIMESTAMP;

-- Get Kibana API metrics
SELECT * FROM KIBANA_API_METRICS 
WHERE TEST_RUN_ID = 'TEST_001'
ORDER BY TOTAL_COUNT DESC;
```

## Configuration Files

### AppDynamics Config Format:
```json
{
  "description": "AppDynamics monitoring configuration",
  "applications": [
    {
      "app_name": "Application1",
      "tiers": [
        {
          "tier_name": "WebTier",
          "nodes": ["Node1", "Node2"]
        }
      ]
    }
  ]
}
```

### Kibana Config Format:
```json
{
  "description": "Kibana monitoring configuration",
  "dashboards": [
    {
      "id": "dashboard-id",
      "name": "API Performance Dashboard",
      "panel_count": 5
    }
  ]
}
```

## Troubleshooting

### Oracle Connection Issues:
```bash
# Check Oracle Instant Client
python3 -c "import cx_Oracle; print(cx_Oracle.clientversion())"

# Test connection
python3 -c "import cx_Oracle; cx_Oracle.connect('user/pass@host:1521/service')"
```

### AppDynamics Issues:
- Verify controller URL is accessible
- Check username format: `user@account`
- Test with discovery script first

### Kibana Issues:
- Verify index pattern exists
- Check field names match your data
- Test with test script first

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review Jenkins console output
3. Verify database connections
4. Test individual components with test scripts

## License

Internal use only - [Your Company Name]


```

Now you have all the missing files! Your project structure is complete:
```
performance-monitoring/
├── config/
│   ├── __init__.py ✅
│   └── config.py ✅
├── fetchers/
│   ├── __init__.py ✅
│   ├── appdynamics_fetcher.py ✅
│   └── kibana_fetcher.py ✅
├── database/
│   ├── __init__.py ✅
│   └── db_handler.py ✅
├── orchestrator/
│   ├── __init__.py ✅
│   └── monitoring_orchestrator.py ✅
├── utils/
│   ├── __init__.py ✅
│   └── logger.py ✅
├── generate_appd_config.py ✅
├── generate_kibana_config.py ✅
├── monitoring_main.py ✅
├── generate_report_main.py ✅
├── test_appd_discovery.py ✅
├── test_kibana.py ✅
├── requirements.txt ✅
├── README.md ✅
├── verify_installation.py ✅
└── Jenkinsfile ✅