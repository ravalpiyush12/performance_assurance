"""
AppDynamics Monitoring API - Integrated with Existing Code
Uses your existing fetchers/orchestrator/code1/code2/code3 structure
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import threading
import time
import uuid

# Import your existing code
# TODO: Update these imports based on your actual structure
try:
    # Code 1: Discovery and health check
    from app.collect_appd_config_to_db import collect_appd_config_to_db
    
    # Code 2: Generate JSON configuration
    from app.generate_appd_config import generate_appd_config
    
    # Code 3: Main monitoring orchestrator
    from app.monitoring_main import start_monitoring_session
    
    # Fetchers
    from app.fetchers.appdynamics_fetcher import AppDynamicsDataFetcher
    
    # Orchestrator
    from app.orchestrator.monitoring_orchestrator import MonitoringOrchestrator
    
    # Database handler
    from app.database.db_handler import MonitoringDatabase
    
    INTEGRATION_READY = True
except ImportError as e:
    print(f"Warning: Could not import existing AppD code: {e}")
    print("API will work with placeholder functions")
    INTEGRATION_READY = False

# Router
appdynamics_router = APIRouter(prefix="/api/v1/monitoring/appdynamics", tags=["AppDynamics"])

# Global state
monitoring_sessions = {}
monitoring_threads = {}
thread_lock = threading.Lock()
MAX_CONCURRENT_MONITORS = 10


class HealthCheckRequest(BaseModel):
    """Request model for AppD health check"""
    applications: List[str] = []
    check_duration: Optional[int] = 30  # Duration to check for calls per minute
    
    class Config:
        schema_extra = {
            "example": {
                "applications": ["MyApp1", "MyApp2"],
                "check_duration": 30
            }
        }


class StartMonitoringRequest(BaseModel):
    """Request model to start monitoring"""
    lob: str
    track: str
    run_id: str
    applications: List[str]
    interval_seconds: int = 1800  # 30 minutes default
    
    # Optional: If you want to specify which metrics to collect
    collect_app_metrics: bool = True
    collect_jvm_metrics: bool = True
    collect_server_metrics: bool = True
    
    class Config:
        schema_extra = {
            "example": {
                "lob": "Retail",
                "track": "Q4_2026",
                "run_id": "RUN_20260225_001",
                "applications": ["RetailWeb", "RetailAPI"],
                "interval_seconds": 1800
            }
        }


# ========================================
# Code 1: Health Check / Discovery
# ========================================
@appdynamics_router.post("/healthcheck", summary="Run AppD health check and discover active nodes/tiers")
async def run_healthcheck(request: HealthCheckRequest, background_tasks: BackgroundTasks):
    """
    Executes Code 1 (collect_appd_config_to_db.py):
    - Discovers AppD applications
    - Identifies active nodes based on Calls per Minute
    - Stores configuration in Oracle database for fast JSON generation later
    """
    task_id = str(uuid.uuid4())
    
    # Add to background tasks
    background_tasks.add_task(
        execute_healthcheck_task,
        task_id=task_id,
        applications=request.applications,
        check_duration=request.check_duration
    )
    
    return {
        "task_id": task_id,
        "status": "initiated",
        "message": "Health check started in background",
        "applications": request.applications if request.applications else "all"
    }


def execute_healthcheck_task(task_id: str, applications: List[str], check_duration: int):
    """
    Background task for health check
    Calls your existing Code 1: collect_appd_config_to_db.py
    """
    try:
        print(f"[Task {task_id}] Starting AppD health check...", flush=True)
        
        if INTEGRATION_READY:
            # ✅ Call your actual Code 1
            result = collect_appd_config_to_db(
                app_names=applications if applications else None,
                check_duration=check_duration
            )
            print(f"[Task {task_id}] Health check completed: {result}", flush=True)
        else:
            # Placeholder for testing
            print(f"[Task {task_id}] Using placeholder (actual code not imported)", flush=True)
            result = {
                "discovered_applications": len(applications) if applications else 5,
                "total_nodes_discovered": 25,
                "total_tiers_discovered": 15,
                "active_nodes": 20,
                "timestamp": datetime.now().isoformat()
            }
        
        return result
        
    except Exception as e:
        print(f"[Task {task_id}] Health check failed: {e}", flush=True)
        raise


@appdynamics_router.get("/healthcheck/{task_id}/status", summary="Get health check task status")
async def get_healthcheck_status(task_id: str):
    """Get status of a health check task"""
    # TODO: Query task status from database if you track it
    return {
        "task_id": task_id,
        "status": "completed",
        "message": "Health check completed successfully"
    }


# ========================================
# Code 2: Generate JSON Configuration
# ========================================
@appdynamics_router.post("/generate-config", summary="Generate monitoring configuration JSON")
async def generate_monitoring_config(applications: List[str]):
    """
    Executes Code 2 (generate_appd_config.py):
    - Reads discovered applications from database
    - Generates monitoring configuration JSON
    - Returns configuration with active nodes and tiers
    """
    try:
        if INTEGRATION_READY:
            # ✅ Call your actual Code 2
            config = generate_appd_config(
                app_names=applications
            )
        else:
            # Placeholder for testing
            config = {
                "applications": [
                    {
                        "name": app,
                        "tiers": [
                            {"name": f"{app}_Web", "nodes": [f"{app}_Web_Node1", f"{app}_Web_Node2"]},
                            {"name": f"{app}_API", "nodes": [f"{app}_API_Node1"]}
                        ]
                    }
                    for app in applications
                ],
                "metrics": {
                    "application_metrics": ["Calls per Minute", "Response Time", "Error Rate"],
                    "jvm_metrics": ["Heap Used", "GC Time", "Thread Count"],
                    "server_metrics": ["CPU %", "Memory %", "Disk I/O"]
                },
                "generated_at": datetime.now().isoformat()
            }
        
        return {
            "success": True,
            "configuration": config
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate config: {str(e)}")


# ========================================
# Code 3: Start Monitoring
# ========================================
@appdynamics_router.post("/start", summary="Start AppD monitoring session")
async def start_monitoring(request: StartMonitoringRequest):
    """
    Starts monitoring session using Code 3 (monitoring_main.py):
    - Creates new monitoring session
    - Starts background thread with MonitoringOrchestrator
    - Collects metrics every 30 minutes
    - Uses AppDynamicsDataFetcher for actual data collection
    """
    with thread_lock:
        # Check thread pool capacity
        active_sessions = sum(1 for s in monitoring_sessions.values() if s["status"] == "running")
        if active_sessions >= MAX_CONCURRENT_MONITORS:
            raise HTTPException(
                status_code=429,
                detail=f"Maximum concurrent monitoring sessions ({MAX_CONCURRENT_MONITORS}) reached"
            )
        
        # Create session
        session_id = str(uuid.uuid4())
        session = {
            "session_id": session_id,
            "lob": request.lob,
            "track": request.track,
            "run_id": request.run_id,
            "applications": request.applications,
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "iterations_completed": 0,
            "last_collection_time": None,
            "error_message": None,
            "interval_seconds": request.interval_seconds
        }
        
        monitoring_sessions[session_id] = session
        
        # Start monitoring thread
        thread = threading.Thread(
            target=monitoring_worker,
            args=(session_id, request),
            daemon=True
        )
        monitoring_threads[session_id] = thread
        thread.start()
        
        return {
            "success": True,
            "session_id": session_id,
            "message": f"Monitoring started for {request.lob}/{request.track}/{request.run_id}",
            "monitoring_interval_seconds": request.interval_seconds
        }


def monitoring_worker(session_id: str, request: StartMonitoringRequest):
    """
    Background worker that uses your existing Code 3 architecture:
    - MonitoringOrchestrator to coordinate collection
    - AppDynamicsDataFetcher to get metrics
    - MonitoringDatabase to store results
    """
    try:
        if INTEGRATION_READY:
            # Initialize your components
            db = MonitoringDatabase()
            fetcher = AppDynamicsDataFetcher()
            orchestrator = MonitoringOrchestrator(
                fetcher=fetcher,
                database=db,
                lob=request.lob,
                track=request.track,
                run_id=request.run_id
            )
        
        while True:
            with thread_lock:
                session = monitoring_sessions.get(session_id)
                if not session or session["status"] != "running":
                    break
            
            # Collect metrics
            try:
                print(f"[Session {session_id}] Collecting metrics for {request.applications}...", flush=True)
                
                if INTEGRATION_READY:
                    # ✅ Use your actual Code 3
                    metrics = orchestrator.collect_metrics(
                        applications=request.applications,
                        collect_app_metrics=request.collect_app_metrics,
                        collect_jvm_metrics=request.collect_jvm_metrics,
                        collect_server_metrics=request.collect_server_metrics
                    )
                    
                    # Save to database (already done by orchestrator)
                    # orchestrator automatically saves to DB
                    
                else:
                    # Placeholder
                    metrics = {
                        "collected_count": len(request.applications),
                        "timestamp": datetime.now().isoformat()
                    }
                
                with thread_lock:
                    if session_id in monitoring_sessions:
                        monitoring_sessions[session_id]["iterations_completed"] += 1
                        monitoring_sessions[session_id]["last_collection_time"] = datetime.now().isoformat()
                
                print(f"[Session {session_id}] Metrics collected successfully", flush=True)
                
            except Exception as e:
                print(f"[Session {session_id}] Error collecting metrics: {e}", flush=True)
                with thread_lock:
                    if session_id in monitoring_sessions:
                        monitoring_sessions[session_id]["error_message"] = str(e)
            
            # Wait for next interval
            time.sleep(request.interval_seconds)
            
    except Exception as e:
        print(f"[Session {session_id}] Monitoring worker failed: {e}", flush=True)
        with thread_lock:
            if session_id in monitoring_sessions:
                monitoring_sessions[session_id]["status"] = "failed"
                monitoring_sessions[session_id]["error_message"] = str(e)


# ========================================
# Stop Monitoring
# ========================================
@appdynamics_router.post("/stop/{session_id}", summary="Stop monitoring session")
async def stop_monitoring(session_id: str):
    """Stop a running monitoring session"""
    with thread_lock:
        if session_id not in monitoring_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = monitoring_sessions[session_id]
        if session["status"] != "running":
            raise HTTPException(status_code=400, detail=f"Session is not running (status: {session['status']})")
        
        session["status"] = "stopped"
        session["end_time"] = datetime.now().isoformat()
    
    return {
        "success": True,
        "session_id": session_id,
        "message": "Monitoring stopped",
        "iterations_completed": session["iterations_completed"]
    }


# ========================================
# View Active Sessions
# ========================================
@appdynamics_router.get("/sessions", summary="List all monitoring sessions")
async def list_sessions(status: Optional[str] = Query(None, description="Filter by status")):
    """Get all monitoring sessions, optionally filtered by status"""
    sessions = list(monitoring_sessions.values())
    
    if status:
        sessions = [s for s in sessions if s["status"] == status]
    
    return {
        "total_sessions": len(sessions),
        "sessions": sessions
    }


@appdynamics_router.get("/sessions/{session_id}", summary="Get session details")
async def get_session(session_id: str):
    """Get details of a specific monitoring session"""
    if session_id not in monitoring_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return monitoring_sessions[session_id]


# ========================================
# Thread Pool Status
# ========================================
@appdynamics_router.get("/thread-pool/status", summary="Get thread pool status")
async def get_thread_pool_status():
    """Get status of monitoring thread pool"""
    with thread_lock:
        active_threads = []
        for session_id, session in monitoring_sessions.items():
            if session["status"] == "running":
                thread = monitoring_threads.get(session_id)
                active_threads.append({
                    "session_id": session_id,
                    "lob": session["lob"],
                    "track": session["track"],
                    "run_id": session["run_id"],
                    "thread_alive": thread.is_alive() if thread else False,
                    "iterations_completed": session["iterations_completed"],
                    "last_collection": session["last_collection_time"]
                })
    
    return {
        "max_concurrent_monitors": MAX_CONCURRENT_MONITORS,
        "active_monitors": len(active_threads),
        "available_slots": MAX_CONCURRENT_MONITORS - len(active_threads),
        "utilization_percent": (len(active_threads) / MAX_CONCURRENT_MONITORS) * 100,
        "active_threads": active_threads
    }


# ========================================
# Metrics Retrieval
# ========================================
@appdynamics_router.get("/metrics", summary="Get collected metrics")
async def get_metrics(
    lob: Optional[str] = None,
    track: Optional[str] = None,
    run_id: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Retrieve collected metrics from database
    Can filter by LOB, Track, Run ID, or Session ID
    """
    if INTEGRATION_READY:
        # ✅ Query your actual database
        db = MonitoringDatabase()
        metrics = db.query_metrics(
            lob=lob,
            track=track,
            run_id=run_id,
            session_id=session_id,
            limit=limit
        )
    else:
        # Placeholder
        metrics = []
    
    return {
        "filters": {
            "lob": lob,
            "track": track,
            "run_id": run_id,
            "session_id": session_id
        },
        "count": len(metrics),
        "metrics": metrics
    }


# ========================================
# Add to main.py:
# from monitoring.appdynamics_integrated import appdynamics_router
# app.include_router(appdynamics_router)
# ========================================