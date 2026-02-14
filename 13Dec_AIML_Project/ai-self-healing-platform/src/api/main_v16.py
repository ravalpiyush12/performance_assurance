"""
Main API Server - Production Ready with Mode Control (Version 16)
Save as: src/api/main.py

MODES:
- PRODUCTION: Real metrics from external sources (JMeter, monitoring agents)
- DEVELOPMENT: Auto-generated metrics for testing/demo

Usage:
  Development: python -m uvicorn src.api.main:app --reload --port 8000
  
  Local command:
  $env:MODE="development" 
  & "F:/Piyush Data/Learning/performance_assurance/13Dec_AIML_Project/.venv/Scripts/python.exe" -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000


  Production:  MODE=production python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000

  local command:
  $env:MODE="production" 
  & "F:/Piyush Data/Learning/performance_assurance/13Dec_AIML_Project/.venv/Scripts/python.exe" -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
  
Environment Variables:
  MODE: "production" or "development" (default: development)
  REDIS_HOST: Redis hostname (default: localhost)
  REDIS_PORT: Redis port (default: 6379)
  AUTO_GENERATE_INTERVAL: Seconds between auto-generated metrics (default: 2)
  AUTO_ANOMALY_FREQUENCY: Metrics between anomalies (default: 25-35)
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

# Get mode from environment variable (default: development)
APP_MODE = os.getenv("MODE", "development").lower()
VALID_MODES = ["production", "development", "dev", "prod"]

# Normalize mode
if APP_MODE in ["dev", "development"]:
    APP_MODE = "development"
elif APP_MODE in ["prod", "production"]:
    APP_MODE = "production"
else:
    print(f"❌ Invalid MODE: {APP_MODE}. Must be 'production' or 'development'")
    sys.exit(1)

# Redis configuration from environment
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# Auto-generation settings (only used in development mode)
AUTO_GENERATE_INTERVAL = int(os.getenv("AUTO_GENERATE_INTERVAL", "2"))
AUTO_ANOMALY_MIN = int(os.getenv("AUTO_ANOMALY_MIN", "25"))
AUTO_ANOMALY_MAX = int(os.getenv("AUTO_ANOMALY_MAX", "35"))

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Ensure logs directory
Path('logs').mkdir(exist_ok=True)

# Windows UTF-8 fix
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Logging configuration
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

# Define User class BEFORE importing authentication
class User(BaseModel):
    """User model"""
    username: str
    email: str
    role: str = "user"
    disabled: bool = False

# Try to import Package 1 modules
PACKAGE1_AVAILABLE = False
try:
    from src.monitoring.collector import MetricsCollector, ApplicationMetricsCollector
    from src.security.input_validation import InputValidator
    from src.optimization.caching import CacheManager, MetricsCache
    from src.optimization.query_optimization import get_query_monitor
    
    # Try to import auth functions
    try:
        from src.security.authentication import create_access_token, verify_token
    except ImportError:
        # Define minimal auth functions if not available
        import jwt
        
        SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production-use-env-var")
        ALGORITHM = "HS256"
        
        def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
            to_encode = data.copy()
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=30)
            to_encode.update({"exp": expire})
            encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
            return encoded_jwt
        
        def verify_token(token: str):
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                return payload
            except jwt.PyJWTError:
                raise HTTPException(status_code=401, detail="Invalid token")
    
    logger.info("✅ Package 1 modules imported")
    PACKAGE1_AVAILABLE = True
    
except ImportError as e:
    logger.warning(f"⚠️  Package 1 modules not available: {e}")
    logger.warning("Platform will run in basic mode")
    PACKAGE1_AVAILABLE = False

# Initialize Redis if available
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
        logger.warning("Using in-memory cache fallback")
        REDIS_AVAILABLE = False

# FastAPI app
app = FastAPI(
    title=f"AI-Driven Self-Healing Platform v16 ({APP_MODE.upper()})",
    description=f"Mode: {APP_MODE.upper()} | Auto-metrics: {'DISABLED' if APP_MODE == 'production' else 'ENABLED'}",
    version="16.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Initialize core components
anomaly_detector = AnomalyDetector(contamination=0.1, window_size=100)
performance_predictor = PerformancePredictor()
healing_orchestrator = SelfHealingOrchestrator(cloud_provider=CloudProvider.LOCAL)

# Initialize Package 1 components if available
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

# In-memory storage
metrics_history = deque(maxlen=1000)
anomalies_detected = deque(maxlen=200)
healing_actions_taken = deque(maxlen=200)
active_websockets = []
startup_time = datetime.now()
active_alerts = {}
successful_healings_count = 0
last_healing_timestamp = None

# Background task references
auto_metrics_task = None
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

# =============================================================================
# AUTHENTICATION HELPERS
# =============================================================================

def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[User]:
    """Get current user (optional)"""
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
    """Get current user (required)"""
    if not PACKAGE1_AVAILABLE:
        return User(username="anonymous", email="anon@example.com", role="user")
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    try:
        token = credentials.credentials
        payload = verify_token(token)
        return User(
            username=payload.get("sub"),
            email=f"{payload.get('sub')}@example.com",
            role=payload.get("role", "user")
        )
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

# =============================================================================
# ALERT MANAGEMENT
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
    """Calculate health score (v14 algorithm)"""
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
# PUBLIC ENDPOINTS
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Dashboard"""
    mode_badge = "PRODUCTION" if APP_MODE == "production" else "DEVELOPMENT"
    mode_color = "#dc2626" if APP_MODE == "production" else "#059669"
    auto_metrics_status = "DISABLED" if APP_MODE == "production" else "ENABLED"
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>AI Self-Healing Platform v16</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 900px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
        }}
        .mode-badge {{
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
            background: {mode_color};
            color: white;
            margin: 10px 5px;
        }}
        .status {{
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .status-item {{
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }}
        .status-item:last-child {{
            border-bottom: none;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }}
        .badge-success {{ background: #10b981; color: white; }}
        .badge-warning {{ background: #f59e0b; color: white; }}
        .badge-info {{ background: #3b82f6; color: white; }}
        .code {{
            background: #1e293b;
            color: #10b981;
            padding: 15px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 13px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 AI Self-Healing Platform v16</h1>
        <span class="mode-badge">{mode_badge} MODE</span>
        <p style="margin-top: 10px;">Production-ready with mode control</p>
    </div>
    
    <div class="status">
        <h2>📊 System Configuration</h2>
        <div class="status-item">
            <strong>Mode:</strong> 
            <span class="badge badge-{'warning' if APP_MODE == 'production' else 'info'}">{APP_MODE.upper()}</span>
        </div>
        <div class="status-item">
            <strong>Auto-Generated Metrics:</strong> 
            <span class="badge badge-{'warning' if APP_MODE == 'production' else 'success'}">{auto_metrics_status}</span>
        </div>
        <div class="status-item">
            <strong>Redis:</strong> 
            <span class="badge badge-{'success' if REDIS_AVAILABLE else 'warning'}">{'CONNECTED' if REDIS_AVAILABLE else 'IN-MEMORY'}</span>
        </div>
        <div class="status-item">
            <strong>Package 1:</strong> 
            <span class="badge badge-{'success' if PACKAGE1_AVAILABLE else 'warning'}">{'AVAILABLE' if PACKAGE1_AVAILABLE else 'BASIC MODE'}</span>
        </div>
    </div>
    
    <div class="status">
        <h2>🎯 Mode Explanation</h2>
        <div class="status-item">
            <strong>PRODUCTION Mode:</strong><br>
            • Metrics come from external sources (JMeter, monitoring agents)<br>
            • Auto-generation is DISABLED<br>
            • Use POST /api/v1/metrics to send real data<br>
            • Suitable for deployment on AWS EKS/ECS
        </div>
        <div class="status-item">
            <strong>DEVELOPMENT Mode:</strong><br>
            • Metrics are auto-generated every {AUTO_GENERATE_INTERVAL} seconds<br>
            • Anomalies injected automatically for testing<br>
            • Perfect for demos, testing, and local development<br>
            • No external load generator needed
        </div>
    </div>
    
    <div class="status">
        <h2>🚀 Quick Links</h2>
        <div class="status-item">
            <a href="/docs">📚 API Documentation (Interactive)</a>
        </div>
        <div class="status-item">
            <a href="/health">🏥 Health Check Endpoint</a>
        </div>
        <div class="status-item">
            <a href="/api/v1/status">📊 System Status (JSON)</a>
        </div>
        <div class="status-item">
            <a href="/api/v1/metrics">📈 Recent Metrics</a>
        </div>
        <div class="status-item">
            <a href="/api/v1/anomalies">⚠️  Detected Anomalies</a>
        </div>
    </div>
    
    <div class="status">
        <h2>💻 Change Mode</h2>
        <p><strong>Development Mode (default):</strong></p>
        <div class="code">python -m uvicorn src.api.main:app --reload --port 8000</div>
        
        <p style="margin-top: 15px;"><strong>Production Mode:</strong></p>
        <div class="code">MODE=production python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000</div>
        
        <p style="margin-top: 15px;"><strong>Windows PowerShell:</strong></p>
        <div class="code">$env:MODE="production"; python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000</div>
    </div>
    
    <div class="status">
        <h2>🔐 Test Authentication (if enabled)</h2>
        <p><strong>Credentials:</strong></p>
        <div class="code">Admin: admin / admin123<br>User: user / user123</div>
        
        <p style="margin-top: 10px;"><strong>Login endpoint:</strong></p>
        <div class="code">POST /api/v1/auth/login</div>
    </div>
</body>
</html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if app_metrics:
        app_metrics.increment_request_count()
    
    return {
        "status": "healthy",
        "version": "16.0",
        "mode": APP_MODE,
        "auto_metrics": APP_MODE == "development",
        "timestamp": datetime.now().isoformat(),
        "redis": "connected" if REDIS_AVAILABLE else "in-memory",
        "package1_available": PACKAGE1_AVAILABLE,
        "health_score": calculate_health_score(),
        "uptime_seconds": (datetime.now() - startup_time).total_seconds()
    }

# =============================================================================
# AUTHENTICATION
# =============================================================================

@app.post("/api/v1/auth/login")
async def login(credentials: LoginRequest):
    """Login endpoint"""
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

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/api/v1/status", response_model=SystemStatus)
async def get_system_status(current_user: Optional[User] = Depends(get_current_user_optional)):
    """Get system status"""
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
        auto_metrics=APP_MODE == "development"
    )

@app.get("/api/v1/metrics")
async def get_metrics(limit: int = 50):
    """Get recent metrics"""
    return list(metrics_history)[-limit:]

@app.post("/api/v1/metrics")
async def ingest_metrics(metric: MetricInput, background_tasks: BackgroundTasks):
    """
    Ingest metrics from external sources (JMeter, monitoring agents)
    This is the PRIMARY endpoint for PRODUCTION mode
    """
    metric_dict = metric.dict()
    metrics_history.append(metric_dict)
    background_tasks.add_task(process_metric, metric_dict)
    
    logger.info(f"📥 Metric received: CPU={metric.cpu_usage}%, Memory={metric.memory_usage}%, Latency={metric.response_time}ms")
    
    return {
        "status": "accepted",
        "mode": APP_MODE,
        "message": "Metric processed successfully"
    }

@app.get("/api/v1/anomalies")
async def get_anomalies(limit: int = 20):
    """Get detected anomalies"""
    return list(anomalies_detected)[-limit:]

@app.get("/api/v1/healing-actions")
async def get_healing_actions(limit: int = 20):
    """Get healing actions taken"""
    return list(healing_actions_taken)[-limit:]

@app.get("/api/v1/system-metrics")
async def get_system_metrics():
    """Get system metrics (from monitoring collector)"""
    if not metrics_collector:
        return {"message": "System monitoring not available"}
    
    return {
        "system": metrics_collector.get_recent_metrics(limit=10),
        "summary": metrics_collector.get_metrics_summary()
    }

@app.get("/api/v1/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    if not cache_manager:
        return {"message": "Caching not available"}
    
    return cache_manager.get_stats()

# =============================================================================
# WEBSOCKET
# =============================================================================

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for live updates"""
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
    """Process incoming metrics (anomaly detection + self-healing)"""
    try:
        anomaly_detector.add_metrics(metric)
        
        if anomaly_detector.is_trained:
            anomaly = anomaly_detector.detect_anomaly(metric)
            
            if anomaly:
                anomaly_id = generate_anomaly_id()
                
                anomaly_record = {
                    'id': len(anomalies_detected) + 1,
                    'anomaly_id': anomaly_id,
                    'timestamp': datetime.now().isoformat(),
                    'anomaly_type': anomaly.get('anomaly_type', 'UNKNOWN'),
                    'severity': anomaly.get('severity', 'warning'),
                    'anomaly_score': anomaly.get('anomaly_score', 0.0),
                    'metrics': metric,
                    'status': 'active'
                }
                
                add_active_alert(anomaly_id, anomaly_record)
                anomalies_detected.append(anomaly_record)
                
                action = healing_orchestrator.decide_action(anomaly)
                if action:
                    success = await healing_orchestrator.execute_action(action)
                    
                    action_record = action.to_dict()
                    healing_actions_taken.append(action_record)
                    
                    if success:
                        resolve_alert(anomaly_id)
        
        auto_resolve_old_alerts()
        
    except Exception as e:
        logger.error(f"Error processing metric: {e}")

async def broadcast_update(message: Dict):
    """Broadcast updates to WebSocket clients"""
    disconnected = []
    for ws in active_websockets:
        try:
            await ws.send_json(message)
        except:
            disconnected.append(ws)
    
    for ws in disconnected:
        active_websockets.remove(ws)

async def auto_generate_metrics():
    """
    AUTO-GENERATE METRICS (DEVELOPMENT MODE ONLY)
    Simulates production environment for testing/demo
    """
    logger.info(f"🤖 Auto-metrics generator started (interval: {AUTO_GENERATE_INTERVAL}s, anomaly every {AUTO_ANOMALY_MIN}-{AUTO_ANOMALY_MAX} metrics)")
    counter = 0
    
    while True:
        try:
            counter += 1
            
            # Generate realistic baseline metrics
            cpu = random.uniform(45, 65)
            memory = random.uniform(55, 70)
            latency = random.uniform(180, 350)
            error_rate = random.uniform(0.5, 2.5)
            throughput = random.uniform(90, 140)
            
            # Inject anomaly periodically
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
                'network_throughput': round(random.uniform(300, 700), 2)
            }
            
            await process_metric(metric)
            metrics_history.append(metric)
            
            await asyncio.sleep(AUTO_GENERATE_INTERVAL)
            
        except Exception as e:
            logger.error(f"Error in auto-metrics generator: {e}")
            await asyncio.sleep(AUTO_GENERATE_INTERVAL)

# =============================================================================
# STARTUP/SHUTDOWN EVENTS
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Application startup"""
    global auto_metrics_task, metrics_collection_task
    
    logger.info("=" * 70)
    logger.info("🚀 AI Self-Healing Platform v16 Starting...")
    logger.info("=" * 70)
    logger.info(f"  MODE: {APP_MODE.upper()}")
    logger.info(f"  Redis: {'✅ Connected' if REDIS_AVAILABLE else '⚠️  In-Memory'} ({REDIS_HOST}:{REDIS_PORT})")
    logger.info(f"  Package 1: {'✅ Available' if PACKAGE1_AVAILABLE else '⚠️  Basic Mode'}")
    logger.info(f"  Auto-Metrics: {'❌ DISABLED' if APP_MODE == 'production' else '✅ ENABLED'}")
    logger.info("=" * 70)
    
    # Start system metrics collection (both modes)
    if metrics_collector:
        metrics_collection_task = asyncio.create_task(metrics_collector.start_collection())
        logger.info("✅ System metrics collection started")
    
    # Start auto-generation ONLY in development mode
    if APP_MODE == "development":
        auto_metrics_task = asyncio.create_task(auto_generate_metrics())
        logger.info("✅ Auto-metrics generator started")
    else:
        logger.info("ℹ️  Production mode: Send metrics via POST /api/v1/metrics")
    
    logger.info("=" * 70)
    logger.info("✅ Platform ready")
    logger.info(f"📊 Dashboard: http://localhost:8000")
    logger.info(f"📡 API Docs: http://localhost:8000/docs")
    logger.info("=" * 70)

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("🛑 Shutting down platform...")
    
    if metrics_collector:
        metrics_collector.stop_collection()
    
    logger.info("✅ Shutdown complete")

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    host = "0.0.0.0" if APP_MODE == "production" else "127.0.0.1"
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )