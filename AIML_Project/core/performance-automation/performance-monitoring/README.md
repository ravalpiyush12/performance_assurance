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



16Jan.
    1. Discover Applications/Tiers/Nodes:
bashpython3 test_appd_discovery.py \
    --controller "http://controller:8090" \
    --account "customer1" \
    --username "monitor@customer1" \
    --password "password" \
    --output appd_config.json
2. Run Monitoring:
bashpython3 monitoring_main.py \
    --run-id "TEST_001" \
    --test-name "Load Test" \
    --duration 60 \
    --appd-controller "http://controller:8090" \
    --appd-account "customer1" \
    --appd-user "monitor@customer1" \
    --appd-pass "password" \
    --appd-config "./appd_config.json" \
    --db-user "monitoring" \
    --db-pass "password" \
    --db-dsn "dbhost:1521/ORCL" \
    --collection-interval 300
3. Jenkins Pipeline Parameter:
groovyparameters {
    string(name: 'APPD_CONFIG_FILE', defaultValue: 'config/appd_config.json', 
           description: 'AppDynamics Configuration File')
}
This simplified approach:

✅ Clear Input Format - JSON configuration for apps/tiers/nodes
✅ Auto-Discovery - Automatically discovers nodes if not specified
✅ Three Metric Types - Server, JVM, and Application metrics
✅ 5-Minute Collection - Collects metrics every 5 minutes
✅ Multiple Apps Support - Handles multiple applications, tiers, and nodes
✅ Easy Testing - Discovery script to generate configuration
✅ No Dashboard Dependency - Direct metric collection via REST API




1. Test Single App/Tier/Node (Basic):
bashpython3 test_appd_discovery.py \
    --controller "http://controller:8090" \
    --account "customer1" \
    --username "monitor@customer1" \
    --password "password" \
    --app-name "MyApplication" \
    --tier-name "WebTier" \
    --node-name "WebNode1"
2. Test Single App/Tier/Node with Metrics Collection:
bashpython3 test_appd_discovery.py \
    --controller "http://controller:8090" \
    --account "customer1" \
    --username "monitor@customer1" \
    --password "password" \
    --app-name "MyApplication" \
    --tier-name "WebTier" \
    --node-name "WebNode1" \
    --test-metrics
3. Test Single Config and Generate Config File:
bashpython3 test_appd_discovery.py \
    --controller "http://controller:8090" \
    --account "customer1" \
    --username "monitor@customer1" \
    --password "password" \
    --app-name "MyApplication" \
    --tier-name "WebTier" \
    --node-name "WebNode1" \
    --test-metrics \
    --output test_config.json
4. Discover Nodes for Specific Tier:
bashpython3 test_appd_discovery.py \
    --controller "http://controller:8090" \
    --account "customer1" \
    --username "monitor@customer1" \
    --password "password" \
    --app-name "MyApplication" \
    --discover-tier "WebTier"
5. Discover All Tiers/Nodes for Specific App:
bashpython3 test_appd_discovery.py \
    --controller "http://controller:8090" \
    --account "customer1" \
    --username "monitor@customer1" \
    --password "password" \
    --discover-app "MyApplication" \
    --output myapp_config.json
6. Discover All Applications:
bashpython3 test_appd_discovery.py \
    --controller "http://controller:8090" \
    --account "customer1" \
    --username "monitor@customer1" \
    --password "password" \
    --discover-all \
    --output full_config.json
```

## Example Output (Test Single Config with Metrics):
```
================================================================================
TESTING SINGLE CONFIGURATION
================================================================================
Application: MyApplication
Tier: WebTier
Node: WebNode1
================================================================================

→ Verifying application exists...
  ✓ Application 'MyApplication' found

→ Verifying tier exists...
  ✓ Tier 'WebTier' found

→ Verifying node exists...
  ✓ Node 'WebNode1' found

================================================================================
TESTING METRICS COLLECTION
================================================================================

→ Testing Server Metrics...
  ✓ Server Metrics: 13 metrics, 65 data points
    - cpu_busy: 5 data points
      Latest value: 45.2
    - memory_used_pct: 5 data points
      Latest value: 72.8
    - network_incoming_kb: 5 data points
      Latest value: 1024.5

