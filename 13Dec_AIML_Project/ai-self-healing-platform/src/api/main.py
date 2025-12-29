"""
Main API Server - Complete Integration of All Components (Version 13)
Save as: src/api/main.py

Key Updates in v13:
- Dynamic active alerts tracking with unique IDs
- Auto-resolution of alerts when healing succeeds
- Improved health score calculation
- Fixed import order
- Better alert lifecycle management

This integrates:
- ML Anomaly Detection
- Self-Healing Orchestrator  
- Metrics Collection
- Real-time Dashboard
- WebSocket updates
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import json
import logging
from datetime import datetime
import sys
from pathlib import Path
from collections import deque
import psutil
import random

# Add src to path for imports FIRST
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Ensure logs directory exists
Path('logs').mkdir(exist_ok=True)

# Setup logging with UTF-8 encoding for Windows compatibility
if sys.platform == 'win32':
    # Windows: Force UTF-8 encoding
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/platform.log', mode='a', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import our modules AFTER path setup
try:
    from src.ml.anomaly_detector import AnomalyDetector, PerformancePredictor
    from src.orchestrator.self_healing import SelfHealingOrchestrator, CloudProvider
    logger.info("✅ Successfully imported custom modules")
except ImportError as e:
    logger.error(f"❌ Import error: {e}")
    logger.error("Make sure you're running from the project root directory")
    logger.error("Required files: src/ml/anomaly_detector.py, src/orchestrator/self_healing.py")
    sys.exit(1)

# FastAPI app
app = FastAPI(
    title="AI-Driven Self-Healing Platform",
    description="Intelligent observability and automated remediation for cloud workloads",
    version="13.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
anomaly_detector = AnomalyDetector(contamination=0.1, window_size=100)
performance_predictor = PerformancePredictor()
healing_orchestrator = SelfHealingOrchestrator(cloud_provider=CloudProvider.LOCAL)

# In-memory storage with deques for better performance
metrics_history = deque(maxlen=1000)
anomalies_detected = deque(maxlen=200)
healing_actions_taken = deque(maxlen=200)
active_websockets = []
startup_time = datetime.now()

# NEW in v13: Active alerts tracking
active_alerts = {}  # Dict with anomaly_id as key for O(1) lookups

# Pydantic models
class Metric(BaseModel):
    timestamp: str
    cpu_usage: float
    memory_usage: float
    response_time: float
    error_rate: float
    requests_per_sec: float
    disk_io: Optional[float] = 0.0
    network_throughput: Optional[float] = 0.0

class SystemStatus(BaseModel):
    health_score: float
    active_alerts: int
    total_metrics: int
    healing_actions_count: int
    ml_model_trained: bool
    uptime_seconds: float

class AnomalyResponse(BaseModel):
    id: int
    timestamp: str
    anomaly_type: str
    severity: str
    score: float
    metrics: Dict
    status: Optional[str] = "active"

class HealingActionResponse(BaseModel):
    action_id: str
    timestamp: str
    action_type: str
    target: str
    status: str
    execution_time: Optional[float] = None

# ============================================================================
# NEW in v13: Alert Management Functions
# ============================================================================

def generate_anomaly_id() -> str:
    """Generate unique anomaly ID"""
    return f"anomaly_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"

def add_active_alert(anomaly_id: str, anomaly_data: dict):
    """Add a new active alert"""
    active_alerts[anomaly_id] = {
        **anomaly_data,
        'anomaly_id': anomaly_id,
        'status': 'active',
        'created_at': datetime.now().isoformat()
    }
    logger.info(f"🚨 New active alert: {anomaly_id} - {anomaly_data.get('anomaly_type')}")

def resolve_alert(anomaly_id: str):
    """Mark an alert as resolved and remove from active alerts"""
    if anomaly_id in active_alerts:
        active_alerts[anomaly_id]['status'] = 'resolved'
        active_alerts[anomaly_id]['resolved_at'] = datetime.now().isoformat()
        del active_alerts[anomaly_id]
        logger.info(f"✅ Alert resolved: {anomaly_id}")

def auto_resolve_old_alerts():
    """Auto-resolve alerts older than 5 minutes"""
    now = datetime.now()
    to_remove = []
    
    for anomaly_id, alert in active_alerts.items():
        created_at = datetime.fromisoformat(alert['created_at'])
        age = (now - created_at).total_seconds()
        
        # Auto-resolve if older than 5 minutes
        if age > 300:
            to_remove.append(anomaly_id)
    
    for anomaly_id in to_remove:
        resolve_alert(anomaly_id)
        logger.info(f"⏰ Auto-resolved old alert: {anomaly_id}")

def calculate_health_score() -> float:
    """Calculate dynamic health score based on metrics and alerts"""
    if len(metrics_history) == 0:
        return 100.0
    
    # Get recent metrics (last 20)
    recent_metrics = list(metrics_history)[-20:]
    
    # Calculate averages
    avg_cpu = sum(m['cpu_usage'] for m in recent_metrics) / len(recent_metrics)
    avg_memory = sum(m['memory_usage'] for m in recent_metrics) / len(recent_metrics)
    avg_error = sum(m['error_rate'] for m in recent_metrics) / len(recent_metrics)
    avg_response = sum(m['response_time'] for m in recent_metrics) / len(recent_metrics)
    
    # Start with perfect health
    health = 100.0
    
    # Deduct for high resource usage
    if avg_cpu > 80:
        health -= (avg_cpu - 80) * 0.5
    if avg_memory > 80:
        health -= (avg_memory - 80) * 0.5
    
    # Deduct for errors
    health -= avg_error * 5
    
    # Deduct for slow response times
    if avg_response > 200:
        health -= (avg_response - 200) * 0.02
    
    # Deduct for active alerts (2 points per alert)
    alert_penalty = len(active_alerts) * 2
    health -= alert_penalty
    
    # Ensure between 0 and 100
    health = max(0.0, min(100.0, health))
    
    return round(health, 1)

def get_active_alerts_count() -> int:
    """Get count of currently active alerts"""
    return len(active_alerts)

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Serve embedded dashboard"""
    return HTMLResponse(get_dashboard_html())

