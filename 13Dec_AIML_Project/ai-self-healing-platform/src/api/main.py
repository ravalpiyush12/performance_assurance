"""
Main API Server - Production Ready with Prometheus & Kubernetes Integration (Version 17)
Save as: src/api/main.py

MODES:
- PRODUCTION: Pulls REAL metrics from Prometheus, controls Kubernetes
- DEVELOPMENT: Auto-generated metrics for testing/demo (no external dependencies)

NEW in v17:
- Prometheus integration for REAL metrics
- Kubernetes API integration for REAL scaling
- Monitor external applications (like sample_app.py)
- Trigger actual HPA scaling based on anomalies

Usage:
  Development: python -m uvicorn src.api.main:app --reload --port 8000
  Production:  MODE=production PROMETHEUS_URL=http://prometheus:9090 python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
  
Environment Variables:
  MODE: "production" or "development" (default: development)
  PROMETHEUS_URL: Prometheus server URL (default: http://localhost:9090)
  KUBERNETES_ENABLED: Enable K8s API calls (default: false)
  TARGET_APP: Application to monitor (default: sample-app)
  TARGET_NAMESPACE: K8s namespace (default: default)
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import asyncio
import json
import logging
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path
from collections import deque
import random

# =============================================================================
# ENVIRONMENT CONFIGURATION
# =============================================================================

APP_MODE = os.getenv("MODE", "development").lower()
if APP_MODE in ["dev", "development"]:
    APP_MODE = "development"
elif APP_MODE in ["prod", "production"]:
    APP_MODE = "production"
else:
    print(f"❌ Invalid MODE: {APP_MODE}")
    sys.exit(1)

# Prometheus configuration
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
PROMETHEUS_ENABLED = os.getenv("PROMETHEUS_ENABLED", "false").lower() == "true"

# Kubernetes configuration
KUBERNETES_ENABLED = os.getenv("KUBERNETES_ENABLED", "false").lower() == "true"
TARGET_APP = os.getenv("TARGET_APP", "sample-app")
TARGET_NAMESPACE = os.getenv("TARGET_NAMESPACE", "default")

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# Auto-generation settings (development mode only)
AUTO_GENERATE_INTERVAL = int(os.getenv("AUTO_GENERATE_INTERVAL", "2"))
AUTO_ANOMALY_MIN = int(os.getenv("AUTO_ANOMALY_MIN", "25"))
AUTO_ANOMALY_MAX = int(os.getenv("AUTO_ANOMALY_MAX", "35"))

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
Path('logs').mkdir(exist_ok=True)

# Windows UTF-8 fix
if sys.platform == 'win32':
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

# Import core modules
try:
    from src.ml.anomaly_detector import AnomalyDetector, PerformancePredictor
    from src.orchestrator.self_healing import SelfHealingOrchestrator, CloudProvider
    logger.info("✅ Core modules imported")
except ImportError as e:
    logger.error(f"❌ Core import error: {e}")
    sys.exit(1)

# Define User class
class User(BaseModel):
    username: str
    email: str
    role: str = "user"
    disabled: bool = False

# Import Package 1 modules
PACKAGE1_AVAILABLE = False
try:
    from src.monitoring.collector import MetricsCollector, ApplicationMetricsCollector
    from src.security.input_validation import InputValidator
    from src.optimization.caching import CacheManager, MetricsCache
    from src.optimization.query_optimization import get_query_monitor
    
    try:
        from src.security.authentication import create_access_token, verify_token
    except ImportError:
        import jwt
        SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
        ALGORITHM = "HS256"
        
        def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
            to_encode = data.copy()
            expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
            to_encode.update({"exp": expire})
            return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        def verify_token(token: str):
            try:
                return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            except jwt.PyJWTError:
                raise HTTPException(status_code=401, detail="Invalid token")
    
    logger.info("✅ Package 1 modules imported")
    PACKAGE1_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️  Package 1 modules not available: {e}")
    PACKAGE1_AVAILABLE = False

# =============================================================================
# PROMETHEUS CLIENT
# =============================================================================

prometheus_client = None
if PROMETHEUS_ENABLED and APP_MODE == "production":
    try:
        from prometheus_api_client import PrometheusConnect
        prometheus_client = PrometheusConnect(url=PROMETHEUS_URL, disable_ssl=True)
        # Test connection
        prometheus_client.check_prometheus_connection()
        logger.info(f"✅ Prometheus connected ({PROMETHEUS_URL})")
    except Exception as e:
        logger.warning(f"⚠️  Prometheus not available: {e}")
        prometheus_client = None

# =============================================================================
# KUBERNETES CLIENT
# =============================================================================

kubernetes_client = None
if KUBERNETES_ENABLED:
    try:
        from kubernetes import client, config
        
        # Try in-cluster config first, then local kubeconfig
        try:
            config.load_incluster_config()
            logger.info("✅ Kubernetes in-cluster config loaded")
        except:
            config.load_kube_config()
            logger.info("✅ Kubernetes local config loaded")
        
        kubernetes_client = client.AppsV1Api()
        logger.info(f"✅ Kubernetes client initialized (target: {TARGET_APP})")
    except Exception as e:
        logger.warning(f"⚠️  Kubernetes client not available: {e}")
        kubernetes_client = None

# =============================================================================
# REDIS
# =============================================================================

redis_client = None
REDIS_AVAILABLE = False
if PACKAGE1_AVAILABLE:
    try:
        import redis
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=0,
            decode_responses=True,
            socket_timeout=5
        )
        redis_client.ping()
        logger.info(f"✅ Redis connected ({REDIS_HOST}:{REDIS_PORT})")
        REDIS_AVAILABLE = True
    except Exception as e:
        logger.warning(f"⚠️  Redis not available: {e}")
        REDIS_AVAILABLE = False

# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(
    title=f"AI-Driven Self-Healing Platform v17 ({APP_MODE.upper()})",
    description=f"Production-ready with Prometheus & Kubernetes integration",
    version="17.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)

# Initialize components
anomaly_detector = AnomalyDetector(contamination=0.1, window_size=100)
performance_predictor = PerformancePredictor()
healing_orchestrator = SelfHealingOrchestrator(cloud_provider=CloudProvider.LOCAL)

if PACKAGE1_AVAILABLE:
    cache_manager = CacheManager(redis_client=redis_client, default_ttl=300)
    metrics_cache = MetricsCache(cache_manager)
    metrics_collector = MetricsCollector(collection_interval=5)
    app_metrics = ApplicationMetricsCollector()
    input_validator = InputValidator()
    query_monitor = get_query_monitor()
else:
    cache_manager = None
    app_metrics = None
    metrics_collector = None

# Storage
metrics_history = deque(maxlen=1000)
anomalies_detected = deque(maxlen=200)
healing_actions_taken = deque(maxlen=200)
active_websockets = []
startup_time = datetime.now()
active_alerts = {}
successful_healings_count = 0
last_healing_timestamp = None

# Background tasks
auto_metrics_task = None
prometheus_metrics_task = None
metrics_collection_task = None

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class MetricInput(BaseModel):
    timestamp: str
    cpu_usage: float = Field(..., ge=0, le=100)
    memory_usage: float = Field(..., ge=0, le=100)
    response_time: float = Field(..., ge=0)
    error_rate: float = Field(..., ge=0)
    requests_per_sec: float = Field(..., ge=0)
    disk_io: Optional[float] = 1000.0
    network_throughput: Optional[float] = 500.0

class LoginRequest(BaseModel):
    username: str
    password: str

class SystemStatus(BaseModel):
    health_score: float
    active_alerts: int
    total_metrics: int
    healing_actions_count: int
    ml_model_trained: bool
    uptime_seconds: float
    cache_enabled: bool = False
    redis_available: bool = False
    mode: str = "development"
    auto_metrics: bool = False
    prometheus_enabled: bool = False
    kubernetes_enabled: bool = False
    target_app: Optional[str] = None

# =============================================================================
# PROMETHEUS INTEGRATION
# =============================================================================

async def collect_metrics_from_prometheus():
    """
    Collect REAL metrics from Prometheus (PRODUCTION mode)
    Monitors target application (e.g., sample-app)
    """
    if not prometheus_client:
        logger.error("Prometheus client not available")
        return
    
    logger.info(f"🔍 Starting Prometheus metrics collection for {TARGET_APP}")
    
    while True:
        try:
            # Query CPU usage
            cpu_query = f'avg(rate(container_cpu_usage_seconds_total{{pod=~"{TARGET_APP}-.*",namespace="{TARGET_NAMESPACE}"}}[1m])) * 100'
            cpu_result = prometheus_client.custom_query(query=cpu_query)
            
            # Query Memory usage
            mem_query = f'avg(container_memory_working_set_bytes{{pod=~"{TARGET_APP}-.*",namespace="{TARGET_NAMESPACE}"}} / container_spec_memory_limit_bytes{{pod=~"{TARGET_APP}-.*",namespace="{TARGET_NAMESPACE}"}}) * 100'
            mem_result = prometheus_client.custom_query(query=mem_query)
            
            # Query HTTP request duration (from Prometheus metrics)
            latency_query = f'avg(rate(http_request_duration_seconds_sum{{job="{TARGET_APP}"}}[1m]) / rate(http_request_duration_seconds_count{{job="{TARGET_APP}"}}[1m])) * 1000'
            latency_result = prometheus_client.custom_query(query=latency_query)
            
            # Query HTTP error rate
            error_query = f'sum(rate(http_requests_total{{job="{TARGET_APP}",status=~"5.."}}[1m])) / sum(rate(http_requests_total{{job="{TARGET_APP}"}}[1m])) * 100'
            error_result = prometheus_client.custom_query(query=error_query)
            
            # Query request rate
            req_rate_query = f'sum(rate(http_requests_total{{job="{TARGET_APP}"}}[1m]))'
            req_rate_result = prometheus_client.custom_query(query=req_rate_query)
            
            # Extract values (handle empty results)
            cpu_usage = float(cpu_result[0]['value'][1]) if cpu_result else 0.0
            memory_usage = float(mem_result[0]['value'][1]) if mem_result else 0.0
            response_time = float(latency_result[0]['value'][1]) if latency_result else 0.0
            error_rate = float(error_result[0]['value'][1]) if error_result else 0.0
            requests_per_sec = float(req_rate_result[0]['value'][1]) if req_rate_result else 0.0
            
            # Create metric
            metric = {
                'timestamp': datetime.now().isoformat(),
                'cpu_usage': round(cpu_usage, 2),
                'memory_usage': round(memory_usage, 2),
                'response_time': round(response_time, 2),
                'error_rate': round(error_rate, 2),
                'requests_per_sec': round(requests_per_sec, 2),
                'disk_io': 1000.0,  # Not available from basic metrics
                'network_throughput': 500.0,  # Not available from basic metrics
                'source': 'prometheus'
            }
            
            # Process metric
            await process_metric(metric)
            metrics_history.append(metric)
            
            logger.info(
                f"📊 Prometheus → CPU={cpu_usage:.1f}% Memory={memory_usage:.1f}% "
                f"Latency={response_time:.0f}ms Errors={error_rate:.1f}% "
                f"RPS={requests_per_sec:.0f}"
            )
            
            await asyncio.sleep(15)  # Collect every 15 seconds
            
        except Exception as e:
            logger.error(f"Error collecting Prometheus metrics: {e}")
            await asyncio.sleep(15)

# =============================================================================
# KUBERNETES INTEGRATION
# =============================================================================

async def scale_deployment(deployment_name: str, namespace: str, replicas: int) -> bool:
    """
    Scale a Kubernetes deployment
    """
    if not kubernetes_client:
        logger.warning("Kubernetes client not available")
        return False
    
    try:
        # Get current deployment
        deployment = kubernetes_client.read_namespaced_deployment(
            name=deployment_name,
            namespace=namespace
        )
        
        current_replicas = deployment.spec.replicas
        
        if current_replicas == replicas:
            logger.info(f"Deployment {deployment_name} already at {replicas} replicas")
            return True
        
        # Update replicas
        deployment.spec.replicas = replicas
        
        # Patch deployment
        kubernetes_client.patch_namespaced_deployment(
            name=deployment_name,
            namespace=namespace,
            body=deployment
        )
        
        logger.info(
            f"✅ Scaled {deployment_name} from {current_replicas} → {replicas} replicas"
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Error scaling deployment: {e}")
        return False

async def get_deployment_info(deployment_name: str, namespace: str) -> Optional[Dict]:
    """
    Get deployment information
    """
    if not kubernetes_client:
        return None
    
    try:
        deployment = kubernetes_client.read_namespaced_deployment(
            name=deployment_name,
            namespace=namespace
        )
        
        return {
            'name': deployment.metadata.name,
            'namespace': deployment.metadata.namespace,
            'replicas': deployment.spec.replicas,
            'ready_replicas': deployment.status.ready_replicas or 0,
            'available_replicas': deployment.status.available_replicas or 0,
            'updated_replicas': deployment.status.updated_replicas or 0
        }
    except Exception as e:
        logger.error(f"Error getting deployment info: {e}")
        return None

# =============================================================================
# ALERT MANAGEMENT & HEALTH SCORE
# =============================================================================

def generate_anomaly_id() -> str:
    return f"anomaly_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"

def add_active_alert(anomaly_id: str, anomaly_data: dict):
    active_alerts[anomaly_id] = {
        **anomaly_data,
        'anomaly_id': anomaly_id,
        'status': 'active',
        'created_at': datetime.now().isoformat()
    }

def resolve_alert(anomaly_id: str):
    global successful_healings_count, last_healing_timestamp
    if anomaly_id in active_alerts:
        del active_alerts[anomaly_id]
        successful_healings_count += 1
        last_healing_timestamp = datetime.now()

def auto_resolve_old_alerts():
    now = datetime.now()
    to_remove = []
    for anomaly_id, alert in active_alerts.items():
        created_at = datetime.fromisoformat(alert['created_at'])
        if (now - created_at).total_seconds() > 300:
            to_remove.append(anomaly_id)
    for anomaly_id in to_remove:
        resolve_alert(anomaly_id)

def calculate_health_score() -> float:
    global successful_healings_count, last_healing_timestamp
    
    if len(metrics_history) == 0:
        return 100.0
    
    latest_metric = list(metrics_history)[-1]
    health = 100.0
    
    cpu = latest_metric['cpu_usage']
    memory = latest_metric['memory_usage']
    error_rate = latest_metric['error_rate']
    response_time = latest_metric['response_time']
    
    if cpu > 85:
        health -= (cpu - 85) * 0.3
    if memory > 90:
        health -= (memory - 90) * 0.3
    if error_rate > 5:
        health -= (error_rate - 5) * 2
    if response_time > 1000:
        health -= (response_time - 1000) * 0.01
    
    active_alert_count = len(active_alerts)
    if active_alert_count > 0:
        health -= active_alert_count * 1
    
    if successful_healings_count > 0:
        recovery_bonus = min(10, successful_healings_count * 0.5)
        health += recovery_bonus
    
    if last_healing_timestamp:
        time_since_healing = (datetime.now() - last_healing_timestamp).total_seconds()
        if time_since_healing < 60:
            recent_healing_bonus = (60 - time_since_healing) / 6
            health += recent_healing_bonus
    
    if active_alert_count == 0:
        health += 5
    
    return max(0.0, min(100.0, round(health, 1)))

# =============================================================================
# AUTHENTICATION
# =============================================================================

def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[User]:
    if not PACKAGE1_AVAILABLE or not credentials:
        return None
    try:
        token = credentials.credentials
        payload = verify_token(token)
        return User(
            username=payload.get("sub"),
            email=f"{payload.get('sub')}@example.com",
            role=payload.get("role", "user")
        )
    except:
        return None

def get_current_user_required(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    if not PACKAGE1_AVAILABLE:
        return User(username="anonymous", email="anon@example.com", role="user")
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        token = credentials.credentials
        payload = verify_token(token)
        return User(
            username=payload.get("sub"),
            email=f"{payload.get('sub')}@example.com",
            role=payload.get("role", "user")
        )
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

# =============================================================================
# PUBLIC ENDPOINTS
# =============================================================================
"""
FIXED DASHBOARD WITH PROPER CHART SIZING
Replace the @app.get("/") endpoint with this
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    """Interactive Dashboard - Fixed Chart Sizing"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Self-Healing Platform v17</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .pulse-dot {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .chart-container {
            position: relative;
            height: 300px;
            width: 100%;
        }
        .scrollable {
            scrollbar-width: thin;
            scrollbar-color: rgba(139, 92, 246, 0.3) transparent;
        }
        .scrollable::-webkit-scrollbar {
            width: 6px;
        }
        .scrollable::-webkit-scrollbar-track {
            background: transparent;
        }
        .scrollable::-webkit-scrollbar-thumb {
            background: rgba(139, 92, 246, 0.3);
            border-radius: 3px;
        }
    </style>
</head>
<body class="bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
    <div class="min-h-screen p-6">
        <!-- Header -->
        <div class="mb-6">
            <div class="flex items-center justify-between flex-wrap gap-4">
                <div>
                    <h1 class="text-3xl md:text-4xl font-bold text-white mb-2">
                        🌥️ AI Self-Healing Platform v17
                    </h1>
                    <p class="text-purple-300 text-sm md:text-base">Real-time Monitoring & Autonomous Remediation</p>
                </div>
                <div class="flex items-center gap-4">
                    <div id="connection-status" class="flex items-center gap-2 px-4 py-2 rounded-lg bg-gray-500/20 text-gray-400">
                        <div class="w-2 h-2 rounded-full bg-gray-400"></div>
                        <span class="text-sm">Connecting...</span>
                    </div>
                    <div class="text-right">
                        <div class="text-xs text-purple-300">Mode</div>
                        <div id="mode-indicator" class="text-sm font-bold text-white uppercase">--</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Status Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 mb-6">
            <div class="stat-card rounded-xl p-4 md:p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-purple-300 text-xs md:text-sm">Health Score</p>
                        <p id="health-score" class="text-2xl md:text-3xl font-bold text-white">--</p>
                    </div>
                    <div class="text-2xl md:text-4xl">📊</div>
                </div>
            </div>

            <div class="stat-card rounded-xl p-4 md:p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-purple-300 text-xs md:text-sm">Active Alerts</p>
                        <p id="active-alerts" class="text-2xl md:text-3xl font-bold text-white">--</p>
                    </div>
                    <div class="text-2xl md:text-4xl">⚠️</div>
                </div>
            </div>

            <div class="stat-card rounded-xl p-4 md:p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-purple-300 text-xs md:text-sm">Healing Actions</p>
                        <p id="healing-actions" class="text-2xl md:text-3xl font-bold text-white">--</p>
                    </div>
                    <div class="text-2xl md:text-4xl">⚡</div>
                </div>
            </div>

            <div class="stat-card rounded-xl p-4 md:p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-purple-300 text-xs md:text-sm">Total Metrics</p>
                        <p id="total-metrics" class="text-2xl md:text-3xl font-bold text-white">--</p>
                    </div>
                    <div class="text-2xl md:text-4xl">📈</div>
                </div>
            </div>
        </div>

        <!-- Integration Status -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-4 mb-6">
            <div id="prometheus-status" class="rounded-xl p-3 md:p-4 border bg-gray-500/10 border-gray-500/30">
                <div class="flex items-center gap-3">
                    <span class="text-xl md:text-2xl">🖥️</span>
                    <div>
                        <p class="text-xs text-purple-300">Prometheus</p>
                        <p class="text-sm font-bold text-white">Checking...</p>
                    </div>
                </div>
            </div>

            <div id="kubernetes-status" class="rounded-xl p-3 md:p-4 border bg-gray-500/10 border-gray-500/30">
                <div class="flex items-center gap-3">
                    <span class="text-xl md:text-2xl">☸️</span>
                    <div>
                        <p class="text-xs text-purple-300">Kubernetes</p>
                        <p class="text-sm font-bold text-white">Checking...</p>
                    </div>
                </div>
            </div>

            <div id="redis-status" class="rounded-xl p-3 md:p-4 border bg-gray-500/10 border-gray-500/30">
                <div class="flex items-center gap-3">
                    <span class="text-xl md:text-2xl">💾</span>
                    <div>
                        <p class="text-xs text-purple-300">Cache</p>
                        <p class="text-sm font-bold text-white">Checking...</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6 mb-6">
            <div class="stat-card rounded-xl p-4 md:p-6">
                <h3 class="text-lg md:text-xl font-bold text-white mb-4">CPU & Memory Usage</h3>
                <div class="chart-container">
                    <canvas id="cpuMemoryChart"></canvas>
                </div>
            </div>

            <div class="stat-card rounded-xl p-4 md:p-6">
                <h3 class="text-lg md:text-xl font-bold text-white mb-4">Response Time & Error Rate</h3>
                <div class="chart-container">
                    <canvas id="latencyErrorChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Anomalies & Healing Actions -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
            <div class="stat-card rounded-xl p-4 md:p-6">
                <h3 class="text-lg md:text-xl font-bold text-white mb-4">Recent Anomalies</h3>
                <div id="anomalies-list" class="space-y-3 max-h-80 overflow-y-auto scrollable">
                    <p class="text-purple-300 text-center py-8 text-sm">Loading...</p>
                </div>
            </div>

            <div class="stat-card rounded-xl p-4 md:p-6">
                <h3 class="text-lg md:text-xl font-bold text-white mb-4">Self-Healing Actions</h3>
                <div id="healing-list" class="space-y-3 max-h-80 overflow-y-auto scrollable">
                    <p class="text-purple-300 text-center py-8 text-sm">Loading...</p>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="mt-6 text-center text-purple-300 text-xs md:text-sm">
            <p>AI-Driven Self-Healing Platform | Real-time Monitoring & Autonomous Remediation</p>
            <p class="mt-1">Powered by Machine Learning & Kubernetes Auto-scaling</p>
        </div>
    </div>

    <script>
        // Configuration
        const API_BASE = window.location.origin;
        let cpuMemoryChart, latencyErrorChart;

        // Initialize Charts with proper sizing
        function initCharts() {
            const commonConfig = {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        labels: { 
                            color: '#ffffff',
                            font: { size: 11 }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(30, 27, 75, 0.9)',
                        titleColor: '#a78bfa',
                        bodyColor: '#ffffff',
                        borderColor: '#a78bfa',
                        borderWidth: 1
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { 
                            color: 'rgba(255, 255, 255, 0.1)',
                            drawBorder: false
                        },
                        ticks: { 
                            color: '#a78bfa',
                            font: { size: 10 }
                        }
                    },
                    x: {
                        grid: { 
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        },
                        ticks: { 
                            color: '#a78bfa',
                            font: { size: 10 },
                            maxRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 8
                        }
                    }
                }
            };

            // CPU & Memory Chart
            const cpuMemoryCtx = document.getElementById('cpuMemoryChart').getContext('2d');
            cpuMemoryChart = new Chart(cpuMemoryCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'CPU %',
                            data: [],
                            borderColor: '#f59e0b',
                            backgroundColor: 'rgba(245, 158, 11, 0.1)',
                            borderWidth: 2,
                            tension: 0.4,
                            pointRadius: 0,
                            pointHoverRadius: 4
                        },
                        {
                            label: 'Memory %',
                            data: [],
                            borderColor: '#8b5cf6',
                            backgroundColor: 'rgba(139, 92, 246, 0.1)',
                            borderWidth: 2,
                            tension: 0.4,
                            pointRadius: 0,
                            pointHoverRadius: 4
                        }
                    ]
                },
                options: commonConfig
            });

            // Latency & Error Chart
            const latencyErrorCtx = document.getElementById('latencyErrorChart').getContext('2d');
            latencyErrorChart = new Chart(latencyErrorCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Latency (ms)',
                            data: [],
                            borderColor: '#10b981',
                            backgroundColor: 'rgba(16, 185, 129, 0.1)',
                            borderWidth: 2,
                            tension: 0.4,
                            pointRadius: 0,
                            pointHoverRadius: 4,
                            yAxisID: 'y'
                        },
                        {
                            label: 'Error Rate %',
                            data: [],
                            borderColor: '#ef4444',
                            backgroundColor: 'rgba(239, 68, 68, 0.1)',
                            borderWidth: 2,
                            tension: 0.4,
                            pointRadius: 0,
                            pointHoverRadius: 4,
                            yAxisID: 'y1'
                        }
                    ]
                },
                options: {
                    ...commonConfig,
                    scales: {
                        ...commonConfig.scales,
                        y1: {
                            type: 'linear',
                            position: 'right',
                            beginAtZero: true,
                            grid: { drawOnChartArea: false },
                            ticks: { 
                                color: '#a78bfa',
                                font: { size: 10 }
                            }
                        }
                    }
                }
            });
        }

        // Fetch System Status
        async function fetchSystemStatus() {
            try {
                const response = await fetch(`${API_BASE}/api/v1/status`);
                const data = await response.json();
                
                document.getElementById('health-score').textContent = data.health_score.toFixed(1) + '%';
                document.getElementById('active-alerts').textContent = data.active_alerts;
                document.getElementById('healing-actions').textContent = data.healing_actions_count;
                document.getElementById('total-metrics').textContent = data.total_metrics;
                document.getElementById('mode-indicator').textContent = data.mode.toUpperCase();
                
                const healthScore = data.health_score;
                const healthElement = document.getElementById('health-score');
                if (healthScore >= 90) {
                    healthElement.className = 'text-2xl md:text-3xl font-bold text-green-500';
                } else if (healthScore >= 70) {
                    healthElement.className = 'text-2xl md:text-3xl font-bold text-yellow-500';
                } else {
                    healthElement.className = 'text-2xl md:text-3xl font-bold text-red-500';
                }
                
                updateIntegrationStatus('prometheus-status', data.prometheus_enabled, 'Prometheus', data.prometheus_enabled ? 'Connected' : 'Disabled');
                updateIntegrationStatus('kubernetes-status', data.kubernetes_enabled, 'Kubernetes', data.kubernetes_enabled ? 'Enabled' : 'Disabled');
                updateIntegrationStatus('redis-status', data.redis_available, 'Cache', data.redis_available ? 'Redis' : 'In-Memory');
                
                document.getElementById('connection-status').innerHTML = `
                    <div class="w-2 h-2 rounded-full bg-green-400 pulse-dot"></div>
                    <span class="text-sm">Live</span>
                `;
                document.getElementById('connection-status').className = 'flex items-center gap-2 px-4 py-2 rounded-lg bg-green-500/20 text-green-400';
                
            } catch (error) {
                console.error('Failed to fetch system status:', error);
                document.getElementById('connection-status').innerHTML = `
                    <div class="w-2 h-2 rounded-full bg-red-400"></div>
                    <span class="text-sm">Offline</span>
                `;
                document.getElementById('connection-status').className = 'flex items-center gap-2 px-4 py-2 rounded-lg bg-red-500/20 text-red-400';
            }
        }

        function updateIntegrationStatus(elementId, enabled, name, status) {
            const element = document.getElementById(elementId);
            if (enabled) {
                element.className = 'rounded-xl p-3 md:p-4 border bg-green-500/10 border-green-500/30';
            } else {
                element.className = 'rounded-xl p-3 md:p-4 border bg-gray-500/10 border-gray-500/30';
            }
            element.querySelector('p.font-bold').textContent = status;
        }

        // Fetch Metrics
        async function fetchMetrics() {
            try {
                const response = await fetch(`${API_BASE}/api/v1/metrics?limit=20`);
                const data = await response.json();
                
                if (data.length === 0) return;
                
                const labels = data.map(m => new Date(m.timestamp).toLocaleTimeString());
                const cpuData = data.map(m => m.cpu_usage);
                const memoryData = data.map(m => m.memory_usage);
                const latencyData = data.map(m => m.response_time);
                const errorData = data.map(m => m.error_rate);
                
                cpuMemoryChart.data.labels = labels;
                cpuMemoryChart.data.datasets[0].data = cpuData;
                cpuMemoryChart.data.datasets[1].data = memoryData;
                cpuMemoryChart.update('none');
                
                latencyErrorChart.data.labels = labels;
                latencyErrorChart.data.datasets[0].data = latencyData;
                latencyErrorChart.data.datasets[1].data = errorData;
                latencyErrorChart.update('none');
                
            } catch (error) {
                console.error('Failed to fetch metrics:', error);
            }
        }

        // Fetch Anomalies
        async function fetchAnomalies() {
            try {
                const response = await fetch(`${API_BASE}/api/v1/anomalies?limit=10`);
                const data = await response.json();
                
                const anomaliesList = document.getElementById('anomalies-list');
                
                if (data.length === 0) {
                    anomaliesList.innerHTML = '<p class="text-purple-300 text-center py-8 text-sm">No anomalies detected</p>';
                    return;
                }
                
                anomaliesList.innerHTML = data.map(anomaly => {
                    const severityClass = anomaly.severity === 'critical' 
                        ? 'bg-red-100 text-red-800 border-red-300' 
                        : 'bg-yellow-100 text-yellow-800 border-yellow-300';
                    const severityBadge = anomaly.severity === 'critical'
                        ? 'bg-red-500 text-white'
                        : 'bg-yellow-500 text-white';
                    
                    return `
                        <div class="p-3 rounded-lg border ${severityClass}">
                            <div class="flex items-start justify-between gap-2">
                                <div class="flex-1 min-w-0">
                                    <div class="flex items-center gap-2 mb-1 flex-wrap">
                                        <span class="font-bold text-sm">${anomaly.anomaly_type}</span>
                                        <span class="text-xs px-2 py-0.5 rounded ${severityBadge}">
                                            ${anomaly.severity}
                                        </span>
                                    </div>
                                    <p class="text-xs opacity-75">
                                        Score: ${anomaly.anomaly_score?.toFixed(3)}
                                    </p>
                                    <p class="text-xs opacity-60 mt-1">
                                        ${new Date(anomaly.timestamp).toLocaleTimeString()}
                                    </p>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('');
                
            } catch (error) {
                console.error('Failed to fetch anomalies:', error);
            }
        }

        // Fetch Healing Actions
        async function fetchHealingActions() {
            try {
                const response = await fetch(`${API_BASE}/api/v1/healing-actions?limit=10`);
                const data = await response.json();
                
                const healingList = document.getElementById('healing-list');
                
                if (data.length === 0) {
                    healingList.innerHTML = '<p class="text-purple-300 text-center py-8 text-sm">No healing actions yet</p>';
                    return;
                }
                
                healingList.innerHTML = data.map(action => {
                    const successBadge = action.success 
                        ? 'bg-green-500 text-white' 
                        : 'bg-red-500 text-white';
                    
                    return `
                        <div class="p-3 rounded-lg bg-green-500/10 border border-green-500/30">
                            <div class="flex items-start justify-between gap-2">
                                <div class="flex-1 min-w-0">
                                    <div class="flex items-center gap-2 mb-1">
                                        <span class="text-green-400 text-sm">✓</span>
                                        <span class="font-bold text-white text-sm">${action.action_type}</span>
                                    </div>
                                    <p class="text-xs text-green-200">
                                        Target: ${action.target_resource}
                                    </p>
                                    ${action.kubernetes_action ? `
                                        <p class="text-xs text-green-300 mt-1">
                                            ☸️ K8s: ${action.kubernetes_replicas} replicas
                                        </p>
                                    ` : ''}
                                    <p class="text-xs text-green-300 opacity-60 mt-1">
                                        ${new Date(action.timestamp).toLocaleTimeString()}
                                    </p>
                                </div>
                                <span class="text-xs px-2 py-0.5 rounded ${successBadge} whitespace-nowrap">
                                    ${action.success ? 'Success' : 'Failed'}
                                </span>
                            </div>
                        </div>
                    `;
                }).join('');
                
            } catch (error) {
                console.error('Failed to fetch healing actions:', error);
            }
        }

        // Refresh all data
        async function refreshDashboard() {
            await Promise.all([
                fetchSystemStatus(),
                fetchMetrics(),
                fetchAnomalies(),
                fetchHealingActions()
            ]);
        }

        // Initialize
        window.addEventListener('load', () => {
            initCharts();
            refreshDashboard();
            setInterval(refreshDashboard, 2000);
        });
    </script>
</body>
</html>
    """

