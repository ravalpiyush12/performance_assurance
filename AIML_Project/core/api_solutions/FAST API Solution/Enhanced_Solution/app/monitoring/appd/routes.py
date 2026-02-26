"""
AppDynamics Monitoring FastAPI Routes
All API endpoints for discovery, health check, and monitoring
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import threading
import time
import uuid

# Import AppD components
from .config import appd_config
from .client import AppDynamicsClient
from .database import AppDynamicsDatabase
from .discovery import AppDynamicsDiscoveryService
from .collectors import MetricsCollectorManager
from .orchestrator import MonitoringOrchestrator

# Router
router = APIRouter()

# Global instances
appd_client = None
appd_db = None
discovery_service = None
collectors = None
orchestrator = None
monitoring_threads = {}
thread_lock = threading.Lock()


# Request Models
class DiscoveryRequest(BaseModel):
    lob_names: List[str]

class StartMonitoringRequest(BaseModel):
    run_id: str
    lob_name: str
    track: str
    test_name: Optional[str] = None
    applications: List[str]
    interval_seconds: int = 1800


def initialize_appd_components(oracle_connection_pool):
    """Initialize AppD components - call from main.py startup"""
    global appd_client, appd_db, discovery_service, collectors, orchestrator
    
    print("[AppD] Initializing components...", flush=True)
    appd_client = AppDynamicsClient(appd_config)
    appd_db = AppDynamicsDatabase(oracle_connection_pool)
    discovery_service = AppDynamicsDiscoveryService(appd_client, appd_db, appd_config)
    collectors = MetricsCollectorManager(appd_client, appd_db, appd_config)
    orchestrator = MonitoringOrchestrator(appd_client, appd_db, collectors, appd_config)
    print("[AppD] Initialized successfully", flush=True)


# Discovery Endpoints
@router.post("/discovery/run")
async def run_discovery(request: DiscoveryRequest, background_tasks: BackgroundTasks):
    """Run discovery for LOBs"""
    if not discovery_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    task_id = str(uuid.uuid4())
    background_tasks.add_task(execute_discovery_task, task_id, request.lob_names)
    
    return {
        "task_id": task_id,
        "status": "initiated",
        "lob_names": request.lob_names
    }


def execute_discovery_task(task_id: str, lob_names: List[str]):
    """Background discovery task"""
    results = []
    for lob_name in lob_names:
        try:
            result = discovery_service.run_discovery_for_lob(lob_name)
            results.append(result)
        except Exception as e:
            results.append({'lob_name': lob_name, 'status': 'FAILED', 'error': str(e)})
    return results


# Health Check Endpoints
@router.get("/health/{lob_name}")
async def get_lob_health(lob_name: str):
    """Get active nodes for LOB"""
    if not appd_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    active_nodes = appd_db.get_active_nodes_for_lob(lob_name)
    
    grouped = {}
    for node in active_nodes:
        app = node['application_name']
        if app not in grouped:
            grouped[app] = {}
        tier = node['tier_name']
        if tier not in grouped[app]:
            grouped[app][tier] = []
        grouped[app][tier].append({
            'node_name': node['node_name'],
            'calls_per_minute': node['calls_per_minute']
        })
    
    return {
        "lob_name": lob_name,
        "total_active_nodes": len(active_nodes),
        "applications": grouped
    }


# Monitoring Endpoints
@router.post("/monitoring/start")
async def start_monitoring(request: StartMonitoringRequest):
    """Start monitoring session"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    with thread_lock:
        if request.run_id in monitoring_threads:
            raise HTTPException(status_code=400, detail="Run ID exists")
        
        active_count = sum(1 for t in monitoring_threads.values() if t.is_alive())
        if active_count >= appd_config.APPD_MAX_CONCURRENT_MONITORS:
            raise HTTPException(status_code=429, detail="Max monitors reached")
    
    orchestrator.start_monitoring(request.run_id, request.lob_name, request.applications)
    
    thread = threading.Thread(
        target=monitoring_worker,
        args=(request.run_id, request.interval_seconds),
        daemon=True
    )
    
    with thread_lock:
        monitoring_threads[request.run_id] = thread
    thread.start()
    
    return {
        "success": True,
        "run_id": request.run_id,
        "message": "Monitoring started"
    }


def monitoring_worker(run_id: str, interval_seconds: int):
    """Background monitoring worker"""
    while True:
        try:
            status = orchestrator.get_session_status(run_id)
            if status.get('status') != 'RUNNING':
                break
            
            orchestrator.collect_metrics_once(run_id)
            time.sleep(interval_seconds)
        except Exception as e:
            print(f"[Worker] Error: {e}", flush=True)
            time.sleep(60)


@router.post("/monitoring/stop/{run_id}")
async def stop_monitoring(run_id: str):
    """Stop monitoring session"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    orchestrator.stop_monitoring(run_id)
    return {"success": True, "run_id": run_id}


@router.get("/monitoring/sessions")
async def list_sessions():
    """List all monitoring sessions"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    sessions = orchestrator.get_all_sessions()
    return {"total_sessions": len(sessions), "sessions": sessions}


@router.get("/monitoring/thread-pool/status")
async def get_thread_pool_status():
    """Get thread pool status"""
    with thread_lock:
        active_threads = [
            {'run_id': run_id}
            for run_id, thread in monitoring_threads.items()
            if thread.is_alive()
        ]
    
    return {
        "max_concurrent_monitors": appd_config.APPD_MAX_CONCURRENT_MONITORS,
        "active_monitors": len(active_threads),
        "available_slots": appd_config.APPD_MAX_CONCURRENT_MONITORS - len(active_threads),
        "utilization_percent": (len(active_threads) / appd_config.APPD_MAX_CONCURRENT_MONITORS) * 100,
        "active_threads": active_threads
    }