@app.get("/api/v1/status", response_model=SystemStatus)
async def get_system_status():
    """Get overall system status with DYNAMIC health score and alerts"""
    health_score = calculate_health_score()
    active_alerts_count = get_active_alerts_count()
    
    return SystemStatus(
        health_score=health_score,
        active_alerts=active_alerts_count,  # NOW DYNAMIC!
        total_metrics=len(metrics_history),
        healing_actions_count=len(healing_actions_taken),
        ml_model_trained=anomaly_detector.is_trained,
        uptime_seconds=(datetime.now() - startup_time).total_seconds()
    )

@app.get("/api/v1/metrics")
async def get_metrics(limit: int = 50):
    """Get recent metrics"""
    return list(metrics_history)[-limit:]

@app.post("/api/v1/metrics")
async def ingest_metrics(metric: Metric, background_tasks: BackgroundTasks):
    """Ingest new metrics and trigger anomaly detection"""
    metric_dict = metric.dict()
    metrics_history.append(metric_dict)
    
    # Trigger anomaly detection in background
    background_tasks.add_task(process_metric, metric_dict)
    
    return {"status": "accepted", "timestamp": metric.timestamp}

@app.get("/api/v1/anomalies")
async def get_anomalies(limit: int = 20):
    """Get detected anomalies (all)"""
    return list(anomalies_detected)[-limit:]

@app.get("/api/v1/anomalies/active")
async def get_active_anomalies():
    """Get only currently active (unresolved) anomalies"""
    return list(active_alerts.values())

@app.post("/api/v1/anomalies/{anomaly_id}/resolve")
async def resolve_anomaly_endpoint(anomaly_id: str):
    """Manually resolve an anomaly"""
    if anomaly_id in active_alerts:
        resolve_alert(anomaly_id)
        return {"status": "success", "message": f"Alert {anomaly_id} resolved"}
    return {"status": "error", "message": f"Alert {anomaly_id} not found"}

@app.post("/api/v1/anomalies/{anomaly_id}/acknowledge")
async def acknowledge_anomaly(anomaly_id: str):
    """Acknowledge an anomaly (mark as seen but keep active)"""
    if anomaly_id in active_alerts:
        active_alerts[anomaly_id]['status'] = 'acknowledged'
        active_alerts[anomaly_id]['acknowledged_at'] = datetime.now().isoformat()
        return {"status": "success", "message": f"Alert {anomaly_id} acknowledged"}
    return {"status": "error", "message": f"Alert {anomaly_id} not found"}