@app.get("/health")
async def health_check():
    if app_metrics:
        app_metrics.increment_request_count()
    
    return {
        "status": "healthy",
        "version": "17.0",
        "mode": APP_MODE,
        "auto_metrics": APP_MODE == "development",
        "prometheus_enabled": prometheus_client is not None,
        "kubernetes_enabled": kubernetes_client is not None,
        "timestamp": datetime.now().isoformat(),
        "redis": "connected" if REDIS_AVAILABLE else "in-memory",
        "package1_available": PACKAGE1_AVAILABLE,
        "health_score": calculate_health_score(),
        "uptime_seconds": (datetime.now() - startup_time).total_seconds(),
        "target_app": TARGET_APP if APP_MODE == "production" else None
    }

@app.post("/api/v1/auth/login")
async def login(credentials: LoginRequest):
    if not PACKAGE1_AVAILABLE:
        raise HTTPException(status_code=501, detail="Authentication not available")
    
    valid_users = {"admin": "admin123", "user": "user123"}
    if credentials.username not in valid_users or valid_users[credentials.username] != credentials.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(
        data={"sub": credentials.username, "role": "admin" if credentials.username == "admin" else "user"}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": credentials.username,
        "mode": APP_MODE
    }

@app.get("/api/v1/status", response_model=SystemStatus)
async def get_system_status(current_user: Optional[User] = Depends(get_current_user_optional)):
    if app_metrics:
        app_metrics.increment_request_count()
    
    return SystemStatus(
        health_score=calculate_health_score(),
        active_alerts=len(active_alerts),
        total_metrics=len(metrics_history),
        healing_actions_count=len(healing_actions_taken),
        ml_model_trained=anomaly_detector.is_trained,
        uptime_seconds=(datetime.now() - startup_time).total_seconds(),
        cache_enabled=cache_manager.enabled if cache_manager else False,
        redis_available=REDIS_AVAILABLE,
        mode=APP_MODE,
        auto_metrics=APP_MODE == "development",
        prometheus_enabled=prometheus_client is not None,
        kubernetes_enabled=kubernetes_client is not None,
        target_app=TARGET_APP if APP_MODE == "production" else None
    )

