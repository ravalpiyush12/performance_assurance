"""
Unit Tests for Anomaly Detector
Tests ML-based anomaly detection functionality
Run with: pytest tests/unit/test_anomaly_detector.py -v
"""

import pytest
import numpy as np
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from ml.anomaly_detector import AnomalyDetector, PerformancePredictor, TimeSeriesForecaster


class TestAnomalyDetector:
    """Test suite for AnomalyDetector"""
    
    @pytest.fixture
    def detector(self):
        """Create detector instance"""
        return AnomalyDetector(contamination=0.1, window_size=50)
    
    @pytest.fixture
    def normal_metrics(self):
        """Generate normal metrics"""
        return [
            {
                'cpu_usage': 50 + np.random.randn() * 5,
                'memory_usage': 60 + np.random.randn() * 5,
                'response_time': 200 + np.random.randn() * 20,
                'error_rate': 0.5 + np.random.randn() * 0.2,
                'requests_per_sec': 100 + np.random.randn() * 10,
                'disk_io': 1000 + np.random.randn() * 100,
                'network_throughput': 500 + np.random.randn() * 50
            }
            for _ in range(30)
        ]
    
    def test_initialization(self, detector):
        """Test detector initialization"""
        assert detector.contamination == 0.1
        assert detector.window_size == 50
        assert not detector.is_trained
        assert len(detector.metrics_window) == 0
    
    def test_add_metrics(self, detector, normal_metrics):
        """Test adding metrics"""
        for metric in normal_metrics:
            detector.add_metrics(metric)
        
        assert len(detector.metrics_window) == len(normal_metrics)
    
    def test_feature_extraction(self, detector):
        """Test feature extraction"""
        metric = {
            'cpu_usage': 75.0,
            'memory_usage': 60.0,
            'response_time': 250.0,
            'error_rate': 1.5,
            'requests_per_sec': 100.0,
            'disk_io': 1000.0,
            'network_throughput': 500.0
        }
        
        features = detector._extract_features(metric)
        
        assert len(features) == 7
        assert features[0] == 75.0  # cpu_usage
        assert features[1] == 60.0  # memory_usage
    
    def test_training(self, detector, normal_metrics):
        """Test model training"""
        # Add enough metrics
        for metric in normal_metrics:
            detector.add_metrics(metric)
        
        # Train model
        success = detector._train_model()
        
        assert success
        assert detector.is_trained
    
    def test_anomaly_detection_normal(self, detector, normal_metrics):
        """Test detection on normal metrics"""
        # Train with normal data
        for metric in normal_metrics:
            detector.add_metrics(metric)
        
        # Test on normal metric
        normal_metric = {
            'cpu_usage': 52.0,
            'memory_usage': 61.0,
            'response_time': 205.0,
            'error_rate': 0.6,
            'requests_per_sec': 98.0,
            'disk_io': 1020.0,
            'network_throughput': 510.0
        }
        
        anomaly = detector.detect_anomaly(normal_metric)
        
        # Should not detect as anomaly
        assert anomaly is None
    
    def test_anomaly_detection_abnormal(self, detector, normal_metrics):
        """Test detection on abnormal metrics"""
        # Train with normal data
        for metric in normal_metrics:
            detector.add_metrics(metric)
        
        # Test on anomalous metric
        anomalous_metric = {
            'cpu_usage': 95.0,  # Very high
            'memory_usage': 90.0,  # Very high
            'response_time': 1500.0,  # Very high
            'error_rate': 10.0,  # Very high
            'requests_per_sec': 20.0,  # Very low
            'disk_io': 5000.0,
            'network_throughput': 2000.0
        }
        
        anomaly = detector.detect_anomaly(anomalous_metric)
        
        # Should detect as anomaly
        assert anomaly is not None
        assert anomaly['is_anomaly'] is True
        assert 'anomaly_type' in anomaly
        assert 'severity' in anomaly
        assert anomaly['anomaly_score'] < 0  # Negative score indicates anomaly
    
    def test_anomaly_type_identification(self, detector, normal_metrics):
        """Test anomaly type identification"""
        # Train model
        for metric in normal_metrics:
            detector.add_metrics(metric)
        
        # CPU anomaly
        cpu_anomaly = {
            'cpu_usage': 95.0,
            'memory_usage': 60.0,
            'response_time': 200.0,
            'error_rate': 0.5,
            'requests_per_sec': 100.0,
            'disk_io': 1000.0,
            'network_throughput': 500.0
        }
        
        anomaly_type = detector._identify_anomaly_type(cpu_anomaly)
        assert 'CPU' in anomaly_type
    
    def test_model_persistence(self, detector, normal_metrics, tmp_path):
        """Test model save/load"""
        # Train model
        for metric in normal_metrics:
            detector.add_metrics(metric)
        
        # Save model
        model_path = tmp_path / "test_model.pkl"
        success = detector.save_model(str(model_path))
        
        assert success
        assert model_path.exists()
        
        # Load model into new detector
        new_detector = AnomalyDetector()
        success = new_detector.load_model(str(model_path))
        
        assert success
        assert new_detector.is_trained
    
    def test_retraining(self, detector, normal_metrics):
        """Test model retraining"""
        # Initial training
        for metric in normal_metrics:
            detector.add_metrics(metric)
        
        assert detector.is_trained
        
        # Retrain
        success = detector.retrain()
        
        assert success
        assert detector.is_trained