@app.get("/api/v1/healing-actions")
async def get_healing_actions(limit: int = 20):
    """Get healing actions history"""
    return list(healing_actions_taken)[-limit:]

@app.get("/api/v1/predictions")
async def get_predictions():
    """Get performance predictions"""
    if len(metrics_history) < 10:
        return {"predictions": None, "message": "Insufficient data"}
    
    predictions = performance_predictor.predict_resource_exhaustion(list(metrics_history)[-20:])
    return predictions

@app.get("/api/v1/orchestrator/stats")
async def get_orchestrator_stats():
    """Get orchestrator statistics"""
    return healing_orchestrator.get_statistics()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": (datetime.now() - startup_time).total_seconds(),
        "active_alerts": get_active_alerts_count()
    }

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    active_websockets.append(websocket)
    logger.info(f"WebSocket connected. Total: {len(active_websockets)}")
    
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        active_websockets.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(active_websockets)}")

# ============================================================================
# Background Processing
# ============================================================================

async def process_metric(metric: Dict):
    """Process metric for anomaly detection and healing"""
    try:
        # Add to ML detector
        anomaly_detector.add_metrics(metric)
        
        # Detect anomalies
        if anomaly_detector.is_trained:
            anomaly = anomaly_detector.detect_anomaly(metric)
            
            if anomaly:
                # Generate unique ID
                anomaly_id = generate_anomaly_id()
                
                # Store anomaly with proper structure
                anomaly_record = {
                    'id': len(anomalies_detected) + 1,
                    'anomaly_id': anomaly_id,
                    'timestamp': anomaly.get('timestamp', datetime.now().isoformat()),
                    'anomaly_type': anomaly.get('anomaly_type', 'UNKNOWN'),
                    'severity': anomaly.get('severity', 'warning'),
                    'anomaly_score': anomaly.get('anomaly_score', 0.0),
                    'score': anomaly.get('anomaly_score', 0.0),
                    'confidence': anomaly.get('confidence', 0.0),
                    'metrics': anomaly.get('metrics', metric),
                    'status': 'active'
                }
                
                # Add to active alerts
                add_active_alert(anomaly_id, anomaly_record)
                
                # Store in history
                anomalies_detected.append(anomaly_record)
                
                logger.warning(f"🚨 Anomaly #{len(anomalies_detected)} detected: {anomaly['anomaly_type']} (severity: {anomaly['severity']})")
                
                # Trigger self-healing
                action = healing_orchestrator.decide_action(anomaly)
                if action:
                    # Execute healing action
                    success = await healing_orchestrator.execute_action(action)
                    
                    action_record = action.to_dict()
                    action_record['anomaly_id'] = anomaly_id
                    healing_actions_taken.append(action_record)
                    
                    logger.info(f"🔧 Healing action #{len(healing_actions_taken)} executed: {action.action_type.value} (success: {success})")
                    
                    # NEW in v13: Resolve alert if healing was successful
                    if success:
                        resolve_alert(anomaly_id)
                    
                    # Broadcast to WebSocket clients
                    await broadcast_update({
                        'type': 'healing_action',
                        'data': action_record
                    })
                
                # Broadcast anomaly
                await broadcast_update({
                    'type': 'anomaly',
                    'data': anomaly_record
                })
        
        # Broadcast metric update
        await broadcast_update({
            'type': 'metric',
            'data': metric
        })
        
        # Periodically auto-resolve old alerts
        auto_resolve_old_alerts()
        
    except Exception as e:
        logger.error(f"Error processing metric: {e}", exc_info=True)

async def broadcast_update(message: Dict):
    """Broadcast update to all WebSocket clients"""
    if not active_websockets:
        return
    
    disconnected = []
    for ws in active_websockets:
        try:
            await ws.send_json(message)
        except:
            disconnected.append(ws)
    
    # Remove disconnected clients
    for ws in disconnected:
        active_websockets.remove(ws)

# ============================================================================
# Automatic Metrics Generation for Demo
# ============================================================================

