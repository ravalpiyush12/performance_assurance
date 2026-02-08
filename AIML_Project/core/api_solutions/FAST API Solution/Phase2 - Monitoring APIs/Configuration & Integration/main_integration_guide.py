"""
Integration Code for Main Application (main.py)
Add this code to integrate monitoring into your existing FastAPI application
"""

# ========================================
# 1. ADD IMPORTS AT THE TOP OF main.py
# ========================================

from monitoring_api_endpoints import monitoring_router
from unified_monitoring_manager import UnifiedMonitoringManager
from config_monitoring import get_settings  # Replace existing config import


# ========================================
# 2. MODIFY THE STARTUP EVENT
# ========================================

@app.on_event("startup")
async def startup_event():
    """Initialize application resources"""
    logger.info("Starting Oracle SQL API with Monitoring...")
    
    # Load settings
    settings = get_settings()
    app.state.settings = settings
    
    # Initialize security manager
    app.state.security_manager = SecurityManager(settings)
    logger.info("Security manager initialized")
    
    # Initialize audit logger
    app.state.audit_logger = AuditLogger(settings)
    logger.info(f"Audit logging {'enabled' if settings.ENABLE_AUDIT_LOG else 'disabled'}")
    
    # Initialize Oracle connection pool
    app.state.oracle_pool = OracleConnectionPool(settings)
    try:
        app.state.oracle_pool.initialize()
        logger.info("Oracle connection pool initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Oracle connection pool: {e}")
    
    # Initialize SQL executor
    app.state.sql_executor = SQLExecutor(app.state.oracle_pool, settings)
    
    # ========================================
    # NEW: Initialize Monitoring Manager
    # ========================================
    try:
        app.state.monitoring_manager = UnifiedMonitoringManager(settings)
        enabled_systems = settings.get_enabled_monitors()
        logger.info(f"Monitoring manager initialized. Enabled systems: {enabled_systems}")
    except Exception as e:
        logger.error(f"Failed to initialize monitoring manager: {e}")
        # Continue without monitoring
        app.state.monitoring_manager = None
    
    logger.info(f"Application started successfully in {settings.ENVIRONMENT} environment")


# ========================================
# 3. MODIFY THE SHUTDOWN EVENT
# ========================================

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup application resources"""
    logger.info("Shutting down Oracle SQL API...")
    
    # Close connection pool
    if hasattr(app.state, 'oracle_pool'):
        app.state.oracle_pool.close()
    
    # ========================================
    # NEW: Cleanup Monitoring
    # ========================================
    if hasattr(app.state, 'monitoring_manager') and app.state.monitoring_manager:
        try:
            app.state.monitoring_manager.cleanup()
            logger.info("Monitoring manager cleaned up")
        except Exception as e:
            logger.error(f"Error during monitoring cleanup: {e}")
    
    logger.info("Application shutdown complete")


# ========================================
# 4. REGISTER MONITORING ROUTER
# Add this line after app initialization
# ========================================

# Include monitoring router
app.include_router(monitoring_router)


# ========================================
# 5. OPTIONAL: UPDATE HEALTH CHECK TO INCLUDE MONITORING STATUS
# ========================================

@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check():
    """
    Health check endpoint with monitoring status
    """
    settings: Settings = app.state.settings
    pool: OracleConnectionPool = app.state.oracle_pool
    
    # Check database connectivity
    db_status = {"status": "unknown"}
    try:
        with pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM DUAL")
            cursor.fetchone()
            cursor.close()
            db_status = {"status": "healthy", "message": "Connection successful"}
    except Exception as e:
        db_status = {"status": "unhealthy", "error": str(e)}
    
    # Get pool status
    pool_status = pool.get_pool_status()
    
    # NEW: Get monitoring status
    monitoring_status = {"status": "not_initialized"}
    if hasattr(app.state, 'monitoring_manager') and app.state.monitoring_manager:
        try:
            monitoring_status = {
                "status": "initialized",
                "enabled_systems": settings.get_enabled_monitors(),
                "active_systems": sum(
                    1 for s, status in app.state.monitoring_manager.status.items()
                    if status.value == "running"
                )
            }
        except Exception as e:
            monitoring_status = {"status": "error", "error": str(e)}
    
    overall_status = "healthy" if db_status["status"] == "healthy" else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now().isoformat(),
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        database_status=db_status,
        pool_status=pool_status,
        monitoring_status=monitoring_status  # NEW field
    )


# ========================================
# 6. UPDATE HealthResponse MODEL (if using Pydantic)
# ========================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str
    environment: str
    database_status: Dict[str, Any]
    pool_status: Dict[str, Any]
    monitoring_status: Optional[Dict[str, Any]] = None  # NEW field


# ========================================
# THAT'S IT! Your monitoring is now integrated.
# ========================================

"""
The monitoring API endpoints are now available at:

UNIFIED CONTROL:
- POST   /api/v1/monitoring/start              - Start monitoring
- POST   /api/v1/monitoring/stop               - Stop monitoring  
- GET    /api/v1/monitoring/status             - Get status
- GET    /api/v1/monitoring/dashboard          - Dashboard data

APPDYNAMICS:
- GET    /api/v1/monitoring/appdynamics/metrics
- GET    /api/v1/monitoring/appdynamics/business-transactions

KIBANA:
- GET    /api/v1/monitoring/kibana/logs
- GET    /api/v1/monitoring/kibana/errors
- GET    /api/v1/monitoring/kibana/statistics

SPLUNK:
- POST   /api/v1/monitoring/splunk/search
- GET    /api/v1/monitoring/splunk/errors
- GET    /api/v1/monitoring/splunk/statistics

MONGODB:
- GET    /api/v1/monitoring/mongodb/collection/{name}
- GET    /api/v1/monitoring/mongodb/collections
- GET    /api/v1/monitoring/mongodb/slow-queries
- GET    /api/v1/monitoring/mongodb/statistics
"""