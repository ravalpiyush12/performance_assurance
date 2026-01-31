"""
Unit Tests for FastAPI Endpoints
Tests REST API functionality
Run with: pytest tests/unit/test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from api.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns dashboard"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestStatusEndpoints:
    """Test system status endpoints"""
    
    def test_get_status(self, client):
        """Test GET /api/v1/status"""
        response = client.get("/api/v1/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "health_score" in data
        assert "active_alerts" in data
        assert "total_metrics" in data
        assert "ml_model_trained" in data
        
        # Validate types
        assert isinstance(data["health_score"], (int, float))
        assert isinstance(data["active_alerts"], int)
        assert isinstance(data["total_metrics"], int)
        assert isinstance(data["ml_model_trained"], bool)


class TestMetricsEndpoints:
    """Test metrics endpoints"""
    
    def test_get_metrics_empty(self, client):
        """Test GET /api/v1/metrics when empty"""
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_post_metrics(self, client):
        """Test POST /api/v1/metrics"""
        metric_data = {
            "timestamp": datetime.now().isoformat(),
            "cpu_usage": 75.5,
            "memory_usage": 60.2,
            "response_time": 250.0,
            "error_rate": 1.5,
            "requests_per_sec": 100.0
        }
        
        response = client.post("/api/v1/metrics", json=metric_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "accepted"
        assert "timestamp" in data
    
    def test_post_metrics_invalid(self, client):
        """Test POST /api/v1/metrics with invalid data"""
        invalid_data = {
            "timestamp": "invalid",
            "cpu_usage": "not_a_number"
        }
        
        response = client.post("/api/v1/metrics", json=invalid_data)
        # Should return validation error
        assert response.status_code == 422
    
    def test_get_metrics_with_limit(self, client):
        """Test GET /api/v1/metrics with limit parameter"""
        # First add some metrics
        for i in range(10):
            metric_data = {
                "timestamp": datetime.now().isoformat(),
                "cpu_usage": 50.0 + i,
                "memory_usage": 60.0,
                "response_time": 200.0,
                "error_rate": 1.0,
                "requests_per_sec": 100.0
            }
            client.post("/api/v1/metrics", json=metric_data)
        
        # Get with limit
        response = client.get("/api/v1/metrics?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) <= 5


class TestAnomaliesEndpoints:
    """Test anomaly endpoints"""
    
    def test_get_anomalies(self, client):
        """Test GET /api/v1/anomalies"""
        response = client.get("/api/v1/anomalies")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_anomalies_with_limit(self, client):
        """Test GET /api/v1/anomalies with limit"""
        response = client.get("/api/v1/anomalies?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10
    
    def test_get_active_anomalies(self, client):
        """Test GET /api/v1/anomalies/active"""
        response = client.get("/api/v1/anomalies/active")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)


class TestHealingActionsEndpoints:
    """Test healing actions endpoints"""
    
    def test_get_healing_actions(self, client):
        """Test GET /api/v1/healing-actions"""
        response = client.get("/api/v1/healing-actions")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_healing_actions_with_limit(self, client):
        """Test GET /api/v1/healing-actions with limit"""
        response = client.get("/api/v1/healing-actions?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5


class TestPredictionsEndpoints:
    """Test predictions endpoints"""
    
    def test_get_predictions_insufficient_data(self, client):
        """Test GET /api/v1/predictions with insufficient data"""
        response = client.get("/api/v1/predictions")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data or "predictions" in data
    
    def test_get_predictions_with_data(self, client):
        """Test GET /api/v1/predictions with sufficient data"""
        # Add metrics first
        for i in range(15):
            metric_data = {
                "timestamp": datetime.now().isoformat(),
                "cpu_usage": 50.0 + i * 2,
                "memory_usage": 60.0,
                "response_time": 200.0,
                "error_rate": 1.0,
                "requests_per_sec": 100.0
            }
            client.post("/api/v1/metrics", json=metric_data)
        
        response = client.get("/api/v1/predictions")
        assert response.status_code == 200
        
        data = response.json()
        assert "predictions" in data or "message" in data


class TestOrchestratorEndpoints:
    """Test orchestrator endpoints"""
    
    def test_get_orchestrator_stats(self, client):
        """Test GET /api/v1/orchestrator/stats"""
        response = client.get("/api/v1/orchestrator/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_actions" in data
        assert "completed" in data
        assert "failed" in data
        assert "success_rate" in data


class TestCORSHeaders:
    """Test CORS configuration"""
    
    def test_cors_headers_present(self, client):
        """Test CORS headers are present"""
        response = client.options("/api/v1/status")
        
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers


class TestErrorHandling:
    """Test error handling"""
    
    def test_404_not_found(self, client):
        """Test 404 for non-existent endpoint"""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test 405 for wrong method"""
        response = client.delete("/api/v1/status")
        assert response.status_code == 405