async def auto_generate_metrics():
    """Automatically generate metrics for demonstration"""
    logger.info("🔄 Starting automatic metrics generation...")
    counter = 0
    
    while True:
        try:
            counter += 1
            
            # Generate realistic metrics
            cpu = random.uniform(40, 70)
            memory = random.uniform(50, 75)
            latency = random.uniform(150, 400)
            error_rate = random.uniform(0, 3)
            throughput = random.uniform(80, 150)
            
            # Inject anomaly every ~20 metrics
            if counter % random.randint(18, 25) == 0:
                anomaly_type = random.choice(['cpu', 'memory', 'latency', 'error'])
                logger.info(f"💉 Injecting {anomaly_type} anomaly...")
                
                if anomaly_type == 'cpu':
                    cpu = random.uniform(85, 98)
                elif anomaly_type == 'memory':
                    memory = random.uniform(85, 95)
                elif anomaly_type == 'latency':
                    latency = random.uniform(800, 1500)
                elif anomaly_type == 'error':
                    error_rate = random.uniform(5, 15)
            
            metric = {
                'timestamp': datetime.now().isoformat(),
                'cpu_usage': round(cpu, 2),
                'memory_usage': round(memory, 2),
                'response_time': round(latency, 2),
                'error_rate': round(error_rate, 2),
                'requests_per_sec': round(throughput, 2),
                'disk_io': round(random.uniform(500, 1500), 2),
                'network_throughput': round(random.uniform(300, 700), 2)
            }
            
            # Process metric
            await process_metric(metric)
            metrics_history.append(metric)
            
            await asyncio.sleep(2)  # Generate every 2 seconds
            
        except Exception as e:
            logger.error(f"Error in auto metrics generation: {e}")
            await asyncio.sleep(2)

# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize platform on startup"""
    logger.info("=" * 70)
    logger.info("🚀 AI-Driven Self-Healing Platform v13 Starting...")
    logger.info("=" * 70)
    logger.info("New in v13:")
    logger.info("  • Dynamic active alerts tracking")
    logger.info("  • Auto-resolution of old alerts")
    logger.info("  • Improved health score calculation")
    logger.info("  • Alert lifecycle management")
    logger.info("=" * 70)
    
    # Start automatic metrics generation
    asyncio.create_task(auto_generate_metrics())
    
    logger.info("✅ Platform started successfully!")
    logger.info("📊 Dashboard: http://localhost:8000")
    logger.info("📡 API Docs: http://localhost:8000/docs")
    logger.info("=" * 70)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down platform...")
    
    # Save ML model
    if anomaly_detector.is_trained:
        try:
            anomaly_detector.save_model('data/anomaly_model.pkl')
            logger.info("ML model saved")
        except Exception as e:
            logger.error(f"Error saving model: {e}")

# ============================================================================
# Dashboard HTML
# ============================================================================