@app.get("/api/v1/metrics")
async def get_metrics(limit: int = 50):
    return list(metrics_history)[-limit:]

@app.post("/api/v1/metrics")
async def ingest_metrics(metric: MetricInput, background_tasks: BackgroundTasks):
    metric_dict = metric.dict()
    metric_dict['source'] = 'api'
    metrics_history.append(metric_dict)
    background_tasks.add_task(process_metric, metric_dict)
    
    logger.info(f"📥 Metric received (API): CPU={metric.cpu_usage}%, Memory={metric.memory_usage}%")
    return {"status": "accepted", "mode": APP_MODE, "message": "Metric processed successfully"}

@app.get("/api/v1/anomalies")
async def get_anomalies(limit: int = 20):
    return list(anomalies_detected)[-limit:]

@app.get("/api/v1/healing-actions")
async def get_healing_actions(limit: int = 20):
    return list(healing_actions_taken)[-limit:]

# =============================================================================
# KUBERNETES ENDPOINTS
# =============================================================================

@app.get("/api/v1/target-app/info")
async def get_target_app_info():
    """Get information about the target application"""
    if not kubernetes_client:
        return {"message": "Kubernetes not available"}
    
    info = await get_deployment_info(TARGET_APP, TARGET_NAMESPACE)
    return info or {"message": "Deployment not found"}

