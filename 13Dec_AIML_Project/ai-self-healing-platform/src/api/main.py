"""
Main FastAPI Server - Integrates all components
Provides REST API for the monitoring dashboard
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import json
import logging
from datetime import datetime

# Import our custom modules (assumes they're in the same directory)
# from ml_anomaly_detector import AnomalyDetector, PerformancePredictor
# from self_healing_orchestrator import SelfHealingOrchestrator, ActionType
# from observability_collector import MetricsCollector, LogAggregator, DistributedTracer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI-Driven Self-Healing Platform",
    description="Cloud workload monitoring with automated remediation",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
# anomaly_detector = AnomalyDetector(contamination=0.1)
# performance_predictor = PerformancePredictor()
# healing_orchestrator = SelfHealingOrchestrator()
# metrics_collector = MetricsCollector(collection_interval=5)
# log_aggregator = LogAggregator()
# tracer = DistributedTracer()

# In-memory storage for demo
metrics_history = []
anomalies_detected = []
healing_actions_taken = []
active_websockets = []

# Pydantic models
class MetricData(BaseModel):
    timestamp: str
    cpu_usage: float
    memory_usage: float
    response_time: float
    error_rate: float
    requests_per_sec: float

class AnomalyAlert(BaseModel):
    id: str
    timestamp: str
    anomaly_type: str
    severity: str
    metrics: Dict
    anomaly_score: float

class HealingAction(BaseModel):
    id: str
    timestamp: str
    action_type: str
    target: str
    status: str
    params: Dict
    execution_time: Optional[float] = None

class SystemStatus(BaseModel):
    health_score: float
    active_alerts: int
    total_metrics_collected: int
    healing_actions_count: int
    uptime_seconds: float

# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI-Driven Self-Healing Platform",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/status", response_model=SystemStatus)
async def get_system_status():
    """Get overall system status"""
    # Calculate health score based on recent anomalies
    recent_anomalies = len([a for a in anomalies_detected[-10:]])
    health_score = max(60, 100 - (recent_anomalies * 5))
    
    return SystemStatus(
        health_score=health_score,
        active_alerts=len([a for a in anomalies_detected[-10:]]),
        total_metrics_collected=len(metrics_history),
        healing_actions_count=len(healing_actions_taken),
        uptime_seconds=0  # Would track actual uptime
    )

@app.get("/api/v1/metrics", response_model=List[MetricData])
async def get_metrics(limit: int = 50):
    """Get recent metrics"""
    return metrics_history[-limit:]

@app.post("/api/v1/metrics")
async def ingest_metrics(metric: MetricData, background_tasks: BackgroundTasks):
    """Ingest new metrics and trigger anomaly detection"""
    metrics_history.append(metric)
    
    # Keep history manageable
    if len(metrics_history) > 1000:
        metrics_history[:] = metrics_history[-1000:]
    
    # Trigger anomaly detection in background
    background_tasks.add_task(detect_and_heal, metric)
    
    return {"status": "accepted", "timestamp": metric.timestamp}

@app.get("/api/v1/anomalies", response_model=List[AnomalyAlert])
async def get_anomalies(limit: int = 20):
    """Get detected anomalies"""
    return anomalies_detected[-limit:]

@app.get("/api/v1/healing-actions", response_model=List[HealingAction])
async def get_healing_actions(limit: int = 20):
    """Get healing actions history"""
    return healing_actions_taken[-limit:]

@app.post("/api/v1/healing-actions/{action_id}/retry")
async def retry_healing_action(action_id: str):
    """Retry a failed healing action"""
    action = next((a for a in healing_actions_taken if a['id'] == action_id), None)
    
    if not action:
        return {"error": "Action not found"}, 404
    
    # In production, re-execute the action
    return {"status": "retrying", "action_id": action_id}

@app.get("/api/v1/predictions")
async def get_predictions():
    """Get performance predictions"""
    if len(metrics_history) < 10:
        return {"predictions": None, "message": "Insufficient data"}
    
    # Extract recent metrics for prediction
    recent = metrics_history[-20:]
    cpu_values = [m.cpu_usage for m in recent]
    memory_values = [m.memory_usage for m in recent]
    
    # Simple trend calculation
    cpu_trend = "increasing" if cpu_values[-1] > cpu_values[0] else "decreasing"
    memory_trend = "increasing" if memory_values[-1] > memory_values[0] else "decreasing"
    
    return {
        "predictions": {
            "cpu_trend": cpu_trend,
            "memory_trend": memory_trend,
            "predicted_cpu_5min": min(100, cpu_values[-1] * 1.1),
            "predicted_memory_5min": min(100, memory_values[-1] * 1.05)
        },
        "alerts": []
    }

@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    """WebSocket for real-time metrics streaming"""
    await websocket.accept()
    active_websockets.append(websocket)
    
    try:
        while True:
            # Send latest metrics every 2 seconds
            if metrics_history:
                latest = metrics_history[-1]
                await websocket.send_json({
                    "type": "metric",
                    "data": latest.dict()
                })
            
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        active_websockets.remove(websocket)
        logger.info("WebSocket disconnected")

@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """WebSocket for real-time alerts"""
    await websocket.accept()
    last_sent_count = 0
    
    try:
        while True:
            # Send new alerts
            current_count = len(anomalies_detected)
            if current_count > last_sent_count:
                new_alerts = anomalies_detected[last_sent_count:]
                for alert in new_alerts:
                    await websocket.send_json({
                        "type": "alert",
                        "data": alert
                    })
                last_sent_count = current_count
            
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        logger.info("Alert WebSocket disconnected")

# Background tasks

async def detect_and_heal(metric: MetricData):
    """Detect anomalies and trigger healing"""
    # Simplified anomaly detection logic
    metrics_dict = metric.dict()
    
    # Simple threshold-based detection
    is_anomaly = False
    anomaly_type = None
    
    if metrics_dict['cpu_usage'] > 80:
        is_anomaly = True
        anomaly_type = 'CPU_USAGE'
    elif metrics_dict['memory_usage'] > 85:
        is_anomaly = True
        anomaly_type = 'MEMORY_USAGE'
    elif metrics_dict['response_time'] > 800:
        is_anomaly = True
        anomaly_type = 'RESPONSE_TIME'
    elif metrics_dict['error_rate'] > 5:
        is_anomaly = True
        anomaly_type = 'ERROR_RATE'
    
    if is_anomaly:
        import uuid
        
        anomaly = {
            'id': str(uuid.uuid4()),
            'timestamp': metrics_dict['timestamp'],
            'anomaly_type': anomaly_type,
            'severity': 'critical' if metrics_dict['cpu_usage'] > 90 else 'warning',
            'metrics': metrics_dict,
            'anomaly_score': -0.6 if metrics_dict['cpu_usage'] > 90 else -0.3
        }
        
        anomalies_detected.append(anomaly)
        logger.info(f"Anomaly detected: {anomaly_type}")
        
        # Trigger healing
        await trigger_healing(anomaly)

async def trigger_healing(anomaly: Dict):
    """Trigger appropriate healing action"""
    import uuid
    
    action_mapping = {
        'CPU_USAGE': {'action': 'SCALE_UP', 'target': 'application-cluster'},
        'MEMORY_USAGE': {'action': 'SCALE_UP', 'target': 'application-cluster'},
        'RESPONSE_TIME': {'action': 'ENABLE_CACHE', 'target': 'api-gateway'},
        'ERROR_RATE': {'action': 'TRAFFIC_SHIFT', 'target': 'healthy-instances'}
    }
    
    action_config = action_mapping.get(anomaly['anomaly_type'])
    
    if action_config:
        healing_action = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'action_type': action_config['action'],
            'target': action_config['target'],
            'status': 'executing',
            'params': {'anomaly_id': anomaly['id']},
            'execution_time': None
        }
        
        healing_actions_taken.append(healing_action)
        logger.info(f"Healing action initiated: {action_config['action']}")
        
        # Simulate execution
        await asyncio.sleep(2)
        healing_action['status'] = 'completed'
        healing_action['execution_time'] = 2.0

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting AI-Driven Self-Healing Platform...")
    
    # Start background metrics collection
    # asyncio.create_task(start_metrics_collection())
    
    logger.info("Platform started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down platform...")

# Run with: uvicorn main_api_server:app --reload --host 0.0.0.0 --port 8000

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    