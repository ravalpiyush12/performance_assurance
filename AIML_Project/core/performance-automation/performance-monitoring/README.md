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