→ Testing JVM Metrics...
  ✓ JVM Metrics: 13 metrics, 65 data points
    - heap_used_pct: 5 data points
      Latest value: 68.5
    - gc_time_spent_per_min: 5 data points
      Latest value: 450.2
    - process_cpu_usage_pct: 5 data points
      Latest value: 35.7

→ Testing Application Metrics...
  ✓ Application Metrics: 11 metrics, 55 data points
    - calls_per_min: 5 data points
      Latest value: 1250.0
    - avg_response_time_ms: 5 data points
      Latest value: 125.5
    - errors_per_min: 5 data points
      Latest value: 2.0

================================================================================
METRICS COLLECTION SUMMARY
================================================================================
Total Data Points Collected: 185
  - Server Metrics: 65
  - JVM Metrics: 65
  - Application Metrics: 55

✓ Configuration saved to: test_config.json

================================================================================
✓ TEST COMPLETED SUCCESSFULLY
================================================================================
Generated Config File (test_config.json):
json{
  "description": "Test Configuration",
  "applications": [
    {
      "app_name": "MyApplication",
      "tiers": [
        {
          "tier_name": "WebTier",
          "nodes": [
            "WebNode1"
          ]
        }
      ]
    }
  ]
}
Now you can easily test with a single app/tier/node combination and verify that metrics are being collected correctly before running the full monitoring!Claude is AI and can make mistakes. Please double-check responses.




New Usage Commands
1. Discover Available Metrics (Most Important for Troubleshooting):
bashpython3 test_appd_discovery.py \
    --controller "http://controller:8090" \
    --account "customer1" \
    --username "monitor@customer1" \
    --password "password" \
    --app-name "MyApplication" \
    --tier-name "WebTier" \
    --node-name "WebNode1" \
    --discover-metrics
2. Test with Longer Duration (Try 60 minutes):
bashpython3 test_appd_discovery.py \
    --controller "http://controller:8090" \
    --account "customer1" \
    --username "monitor@customer1" \
    --password "password" \
    --app-name "MyApplication" \
    --tier-name "WebTier" \
    --node-name "WebNode1" \
    --test-metrics \
    --duration 60
3. Quick Diagnostic Command:
bash# This will show you exactly what's wrong
python3 test_appd_discovery.py \
    --controller "http://controller:8090" \
    --account "customer1" \
    --username "monitor@customer1" \
    --password "password" \
    --app-name "MyApplication" \
    --tier-name "WebTier" \
    --node-name "WebNode1" \
    --test-metrics \
    --duration 15
Common Issues and Solutions:
Issue 1: Metric Paths Don't Match
Solution: Run the discover-metrics command to see actual available paths, then update the metric paths in appdynamics_fetcher.py
Issue 2: No Recent Data
Solution: Increase --duration to 60 or more minutes
Issue 3: Node Not Reporting
Solution: Check if the node is showing as "Active" in AppDynamics UI
Issue 4: Wrong Tier/Node Names
Solution: Use the discover commands to get exact names (case-sensitive)
Please run this command and share the output:
bashpython3 test_appd_discovery.py \
    --controller "YOUR_CONTROLLER" \
    --account "YOUR_ACCOUNT" \
    --username "YOUR_USERNAME" \
    --password "YOUR_PASSWORD" \
    --app-name "MyApplication" \
    --tier-name "WebTier" \
    --node-name "WebNode1" \
    --test-metrics \
    --duration 60
This will help us identify:

Whether any metrics are returning data
Which specific metrics are failing
What the actual available metric paths are







Usage Examples
1. Simple - Generate config for single app:
bashpython3 generate_appd_config.py \
    --controller "http://controller:8090" \
    --account "customer1" \
    --username "monitor@customer1" \
    --password "password" \
    --app-names "MyApplication" \
    --output appd_config.json
2. Multiple apps:
bashpython3 generate_appd_config.py \
    --controller "http://controller:8090" \
    --account "customer1" \
    --username "monitor@customer1" \
    --password "password" \
    --app-names "App1,App2,App3" \
    --output appd_config.json