class TestPerformancePredictor:
    """Test suite for PerformancePredictor"""
    
    @pytest.fixture
    def predictor(self):
        """Create predictor instance"""
        return PerformancePredictor()
    
    @pytest.fixture
    def metrics_history(self):
        """Generate metrics history"""
        return [
            {
                'cpu_usage': 50 + i,
                'memory_usage': 60 + i * 0.5,
                'response_time': 200 + i * 10
            }
            for i in range(20)
        ]
    
    def test_prediction(self, predictor, metrics_history):
        """Test resource exhaustion prediction"""
        predictions = predictor.predict_resource_exhaustion(metrics_history)
        
        assert 'predictions' in predictions
        assert 'alerts' in predictions
        assert 'timestamp' in predictions
    
    def test_cpu_exhaustion_alert(self, predictor):
        """Test CPU exhaustion prediction"""
        # Gradually increasing CPU
        history = [
            {'cpu_usage': 70 + i * 2, 'memory_usage': 60, 'response_time': 200}
            for i in range(10)
        ]
        
        predictions = predictor.predict_resource_exhaustion(history)
        
        # Should predict CPU exhaustion
        alerts = predictions.get('alerts', [])
        cpu_alerts = [a for a in alerts if 'CPU' in a.get('type', '')]
        
        assert len(cpu_alerts) > 0
    
    def test_memory_exhaustion_alert(self, predictor):
        """Test memory exhaustion prediction"""
        # Gradually increasing memory
        history = [
            {'cpu_usage': 50, 'memory_usage': 70 + i * 2, 'response_time': 200}
            for i in range(10)
        ]
        
        predictions = predictor.predict_resource_exhaustion(history)
        
        # Should predict memory exhaustion
        alerts = predictions.get('alerts', [])
        memory_alerts = [a for a in alerts if 'MEMORY' in a.get('type', '')]
        
        assert len(memory_alerts) > 0


class TestTimeSeriesForecaster:
    """Test suite for TimeSeriesForecaster"""
    
    @pytest.fixture
    def forecaster(self):
        """Create forecaster instance"""
        return TimeSeriesForecaster(alpha=0.3)
    
    def test_exponential_smoothing(self, forecaster):
        """Test exponential smoothing"""
        values = [10, 12, 11, 13, 12]
        
        for value in values:
            forecast = forecaster.update_and_predict(value)
        
        # Forecast should be close to recent values
        assert 10 <= forecast <= 15
    
    def test_trend_prediction(self, forecaster):
        """Test trend prediction"""
        # Increasing trend
        increasing = [10, 20, 30, 40, 50]
        
        predictions = forecaster.predict_trend(increasing, steps=5)
        
        assert len(predictions) == 5
        # Should predict continuing increase
        assert predictions[0] > 50
        assert predictions[-1] > predictions[0]
    
    def test_trend_prediction_decreasing(self, forecaster):
        """Test decreasing trend prediction"""
        # Decreasing trend
        decreasing = [100, 90, 80, 70, 60]
        
        predictions = forecaster.predict_trend(decreasing, steps=5)
        
        assert len(predictions) == 5
        # Should predict continuing decrease
        assert predictions[0] < 60


# Integration tests
class TestIntegration:
    """Integration tests"""
    
    def test_full_workflow(self):
        """Test complete detection workflow"""
        detector = AnomalyDetector()
        
        # Generate and add normal metrics
        for i in range(30):
            metric = {
                'cpu_usage': 50 + np.random.randn() * 5,
                'memory_usage': 60 + np.random.randn() * 5,
                'response_time': 200 + np.random.randn() * 20,
                'error_rate': 0.5 + np.random.randn() * 0.2,
                'requests_per_sec': 100 + np.random.randn() * 10,
                'disk_io': 1000,
                'network_throughput': 500
            }
            detector.add_metrics(metric)
        
        # Should be trained
        assert detector.is_trained
        
        # Test normal metric
        normal = {
            'cpu_usage': 52, 'memory_usage': 61, 'response_time': 205,
            'error_rate': 0.6, 'requests_per_sec': 98,
            'disk_io': 1000, 'network_throughput': 500
        }
        result = detector.detect_anomaly(normal)
        assert result is None
        
        # Test anomalous metric
        anomalous = {
            'cpu_usage': 95, 'memory_usage': 90, 'response_time': 1500,
            'error_rate': 10, 'requests_per_sec': 20,
            'disk_io': 5000, 'network_throughput': 2000
        }
        result = detector.detect_anomaly(anomalous)
        assert result is not None
        assert result['is_anomaly'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])