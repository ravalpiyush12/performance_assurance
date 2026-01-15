Setup Instructions

Install Oracle Instant Client (if not already installed):

bash# Download from Oracle website
# Extract and set environment variables
export ORACLE_HOME=/path/to/instantclient
export LD_LIBRARY_PATH=$ORACLE_HOME:$LD_LIBRARY_PATH

Install Python dependencies:

bashpip install -r requirements.txt

Configure credentials in Jenkins or create .env file
Test individual components:

bash# Test Kibana connection
python3 -c "from fetchers.kibana_fetcher import KibanaDataFetcher; k = KibanaDataFetcher('URL', 'user', 'pass'); k.test_connection()"

# Test AppDynamics connection
python3 -c "from fetchers.appdynamics_fetcher import AppDynamicsDataFetcher; a = AppDynamicsDataFetcher('URL', 'account', 'user', 'pass'); a.test_connection()"

# Test Oracle connection
python3 -c "from database.db_handler import MonitoringDataDB; db = MonitoringDataDB('user', 'pass', 'dsn'); db.close()"
All scripts are ready to use! Let me know if you need any modifications or have questions about specific components.

# Kibana Configuration
KIBANA_URL=http://your-kibana:5601
KIBANA_USERNAME=your_username
KIBANA_PASSWORD=your_password
KIBANA_VIZ_IDS=viz-id-1,viz-id-2,viz-id-3

# AppDynamics Configuration
APPD_CONTROLLER_URL=http://your-controller:8090
APPD_ACCOUNT_NAME=your_account
APPD_USERNAME=your_username
APPD_PASSWORD=your_password
APPD_APP_NAME=YourApplication
APPD_TIER_NAME=YourTier
APPD_NODE_NAME=YourNode

# Oracle Database Configuration
ORACLE_USER=monitoring_user
ORACLE_PASSWORD=your_password
ORACLE_DSN=hostname:1521/ORCL

# Monitoring Configuration
COLLECTION_INTERVAL=300
TEST_DURATION=3600
ENABLE_KIBANA=true
ENABLE_APPDYNAMICS=true


15Jan Updates:
Test Dashboard Discovery:
bashpython3 test_dashboard_discovery.py \
    --controller "http://controller:8090" \
    --account "customer1" \
    --username "monitor@customer1" \
    --password "password" \
    --dashboard-id 123 \
    --output dashboard_config.json
Run Monitoring with Dashboard ID:
bashpython3 monitoring_main.py \
    --run-id "TEST_001" \
    --test-name "Load Test" \
    --duration 60 \
    --kibana-url "http://kibana:5601" \
    --kibana-user "admin" \
    --kibana-pass "password" \
    --appd-controller "http://controller:8090" \
    --appd-account "customer1" \
    --appd-user "monitor@customer1" \
    --appd-pass "password" \
    --appd-dashboard-id 123 \
    --db-user "monitoring" \
    --db-pass "password" \
    --db-dsn "dbhost:1521/ORCL"



    Test Dashboard Discovery with Verbose Output:
bashpython3 test_dashboard_discovery.py \
    --controller "http://controller:8090" \
    --account "customer1" \
    --username "monitor@customer1" \
    --password "password" \
    --dashboard-id 123 \
    --output dashboard_config.json \
    --verbose
Run Monitoring:
bashpython3 monitoring_main.py \
    --run-id "TEST_001" \
    --test-name "Load Test" \
    --duration 60 \
    --kibana-url "http://kibana:5601" \
    --kibana-user "admin" \
    --kibana-pass "password" \
    --appd-controller "http://controller:8090" \
    --appd-account "customer1" \
    --appd-user "monitor@customer1" \
    --appd-pass "password" \
    --appd-dashboard-id 123 \
    --db-user "monitoring" \
    --db-pass "password" \
    --db-dsn "dbhost:1521/ORCL"
