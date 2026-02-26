"""
Integration Tests for AppDynamics Monitoring
Tests discovery, health check, and monitoring workflows
"""
import pytest
import requests
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/v1/monitoring/appd"
TEST_LOB = "Retail"
TEST_RUN_ID = f"TEST_RUN_{int(time.time())}"


class TestAppDDiscovery:
    """Test discovery functionality"""
    
    def test_run_discovery(self):
        """Test running discovery for LOB"""
        response = requests.post(
            f"{BASE_URL}/discovery/run",
            json={"lob_names": [TEST_LOB]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "initiated"
        assert TEST_LOB in data["lob_names"]
        print(f"✓ Discovery initiated: {data['task_id']}")
    
    def test_discovery_with_multiple_lobs(self):
        """Test discovery with multiple LOBs"""
        response = requests.post(
            f"{BASE_URL}/discovery/run",
            json={"lob_names": ["Retail", "Banking"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["lob_names"]) == 2
        print(f"✓ Multiple LOB discovery: {data['task_id']}")
    
    def test_discovery_empty_lobs(self):
        """Test discovery with empty LOB list"""
        response = requests.post(
            f"{BASE_URL}/discovery/run",
            json={"lob_names": []}
        )
        
        # Should accept but warn
        assert response.status_code in [200, 400]


class TestAppDHealthCheck:
    """Test health check functionality"""
    
    def test_health_check_valid_lob(self):
        """Test health check for valid LOB"""
        response = requests.get(f"{BASE_URL}/health/{TEST_LOB}")
        
        assert response.status_code == 200
        data = response.json()
        assert "lob_name" in data
        assert "total_active_nodes" in data
        assert "applications" in data
        print(f"✓ Health check: {data['total_active_nodes']} active nodes")
    
    def test_health_check_invalid_lob(self):
        """Test health check for invalid LOB"""
        response = requests.get(f"{BASE_URL}/health/InvalidLOB")
        
        # Should handle gracefully
        assert response.status_code in [200, 404, 500]


class TestAppDMonitoring:
    """Test monitoring functionality"""
    
    def test_start_monitoring(self):
        """Test starting a monitoring session"""
        response = requests.post(
            f"{BASE_URL}/monitoring/start",
            json={
                "run_id": TEST_RUN_ID,
                "lob_name": TEST_LOB,
                "track": "Q1_2026",
                "test_name": "Integration Test",
                "applications": ["RetailWeb"],
                "interval_seconds": 300
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["run_id"] == TEST_RUN_ID
        print(f"✓ Monitoring started: {TEST_RUN_ID}")
    
    def test_list_sessions(self):
        """Test listing monitoring sessions"""
        response = requests.get(f"{BASE_URL}/monitoring/sessions")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_sessions" in data
        assert "sessions" in data
        print(f"✓ Active sessions: {data['total_sessions']}")
    
    def test_get_session_details(self):
        """Test getting session details"""
        response = requests.get(f"{BASE_URL}/monitoring/sessions/{TEST_RUN_ID}")
        
        if response.status_code == 200:
            data = response.json()
            assert data["run_id"] == TEST_RUN_ID
            assert "status" in data
            print(f"✓ Session details: {data['status']}")
    
    def test_thread_pool_status(self):
        """Test thread pool status"""
        response = requests.get(f"{BASE_URL}/monitoring/thread-pool/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "max_concurrent_monitors" in data
        assert "active_monitors" in data
        assert "utilization_percent" in data
        print(f"✓ Thread pool: {data['active_monitors']}/{data['max_concurrent_monitors']}")
    
    def test_stop_monitoring(self):
        """Test stopping a monitoring session"""
        # Wait a bit
        time.sleep(2)
        
        response = requests.post(f"{BASE_URL}/monitoring/stop/{TEST_RUN_ID}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        print(f"✓ Monitoring stopped: {TEST_RUN_ID}")


class TestAppDErrorHandling:
    """Test error handling"""
    
    def test_duplicate_run_id(self):
        """Test starting monitoring with duplicate run ID"""
        dup_run_id = f"DUP_TEST_{int(time.time())}"
        
        # Start first session
        response1 = requests.post(
            f"{BASE_URL}/monitoring/start",
            json={
                "run_id": dup_run_id,
                "lob_name": TEST_LOB,
                "track": "Q1_2026",
                "applications": ["RetailWeb"],
                "interval_seconds": 300
            }
        )
        
        # Try duplicate
        response2 = requests.post(
            f"{BASE_URL}/monitoring/start",
            json={
                "run_id": dup_run_id,
                "lob_name": TEST_LOB,
                "track": "Q1_2026",
                "applications": ["RetailWeb"],
                "interval_seconds": 300
            }
        )
        
        assert response2.status_code == 400
        print("✓ Duplicate run ID rejected")
        
        # Cleanup
        requests.post(f"{BASE_URL}/monitoring/stop/{dup_run_id}")
    
    def test_stop_nonexistent_session(self):
        """Test stopping non-existent session"""
        response = requests.post(f"{BASE_URL}/monitoring/stop/FAKE_RUN_ID")
        
        assert response.status_code == 404
        print("✓ Non-existent session handled")


class TestAppDWorkflow:
    """Test complete workflow"""
    
    def test_complete_workflow(self):
        """Test complete discovery -> health check -> monitor -> stop workflow"""
        workflow_run_id = f"WORKFLOW_{int(time.time())}"
        
        # Step 1: Discovery
        print("\n--- Step 1: Discovery ---")
        response = requests.post(
            f"{BASE_URL}/discovery/run",
            json={"lob_names": [TEST_LOB]}
        )
        assert response.status_code == 200
        print("✓ Discovery initiated")
        
        # Wait for discovery
        time.sleep(5)
        
        # Step 2: Health Check
        print("\n--- Step 2: Health Check ---")
        response = requests.get(f"{BASE_URL}/health/{TEST_LOB}")
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Found {data['total_active_nodes']} active nodes")
        
        # Step 3: Start Monitoring
        print("\n--- Step 3: Start Monitoring ---")
        response = requests.post(
            f"{BASE_URL}/monitoring/start",
            json={
                "run_id": workflow_run_id,
                "lob_name": TEST_LOB,
                "track": "Q1_2026",
                "applications": ["RetailWeb"],
                "interval_seconds": 300
            }
        )
        assert response.status_code == 200
        print(f"✓ Monitoring started: {workflow_run_id}")
        
        # Step 4: Check Status
        print("\n--- Step 4: Check Status ---")
        response = requests.get(f"{BASE_URL}/monitoring/thread-pool/status")
        data = response.json()
        print(f"✓ Active monitors: {data['active_monitors']}")
        
        # Step 5: Stop Monitoring
        print("\n--- Step 5: Stop Monitoring ---")
        time.sleep(2)
        response = requests.post(f"{BASE_URL}/monitoring/stop/{workflow_run_id}")
        assert response.status_code == 200
        print(f"✓ Monitoring stopped")
        
        print("\n✓ Complete workflow successful!")


def run_all_tests():
    """Run all tests"""
    print("="  * 60)
    print("AppDynamics Integration Tests")
    print("=" * 60)
    
    # Discovery tests
    print("\n" + "=" * 60)
    print("Testing Discovery")
    print("=" * 60)
    discovery = TestAppDDiscovery()
    discovery.test_run_discovery()
    discovery.test_discovery_with_multiple_lobs()
    
    # Health check tests
    print("\n" + "=" * 60)
    print("Testing Health Check")
    print("=" * 60)
    health = TestAppDHealthCheck()
    health.test_health_check_valid_lob()
    
    # Monitoring tests
    print("\n" + "=" * 60)
    print("Testing Monitoring")
    print("=" * 60)
    monitoring = TestAppDMonitoring()
    monitoring.test_thread_pool_status()
    monitoring.test_start_monitoring()
    monitoring.test_list_sessions()
    monitoring.test_get_session_details()
    time.sleep(2)
    monitoring.test_stop_monitoring()
    
    # Error handling tests
    print("\n" + "=" * 60)
    print("Testing Error Handling")
    print("=" * 60)
    errors = TestAppDErrorHandling()
    errors.test_duplicate_run_id()
    errors.test_stop_nonexistent_session()
    
    # Workflow test
    print("\n" + "=" * 60)
    print("Testing Complete Workflow")
    print("=" * 60)
    workflow = TestAppDWorkflow()
    workflow.test_complete_workflow()
    
    print("\n" + "=" * 60)
    print("✓ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()


"""
Usage:

1. With pytest:
   pytest test_appd_integration.py -v

2. Directly:
   python test_appd_integration.py

3. Specific test class:
   pytest test_appd_integration.py::TestAppDDiscovery -v

4. Specific test:
   pytest test_appd_integration.py::TestAppDMonitoring::test_start_monitoring -v
"""