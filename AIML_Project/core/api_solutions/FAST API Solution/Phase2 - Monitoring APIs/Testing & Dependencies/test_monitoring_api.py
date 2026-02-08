"""
Monitoring API Test Suite
Tests all monitoring endpoints
"""
import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "local-dev-api-key"

# Test Configurations
APPDYNAMICS_CONFIG = {
    "controller_url": "https://appdynamics.example.com",
    "account_name": "customer1",
    "username": "api_user",
    "password": "api_password",
    "application_name": "MyApp"
}

KIBANA_CONFIG = {
    "kibana_url": "https://kibana.example.com",
    "elasticsearch_url": "https://elasticsearch.example.com",
    "username": "elastic",
    "password": "changeme",
    "index_pattern": "logstash-*"
}

SPLUNK_CONFIG = {
    "splunk_url": "https://splunk.example.com:8089",
    "username": "admin",
    "password": "changeme",
    "search_index": "main"
}

MONGODB_CONFIG = {
    "connection_string": "mongodb://localhost:27017",
    "database_name": "myapp",
    "collections": ["users", "orders", "products"]
}


def print_section(title):
    """Print section header"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def print_result(test_name, success, details=None):
    """Print test result"""
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"   {details}")


def test_appdynamics_monitoring():
    """Test AppDynamics monitoring lifecycle"""
    print_section("AppDynamics Monitoring")
    
    headers = {"X-API-Key": API_KEY}
    results = []
    
    # Test 1: Start monitoring
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/monitoring/appdynamics/start",
            headers=headers,
            json=APPDYNAMICS_CONFIG
        )
        success = response.status_code in [200, 201]
        print_result("Start AppDynamics Monitoring", success, 
                    f"Status: {response.status_code}")
        results.append(success)
    except Exception as e:
        print_result("Start AppDynamics Monitoring", False, str(e))
        results.append(False)
    
    # Test 2: Get status
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/monitoring/appdynamics/status",
            headers=headers
        )
        success = response.status_code == 200
        if success:
            data = response.json()
            print_result("Get AppDynamics Status", True, 
                        f"Active: {data.get('active', False)}")
        else:
            print_result("Get AppDynamics Status", False)
        results.append(success)
    except Exception as e:
        print_result("Get AppDynamics Status", False, str(e))
        results.append(False)
    
    # Test 3: Stop monitoring
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/monitoring/appdynamics/stop",
            headers=headers
        )
        success = response.status_code in [200, 201]
        print_result("Stop AppDynamics Monitoring", success)
        results.append(success)
    except Exception as e:
        print_result("Stop AppDynamics Monitoring", False, str(e))
        results.append(False)
    
    return all(results)


def test_kibana_monitoring():
    """Test Kibana monitoring lifecycle"""
    print_section("Kibana Monitoring")
    
    headers = {"X-API-Key": API_KEY}
    results = []
    
    # Test 1: Start monitoring
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/monitoring/kibana/start",
            headers=headers,
            json=KIBANA_CONFIG
        )
        success = response.status_code in [200, 201]
        print_result("Start Kibana Monitoring", success, 
                    f"Status: {response.status_code}")
        results.append(success)
    except Exception as e:
        print_result("Start Kibana Monitoring", False, str(e))
        results.append(False)
    
    # Test 2: Get status
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/monitoring/kibana/status",
            headers=headers
        )
        success = response.status_code == 200
        print_result("Get Kibana Status", success)
        results.append(success)
    except Exception as e:
        print_result("Get Kibana Status", False, str(e))
        results.append(False)
    
    # Test 3: Stop monitoring
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/monitoring/kibana/stop",
            headers=headers
        )
        success = response.status_code in [200, 201]
        print_result("Stop Kibana Monitoring", success)
        results.append(success)
    except Exception as e:
        print_result("Stop Kibana Monitoring", False, str(e))
        results.append(False)
    
    return all(results)


def test_splunk_monitoring():
    """Test Splunk monitoring lifecycle"""
    print_section("Splunk Monitoring")
    
    headers = {"X-API-Key": API_KEY}
    results = []
    
    # Start monitoring
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/monitoring/splunk/start",
            headers=headers,
            json=SPLUNK_CONFIG
        )
        success = response.status_code in [200, 201]
        print_result("Start Splunk Monitoring", success)
        results.append(success)
    except Exception as e:
        print_result("Start Splunk Monitoring", False, str(e))
        results.append(False)
    
    # Get status
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/monitoring/splunk/status",
            headers=headers
        )
        success = response.status_code == 200
        print_result("Get Splunk Status", success)
        results.append(success)
    except Exception as e:
        print_result("Get Splunk Status", False, str(e))
        results.append(False)
    
    # Stop monitoring
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/monitoring/splunk/stop",
            headers=headers
        )
        success = response.status_code in [200, 201]
        print_result("Stop Splunk Monitoring", success)
        results.append(success)
    except Exception as e:
        print_result("Stop Splunk Monitoring", False, str(e))
        results.append(False)
    
    return all(results)


def test_mongodb_monitoring():
    """Test MongoDB monitoring lifecycle"""
    print_section("MongoDB Monitoring")
    
    headers = {"X-API-Key": API_KEY}
    results = []
    
    # Start monitoring
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/monitoring/mongodb/start",
            headers=headers,
            json=MONGODB_CONFIG
        )
        success = response.status_code in [200, 201]
        print_result("Start MongoDB Monitoring", success)
        results.append(success)
    except Exception as e:
        print_result("Start MongoDB Monitoring", False, str(e))
        results.append(False)
    
    # Get status
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/monitoring/mongodb/status",
            headers=headers
        )
        success = response.status_code == 200
        print_result("Get MongoDB Status", success)
        results.append(success)
    except Exception as e:
        print_result("Get MongoDB Status", False, str(e))
        results.append(False)
    
    # Analyze collections
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/monitoring/mongodb/analyze",
            headers=headers
        )
        success = response.status_code in [200, 400]  # 400 if not started
        print_result("Analyze MongoDB Collections", success)
        results.append(success)
    except Exception as e:
        print_result("Analyze MongoDB Collections", False, str(e))
        results.append(False)
    
    # Stop monitoring
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/monitoring/mongodb/stop",
            headers=headers
        )
        success = response.status_code in [200, 201]
        print_result("Stop MongoDB Monitoring", success)
        results.append(success)
    except Exception as e:
        print_result("Stop MongoDB Monitoring", False, str(e))
        results.append(False)
    
    return all(results)


def test_unified_endpoints():
    """Test unified monitoring endpoints"""
    print_section("Unified Monitoring Endpoints")
    
    headers = {"X-API-Key": API_KEY}
    results = []
    
    # Get all status
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/monitoring/status",
            headers=headers
        )
        success = response.status_code == 200
        if success:
            data = response.json()
            print_result("Get All Monitoring Status", True, 
                        f"Monitors: {len(data.get('monitors', {}))}")
        else:
            print_result("Get All Monitoring Status", False)
        results.append(success)
    except Exception as e:
        print_result("Get All Monitoring Status", False, str(e))
        results.append(False)
    
    # Get dashboard
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/monitoring/dashboard",
            headers=headers
        )
        success = response.status_code == 200
        if success:
            data = response.json()
            summary = data.get('summary', {})
            print_result("Get Monitoring Dashboard", True,
                        f"Active: {summary.get('active_monitors', 0)}/{summary.get('total_monitors', 0)}")
        else:
            print_result("Get Monitoring Dashboard", False)
        results.append(success)
    except Exception as e:
        print_result("Get Monitoring Dashboard", False, str(e))
        results.append(False)
    
    # Stop all
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/monitoring/stop-all",
            headers=headers
        )
        success = response.status_code in [200, 201]
        if success:
            data = response.json()
            print_result("Stop All Monitoring", True,
                        f"Stopped: {data.get('successful', 0)}/{data.get('total', 0)}")
        else:
            print_result("Stop All Monitoring", False)
        results.append(success)
    except Exception as e:
        print_result("Stop All Monitoring", False, str(e))
        results.append(False)
    
    return all(results)


def run_all_tests():
    """Run all monitoring tests"""
    print("\n" + "=" * 60)
    print(" Monitoring API Test Suite")
    print(" " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    results = []
    
    # Run individual monitoring tests
    results.append(("AppDynamics", test_appdynamics_monitoring()))
    results.append(("Kibana", test_kibana_monitoring()))
    results.append(("Splunk", test_splunk_monitoring()))
    results.append(("MongoDB", test_mongodb_monitoring()))
    results.append(("Unified Endpoints", test_unified_endpoints()))
    
    # Summary
    print_section("Test Summary")
    total = len(results)
    passed = sum(1 for _, success in results if success)
    failed = total - passed
    
    print(f"Total Test Suites: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    print("\nDetailed Results:")
    for test_name, success in results:
        status = "✓" if success else "✗"
        print(f"  {status} {test_name}")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)