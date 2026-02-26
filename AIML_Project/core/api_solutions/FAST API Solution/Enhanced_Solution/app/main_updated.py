"""
Complete main.py with Oracle SQL API + AppDynamics Integration
Supports all existing Oracle SQL functionality plus AppD monitoring
"""
from fastapi import FastAPI, HTTPException, Request, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List
from contextlib import asynccontextmanager
import logging
from pathlib import Path
from datetime import datetime

# Core imports
from config.settings import get_settings
from database.connection_manager import ConnectionManager
from core.security import verify_api_key
from database.sql_executor import execute_query
from utils.audit import log_audit

# AppDynamics monitoring
from monitoring.appd.routes import router as appd_router, initialize_appd_components

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Pydantic models for Oracle SQL API
class SQLExecuteRequest(BaseModel):
    database: str
    query: str
    
    class Config:
        schema_extra = {
            "example": {
                "database": "CQE_NFT",
                "query": "SELECT * FROM your_table WHERE id = 1"
            }
        }


class SQLExecuteResponse(BaseModel):
    columns: List[str]
    rows: List[List]
    row_count: int
    execution_time: float


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("="  * 60)
    logger.info("Starting CQE NFT Monitoring API Solutions")
    logger.info("=" * 60)
    
    try:
        # Initialize settings
        settings = get_settings()
        logger.info(f"Environment: {settings.ENVIRONMENT}")
        logger.info(f"Version: {settings.VERSION}")
        
        # Initialize Oracle connection pools
        logger.info("Initializing Oracle connection pools...")
        app.state.connection_manager = ConnectionManager(settings)
        app.state.connection_manager.initialize_pools()
        logger.info("✓ Oracle pools initialized")
        
        # Log available databases
        for db_name in app.state.connection_manager.pools.keys():
            logger.info(f"  - {db_name} pool ready")
        
        # Initialize AppDynamics monitoring
        logger.info("Initializing AppDynamics monitoring...")
        try:
            # Get main Oracle pool for AppD
            oracle_pool = app.state.connection_manager.pools.get('CQE_NFT')
            if oracle_pool and oracle_pool.pool:
                initialize_appd_components(oracle_pool.pool)
                logger.info("✓ AppDynamics monitoring initialized")
            else:
                logger.warning("⚠ Oracle pool not available for AppDynamics")
        except Exception as e:
            logger.error(f"✗ AppDynamics initialization failed: {e}")
            logger.warning("Application will start without AppD monitoring")
        
        logger.info("=" * 60)
        logger.info("✓ Application started successfully")
        logger.info(f"✓ Listening on port: {settings.PORT}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"✗ Startup failed: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("=" * 60)
    logger.info("Shutting down application...")
    logger.info("=" * 60)
    
    try:
        if hasattr(app.state, 'connection_manager'):
            logger.info("Closing database connections...")
            app.state.connection_manager.close_all()
            logger.info("✓ Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    
    logger.info("✓ Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="CQE NFT Monitoring API Solutions",
    description="Multi-Database SQL Execution + Integrated Monitoring (AppDynamics, Kibana, MongoDB)",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Templates
templates = Jinja2Templates(directory="templates")


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if app.debug else "An error occurred"
        }
    )


# ==========================================
# Core Endpoints
# ==========================================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint - serve main UI"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    Returns status of application and database connections
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": get_settings().VERSION,
            "environment": get_settings().ENVIRONMENT,
            "databases": {}
        }
        
        # Check database connections
        if hasattr(app.state, 'connection_manager'):
            for db_name, pool_wrapper in app.state.connection_manager.pools.items():
                try:
                    conn = pool_wrapper.pool.acquire()
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1 FROM DUAL")
                    cursor.fetchone()
                    cursor.close()
                    conn.close()
                    
                    health_status["databases"][db_name] = {
                        "status": "healthy",
                        "type": pool_wrapper.config.get('type', 'unknown')
                    }
                except Exception as e:
                    health_status["databases"][db_name] = {
                        "status": "unhealthy",
                        "error": str(e)
                    }
                    health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.get("/api/v1/databases")
