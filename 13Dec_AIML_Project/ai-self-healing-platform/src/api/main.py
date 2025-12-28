"""
Main API Server - Complete Integration of All Components
Save as: src/api/main.py

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

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Ensure logs directory exists
Path('logs').mkdir(exist_ok=True)

# Setup logging with UTF-8 encoding for Windows compatibility
import sys
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

# FastAPI app
app = FastAPI(
    title="AI-Driven Self-Healing Platform",
    description="Intelligent observability and automated remediation for cloud workloads",
    version="1.0.0"
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

# In-memory storage
metrics_history = []
anomalies_detected = []
healing_actions_taken = []
active_websockets = []

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

class HealingActionResponse(BaseModel):
    action_id: str
    timestamp: str
    action_type: str
    target: str
    status: str
    execution_time: Optional[float] = None

# API Endpoints

@app.get("/")
async def root():
    """Serve embedded dashboard"""
    return HTMLResponse(get_dashboard_html())

@app.get("/api/v1/status", response_model=SystemStatus)
async def get_system_status():
    """Get overall system status"""
    recent_anomalies = len([a for a in anomalies_detected[-10:]])
    health_score = max(60, min(100, 100 - (recent_anomalies * 5)))
    
    return SystemStatus(
        health_score=health_score,
        active_alerts=len([a for a in anomalies_detected[-5:]]),
        total_metrics=len(metrics_history),
        healing_actions_count=len(healing_actions_taken),
        ml_model_trained=anomaly_detector.is_trained,
        uptime_seconds=0  # Would track actual uptime
    )

@app.get("/api/v1/metrics")
async def get_metrics(limit: int = 50):
    """Get recent metrics"""
    return metrics_history[-limit:]

@app.post("/api/v1/metrics")
async def ingest_metrics(metric: Metric, background_tasks: BackgroundTasks):
    """Ingest new metrics and trigger anomaly detection"""
    metric_dict = metric.dict()
    metrics_history.append(metric_dict)
    
    # Keep history manageable
    if len(metrics_history) > 1000:
        metrics_history[:] = metrics_history[-1000:]
    
    # Trigger anomaly detection in background
    background_tasks.add_task(process_metric, metric_dict)
    
    return {"status": "accepted", "timestamp": metric.timestamp}

@app.get("/api/v1/anomalies")
async def get_anomalies(limit: int = 20):
    """Get detected anomalies"""
    return anomalies_detected[-limit:]

@app.get("/api/v1/healing-actions")
async def get_healing_actions(limit: int = 20):
    """Get healing actions history"""
    return healing_actions_taken[-limit:]

@app.get("/api/v1/predictions")
async def get_predictions():
    """Get performance predictions"""
    if len(metrics_history) < 10:
        return {"predictions": None, "message": "Insufficient data"}
    
    predictions = performance_predictor.predict_resource_exhaustion(metrics_history[-20:])
    return predictions

@app.get("/api/v1/orchestrator/stats")
async def get_orchestrator_stats():
    """Get orchestrator statistics"""
    return healing_orchestrator.get_statistics()

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

# Background processing

async def process_metric(metric: Dict):
    """Process metric for anomaly detection and healing"""
    try:
        # Add to ML detector
        anomaly_detector.add_metrics(metric)
        
        # Detect anomalies
        if anomaly_detector.is_trained:
            anomaly = anomaly_detector.detect_anomaly(metric)
            
            if anomaly:
                # Store anomaly with proper structure
                anomaly_record = {
                    'id': len(anomalies_detected) + 1,
                    'timestamp': anomaly.get('timestamp', datetime.now().isoformat()),
                    'anomaly_type': anomaly.get('anomaly_type', 'UNKNOWN'),
                    'severity': anomaly.get('severity', 'warning'),
                    'anomaly_score': anomaly.get('anomaly_score', 0.0),
                    'score': anomaly.get('anomaly_score', 0.0),  # Duplicate for compatibility
                    'confidence': anomaly.get('confidence', 0.0),
                    'metrics': anomaly.get('metrics', metric)
                }
                anomalies_detected.append(anomaly_record)
                
                logger.warning(f"[ANOMALY] Anomaly #{len(anomalies_detected)} detected: {anomaly['anomaly_type']} (severity: {anomaly['severity']})")
                
                # Trigger self-healing
                action = healing_orchestrator.decide_action(anomaly)
                if action:
                    # Execute healing action
                    success = await healing_orchestrator.execute_action(action)
                    
                    action_record = action.to_dict()
                    healing_actions_taken.append(action_record)
                    
                    logger.info(f"[HEALING] Healing action #{len(healing_actions_taken)} executed: {action.action_type.value} (success: {success})")
                    
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

# Automatic metrics generation for demo
async def auto_generate_metrics():
    """Automatically generate metrics for demonstration"""
    logger.info("Starting automatic metrics generation...")
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
                logger.info(f"[ANOMALY INJECTION] Injecting {anomaly_type} anomaly...")
                
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

@app.on_event("startup")
async def startup_event():
    """Initialize platform on startup"""
    logger.info("=" * 60)
    logger.info("AI-Driven Self-Healing Platform Starting...")
    logger.info("=" * 60)
    
    # Start automatic metrics generation
    asyncio.create_task(auto_generate_metrics())
    
    logger.info("Platform started successfully!")
    logger.info("Dashboard: http://localhost:8000")
    logger.info("API Docs: http://localhost:8000/docs")
    logger.info("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down platform...")
    
    # Save ML model
    if anomaly_detector.is_trained:
        anomaly_detector.save_model('data/anomaly_model.pkl')
        logger.info("ML model saved")

def get_dashboard_html():
    """Embedded dashboard HTML"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>AI Self-Healing Platform - Live Demo</title>
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
        }
        .stat-label { color: #94a3b8; font-size: 0.875rem; margin-bottom: 8px; }
        .stat-value { font-size: 2rem; font-weight: 700; }
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
    </style>
</head>
<body>
    <div class="connection" id="connectionStatus">
        <div class="pulse"></div>
        <span>Connecting...</span>
    </div>

    <div class="container">
        <header>
            <h1>🤖 AI Self-Healing Platform</h1>
            <p class="subtitle">Real-time Observability & Automated Remediation Demo</p>
            <div style="margin-top: 15px;">
                <button onclick="forceRefresh()" style="padding: 8px 16px; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">
                    🔄 Refresh Data
                </button>
                <button onclick="checkAPI()" style="padding: 8px 16px; background: #10b981; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; margin-left: 10px;">
                    🔍 Check API
                </button>
            </div>
        </header>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">System Health</div>
                <div class="stat-value" style="color: #10b981" id="health">--</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Active Alerts</div>
                <div class="stat-value" style="color: #f59e0b" id="alerts">0</div>
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
                <div class="chart-title">⚠️ Detected Anomalies</div>
                <div id="anomaliesList"><p style="color: #64748b; text-align: center; padding: 20px;">No anomalies detected</p></div>
            </div>
            <div class="alerts">
                <div class="chart-title">✅ Self-Healing Actions</div>
                <div id="healingList"><p style="color: #64748b; text-align: center; padding: 20px;">No actions taken</p></div>
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
                    console.log('📨 Received:', message.type, message.data);
                    
                    if (message.type === 'metric') {
                        updateCharts(message.data);
                    } else if (message.type === 'anomaly') {
                        console.log('⚠️ Anomaly detected!', message.data);
                        // Force refresh the dashboard
                        updateDashboard();
                    } else if (message.type === 'healing_action') {
                        console.log('✅ Healing action!', message.data);
                        // Force refresh the dashboard
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

                // Update status cards
                document.getElementById('health').textContent = status.health_score.toFixed(0) + '%';
                document.getElementById('alerts').textContent = status.active_alerts;
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
                                Score: ${a.anomaly_score ? a.anomaly_score.toFixed(3) : a.score ? a.score.toFixed(3) : 'N/A'}
                            </div>
                        </div>
                    `).join('');
                } else {
                    document.getElementById('anomaliesList').innerHTML = '<p style="color: #64748b; text-align: center; padding: 20px;">No anomalies detected yet...</p>';
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
                            </div>
                        </div>
                    `).join('');
                } else {
                    document.getElementById('healingList').innerHTML = '<p style="color: #64748b; text-align: center; padding: 20px;">No healing actions taken yet...</p>';
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
                const [anomalies, healing] = await Promise.all([
                    fetch('/api/v1/anomalies').then(r => r.json()),
                    fetch('/api/v1/healing-actions').then(r => r.json())
                ]);
                console.log('📊 Anomalies:', anomalies);
                console.log('✅ Healing Actions:', healing);
                alert(`Anomalies: ${anomalies.length}\nHealing Actions: ${healing.length}\n\nCheck browser console for details (F12)`);
            } catch (error) {
                console.error('Error:', error);
                alert('Error checking API. See console for details.');
            }
        }
    </script>
</body>
</html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    