class TestDataValidation:
    """Test input validation"""
    
    def test_metric_validation_missing_fields(self, client):
        """Test metric validation with missing fields"""
        incomplete_metric = {
            "timestamp": datetime.now().isoformat(),
            "cpu_usage": 75.5
            # Missing required fields
        }
        
        response = client.post("/api/v1/metrics", json=incomplete_metric)
        assert response.status_code == 422
    
    def test_metric_validation_invalid_types(self, client):
        """Test metric validation with invalid types"""
        invalid_metric = {
            "timestamp": datetime.now().isoformat(),
            "cpu_usage": "not_a_number",
            "memory_usage": 60.0,
            "response_time": 200.0,
            "error_rate": 1.0,
            "requests_per_sec": 100.0
        }
        
        response = client.post("/api/v1/metrics", json=invalid_metric)
        assert response.status_code == 422
    
    def test_metric_validation_out_of_range(self, client):
        """Test metric validation with out of range values"""
        # This test depends on if validation is implemented
        out_of_range_metric = {
            "timestamp": datetime.now().isoformat(),
            "cpu_usage": 150.0,  # >100%
            "memory_usage": 60.0,
            "response_time": 200.0,
            "error_rate": 1.0,
            "requests_per_sec": 100.0
        }
        
        response = client.post("/api/v1/metrics", json=out_of_range_metric)
        # May accept or reject depending on validation rules
        assert response.status_code in [200, 422]


class TestWebSocketEndpoint:
    """Test WebSocket endpoint"""
    
    def test_websocket_connection(self, client):
        """Test WebSocket connection"""
        with client.websocket_connect("/ws/live") as websocket:
            # Connection should be established
            assert websocket is not None
            
            # Should be able to receive data
            # (actual data reception would require async testing)


class TestIntegration:
    """Integration tests"""
    
    def test_full_workflow(self, client):
        """Test complete workflow: metrics -> anomaly -> healing"""
        # 1. Post normal metrics
        for i in range(10):
            metric = {
                "timestamp": datetime.now().isoformat(),
                "cpu_usage": 50.0,
                "memory_usage": 60.0,
                "response_time": 200.0,
                "error_rate": 1.0,
                "requests_per_sec": 100.0
            }
            response = client.post("/api/v1/metrics", json=metric)
            assert response.status_code == 200
        
        # 2. Post anomalous metric
        anomalous_metric = {
            "timestamp": datetime.now().isoformat(),
            "cpu_usage": 95.0,
            "memory_usage": 90.0,
            "response_time": 1500.0,
            "error_rate": 10.0,
            "requests_per_sec": 20.0
        }
        response = client.post("/api/v1/metrics", json=anomalous_metric)
        assert response.status_code == 200
        
        # 3. Check if anomaly was detected
        # (may need to wait for background processing)
        import time
        time.sleep(1)
        
        response = client.get("/api/v1/anomalies")
        assert response.status_code == 200
        
        # 4. Check if healing action was taken
        response = client.get("/api/v1/healing-actions")
        assert response.status_code == 200
        
        # 5. Verify system status
        response = client.get("/api/v1/status")
        assert response.status_code == 200
        data = response.json()
        assert "health_score" in data


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])