3. With verification:
bashpython3 generate_appd_config.py \
    --controller "http://controller:8090" \
    --account "customer1" \
    --username "monitor@customer1" \
    --password "password" \
    --app-names "MyApplication" \
    --output appd_config.json \
    --verify
4. Exclude specific tiers or nodes:
bashpython3 generate_appd_config.py \
    --controller "http://controller:8090" \
    --account "customer1" \
    --username "monitor@customer1" \
    --password "password" \
    --app-names "App1,App2" \
    --exclude-tiers "TestTier,DevTier" \
    --exclude-nodes "TestNode1,DevNode1" \
    --output appd_config.json
5. Complete workflow:
bash# Step 1: Generate config
python3 generate_appd_config.py \
    --controller "http://controller:8090" \
    --account "customer1" \
    --username "monitor@customer1" \
    --password "password" \
    --app-names "Production-App1,Production-App2" \
    --output production_config.json \
    --verify

# Step 2: Run monitoring
python3 monitoring_main.py \
    --run-id "PROD_TEST_001" \
    --test-name "Production Load Test" \
    --duration 60 \
    --appd-controller "http://controller:8090" \
    --appd-account "customer1" \
    --appd-user "monitor@customer1" \
    --appd-pass "password" \
    --appd-config "production_config.json" \
    --db-user "monitoring" \
    --db-pass "password" \
    --db-dsn "dbhost:1521/ORCL"
```

## Example Output
```
================================================================================
AppDynamics Configuration Generator
================================================================================
Applications to process: 2
  - Application1
  - Application2

→ Connecting to AppDynamics...
✓ AppDynamics connection successful

→ Fetching available applications...
✓ Found 5 total applications in AppDynamics

================================================================================
GENERATING CONFIGURATION
================================================================================

[1/2] Processing: Application1
--------------------------------------------------------------------------------
  Found 3 tiers
  [1/3] WebTier
      - WebNode1
      - WebNode2
      - WebNode3
  [2/3] AppTier
      - AppNode1
      - AppNode2
  [3/3] DatabaseTier
      - DBNode1

[2/2] Processing: Application2
--------------------------------------------------------------------------------
  Found 2 tiers
  [1/2] ServiceTier
      - ServiceNode1
      - ServiceNode2
  [2/2] APITier
      - APINode1

================================================================================
CONFIGURATION SUMMARY
================================================================================
Applications: 2
Total Tiers: 5
Total Nodes: 9

→ Saving configuration...
✓ Configuration saved to: appd_config.json

================================================================================
✓ CONFIGURATION GENERATED SUCCESSFULLY
================================================================================

To use this configuration with monitoring:

python3 monitoring_main.py \
    --run-id "TEST_001" \
    --duration 60 \
    --appd-controller "http://controller:8090" \
    --appd-account "customer1" \
    --appd-user "monitor@customer1" \
    --appd-pass "YOUR_PASSWORD" \
    --appd-config "appd_config.json" \
    --db-user "oracle_user" \
    --db-pass "oracle_pass" \
    --db-dsn "host:1521/ORCL"
Generated Config File (appd_config.json):
json{
  "description": "Auto-generated configuration for 2 application(s)",
  "generated_at": "2025-01-17 10:30:45.123456",
  "applications": [
    {
      "app_name": "Application1",
      "tiers": [
        {
          "tier_name": "WebTier",
          "nodes": [
            "WebNode1",
            "WebNode2",
            "WebNode3"
          ]
        },
        {
          "tier_name": "AppTier",
          "nodes": [
            "AppNode1",
            "AppNode2"
          ]
        },
        {
          "tier_name": "DatabaseTier",
          "nodes": [
            "DBNode1"
          ]
        }
      ]
    },
    {
      "app_name": "Application2",
      "tiers": [
        {
          "tier_name": "ServiceTier",
          "nodes": [
            "ServiceNode1",
            "ServiceNode2"
          ]
        },
        {
          "tier_name": "APITier",
          "nodes": [
            "APINode1"
          ]
        }
      ]
    }
  ]
}
