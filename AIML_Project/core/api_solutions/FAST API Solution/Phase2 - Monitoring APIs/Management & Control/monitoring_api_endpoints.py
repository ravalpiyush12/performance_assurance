"""
Monitoring API Endpoints
FastAPI endpoints for all monitoring systems
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from security import verify_api_key_dependency
from unified_monitoring_manager import (
    UnifiedMonitoringManager,
    MonitoringSystem,
    MonitoringStatus
)
from audit import AuditLogger

# Create monitoring router
monitoring_router = APIRouter(prefix="/api/v1/monitoring", tags=["Monitoring"])


# Request/Response Models
class StartMonitoringRequest(BaseModel):
    """Start monitoring request"""
    system: str = Field(..., description="Monitoring system (appdynamics/kibana/splunk/mongodb/all)")
    parameters: Optional[Dict[str, Any]] = Field(default={}, description="System-specific parameters")


class StopMonitoringRequest(BaseModel):
    """Stop monitoring request"""
    system: str = Field(..., description="Monitoring system to stop")


class MonitoringStatusResponse(BaseModel):
    """Monitoring status response"""
    status: str
    timestamp: str
    systems: Dict[str, Any]


# ========================================
# UNIFIED MONITORING CONTROL ENDPOINTS
# ========================================

@monitoring_router.post("/start", tags=["Unified Control"])
async def start_monitoring(
    request: StartMonitoringRequest,
    api_key: str = Depends(verify_api_key_dependency)
):
    """
    Start monitoring for specified system(s)
    
    Systems: appdynamics, kibana, splunk, mongodb, all
    
    Parameters examples:
    - AppDynamics: {"application_name": "MyApp", "duration_minutes": 60}
    - Kibana: {"index_pattern": "logs-*", "time_range_minutes": 60}
    - Splunk: {"index": "main", "time_range_minutes": 60}
    - MongoDB: {"database_name": "mydb", "collections": ["users"]}
    """
    from main import app
    
    monitoring_manager: UnifiedMonitoringManager = app.state.monitoring_manager
    audit_logger: AuditLogger = app.state.audit_logger
    
    try:
        # Validate system
        try:
            system_enum = MonitoringSystem(request.system.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid monitoring system: {request.system}. Valid: {[s.value for s in MonitoringSystem]}"
            )
        
        # Start monitoring
        result = monitoring_manager.start_monitoring(
            system=system_enum,
            **request.parameters
        )
        
        # Audit log
        audit_logger.log_request(
            request_id=f"mon-start-{datetime.now().timestamp()}",
            username=api_key[:10],
            api_key=api_key,
            operation_type="MONITORING_START",
            sql_preview=f"System: {request.system}",
            metadata={"system": request.system, "parameters": request.parameters}
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start monitoring: {str(e)}"
        )


@monitoring_router.post("/stop", tags=["Unified Control"])
async def stop_monitoring(
    request: StopMonitoringRequest,
    api_key: str = Depends(verify_api_key_dependency)
):
    """
    Stop monitoring for specified system(s)
    
    Systems: appdynamics, kibana, splunk, mongodb, all
    """
    from main import app
    
    monitoring_manager: UnifiedMonitoringManager = app.state.monitoring_manager
    audit_logger: AuditLogger = app.state.audit_logger
    
    try:
        # Validate system
        try:
            system_enum = MonitoringSystem(request.system.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid monitoring system: {request.system}"
            )
        
        # Stop monitoring
        result = monitoring_manager.stop_monitoring(system=system_enum)
        
        # Audit log
        audit_logger.log_request(
            request_id=f"mon-stop-{datetime.now().timestamp()}",
            username=api_key[:10],
            api_key=api_key,
            operation_type="MONITORING_STOP",
            sql_preview=f"System: {request.system}",
            metadata={"system": request.system}
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop monitoring: {str(e)}"
        )


@monitoring_router.get("/status", tags=["Unified Control"])
async def get_monitoring_status(
    system: Optional[str] = Query(None, description="Specific system or leave empty for all"),
    api_key: str = Depends(verify_api_key_dependency)
):
    """
    Get monitoring status for all or specific system
    
    Leave system parameter empty to get status of all systems
    """
    from main import app
    
    monitoring_manager: UnifiedMonitoringManager = app.state.monitoring_manager
    
    try:
        if system:
            try:
                system_enum = MonitoringSystem(system.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid monitoring system: {system}"
                )
            return monitoring_manager.get_status(system=system_enum)
        else:
            return monitoring_manager.get_status()
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitoring status: {str(e)}"
        )


@monitoring_router.get("/dashboard", tags=["Unified Control"])
async def get_monitoring_dashboard(
    api_key: str = Depends(verify_api_key_dependency)
):
    """
    Get comprehensive monitoring dashboard data
    
    Returns status and metrics for all configured monitoring systems
    """
    from main import app
    
    monitoring_manager: UnifiedMonitoringManager = app.state.monitoring_manager
    
    try:
        return monitoring_manager.get_dashboard_data()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard data: {str(e)}"
        )


# ========================================
# APPDYNAMICS ENDPOINTS
# ========================================

@monitoring_router.get("/appdynamics/metrics", tags=["AppDynamics"])
async def get_appdynamics_metrics(
    metric_path: str = Query("Overall Application Performance|*", description="Metric path"),
    time_range_minutes: int = Query(15, description="Time range in minutes"),
    api_key: str = Depends(verify_api_key_dependency)
):
    """
    Fetch metrics from AppDynamics
    """
    from main import app
    
    monitoring_manager: UnifiedMonitoringManager = app.state.monitoring_manager
    
    if MonitoringSystem.APPDYNAMICS not in monitoring_manager.monitors:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AppDynamics monitoring not configured"
        )
    
    try:
        monitor = monitoring_manager.monitors[MonitoringSystem.APPDYNAMICS]
        return monitor.fetch_metrics(
            metric_path=metric_path,
            time_range_minutes=time_range_minutes
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch metrics: {str(e)}"
        )


@monitoring_router.get("/appdynamics/business-transactions", tags=["AppDynamics"])
async def get_business_transactions(
    api_key: str = Depends(verify_api_key_dependency)
):
    """
    Get business transactions from AppDynamics
    """
    from main import app
    
    monitoring_manager: UnifiedMonitoringManager = app.state.monitoring_manager
    
    if MonitoringSystem.APPDYNAMICS not in monitoring_manager.monitors:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AppDynamics monitoring not configured"
        )
    
    try:
        monitor = monitoring_manager.monitors[MonitoringSystem.APPDYNAMICS]
        return monitor.get_business_transactions()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch business transactions: {str(e)}"
        )


# ========================================
# KIBANA ENDPOINTS
# ========================================

@monitoring_router.get("/kibana/logs", tags=["Kibana"])
async def fetch_kibana_logs(
    time_range_minutes: int = Query(15, description="Time range in minutes"),
    size: int = Query(100, description="Number of logs to fetch"),
    log_level: Optional[str] = Query(None, description="Filter by log level"),
    api_key: str = Depends(verify_api_key_dependency)
):
    """
    Fetch logs from Kibana/Elasticsearch
    """
    from main import app
    
    monitoring_manager: UnifiedMonitoringManager = app.state.monitoring_manager
    
    if MonitoringSystem.KIBANA not in monitoring_manager.monitors:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kibana monitoring not configured"
        )
    
    try:
        monitor = monitoring_manager.monitors[MonitoringSystem.KIBANA]
        return monitor.fetch_logs(
            time_range_minutes=time_range_minutes,
            size=size,
            log_level=log_level
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch logs: {str(e)}"
        )


@monitoring_router.get("/kibana/errors", tags=["Kibana"])
async def search_kibana_errors(
    time_range_minutes: int = Query(60, description="Time range in minutes"),
    size: int = Query(50, description="Number of errors to fetch"),
    api_key: str = Depends(verify_api_key_dependency)
):
    """
    Search for error logs in Kibana
    """
    from main import app
    
    monitoring_manager: UnifiedMonitoringManager = app.state.monitoring_manager
    
    if MonitoringSystem.KIBANA not in monitoring_manager.monitors:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kibana monitoring not configured"
        )
    
    try:
        monitor = monitoring_manager.monitors[MonitoringSystem.KIBANA]
        return monitor.search_errors(
            time_range_minutes=time_range_minutes,
            size=size
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search errors: {str(e)}"
        )


@monitoring_router.get("/kibana/statistics", tags=["Kibana"])
async def get_kibana_statistics(
    time_range_minutes: int = Query(60, description="Time range in minutes"),
    api_key: str = Depends(verify_api_key_dependency)
):
    """
    Get log statistics from Kibana
    """
    from main import app
    
    monitoring_manager: UnifiedMonitoringManager = app.state.monitoring_manager
    
    if MonitoringSystem.KIBANA not in monitoring_manager.monitors:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kibana monitoring not configured"
        )
    
    try:
        monitor = monitoring_manager.monitors[MonitoringSystem.KIBANA]
        return monitor.get_log_statistics(time_range_minutes=time_range_minutes)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


# ========================================
# SPLUNK ENDPOINTS
# ========================================

@monitoring_router.post("/splunk/search", tags=["Splunk"])
async def splunk_search(
    search_query: str = Query(..., description="SPL search query"),
    earliest_time: str = Query("-15m", description="Earliest time"),
    latest_time: str = Query("now", description="Latest time"),
    max_results: int = Query(100, description="Maximum results"),
    api_key: str = Depends(verify_api_key_dependency)
):
    """
    Execute Splunk search query
    """
    from main import app
    
    monitoring_manager: UnifiedMonitoringManager = app.state.monitoring_manager
    
    if MonitoringSystem.SPLUNK not in monitoring_manager.monitors:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Splunk monitoring not configured"
        )
    
    try:
        monitor = monitoring_manager.monitors[MonitoringSystem.SPLUNK]
        return monitor.search_events(
            search_query=search_query,
            earliest_time=earliest_time,
            latest_time=latest_time,
            max_results=max_results
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute search: {str(e)}"
        )


@monitoring_router.get("/splunk/errors", tags=["Splunk"])
async def search_splunk_errors(
    time_range_minutes: int = Query(60, description="Time range in minutes"),
    max_results: int = Query(50, description="Maximum results"),
    api_key: str = Depends(verify_api_key_dependency)
):
    """
    Search for error events in Splunk
    """
    from main import app
    
    monitoring_manager: UnifiedMonitoringManager = app.state.monitoring_manager
    
    if MonitoringSystem.SPLUNK not in monitoring_manager.monitors:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Splunk monitoring not configured"
        )
    
    try:
        monitor = monitoring_manager.monitors[MonitoringSystem.SPLUNK]
        return monitor.search_errors(
            time_range_minutes=time_range_minutes,
            max_results=max_results
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search errors: {str(e)}"
        )


@monitoring_router.get("/splunk/statistics", tags=["Splunk"])
async def get_splunk_statistics(
    time_range_minutes: int = Query(60, description="Time range in minutes"),
    api_key: str = Depends(verify_api_key_dependency)
):
    """
    Get event statistics from Splunk
    """
    from main import app
    
    monitoring_manager: UnifiedMonitoringManager = app.state.monitoring_manager
    
    if MonitoringSystem.SPLUNK not in monitoring_manager.monitors:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Splunk monitoring not configured"
        )
    
    try:
        monitor = monitoring_manager.monitors[MonitoringSystem.SPLUNK]
        return monitor.get_event_statistics(time_range_minutes=time_range_minutes)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


# ========================================
# MONGODB ENDPOINTS
# ========================================

@monitoring_router.get("/mongodb/collection/{collection_name}", tags=["MongoDB"])
async def analyze_mongodb_collection(
    collection_name: str,
    sample_size: int = Query(1000, description="Sample size for analysis"),
    api_key: str = Depends(verify_api_key_dependency)
):
    """
    Analyze a specific MongoDB collection
    """
    from main import app
    
    monitoring_manager: UnifiedMonitoringManager = app.state.monitoring_manager
    
    if MonitoringSystem.MONGODB not in monitoring_manager.monitors:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MongoDB monitoring not configured"
        )
    
    try:
        monitor = monitoring_manager.monitors[MonitoringSystem.MONGODB]
        return monitor.analyze_collection(
            collection_name=collection_name,
            sample_size=sample_size
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze collection: {str(e)}"
        )


@monitoring_router.get("/mongodb/collections", tags=["MongoDB"])
async def analyze_all_mongodb_collections(
    api_key: str = Depends(verify_api_key_dependency)
):
    """
    Analyze all collections in MongoDB database
    """
    from main import app
    
    monitoring_manager: UnifiedMonitoringManager = app.state.monitoring_manager
    
    if MonitoringSystem.MONGODB not in monitoring_manager.monitors:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MongoDB monitoring not configured"
        )
    
    try:
        monitor = monitoring_manager.monitors[MonitoringSystem.MONGODB]
        return monitor.analyze_all_collections()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze collections: {str(e)}"
        )


@monitoring_router.get("/mongodb/slow-queries", tags=["MongoDB"])
async def get_mongodb_slow_queries(
    threshold_ms: int = Query(100, description="Slow query threshold in ms"),
    limit: int = Query(50, description="Maximum results"),
    api_key: str = Depends(verify_api_key_dependency)
):
    """
    Get slow queries from MongoDB profiling
    """
    from main import app
    
    monitoring_manager: UnifiedMonitoringManager = app.state.monitoring_manager
    
    if MonitoringSystem.MONGODB not in monitoring_manager.monitors:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MongoDB monitoring not configured"
        )
    
    try:
        monitor = monitoring_manager.monitors[MonitoringSystem.MONGODB]
        return monitor.get_slow_queries(
            threshold_ms=threshold_ms,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get slow queries: {str(e)}"
        )


@monitoring_router.get("/mongodb/statistics", tags=["MongoDB"])
async def get_mongodb_statistics(
    api_key: str = Depends(verify_api_key_dependency)
):
    """
    Get comprehensive MongoDB database statistics
    """
    from main import app
    
    monitoring_manager: UnifiedMonitoringManager = app.state.monitoring_manager
    
    if MonitoringSystem.MONGODB not in monitoring_manager.monitors:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MongoDB monitoring not configured"
        )
    
    try:
        monitor = monitoring_manager.monitors[MonitoringSystem.MONGODB]
        return monitor.get_database_statistics()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )