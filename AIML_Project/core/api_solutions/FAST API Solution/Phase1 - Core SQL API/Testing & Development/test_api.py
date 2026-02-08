"""
Test Script for Oracle SQL API
Tests all endpoints and functionality
"""
import requests
import json
from datetime import datetime
import time

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "local-dev-api-key"  # Update with your local API key

# Test data
TEST_USERNAME = "test_user"
TEST_SQL_SELECT = "SELECT SYSDATE, USER FROM DUAL"
TEST_SQL_CREATE_TABLE = """
CREATE TABLE test_table (
    id NUMBER PRIMARY KEY,
    name VARCHAR2(100),
    created_date DATE
)
"""
TEST_SQL_INSERT = """
INSERT INTO test_table (id, name, created_date)
VALUES (1, 'Test Record', SYSDATE)
"""
TEST_SQL_SELECT_TABLE = "SELECT * FROM test_table"
TEST_SQL_UPDATE = "UPDATE test_table SET name = 'Updated Record' WHERE id = 1"
TEST_SQL_DELETE = "DELETE FROM test_table WHERE id = 1"


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


def test_health_check():
    """Test health check endpoint"""
    print_section("1. Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        
        if response.status_code == 200:
            data = response.json()
            print_result("Health Check", True)
            print(f"   Status: {data['status']}")
            print(f"   Environment: {data['environment']}")
            print(f"   Database: {data['database_status']['status']}")
            print(f"   Pool: Open={data['pool_status'].get('open_connections', 0)}, Busy={data['pool_status'].get('busy_connections', 0)}")
            return True
        else:
            print_result("Health Check", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_result("Health Check", False, str(e))
        return False


def test_root_endpoint():
    """Test root endpoint"""
    print_section("2. Root Endpoint")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        
        if response.status_code == 200:
            data = response.json()
            print_result("Root Endpoint", True)
            print(f"   Service: {data['service']}")
            print(f"   Version: {data['version']}")
            return True
        else:
            print_result("Root Endpoint", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_result("Root Endpoint", False, str(e))
        return False


def test_authentication():
    """Test token generation"""
    print_section("3. Authentication")
    
    try:
        payload = {
            "username": TEST_USERNAME,
            "api_key": API_KEY
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/auth/token", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print_result("Token Generation", True)
            print(f"   Token Type: {data['token_type']}")
            print(f"   Expires In: {data['expires_in']} seconds")
            return data['access_token']
        else:
            print_result("Token Generation", False, f"Status: {response.status_code}")
            return None
    except Exception as e:
        print_result("Token Generation", False, str(e))
        return None


def test_sql_select():
    """Test SELECT query execution"""
    print_section("4. SQL SELECT Query")
    
    try:
        headers = {"X-API-Key": API_KEY}
        payload = {
            "sql_content": TEST_SQL_SELECT,
            "username": TEST_USERNAME,
            "description": "Test SELECT query"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/sql/execute",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print_result("SELECT Query", True)
            print(f"   Request ID: {data['request_id']}")
            print(f"   Operation: {data['operation_type']}")
            print(f"   Rows: {data['rows_affected']}")
            print(f"   Execution Time: {data['execution_time_seconds']}s")
            print(f"   Data: {data['data']}")
            return True
        else:
            print_result("SELECT Query", False, f"Status: {response.status_code}, {response.text}")
            return False
    except Exception as e:
        print_result("SELECT Query", False, str(e))
        return False


def test_sql_validation():
    """Test SQL validation with invalid SQL"""
    print_section("5. SQL Validation")
    
    try:
        headers = {"X-API-Key": API_KEY}
        payload = {
            "sql_content": "DROP TABLE important_data",
            "username": TEST_USERNAME,
            "description": "Test validation"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/sql/execute",
            headers=headers,
            json=payload
        )
        
        # Should return 400 Bad Request
        if response.status_code == 400:
            print_result("SQL Validation (DROP blocked)", True)
            print(f"   Error: {response.json()['detail']}")
            return True
        else:
            print_result("SQL Validation", False, "DROP TABLE should be blocked")
            return False
    except Exception as e:
        print_result("SQL Validation", False, str(e))
        return False


def test_rate_limit_status():
    """Test rate limit status endpoint"""
    print_section("6. Rate Limit Status")
    
    try:
        headers = {"X-API-Key": API_KEY}
        
        response = requests.get(
            f"{BASE_URL}/api/v1/rate-limit/status",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print_result("Rate Limit Status", True)
            print(f"   Limit: {data['limit']} requests")
            print(f"   Period: {data['period_seconds']} seconds")
            print(f"   Remaining: {data['remaining']}")
            return True
        else:
            print_result("Rate Limit Status", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_result("Rate Limit Status", False, str(e))
        return False


def test_pool_status():
    """Test connection pool status"""
    print_section("7. Connection Pool Status")
    
    try:
        headers = {"X-API-Key": API_KEY}
        
        response = requests.get(
            f"{BASE_URL}/api/v1/pool/status",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print_result("Pool Status", True)
            print(f"   Status: {data.get('status', 'unknown')}")
            if data.get('status') == 'active':
                print(f"   Open: {data.get('open_connections', 0)}")
                print(f"   Busy: {data.get('busy_connections', 0)}")
                print(f"   Max: {data.get('max_connections', 0)}")
            return True
        else:
            print_result("Pool Status", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_result("Pool Status", False, str(e))
        return False


def test_unauthorized_access():
    """Test unauthorized access"""
    print_section("8. Unauthorized Access")
    
    try:
        # No API key
        payload = {
            "sql_content": TEST_SQL_SELECT,
            "username": TEST_USERNAME
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/sql/execute",
            json=payload
        )
        
        # Should return 401 Unauthorized
        if response.status_code == 401:
            print_result("Unauthorized Access Blocked", True)
            return True
        else:
            print_result("Unauthorized Access", False, "Should require API key")
            return False
    except Exception as e:
        print_result("Unauthorized Access", False, str(e))
        return False


def test_sql_file_upload():
    """Test SQL file upload"""
    print_section("9. SQL File Upload")
    
    try:
        # Create temporary SQL file
        sql_content = TEST_SQL_SELECT
        
        headers = {"X-API-Key": API_KEY}
        files = {
            'file': ('test.sql', sql_content, 'text/plain')
        }
        data = {
            'username': TEST_USERNAME,
            'description': 'Test file upload'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/sql/execute-file",
            headers=headers,
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print_result("SQL File Upload", True)
            print(f"   Request ID: {result['request_id']}")
            print(f"   Rows: {result['rows_affected']}")
            return True
        else:
            print_result("SQL File Upload", False, f"Status: {response.status_code}, {response.text}")
            return False
    except Exception as e:
        print_result("SQL File Upload", False, str(e))
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print(" Oracle SQL API - Test Suite")
    print(" " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health_check()))
    time.sleep(0.5)
    
    results.append(("Root Endpoint", test_root_endpoint()))
    time.sleep(0.5)
    
    token = test_authentication()
    results.append(("Authentication", token is not None))
    time.sleep(0.5)
    
    results.append(("SQL SELECT", test_sql_select()))
    time.sleep(0.5)
    
    results.append(("SQL Validation", test_sql_validation()))
    time.sleep(0.5)
    
    results.append(("Rate Limit Status", test_rate_limit_status()))
    time.sleep(0.5)
    
    results.append(("Pool Status", test_pool_status()))
    time.sleep(0.5)
    
    results.append(("Unauthorized Access", test_unauthorized_access()))
    time.sleep(0.5)
    
    results.append(("SQL File Upload", test_sql_file_upload()))
    
    # Summary
    print_section("Test Summary")
    total = len(results)
    passed = sum(1 for _, success in results if success)
    failed = total - passed
    
    print(f"Total Tests: {total}")
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