@app.post("/api/v1/target-app/scale")
async def scale_target_app(replicas: int, current_user: User = Depends(get_current_user_required)):
    """Manually scale the target application"""
    if not kubernetes_client:
        raise HTTPException(status_code=501, detail="Kubernetes not available")
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    
    success = await scale_deployment(TARGET_APP, TARGET_NAMESPACE, replicas)
    
    if success:
        return {"status": "success", "message": f"Scaled {TARGET_APP} to {replicas} replicas"}
    else:
        raise HTTPException(status_code=500, detail="Failed to scale deployment")

# =============================================================================
# WEBSOCKET
# =============================================================================

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        active_websockets.remove(websocket)

# =============================================================================
# BACKGROUND PROCESSING
# =============================================================================

async def process_metric(metric: Dict):
    try:
        anomaly_detector.add_metrics(metric)
        
        if anomaly_detector.is_trained:
            anomaly = anomaly_detector.detect_anomaly(metric)
            
            if anomaly:
                anomaly_id = generate_anomaly_id()
                anomaly_type = anomaly.get('anomaly_type', 'UNKNOWN')
                
                anomaly_record = {
                    'id': len(anomalies_detected) + 1,
                    'anomaly_id': anomaly_id,
                    'timestamp': datetime.now().isoformat(),
                    'anomaly_type': anomaly_type,
                    'severity': anomaly.get('severity', 'warning'),
                    'anomaly_score': anomaly.get('anomaly_score', 0.0),
                    'metrics': metric,
                    'status': 'active',
                    'source': metric.get('source', 'unknown')
                }
                
                add_active_alert(anomaly_id, anomaly_record)
                anomalies_detected.append(anomaly_record)
                
                # Decide self-healing action
                action = healing_orchestrator.decide_action(anomaly)
                if action:
                    # Execute action
                    success = await healing_orchestrator.execute_action(action)
                    
                    action_record = action.to_dict()
                    action_record['kubernetes_action'] = False
                    healing_actions_taken.append(action_record)
                    
                    # If Kubernetes is enabled and anomaly is critical, scale target app
                    if kubernetes_client and anomaly.get('severity') == 'critical':
                        if anomaly_type in ['CPU_USAGE', 'MEMORY_USAGE', 'RESPONSE_TIME']:
                            # Get current deployment info
                            deployment_info = await get_deployment_info(TARGET_APP, TARGET_NAMESPACE)
                            if deployment_info:
                                current_replicas = deployment_info['replicas']
                                new_replicas = min(current_replicas + 2, 10)  # Scale up by 2, max 10
                                
                                logger.info(f"🎯 Triggering K8s scaling: {TARGET_APP} {current_replicas} → {new_replicas}")
                                k8s_success = await scale_deployment(TARGET_APP, TARGET_NAMESPACE, new_replicas)
                                
                                if k8s_success:
                                    action_record['kubernetes_action'] = True
                                    action_record['kubernetes_replicas'] = new_replicas
                    
                    if success:
                        resolve_alert(anomaly_id)
        
        auto_resolve_old_alerts()
        
    except Exception as e:
        logger.error(f"Error processing metric: {e}")

