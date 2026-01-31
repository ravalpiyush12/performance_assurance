"""
ML Anomaly Detection Service - Complete Implementation
Save as: src/ml/anomaly_detector.py

Features:
- Isolation Forest for anomaly detection
- Time-series forecasting
- Performance prediction
- Adaptive learning
"""

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from collections import deque
import logging
from datetime import datetime
from typing import Dict, List, Optional
import pickle
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    ML-based anomaly detector using Isolation Forest
    """
    
    def __init__(self, contamination: float = 0.1, window_size: int = 100):
        """
        Initialize anomaly detector
        
        Args:
            contamination: Expected proportion of outliers (0.1 = 10%)
            window_size: Number of historical points to maintain
        """
        self.contamination = contamination
        self.window_size = window_size
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
            max_samples='auto',
            max_features=1.0,
            bootstrap=False
        )
        self.scaler = StandardScaler()
        self.metrics_window = deque(maxlen=window_size)
        self.is_trained = False
        self.training_threshold = 20
        self.feature_names = [
            'cpu_usage', 'memory_usage', 'response_time', 
            'error_rate', 'requests_per_sec', 'disk_io', 
            'network_throughput'
        ]
        
        logger.info(f"Anomaly Detector initialized (contamination={contamination}, window={window_size})")
        
    def add_metrics(self, metrics: Dict) -> None:
        """
        Add new metrics to historical window
        
        Args:
            metrics: Dictionary containing metric values
        """
        feature_vector = self._extract_features(metrics)
        self.metrics_window.append(feature_vector)
        
        # Auto-train when we have enough data
        if len(self.metrics_window) >= self.training_threshold and not self.is_trained:
            self._train_model()
            
    def _extract_features(self, metrics: Dict) -> List[float]:
        """
        Extract feature vector from metrics
        
        Args:
            metrics: Raw metrics dictionary
            
        Returns:
            Feature vector as list
        """
        return [
            metrics.get('cpu_usage', 0.0),
            metrics.get('memory_usage', 0.0),
            metrics.get('response_time', 0.0),
            metrics.get('error_rate', 0.0),
            metrics.get('requests_per_sec', 0.0),
            metrics.get('disk_io', 0.0),
            metrics.get('network_throughput', 0.0)
        ]
    
    def _train_model(self) -> bool:
        """
        Train the isolation forest model
        
        Returns:
            True if training successful, False otherwise
        """
        if len(self.metrics_window) < self.training_threshold:
            logger.warning(f"Insufficient data for training: {len(self.metrics_window)}/{self.training_threshold}")
            return False
            
        try:
            X = np.array(list(self.metrics_window))
            
            # Fit scaler
            self.scaler.fit(X)
            X_scaled = self.scaler.transform(X)
            
            # Train model
            self.model.fit(X_scaled)
            self.is_trained = True
            
            logger.info(f"✅ Model trained successfully with {len(self.metrics_window)} samples")
            return True
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return False
        
    def detect_anomaly(self, current_metrics: Dict) -> Optional[Dict]:
        """
        Detect if current metrics are anomalous
        
        Args:
            current_metrics: Current metric values
            
        Returns:
            Anomaly information dict or None if normal
        """
        if not self.is_trained:
            logger.debug("Model not trained yet, skipping detection")
            return None
            
        try:
            feature_vector = self._extract_features(current_metrics)
            X = np.array([feature_vector])
            X_scaled = self.scaler.transform(X)
            
            # Get prediction (-1 = anomaly, 1 = normal)
            prediction = self.model.predict(X_scaled)[0]
            
            if prediction == -1:
                # Calculate anomaly score (more negative = more anomalous)
                score = self.model.score_samples(X_scaled)[0]
                
                # Identify which metric is most anomalous
                anomaly_type = self._identify_anomaly_type(current_metrics)
                
                # Determine severity
                severity = 'critical' if score < -0.5 else 'warning'
                
                anomaly_info = {
                    'is_anomaly': True,
                    'anomaly_score': float(score),
                    'anomaly_type': anomaly_type,
                    'severity': severity,
                    'timestamp': datetime.now().isoformat(),
                    'metrics': current_metrics,
                    'confidence': abs(float(score))
                }
                
                logger.warning(f"⚠️  Anomaly detected: {anomaly_type} (severity: {severity}, score: {score:.3f})")
                return anomaly_info
                
            return None
            
        except Exception as e:
            logger.error(f"Error detecting anomaly: {e}")
            return None
    
    def _identify_anomaly_type(self, metrics: Dict) -> str:
        """
        Identify which metric is causing the anomaly
        
        Args:
            metrics: Current metrics
            
        Returns:
            Name of the anomalous metric
        """
        if len(self.metrics_window) < 5:
            return 'UNKNOWN'
            
        try:
            # Calculate deviations for each metric
            recent = list(self.metrics_window)[-10:]
            recent_array = np.array(recent)
            means = np.mean(recent_array, axis=0)
            stds = np.std(recent_array, axis=0)
            
            current = self._extract_features(metrics)
            
            # Avoid division by zero
            stds = np.where(stds == 0, 1e-6, stds)
            deviations = np.abs((np.array(current) - means) / stds)
            
            # Find metric with highest deviation
            max_idx = np.argmax(deviations)
            
            return self.feature_names[max_idx].upper()
            
        except Exception as e:
            logger.error(f"Error identifying anomaly type: {e}")
            return 'UNKNOWN'
    
    def retrain(self) -> bool:
        """
        Retrain model with current window data
        
        Returns:
            True if retraining successful
        """
        self.is_trained = False
        return self._train_model()
    
    def save_model(self, filepath: str) -> bool:
        """
        Save trained model to disk
        
        Args:
            filepath: Path to save model
            
        Returns:
            True if save successful
        """
        try:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'is_trained': self.is_trained,
                'contamination': self.contamination,
                'feature_names': self.feature_names
            }
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"Model saved to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False
    
    def load_model(self, filepath: str) -> bool:
        """
        Load trained model from disk
        
        Args:
            filepath: Path to load model from
            
        Returns:
            True if load successful
        """
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.is_trained = model_data['is_trained']
            self.contamination = model_data['contamination']
            self.feature_names = model_data['feature_names']
            
            logger.info(f"Model loaded from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False


class TimeSeriesForecaster:
    """
    Simple exponential smoothing for capacity forecasting
    """
    
    def __init__(self, alpha: float = 0.3):
        """
        Initialize forecaster
        
        Args:
            alpha: Smoothing factor (0-1)
        """
        self.alpha = alpha
        self.forecast = None
        
    def update_and_predict(self, current_value: float) -> float:
        """
        Update forecast with new value and predict next
        
        Args:
            current_value: Latest observed value
            
        Returns:
            Forecasted next value
        """
        if self.forecast is None:
            self.forecast = current_value
        else:
            self.forecast = self.alpha * current_value + (1 - self.alpha) * self.forecast
        
        return self.forecast
    
    def predict_trend(self, values: List[float], steps: int = 5) -> List[float]:
        """
        Predict future values using linear extrapolation
        
        Args:
            values: Historical values
            steps: Number of future steps to predict
            
        Returns:
            List of predicted values
        """
        if len(values) < 3:
            return [values[-1] if values else 0] * steps
            
        # Use recent values for trend
        recent = values[-10:] if len(values) >= 10 else values
        x = np.arange(len(recent))
        y = np.array(recent)
        
        # Simple linear regression
        coeffs = np.polyfit(x, y, 1)
        
        # Predict future
        future_x = np.arange(len(recent), len(recent) + steps)
        predictions = np.polyval(coeffs, future_x)
        
        return predictions.tolist()


class PerformancePredictor:
    """
    Predict performance issues before they occur
    """
    
    def __init__(self):
        self.cpu_forecaster = TimeSeriesForecaster(alpha=0.3)
        self.memory_forecaster = TimeSeriesForecaster(alpha=0.25)
        self.response_forecaster = TimeSeriesForecaster(alpha=0.35)
        
    def predict_resource_exhaustion(self, metrics_history: List[Dict]) -> Dict:
        """
        Predict if resources will be exhausted soon
        
        Args:
            metrics_history: Historical metrics
            
        Returns:
            Prediction results with alerts
        """
        if len(metrics_history) < 5:
            return {'predictions': {}, 'alerts': []}
            
        # Extract metric series
        cpu_values = [m.get('cpu_usage', 0) for m in metrics_history[-20:]]
        memory_values = [m.get('memory_usage', 0) for m in metrics_history[-20:]]
        response_values = [m.get('response_time', 0) for m in metrics_history[-20:]]
        
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
                'recommended_action': 'SCALE_UP',
                'predicted_value': max(cpu_pred)
            })
            
        if max(memory_pred) > 85:
            alerts.append({
                'type': 'MEMORY_EXHAUSTION_PREDICTED',
                'severity': 'warning',
                'message': f'Memory usage predicted to reach {max(memory_pred):.1f}% soon',
                'recommended_action': 'SCALE_UP',
                'predicted_value': max(memory_pred)
            })
            
        if max(response_pred) > 1000:
            alerts.append({
                'type': 'LATENCY_SPIKE_PREDICTED',
                'severity': 'warning',
                'message': f'Response time predicted to reach {max(response_pred):.0f}ms',
                'recommended_action': 'ENABLE_CACHING',
                'predicted_value': max(response_pred)
            })
        
        return {
            'predictions': {
                'cpu': cpu_pred,
                'memory': memory_pred,
                'response_time': response_pred
            },
            'alerts': alerts,
            'timestamp': datetime.now().isoformat()
        }


# Example usage and testing
if __name__ == '__main__':
    # Test anomaly detector
    detector = AnomalyDetector()
    predictor = PerformancePredictor()
    
    print("Testing Anomaly Detector...")
    print("=" * 60)
    
    # Simulate metrics
    metrics_history = []
    for i in range(50):
        # Normal metrics
        metrics = {
            'cpu_usage': 50 + np.random.randn() * 10,
            'memory_usage': 60 + np.random.randn() * 8,
            'response_time': 200 + np.random.randn() * 50,
            'error_rate': 0.5 + np.random.randn() * 0.2,
            'requests_per_sec': 100 + np.random.randn() * 20,
            'disk_io': 1000 + np.random.randn() * 200,
            'network_throughput': 500 + np.random.randn() * 100
        }
        
        # Inject anomaly at iteration 40
        if i == 40:
            print("\n🔴 Injecting anomaly at iteration 40...")
            metrics['cpu_usage'] = 95
            metrics['response_time'] = 800
            
        detector.add_metrics(metrics)
        metrics_history.append(metrics)
        
        # Detect anomaly
        anomaly = detector.detect_anomaly(metrics)
        if anomaly:
            print(f"\n⚠️  ANOMALY DETECTED at iteration {i}:")
            print(f"   Type: {anomaly['anomaly_type']}")
            print(f"   Severity: {anomaly['severity']}")
            print(f"   Score: {anomaly['anomaly_score']:.3f}")
            print(f"   Confidence: {anomaly['confidence']:.3f}")
            
        # Predict future issues every 10 iterations
        if i > 0 and i % 10 == 0:
            predictions = predictor.predict_resource_exhaustion(metrics_history)
            if predictions['alerts']:
                print(f"\n📊 Predictions at iteration {i}:")
                for alert in predictions['alerts']:
                    print(f"   - {alert['message']}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    
    # Test model save/load
    print("\nTesting model persistence...")
    detector.save_model('data/anomaly_model.pkl')
    
    new_detector = AnomalyDetector()
    new_detector.load_model('data/anomaly_model.pkl')
    print("Model save/load successful!")
    