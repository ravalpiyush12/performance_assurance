"""
AI/ML Anomaly Detection Service
Implements Isolation Forest and time-series forecasting for cloud workload monitoring
"""

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from collections import deque
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnomalyDetector:
    def __init__(self, contamination=0.1, window_size=100):
        """
        Initialize ML-based anomaly detector
        
        Args:
            contamination: Expected proportion of outliers (0.1 = 10%)
            window_size: Number of historical points to maintain
        """
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.metrics_window = deque(maxlen=window_size)
        self.is_trained = False
        
    def add_metrics(self, metrics):
        """Add new metrics to historical window"""
        feature_vector = self._extract_features(metrics)
        self.metrics_window.append(feature_vector)
        
        # Train model when we have enough data
        if len(self.metrics_window) >= 20 and not self.is_trained:
            self._train_model()
            
    def _extract_features(self, metrics):
        """Extract feature vector from metrics"""
        return [
            metrics.get('cpu_usage', 0),
            metrics.get('memory_usage', 0),
            metrics.get('response_time', 0),
            metrics.get('error_rate', 0),
            metrics.get('requests_per_sec', 0),
            metrics.get('disk_io', 0),
            metrics.get('network_throughput', 0)
        ]
    
    def _train_model(self):
        """Train the isolation forest model"""
        if len(self.metrics_window) < 20:
            return
            
        X = np.array(list(self.metrics_window))
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_trained = True
        logger.info("Anomaly detection model trained successfully")
        
    def detect_anomaly(self, current_metrics):
        """
        Detect if current metrics are anomalous
        
        Returns:
            dict: Anomaly information or None
        """
        if not self.is_trained:
            return None
            
        feature_vector = self._extract_features(current_metrics)
        X = np.array([feature_vector])
        X_scaled = self.scaler.transform(X)
        
        # Get anomaly prediction (-1 = anomaly, 1 = normal)
        prediction = self.model.predict(X_scaled)[0]
        
        if prediction == -1:
            # Calculate anomaly score
            score = self.model.score_samples(X_scaled)[0]
            
            # Identify which metric is most anomalous
            anomaly_type = self._identify_anomaly_type(current_metrics)
            
            return {
                'is_anomaly': True,
                'anomaly_score': float(score),
                'anomaly_type': anomaly_type,
                'severity': 'critical' if score < -0.5 else 'warning',
                'timestamp': datetime.now().isoformat(),
                'metrics': current_metrics
            }
        
        return None
    
    def _identify_anomaly_type(self, metrics):
        """Identify which metric is causing the anomaly"""
        if len(self.metrics_window) < 5:
            return 'UNKNOWN'
            
        # Calculate deviations for each metric
        recent = list(self.metrics_window)[-10:]
        recent_array = np.array(recent)
        means = np.mean(recent_array, axis=0)
        stds = np.std(recent_array, axis=0)
        
        current = self._extract_features(metrics)
        deviations = np.abs((np.array(current) - means) / (stds + 1e-6))
        
        # Find metric with highest deviation
        max_idx = np.argmax(deviations)
        metric_names = ['cpu_usage', 'memory_usage', 'response_time', 
                       'error_rate', 'requests_per_sec', 'disk_io', 
                       'network_throughput']
        
        return metric_names[max_idx].upper()


class TimeSeriesForecaster:
    """Simple exponential smoothing for capacity forecasting"""
    
    def __init__(self, alpha=0.3):
        self.alpha = alpha
        self.forecast = None
        
    def update_and_predict(self, current_value):
        """Update forecast with new value and predict next"""
        if self.forecast is None:
            self.forecast = current_value
        else:
            self.forecast = self.alpha * current_value + (1 - self.alpha) * self.forecast
        
        return self.forecast
    
    def predict_trend(self, values, steps=5):
        """Predict future values using simple linear extrapolation"""
        if len(values) < 3:
            return [values[-1]] * steps if values else [0] * steps
            
        # Calculate trend
        recent = values[-10:]
        x = np.arange(len(recent))
        y = np.array(recent)
        
        # Simple linear regression
        coeffs = np.polyfit(x, y, 1)
        
        # Predict future
        future_x = np.arange(len(recent), len(recent) + steps)
        predictions = np.polyval(coeffs, future_x)
        
        return predictions.tolist()