async def auto_generate_metrics():
    """Auto-generate metrics (DEVELOPMENT mode only)"""
    logger.info(f"🤖 Auto-metrics generator started (interval: {AUTO_GENERATE_INTERVAL}s)")
    counter = 0
    
    while True:
        try:
            counter += 1
            
            cpu = random.uniform(45, 65)
            memory = random.uniform(55, 70)
            latency = random.uniform(180, 350)
            error_rate = random.uniform(0.5, 2.5)
            throughput = random.uniform(90, 140)
            
            if counter % random.randint(AUTO_ANOMALY_MIN, AUTO_ANOMALY_MAX) == 0:
                anomaly_type = random.choice(['cpu', 'memory', 'latency', 'error'])
                if anomaly_type == 'cpu':
                    cpu = random.uniform(85, 95)
                elif anomaly_type == 'memory':
                    memory = random.uniform(85, 92)
                elif anomaly_type == 'latency':
                    latency = random.uniform(800, 1200)
                elif anomaly_type == 'error':
                    error_rate = random.uniform(5, 10)
                logger.info(f"🎯 Injecting {anomaly_type.upper()} anomaly (counter: {counter})")
            
            metric = {
                'timestamp': datetime.now().isoformat(),
                'cpu_usage': round(cpu, 2),
                'memory_usage': round(memory, 2),
                'response_time': round(latency, 2),
                'error_rate': round(error_rate, 2),
                'requests_per_sec': round(throughput, 2),
                'disk_io': round(random.uniform(500, 1500), 2),
                'network_throughput': round(random.uniform(300, 700), 2),
                'source': 'auto-generator'
            }
            
            await process_metric(metric)
            metrics_history.append(metric)
            
            await asyncio.sleep(AUTO_GENERATE_INTERVAL)
            
        except Exception as e:
            logger.error(f"Error in auto-metrics generator: {e}")
            await asyncio.sleep(AUTO_GENERATE_INTERVAL)