async def get_databases():
    """Get list of available databases"""
    try:
        databases = []
        if hasattr(app.state, 'connection_manager'):
            for db_name, pool_wrapper in app.state.connection_manager.pools.items():
                databases.append({
                    "name": db_name,
                    "status": "available",
                    "type": pool_wrapper.config.get('type', 'Oracle'),
                    "allowed_operations": pool_wrapper.config.get('allowed_operations', ['SELECT'])
                })
        
        return {
            "total_databases": len(databases),
            "databases": databases
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Oracle SQL API Endpoints
# ==========================================

@app.post("/api/v1/sql/execute", response_model=SQLExecuteResponse)
async def execute_sql(
    request: SQLExecuteRequest,
    x_api_key: str = Header(..., alias="X-API-Key")
):
    """
    Execute SQL query on specified database
    
    Requires valid API key in X-API-Key header
    """
    start_time = datetime.now()
    
    try:
        # Verify API key
        api_key_valid = verify_api_key(x_api_key, request.database)
        if not api_key_valid:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Get connection pool
        if not hasattr(app.state, 'connection_manager'):
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        pool_wrapper = app.state.connection_manager.pools.get(request.database)
        if not pool_wrapper:
            raise HTTPException(status_code=404, detail=f"Database {request.database} not found")
        
        # Execute query
        result = execute_query(pool_wrapper.pool, request.query)
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Log audit
        log_audit(
            database=request.database,
            query=request.query,
            user=x_api_key[:8] + "...",
            success=True,
            row_count=len(result['rows'])
        )
        
        return SQLExecuteResponse(
            columns=result['columns'],
            rows=result['rows'],
            row_count=len(result['rows']),
            execution_time=execution_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SQL execution failed: {e}")
        
        # Log audit failure
        log_audit(
            database=request.database,
            query=request.query,
            user=x_api_key[:8] + "...",
            success=False,
            error=str(e)
        )
        
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/logs")
async def get_audit_logs(limit: int = 100):
    """Get recent audit logs"""
    try:
        # Get main Oracle pool
        if not hasattr(app.state, 'connection_manager'):
            raise HTTPException(status_code=503, detail="Database not available")
        
        pool_wrapper = app.state.connection_manager.pools.get('CQE_NFT')
        if not pool_wrapper:
            raise HTTPException(status_code=404, detail="Audit database not found")
        
        conn = pool_wrapper.pool.acquire()
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT * FROM (
                SELECT 
                    LOG_ID,
                    DATABASE_NAME,
                    QUERY_TEXT,
                    USERNAME,
                    EXECUTED_AT,
                    SUCCESS,
                    ROW_COUNT,
                    ERROR_MESSAGE
                FROM AUDIT_LOGS
                ORDER BY EXECUTED_AT DESC
            ) WHERE ROWNUM <= {limit}
        """)
        
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        logs = []
        for row in rows:
            log_dict = dict(zip(columns, row))
            # Convert datetime to string
            if log_dict.get('EXECUTED_AT'):
                log_dict['EXECUTED_AT'] = log_dict['EXECUTED_AT'].isoformat()
            logs.append(log_dict)
        
        return {
            "total_logs": len(logs),
            "logs": logs
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/config/environment")
async def get_environment_info():
    """Get environment configuration info"""
    settings = get_settings()
    return {
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
        "debug": app.debug
    }


# ==========================================
# Include Routers
# ==========================================

# AppDynamics Monitoring
app.include_router(
    appd_router,
    prefix="/api/v1/monitoring/appd",
    tags=["AppDynamics Monitoring"]
)

# TODO: Add Kibana monitoring router
# from monitoring.kibana.routes import router as kibana_router
# app.include_router(
#     kibana_router,
#     prefix="/api/v1/monitoring/kibana",
#     tags=["Kibana Monitoring"]
# )

# TODO: Add MongoDB monitoring router
# from monitoring.mongodb.routes import router as mongodb_router
# app.include_router(
#     mongodb_router,
#     prefix="/api/v1/monitoring/mongodb",
#     tags=["MongoDB Monitoring"]
# )


# ==========================================
# Static files (if needed)
# ==========================================
# app.mount("/static", StaticFiles(directory="static"), name="static")


# ==========================================
# Development runner
# ==========================================
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


"""
Production deployment:

1. Using Gunicorn:
   gunicorn main:app \
     --workers 4 \
     --worker-class uvicorn.workers.UvicornWorker \
     --bind 0.0.0.0:8000 \
     --log-level info \
     --access-logfile logs/access.log \
     --error-logfile logs/error.log

2. Using Uvicorn:
   uvicorn main:app \
     --host 0.0.0.0 \
     --port 8000 \
     --workers 4 \
     --log-level info

3. With systemd service (/etc/systemd/system/cqe-api.service):
   [Unit]
   Description=CQE NFT Monitoring API
   After=network.target
   
   [Service]
   Type=notify
   User=your_user
   WorkingDirectory=/path/to/project
   Environment="PATH=/path/to/venv/bin"
   ExecStart=/path/to/venv/bin/gunicorn main:app \
     --workers 4 \
     --worker-class uvicorn.workers.UvicornWorker \
     --bind 0.0.0.0:8000
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
"""