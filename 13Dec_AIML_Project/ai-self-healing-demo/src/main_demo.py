"""
Complete Demo - Main API Server
Save as: src/api/main.py

This is a COMPLETE, WORKING demo for your Dec 30 presentation.
Run with: python src/api/main.py
Access dashboard at: http://localhost:8000
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import json
import logging
from datetime import datetime
import random
import numpy as np
from sklearn.ensemble import IsolationForest
import psutil

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="AI Self-Healing Platform Demo")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
metrics_history = []
anomalies_detected = []
healing_actions = []
active_websockets = []

# ML Model for Anomaly Detection
class AnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.is_trained = False
        self.scaler_mean = None
        self.scaler_std = None
        
    def train(self, data):
        """Train the model with historical data"""
        if len(data) < 20:
            return False
        
        X = np.array(data)
        self.scaler_mean = np.mean(X, axis=0)
        self.scaler_std = np.std(X, axis=0) + 1e-6
        X_scaled = (X - self.scaler_mean) / self.scaler_std
        
        self.model.fit(X_scaled)
        self.is_trained = True
        logger.info("✅ ML model trained successfully")
        return True
    
    def predict(self, metric):
        """Predict if metric is anomalous"""
        if not self.is_trained:
            return None
        
        X = np.array([metric])
        X_scaled = (X - self.scaler_mean) / self.scaler_std
        
        prediction = self.model.predict(X_scaled)[0]
        score = self.model.score_samples(X_scaled)[0]
        
        if prediction == -1:  # Anomaly
            return {
                'is_anomaly': True,
                'score': float(score),
                'severity': 'critical' if score < -0.5 else 'warning'
            }
        return None

# Initialize ML detector
detector = AnomalyDetector()

# Self-Healing Orchestrator
class SelfHealingOrchestrator:
    def __init__(self):
        self.cooldown = {}
        
    def decide_action(self, anomaly, metrics):
        """Decide which healing action to take"""
        anomaly_type = self._identify_anomaly_type(metrics)
        
        # Check cooldown
        if anomaly_type in self.cooldown:
            return None
        
        action = None
        
        if metrics[0] > 80:  # High CPU
            action = {
                'type': 'AUTO_SCALE',
                'target': 'web-service',
                'description': 'Scaling up 2 instances due to high CPU',
                'icon': '🔄'
            }
        elif metrics[1] > 85:  # High Memory
            action = {
                'type': 'AUTO_SCALE',
                'target': 'api-service',
                'description': 'Scaling up 2 instances due to high memory',
                'icon': '🔄'
            }
        elif metrics[2] > 800:  # High Latency
            action = {
                'type': 'ENABLE_CACHE',
                'target': 'api-gateway',
                'description': 'Enabled aggressive caching to reduce latency',
                'icon': '⚡'
            }
        elif metrics[3] > 5:  # High Error Rate
            action = {
                'type': 'TRAFFIC_SHIFT',
                'target': 'healthy-instances',
                'description': 'Redirected traffic to healthy instances',
                'icon': '🔀'
            }
        
        if action:
            self.cooldown[anomaly_type] = True
            asyncio.create_task(self._clear_cooldown(anomaly_type))
        
        return action
    
    def _identify_anomaly_type(self, metrics):
        """Identify which metric is anomalous"""
        thresholds = [80, 85, 800, 5, 50]
        deviations = [abs(m - t) / t for m, t in zip(metrics, thresholds)]
        max_idx = np.argmax(deviations)
        types = ['CPU', 'MEMORY', 'LATENCY', 'ERROR_RATE', 'THROUGHPUT']
        return types[max_idx]
    
    async def _clear_cooldown(self, anomaly_type):
        """Clear cooldown after 60 seconds"""
        await asyncio.sleep(60)
        if anomaly_type in self.cooldown:
            del self.cooldown[anomaly_type]

orchestrator = SelfHealingOrchestrator()

# Metrics Generator (simulates real system)
class MetricsGenerator:
    def __init__(self):
        self.counter = 0
        
    def generate(self):
        """Generate realistic metrics with occasional anomalies"""
        self.counter += 1
        
        # Normal values
        cpu = random.uniform(40, 70)
        memory = random.uniform(50, 75)
        latency = random.uniform(150, 400)
        error_rate = random.uniform(0, 3)
        throughput = random.uniform(80, 150)
        
        # Inject anomaly every ~20 metrics
        if self.counter % random.randint(15, 25) == 0:
            anomaly_type = random.choice(['cpu', 'memory', 'latency', 'error'])
            if anomaly_type == 'cpu':
                cpu = random.uniform(85, 98)
            elif anomaly_type == 'memory':
                memory = random.uniform(85, 95)
            elif anomaly_type == 'latency':
                latency = random.uniform(800, 1500)
            elif anomaly_type == 'error':
                error_rate = random.uniform(5, 15)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_usage': round(cpu, 2),
            'memory_usage': round(memory, 2),
            'response_time': round(latency, 2),
            'error_rate': round(error_rate, 2),
            'requests_per_sec': round(throughput, 2)
        }

generator = MetricsGenerator()

# Pydantic Models
class Metric(BaseModel):
    timestamp: str
    cpu_usage: float
    memory_usage: float
    response_time: float
    error_rate: float
    requests_per_sec: float

class SystemStatus(BaseModel):
    health_score: float
    active_alerts: int
    total_metrics: int
    healing_actions_count: int

# API Endpoints
@app.get("/")
async def root():
    """Serve the dashboard HTML"""
    return HTMLResponse(get_dashboard_html())

@app.get("/api/v1/status", response_model=SystemStatus)
async def get_status():
    """Get system status"""
    recent_anomalies = len([a for a in anomalies_detected[-10:]])
    health_score = max(60, 100 - (recent_anomalies * 5))
    
    return SystemStatus(
        health_score=health_score,
        active_alerts=len(anomalies_detected[-5:]),
        total_metrics=len(metrics_history),
        healing_actions_count=len(healing_actions)
    )

@app.get("/api/v1/metrics")
async def get_metrics(limit: int = 50):
    """Get recent metrics"""
    return metrics_history[-limit:]

@app.get("/api/v1/anomalies")
async def get_anomalies(limit: int = 20):
    """Get detected anomalies"""
    return anomalies_detected[-limit:]

@app.get("/api/v1/healing-actions")
async def get_healing_actions(limit: int = 20):
    """Get healing actions"""
    return healing_actions[-limit:]

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    active_websockets.append(websocket)
    
    try:
        while True:
            await asyncio.sleep(2)  # Send updates every 2 seconds
    except WebSocketDisconnect:
        active_websockets.remove(websocket)

# Background task for continuous monitoring
async def monitoring_loop():
    """Continuously generate metrics and detect anomalies"""
    await asyncio.sleep(2)  # Wait for startup
    
    while True:
        try:
            # Generate new metric
            metric = generator.generate()
            metrics_history.append(metric)
            
            # Keep history manageable
            if len(metrics_history) > 1000:
                metrics_history[:] = metrics_history[-1000:]
            
            # Extract features for ML
            features = [
                metric['cpu_usage'],
                metric['memory_usage'],
                metric['response_time'],
                metric['error_rate'],
                metric['requests_per_sec']
            ]
            
            # Train model after collecting enough data
            if not detector.is_trained and len(metrics_history) >= 20:
                all_features = [
                    [m['cpu_usage'], m['memory_usage'], m['response_time'], 
                     m['error_rate'], m['requests_per_sec']]
                    for m in metrics_history
                ]
                detector.train(all_features)
            
            # Detect anomalies
            if detector.is_trained:
                anomaly = detector.predict(features)
                
                if anomaly:
                    anomaly_record = {
                        'id': len(anomalies_detected) + 1,
                        'timestamp': metric['timestamp'],
                        'severity': anomaly['severity'],
                        'score': anomaly['score'],
                        'metrics': metric
                    }
                    anomalies_detected.append(anomaly_record)
                    logger.info(f"⚠️  Anomaly detected: {anomaly['severity']}")
                    
                    # Trigger self-healing
                    action = orchestrator.decide_action(anomaly, features)
                    if action:
                        action_record = {
                            'id': len(healing_actions) + 1,
                            'timestamp': datetime.now().isoformat(),
                            'status': 'executing',
                            **action
                        }
                        healing_actions.append(action_record)
                        logger.info(f"✅ Healing action: {action['type']}")
                        
                        # Simulate action completion
                        await asyncio.sleep(3)
                        action_record['status'] = 'completed'
            
            # Broadcast to WebSocket clients
            for ws in active_websockets:
                try:
                    await ws.send_json({
                        'type': 'update',
                        'metric': metric,
                        'health': (await get_status()).dict()
                    })
                except:
                    pass
            
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            await asyncio.sleep(2)

@app.on_event("startup")
async def startup_event():
    """Start background monitoring"""
    asyncio.create_task(monitoring_loop())
    logger.info("🚀 AI Self-Healing Platform started!")
    logger.info("📊 Dashboard: http://localhost:8000")

def get_dashboard_html():
    """Complete embedded dashboard HTML"""
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
        .container { max-width: 1400px; margin: 0 auto; }
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
        .stat-value { font-size: 2rem; font-weight: 700; color: #10b981; }
        .charts {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
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
        .alert-item {
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 4px solid #f59e0b;
            background: rgba(251, 146, 60, 0.1);
        }
        .healing-item {
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 4px solid #10b981;
            background: rgba(16, 185, 129, 0.1);
        }
        .status { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
        .status.completed { background: #10b981; color: white; }
        .status.executing { background: #fbbf24; color: #1e293b; }
        .connection { position: fixed; top: 20px; right: 20px; padding: 8px 16px; border-radius: 8px; font-size: 0.875rem; font-weight: 600; background: rgba(16, 185, 129, 0.2); border: 1px solid #10b981; color: #10b981; }
        .pulse { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: currentColor; margin-right: 8px; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
    </style>
</head>
<body>
    <div class="connection"><div class="pulse"></div>Live</div>
    <div class="container">
        <header>
            <h1>AI Self-Healing Platform</h1>
            <p style="color: #94a3b8;">Real-time Monitoring & Automated Remediation Demo</p>
        </header>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">System Health</div>
                <div class="stat-value" id="health">--</div>
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
                <div class="stat-label">Total Metrics</div>
                <div class="stat-value" style="color: #a78bfa" id="metrics">0</div>
            </div>
        </div>

        <div class="charts">
            <div class="chart-container">
                <div class="chart-title">📊 CPU & Memory Usage</div>
                <canvas id="metricsChart"></canvas>
            </div>
            <div class="chart-container">
                <div class="chart-title">⚡ Response Time & Errors</div>
                <canvas id="perfChart"></canvas>
            </div>
        </div>

        <div class="charts">
            <div class="alerts">
                <div class="chart-title">⚠️ Detected Anomalies</div>
                <div id="anomaliesList"></div>
            </div>
            <div class="alerts">
                <div class="chart-title">✅ Self-Healing Actions</div>
                <div id="healingList"></div>
            </div>
        </div>
    </div>

    <script>
        let metricsChart, perfChart;
        
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

        // Fetch data
        async function updateDashboard() {
            try {
                const [status, metrics, anomalies, healing] = await Promise.all([
                    fetch('/api/v1/status').then(r => r.json()),
                    fetch('/api/v1/metrics?limit=20').then(r => r.json()),
                    fetch('/api/v1/anomalies?limit=5').then(r => r.json()),
                    fetch('/api/v1/healing-actions?limit=5').then(r => r.json())
                ]);

                document.getElementById('health').textContent = status.health_score.toFixed(0) + '%';
                document.getElementById('alerts').textContent = status.active_alerts;
                document.getElementById('actions').textContent = status.healing_actions_count;
                document.getElementById('metrics').textContent = status.total_metrics;

                if (metrics.length > 0) {
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

                document.getElementById('anomaliesList').innerHTML = anomalies.length ? 
                    anomalies.map(a => `<div class="alert-item"><strong>${a.severity.toUpperCase()}</strong> - ${new Date(a.timestamp).toLocaleTimeString()}<br>CPU: ${a.metrics.cpu_usage}%, Memory: ${a.metrics.memory_usage}%, Latency: ${a.metrics.response_time}ms</div>`).join('') :
                    '<p style="color: #64748b; text-align: center; padding: 20px;">No anomalies detected</p>';

                document.getElementById('healingList').innerHTML = healing.length ?
                    healing.map(h => `<div class="healing-item"><div style="display: flex; justify-content: space-between;"><span>${h.icon} ${h.type}</span><span class="status ${h.status}">${h.status}</span></div><div style="font-size: 0.875rem; color: #94a3b8; margin-top: 5px;">${h.description}</div></div>`).join('') :
                    '<p style="color: #64748b; text-align: center; padding: 20px;">No actions taken</p>';

            } catch (error) {
                console.error('Error updating dashboard:', error);
            }
        }

        // Update every 2 seconds
        setInterval(updateDashboard, 2000);
        updateDashboard();
    </script>
</body>
</html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    