# =============================================================================
# STARTUP/SHUTDOWN
# =============================================================================

@app.on_event("startup")
async def startup_event():
    global auto_metrics_task, prometheus_metrics_task, metrics_collection_task
    
    logger.info("=" * 70)
    logger.info("🚀 AI Self-Healing Platform v17 Starting...")
    logger.info("=" * 70)
    logger.info(f"  MODE: {APP_MODE.upper()}")
    logger.info(f"  Prometheus: {'✅ Enabled' if prometheus_client else '❌ Disabled'} ({PROMETHEUS_URL if prometheus_client else 'N/A'})")
    logger.info(f"  Kubernetes: {'✅ Enabled' if kubernetes_client else '❌ Disabled'} (target: {TARGET_APP if kubernetes_client else 'N/A'})")
    logger.info(f"  Redis: {'✅ Connected' if REDIS_AVAILABLE else '⚠️  In-Memory'} ({REDIS_HOST}:{REDIS_PORT})")
    logger.info(f"  Package 1: {'✅ Available' if PACKAGE1_AVAILABLE else '⚠️  Basic Mode'}")
    logger.info(f"  Auto-Metrics: {'❌ DISABLED' if APP_MODE == 'production' else '✅ ENABLED'}")
    logger.info("=" * 70)
    
    # System metrics collection
    if metrics_collector:
        metrics_collection_task = asyncio.create_task(metrics_collector.start_collection())
        logger.info("✅ System metrics collection started")
    
    # Start appropriate metrics source
    if APP_MODE == "production" and prometheus_client:
        prometheus_metrics_task = asyncio.create_task(collect_metrics_from_prometheus())
        logger.info(f"✅ Prometheus metrics collection started (target: {TARGET_APP})")
    elif APP_MODE == "development":
        auto_metrics_task = asyncio.create_task(auto_generate_metrics())
        logger.info("✅ Auto-metrics generator started")
    else:
        logger.info("ℹ️  Production mode: Send metrics via POST /api/v1/metrics or enable Prometheus")
    
    logger.info("=" * 70)
    logger.info("✅ Platform ready")
    logger.info(f"📊 Dashboard: http://localhost:8000")
    logger.info(f"📡 API Docs: http://localhost:8000/docs")
    logger.info("=" * 70)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Shutting down platform...")
    if metrics_collector:
        metrics_collector.stop_collection()
    logger.info("✅ Shutdown complete")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    host = "0.0.0.0" if APP_MODE == "production" else "127.0.0.1"
    uvicorn.run(app, host=host, port=port, log_level="info")