class PerformancePredictor:
    """Predict performance issues before they occur"""
    
    def __init__(self):
        self.cpu_forecaster = TimeSeriesForecaster(alpha=0.3)
        self.memory_forecaster = TimeSeriesForecaster(alpha=0.25)
        self.response_forecaster = TimeSeriesForecaster(alpha=0.35)
        
    def predict_resource_exhaustion(self, metrics_history):
        """
        Predict if resources will be exhausted soon
        
        Returns:
            dict: Prediction results
        """
        if len(metrics_history) < 5:
            return {'predictions': [], 'alerts': []}
            
        cpu_values = [m['cpu_usage'] for m in metrics_history[-20:]]
        memory_values = [m['memory_usage'] for m in metrics_history[-20:]]
        response_values = [m['response_time'] for m in metrics_history[-20:]]
        
        # Predict next 5 data points
        cpu_pred = self.cpu_forecaster.predict_trend(cpu_values, steps=5)
        memory_pred = self.memory_forecaster.predict_trend(memory_values, steps=5)
        response_pred = self.response_forecaster.predict_trend(response_values, steps=5)
        
        alerts = []
        
        # Check for resource exhaustion
        if max(cpu_pred) > 85:
            alerts.append({
                'type': 'CPU_EXHAUSTION_PREDICTED',
                'severity': 'warning',
                'message': f'CPU usage predicted to reach {max(cpu_pred):.1f}% soon',
                'recommended_action': 'SCALE_UP'
            })
            
        if max(memory_pred) > 85:
            alerts.append({
                'type': 'MEMORY_EXHAUSTION_PREDICTED',
                'severity': 'warning',
                'message': f'Memory usage predicted to reach {max(memory_pred):.1f}% soon',
                'recommended_action': 'SCALE_UP'
            })
            
        if max(response_pred) > 1000:
            alerts.append({
                'type': 'LATENCY_SPIKE_PREDICTED',
                'severity': 'warning',
                'message': f'Response time predicted to reach {max(response_pred):.0f}ms',
                'recommended_action': 'ENABLE_CACHING'
            })
        
        return {
            'predictions': {
                'cpu': cpu_pred,
                'memory': memory_pred,
                'response_time': response_pred
            },
            'alerts': alerts
        }


# Example usage
if __name__ == '__main__':
    detector = AnomalyDetector()
    predictor = PerformancePredictor()
    
    # Simulate metrics
    metrics_history = []
    for i in range(50):
        metrics = {
            'cpu_usage': 50 + np.random.randn() * 10,
            'memory_usage': 60 + np.random.randn() * 8,
            'response_time': 200 + np.random.randn() * 50,
            'error_rate': 0.5 + np.random.randn() * 0.2,
            'requests_per_sec': 100 + np.random.randn() * 20,
            'disk_io': 1000 + np.random.randn() * 200,
            'network_throughput': 500 + np.random.randn() * 100
        }
        
        # Add anomaly at iteration 40
        if i == 40:
            metrics['cpu_usage'] = 95
            metrics['response_time'] = 800
            
        detector.add_metrics(metrics)
        metrics_history.append(metrics)
        
        # Detect anomaly
        anomaly = detector.detect_anomaly(metrics)
        if anomaly:
            logger.info(f"Anomaly detected: {json.dumps(anomaly, indent=2)}")
            
        # Predict future issues
        if i % 10 == 0:
            predictions = predictor.predict_resource_exhaustion(metrics_history)
            if predictions['alerts']:
                logger.info(f"Predictions: {json.dumps(predictions, indent=2)}")
                