def get_dashboard_html():
    """Embedded dashboard HTML with v13 improvements"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>AI Self-Healing Platform v13 - Live Demo</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            color: #f1f5f9;
            padding: 20px;
        }
        .container { max-width: 1600px; margin: 0 auto; }
        header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(30, 41, 59, 0.5);
            border-radius: 12px;
            border: 1px solid rgba(148, 163, 184, 0.1);
        }
        h1 {
            font-size: 2.5rem;
            background: linear-gradient(to right, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        .subtitle { color: #94a3b8; font-size: 1rem; }
        .version-badge {
            display: inline-block;
            padding: 4px 12px;
            background: linear-gradient(135deg, #10b981, #059669);
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 700;
            margin-left: 10px;
            color: white;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: rgba(30, 41, 59, 0.5);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid rgba(148, 163, 184, 0.1);
            transition: transform 0.2s;
        }
        .stat-card:hover {
            transform: translateY(-2px);
            border-color: rgba(148, 163, 184, 0.3);
        }
        .stat-label { color: #94a3b8; font-size: 0.875rem; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
        .stat-value { font-size: 2rem; font-weight: 700; }
        .stat-value.green { color: #10b981; }
        .stat-value.yellow { color: #fbbf24; }
        .stat-value.red { color: #ef4444; }
        .charts {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .chart-container {
            background: rgba(30, 41, 59, 0.5);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid rgba(148, 163, 184, 0.1);
        }
        .chart-title { font-size: 1.25rem; font-weight: 600; margin-bottom: 15px; }
        .alerts {
            background: rgba(30, 41, 59, 0.5);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid rgba(148, 163, 184, 0.1);
            max-height: 400px;
            overflow-y: auto;
        }
        .alert-item, .healing-item {
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 4px solid;
        }
        .alert-item { border-left-color: #f59e0b; background: rgba(251, 146, 60, 0.1); }
        .healing-item { border-left-color: #10b981; background: rgba(16, 185, 129, 0.1); }
        .status {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .status.completed { background: #10b981; color: white; }
        .status.executing { background: #fbbf24; color: #1e293b; animation: pulse 1s infinite; }
        .status.failed { background: #ef4444; color: white; }
        .connection {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 0.875rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            z-index: 1000;
        }
        .connection.connected {
            background: rgba(16, 185, 129, 0.2);
            border: 1px solid #10b981;
            color: #10b981;
        }
        .connection.disconnected {
            background: rgba(239, 68, 68, 0.2);
            border: 1px solid #ef4444;
            color: #ef4444;
        }
        .pulse {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: currentColor;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .no-data {
            color: #64748b;
            text-align: center;
            padding: 20px;
            font-style: italic;
        }
        .success-message {
            color: #10b981;
            text-align: center;
            padding: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
    </style>
</head>
<body>
    <div class="connection" id="connectionStatus">
        <div class="pulse"></div>
        <span>Connecting...</span>
    </div>

    <div class="container">
        <header>
            <h1>🤖 AI Self-Healing Platform<span class="version-badge">v13</span></h1>
            <p class="subtitle">Real-time Observability & Automated Remediation with Dynamic Alert Management</p>
            <div style="margin-top: 15px;">
                <button onclick="forceRefresh()" style="padding: 8px 16px; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">
                    🔄 Refresh Data
                </button>
                <button onclick="checkAPI()" style="padding: 8px 16px; background: #10b981; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; margin-left: 10px;">
                    🔍 Check API
                </button>
                <button onclick="viewActiveAlerts()" style="padding: 8px 16px; background: #f59e0b; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; margin-left: 10px;">
                    ⚠️ View Active Alerts
                </button>
            </div>
        </header>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">System Health</div>
                <div class="stat-value green" id="health">--</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Active Alerts 🆕</div>
                <div class="stat-value yellow" id="alerts">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Healing Actions</div>
                <div class="stat-value" style="color: #60a5fa" id="actions">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">ML Model Status</div>
                <div class="stat-value" style="color: #a78bfa; font-size: 1.2rem" id="mlStatus">Training...</div>
            </div>
        </div>

        <div class="charts">
            <div class="chart-container">
                <div class="chart-title">📊 CPU & Memory Usage</div>
                <canvas id="metricsChart"></canvas>
            </div>
            <div class="chart-container">
                <div class="chart-title">⚡ Response Time & Error Rate</div>
                <canvas id="perfChart"></canvas>
            </div>
        </div>

        <div class="charts">
            <div class="alerts">
                <div class="chart-title">⚠️ Recent Anomalies (Last 10)</div>
                <div id="anomaliesList"><p class="no-data">Waiting for data...</p></div>
            </div>
            <div class="alerts">
                <div class="chart-title">✅ Self-Healing Actions</div>
                <div id="healingList"><p class="no-data">Waiting for data...</p></div>
            </div>
        </div>
    </div>

    <script>
        let metricsChart, perfChart;
        let ws;

        // Initialize charts
        const ctx1 = document.getElementById('metricsChart').getContext('2d');
        metricsChart = new Chart(ctx1, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'CPU %',
                    data: [],
                    borderColor: '#60a5fa',
                    backgroundColor: 'rgba(96, 165, 250, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Memory %',
                    data: [],
                    borderColor: '#a78bfa',
                    backgroundColor: 'rgba(167, 139, 250, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                animation: { duration: 300 },
                plugins: { legend: { labels: { color: '#f1f5f9' } } },
                scales: {
                    y: { beginAtZero: true, max: 100, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148, 163, 184, 0.1)' } },
                    x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148, 163, 184, 0.1)' } }
                }
            }
        });

        const ctx2 = document.getElementById('perfChart').getContext('2d');
        perfChart = new Chart(ctx2, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Response Time (ms)',
                    data: [],
                    borderColor: '#fbbf24',
                    backgroundColor: 'rgba(251, 191, 36, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y'
                }, {
                    label: 'Error Rate %',
                    data: [],
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                animation: { duration: 300 },
                plugins: { legend: { labels: { color: '#f1f5f9' } } },
                scales: {
                    y: { type: 'linear', position: 'left', beginAtZero: true, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148, 163, 184, 0.1)' } },
                    y1: { type: 'linear', position: 'right', beginAtZero: true, max: 15, ticks: { color: '#94a3b8' }, grid: { display: false } },
                    x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148, 163, 184, 0.1)' } }
                }
            }
        });

        // WebSocket connection
        function connectWebSocket() {
            ws = new WebSocket(`ws://${window.location.host}/ws/live`);
            
            ws.onopen = () => {
                console.log('✅ WebSocket connected');
                document.getElementById('connectionStatus').className = 'connection connected';
                document.getElementById('connectionStatus').innerHTML = '<div class="pulse"></div><span>Live</span>';
            };
            
            ws.onclose = () => {
                console.log('❌ WebSocket disconnected');
                document.getElementById('connectionStatus').className = 'connection disconnected';
                document.getElementById('connectionStatus').innerHTML = '<div class="pulse"></div><span>Disconnected</span>';
                setTimeout(connectWebSocket, 3000);
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
            
            ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    console.log('📨 Received:', message.type);
                    
                    if (message.type === 'metric') {
                        updateCharts(message.data);
                    } else if (message.type === 'anomaly' || message.type === 'healing_action') {
                        updateDashboard();
                    }
                } catch (error) {
                    console.error('Error processing message:', error);
                }
            };
        }

        // Update charts
        function updateCharts(metric) {
            const time = new Date(metric.timestamp).toLocaleTimeString();
            
            if (metricsChart.data.labels.length > 20) {
                metricsChart.data.labels.shift();
                metricsChart.data.datasets[0].data.shift();
                metricsChart.data.datasets[1].data.shift();
                perfChart.data.labels.shift();
                perfChart.data.datasets[0].data.shift();
                perfChart.data.datasets[1].data.shift();
            }

            metricsChart.data.labels.push(time);
            metricsChart.data.datasets[0].data.push(metric.cpu_usage);
            metricsChart.data.datasets[1].data.push(metric.memory_usage);
            metricsChart.update('none');

            perfChart.data.labels.push(time);
            perfChart.data.datasets[0].data.push(metric.response_time);
            perfChart.data.datasets[1].data.push(metric.error_rate);
            perfChart.update('none');
        }

        // Fetch data
        async function updateDashboard() {
            try {
                const [status, metrics, anomalies, healing] = await Promise.all([
                    fetch('/api/v1/status').then(r => r.json()),
                    fetch('/api/v1/metrics?limit=20').then(r => r.json()),
                    fetch('/api/v1/anomalies?limit=10').then(r => r.json()),
                    fetch('/api/v1/healing-actions?limit=10').then(r => r.json())
                ]);

                // Update status cards with color coding
                const health = status.health_score;
                const healthEl = document.getElementById('health');
                healthEl.textContent = health.toFixed(0) + '%';
                healthEl.className = 'stat-value ' + (health >= 90 ? 'green' : health >= 70 ? 'yellow' : 'red');
                
                const alertsEl = document.getElementById('alerts');
                alertsEl.textContent = status.active_alerts;
                alertsEl.className = 'stat-value ' + (status.active_alerts === 0 ? 'green' : status.active_alerts < 3 ? 'yellow' : 'red');
                
                document.getElementById('actions').textContent = status.healing_actions_count;
                document.getElementById('mlStatus').textContent = status.ml_model_trained ? '✓ Trained' : 'Training...';

                // Update charts if we have metrics
                if (metrics.length > 0 && !ws) {
                    const labels = metrics.map(m => new Date(m.timestamp).toLocaleTimeString());
                    metricsChart.data.labels = labels;
                    metricsChart.data.datasets[0].data = metrics.map(m => m.cpu_usage);
                    metricsChart.data.datasets[1].data = metrics.map(m => m.memory_usage);
                    metricsChart.update('none');

                    perfChart.data.labels = labels;
                    perfChart.data.datasets[0].data = metrics.map(m => m.response_time);
                    perfChart.data.datasets[1].data = metrics.map(m => m.error_rate);
                    perfChart.update('none');
                }

                // Update anomalies list
                if (anomalies && anomalies.length > 0) {
                    document.getElementById('anomaliesList').innerHTML = anomalies.map(a => `
                        <div class="alert-item">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <strong>${a.severity ? a.severity.toUpperCase() : 'UNKNOWN'}</strong>
                                <span style="font-size: 0.75rem; color: #94a3b8;">${new Date(a.timestamp).toLocaleTimeString()}</span>
                            </div>
                            <div style="font-size: 0.875rem; color: #94a3b8;">
                                Type: ${a.anomaly_type || 'UNKNOWN'}<br>
                                Score: ${a.anomaly_score ? a.anomaly_score.toFixed(3) : a.score ? a.score.toFixed(3) : 'N/A'}<br>
                                ${a.anomaly_id ? `ID: ${a.anomaly_id}<br>` : ''}
                                Status: ${a.status || 'active'}
                            </div>
                        </div>
                    `).join('');
                } else {
                    document.getElementById('anomaliesList').innerHTML = '<p class="success-message">✅ No anomalies detected - System healthy!</p>';
                }

                // Update healing actions list
                if (healing && healing.length > 0) {
                    document.getElementById('healingList').innerHTML = healing.map(h => `
                        <div class="healing-item">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <strong>${h.action_type ? h.action_type.toUpperCase().replace(/_/g, ' ') : 'ACTION'}</strong>
                                <span class="status ${h.status}">${h.status || 'pending'}</span>
                            </div>
                            <div style="font-size: 0.875rem; color: #94a3b8;">
                                Target: ${h.target}<br>
                                ${h.execution_time ? `Time: ${h.execution_time.toFixed(2)}s` : 'Executing...'}
                                ${h.anomaly_id ? `<br>For: ${h.anomaly_id}` : ''}
                            </div>
                        </div>
                    `).join('');
                } else {
                    document.getElementById('healingList').innerHTML = '<p class="no-data">No healing actions taken yet</p>';
                }

            } catch (error) {
                console.error('Error updating dashboard:', error);
            }
        }

        // Initialize
        connectWebSocket();
        setInterval(updateDashboard, 2000);
        updateDashboard();

        // Helper functions
        function forceRefresh() {
            console.log('🔄 Force refreshing...');
            updateDashboard();
        }

        async function checkAPI() {
            console.log('🔍 Checking API...');
            try {
                const [status, anomalies, healing, activeAlerts] = await Promise.all([
                    fetch('/api/v1/status').then(r => r.json()),
                    fetch('/api/v1/anomalies').then(r => r.json()),
                    fetch('/api/v1/healing-actions').then(r => r.json()),
                    fetch('/api/v1/anomalies/active').then(r => r.json())
                ]);
                console.log('📊 Status:', status);
                console.log('⚠️ All Anomalies:', anomalies);
                console.log('🚨 Active Alerts:', activeAlerts);
                console.log('✅ Healing Actions:', healing);
                alert(`System Status:
Health Score: ${status.health_score.toFixed(1)}%
Active Alerts: ${status.active_alerts}
Total Anomalies: ${anomalies.length}
Healing Actions: ${healing.length}

Check browser console for details (F12)`);
            } catch (error) {
                console.error('Error:', error);
                alert('Error checking API. See console for details.');
            }
        }

        async function viewActiveAlerts() {
            try {
                const activeAlerts = await fetch('/api/v1/anomalies/active').then(r => r.json());
                console.log('🚨 Active Alerts:', activeAlerts);
                
                if (activeAlerts.length === 0) {
                    alert('✅ No active alerts! System is healthy.');
                } else {
                    const alertList = activeAlerts.map(a => 
                        `${a.severity.toUpperCase()}: ${a.anomaly_type} (${a.anomaly_id})`
                    ).join('\\n');
                    alert(`Active Alerts (${activeAlerts.length}):
${alertList}

See console for full details (F12)`);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error fetching active alerts. See console for details.');
            }
        }
    </script>
</body>
</html>
    """

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*70)
    print("🚀 AI Self-Healing Platform v13 - Starting...")
    print("="*70)
    print("\n📊 Dashboard: http://localhost:8000")
    print("📡 API Docs: http://localhost:8000/docs")
    print("🔧 Health Check: http://localhost:8000/health")
    print("\n💡 New in v13:")
    print("   • Dynamic active alerts count (no longer hardcoded)")
    print("   • Auto-resolution when healing succeeds")
    print("   • Auto-cleanup of old alerts (>5 minutes)")
    print("   • New endpoint: GET /api/v1/anomalies/active")
    print("   • Improved health score calculation")
    print("   • Alert acknowledgement support")
    print("\n" + "="*70 + "\n")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        log_level="info",
        access_log=True
    )
    