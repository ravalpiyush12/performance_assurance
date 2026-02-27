"""
Enhanced Oracle SQL API - Multi-Database with AppDynamics Integration
Complete main.py with all integrations:
- 7 Oracle databases with individual authentication
- Config API endpoints for frontend
- Audit API endpoints  
- Dual audit logging (JSONL + Oracle DB)
- Client IP tracking
- Enhanced UI with auto API key detection
- AppDynamics monitoring integration

FastAPI 0.88.0 + Pydantic 1.10.x Compatible
"""
import sys
import logging
from fastapi import FastAPI, Request, Depends, HTTPException, UploadFile, File, status, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)

logger = logging.getLogger(__name__)

# ========================================
# Import Configuration and Managers
# ========================================
from app.config.settings import get_settings, Settings, DatabaseConfig
from app.config.database_config import get_databases_config
from app.core.security import SecurityManager
from app.core.sql_validator import SQLValidator
from app.database.connection_manager import ConnectionManager
from app.database.sql_executor import SQLExecutor
from app.utils.audit import AuditLogger

# AppDynamics monitoring
from monitoring.appd.routes import router as appd_router, initialize_appd_components

# ========================================
# Global Initialization (for preload_app)
# ========================================
print("\n" + "=" * 80, flush=True)
print("ORACLE SQL API - MULTI-DATABASE INITIALIZATION", flush=True)
print("=" * 80 + "\n", flush=True)
sys.stdout.flush()

# Initialize global objects
_settings = None
_connection_manager = None
_security_managers = {}  # One per database
_audit_logger = None
_sql_executors = {}  # One per database

try:
    # Load settings
    print("Loading settings...", flush=True)
    _settings = get_settings()
    print(f"✓ Settings loaded: {_settings.APP_VERSION}", flush=True)
    sys.stdout.flush()
    
    # Initialize connection manager
    print("\nInitializing connection manager...", flush=True)
    _connection_manager = ConnectionManager(_settings)
    _connection_manager.initialize_all()
    print(f"✓ Connection manager initialized: {len(_connection_manager.pools)} databases", flush=True)
    sys.stdout.flush()
    
    # Get CQE_NFT pool for audit logging
    cqe_nft_pool = _connection_manager.get_pool("CQE_NFT")
    
    # Initialize dual audit logger (JSONL + Oracle DB)
    print("\nInitializing dual audit logger...", flush=True)
    _audit_logger = AuditLogger(_settings, cqe_nft_pool=cqe_nft_pool)
    print("✓ Audit logger initialized", flush=True)
    print(f"  File audit: {'Enabled' if _audit_logger.file_audit_enabled else 'Disabled'}", flush=True)
    print(f"  DB audit: {'Enabled' if _audit_logger.db_audit_enabled else 'Disabled'}", flush=True)
    sys.stdout.flush()
    
    # Initialize security managers and SQL executors for each database
    print("\nInitializing database-specific components...", flush=True)
    databases = _settings.get_databases()
    
    for db_name, db_config in databases.items():
        # Security manager
        _security_managers[db_name] = SecurityManager(db_config)
        
        # SQL executor (if pool exists)
        pool = _connection_manager.get_pool(db_name)
        if pool:
            _sql_executors[db_name] = SQLExecutor(pool, db_config)
            print(f"  ✓ {db_name}: Security + Executor ready", flush=True)
        else:
            print(f"  ✗ {db_name}: Pool unavailable, skipping executor", flush=True)
    
    sys.stdout.flush()
    
    print("\n" + "=" * 80, flush=True)
    print("✓ INITIALIZATION COMPLETE", flush=True)
    print(f"  Available: {', '.join(_connection_manager.get_available_databases())}", flush=True)
    if _connection_manager.failed_databases:
        print(f"  Failed: {', '.join(_connection_manager.failed_databases.keys())}", flush=True)
    print("=" * 80 + "\n", flush=True)
    sys.stdout.flush()
    
except Exception as e:
    print(f"\n✗ INITIALIZATION FAILED: {e}", flush=True)
    import traceback
    traceback.print_exc(file=sys.stdout)
    sys.stdout.flush()
    raise


# ========================================
# Create FastAPI App
# ========================================
app = FastAPI(
    title="Oracle SQL API - Multi-Database with AppDynamics",
    description="Multi-database Oracle SQL API with integrated monitoring UI and AppDynamics",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

if os.path.exists("templates"):
    templates = Jinja2Templates(directory="templates")


# ========================================
# Startup/Shutdown Events
# ========================================
@app.on_event("startup")
async def startup_event():
    """Assign pre-initialized objects to app.state"""
    print("FastAPI startup: Assigning app.state", flush=True)
    
    app.state.settings = _settings
    app.state.connection_manager = _connection_manager
    app.state.security_managers = _security_managers
    app.state.audit_logger = _audit_logger
    app.state.sql_executors = _sql_executors

    # Initialize AppDynamics monitoring
    print("Initializing AppDynamics monitoring...", flush=True)
    try:
        oracle_pool = app.state.connection_manager.get_pool('CQE_NFT')
        if oracle_pool:
            initialize_appd_components(oracle_pool.pool)
            print("✓ AppDynamics monitoring initialized", flush=True)
        else:
            print("⚠ Oracle pool not available for AppDynamics", flush=True)
    except Exception as e:
        print(f"✗ AppDynamics initialization failed: {e}", flush=True)
        import traceback
        traceback.print_exc(file=sys.stdout)
    
    print("✓ app.state assigned", flush=True)
    sys.stdout.flush()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Shutting down...", flush=True)
    
    if hasattr(app.state, 'connection_manager'):
        app.state.connection_manager.close_all()
    
    print("✓ Shutdown complete", flush=True)
    sys.stdout.flush()


# ========================================
# Pydantic Models
# ========================================
class SQLExecuteRequest(BaseModel):
    """Request model for SQL execution"""
    sql: str = Field(..., description="SQL query to execute")
    params: Optional[Dict[str, Any]] = Field(None, description="Optional bind parameters")
    fetch_size: Optional[int] = Field(1000, description="Number of rows to fetch")
    
    class Config:
        schema_extra = {
            "example": {
                "sql": "SELECT * FROM users WHERE status = :status",
                "params": {"status": "active"},
                "fetch_size": 100
            }
        }


class SQLExecuteResponse(BaseModel):
    """Response model for SQL execution"""
    database: str
    success: bool
    message: str
    rows_affected: Optional[int] = None
    data: Optional[List[Dict[str, Any]]] = None
    columns: Optional[List[str]] = None
    execution_time_ms: float
    timestamp: str


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    timestamp: str
    version: str
    environment: str
    databases: Dict[str, Dict[str, Any]]


# ========================================
# Security Dependencies
# ========================================
def get_api_key_header(request: Request) -> str:
    """Extract API key from header"""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header missing"
        )
    return api_key


def verify_database_access(db_name: str, api_key: str = Depends(get_api_key_header)):
    """Verify API key for specific database"""
    db_name_upper = db_name.upper()
    
    if db_name_upper not in app.state.security_managers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database '{db_name}' not configured"
        )
    
    security_manager = app.state.security_managers[db_name_upper]
    
    if not security_manager.verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Invalid API key for database '{db_name}'"
        )
    
    return db_name_upper


def get_database_executor(db_name: str = Depends(verify_database_access)) -> SQLExecutor:
    """Get SQL executor for verified database"""
    if db_name not in app.state.sql_executors:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database '{db_name}' is not available"
        )
    
    return app.state.sql_executors[db_name]


# ========================================
# Audit Logs UI Route
# ========================================
@app.get("/logs", response_class=HTMLResponse, include_in_schema=False)
async def audit_logs_ui(request: Request):
    """
    Audit logs viewer UI
    Shows recent audit logs from both JSONL files and database
    """
    
    # Get recent logs (last 24 hours)
    start_date = datetime.now() - timedelta(hours=24)
    
    logs = []
    stats = {}
    
    if app.state.audit_logger and app.state.audit_logger.db_audit_enabled:
        logs = app.state.audit_logger.query_audit_logs(
            start_date=start_date,
            limit=100
        )
        stats = app.state.audit_logger.get_audit_statistics(
            start_date=start_date
        )
    
    # Generate HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Audit Logs - CQE NFT Monitoring</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f5f5;
                padding: 20px;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                padding: 30px;
            }}
            h1 {{
                color: #333;
                margin-bottom: 10px;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }}
            .stat-card {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
            }}
            .stat-value {{
                font-size: 2em;
                font-weight: bold;
            }}
            .stat-label {{
                opacity: 0.9;
                margin-top: 5px;
            }}
            .filters {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 6px;
                margin: 20px 0;
            }}
            .filters select, .filters input {{
                padding: 10px;
                margin: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }}
            .filters button {{
                padding: 10px 20px;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }}
            .filters button:hover {{
                background: #5568d3;
            }}
            .logs-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            .logs-table th {{
                background: #f8f9fa;
                padding: 12px;
                text-align: left;
                border-bottom: 2px solid #dee2e6;
                font-weight: 600;
            }}
            .logs-table td {{
                padding: 12px;
                border-bottom: 1px solid #e9ecef;
            }}
            .logs-table tr:hover {{
                background: #f8f9fa;
            }}
            .status-success {{
                color: #28a745;
                font-weight: bold;
            }}
            .status-failed {{
                color: #dc3545;
                font-weight: bold;
            }}
            .sql-preview {{
                font-family: monospace;
                font-size: 0.9em;
                max-width: 400px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }}
            .back-btn {{
                display: inline-block;
                padding: 10px 20px;
                background: #6c757d;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                margin-bottom: 20px;
            }}
            .back-btn:hover {{
                background: #5a6268;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-btn">← Back to Dashboard</a>
            <h1>📊 Audit Logs Viewer</h1>
            <p style="color: #666; margin-bottom: 20px;">Last 24 hours of activity</p>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{stats.get('total_events', 0)}</div>
                    <div class="stat-label">Total Events</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{stats.get('successful_events', 0)}</div>
                    <div class="stat-label">Successful</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{stats.get('failed_events', 0)}</div>
                    <div class="stat-label">Failed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{stats.get('avg_execution_time_ms', 0):.0f}ms</div>
                    <div class="stat-label">Avg Execution Time</div>
                </div>
            </div>
            
            <div class="filters">
                <strong>Filters:</strong>
                <select id="dbFilter" onchange="filterLogs()">
                    <option value="">All Databases</option>
                    {''.join([f'<option value="{db}">{db}</option>' for db in stats.get('databases', {}).keys()])}
                </select>
                <select id="statusFilter" onchange="filterLogs()">
                    <option value="">All Status</option>
                    <option value="success">Success</option>
                    <option value="failed">Failed</option>
                </select>
                <button onclick="window.location.reload()">🔄 Refresh</button>
                <button onclick="window.open('/api/v1/audit/logs?limit=1000', '_blank')">📥 Export JSON</button>
            </div>
            
            <table class="logs-table" id="logsTable">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Event Type</th>
                        <th>Database</th>
                        <th>Username</th>
                        <th>SQL Preview</th>
                        <th>Rows</th>
                        <th>Time (ms)</th>
                        <th>Status</th>
                        <th>Client IP</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    # Add log rows
    for log in logs:
        timestamp = log.get('event_timestamp', '')
        event_type = log.get('event_type', '')
        database = log.get('database_name', '')
        username = log.get('username', '')
        sql = log.get('sql_statement', '')
        sql_preview = (sql[:100] + '...') if sql and len(sql) > 100 else (sql or '')
        rows = log.get('rows_affected', 0) or 0
        exec_time = log.get('execution_time_ms', 0) or 0
        status = log.get('status', '')
        client_ip = log.get('client_ip', '')
        
        status_class = 'status-success' if status == 'success' else 'status-failed'
        
        html_content += f"""
                    <tr data-database="{database}" data-status="{status}">
                        <td>{timestamp}</td>
                        <td>{event_type}</td>
                        <td>{database}</td>
                        <td>{username}</td>
                        <td class="sql-preview" title="{sql}">{sql_preview}</td>
                        <td>{rows}</td>
                        <td>{exec_time:.2f}</td>
                        <td class="{status_class}">{status.upper()}</td>
                        <td>{client_ip}</td>
                    </tr>
        """
    
    html_content += """
                </tbody>
            </table>
        </div>
        
        <script>
            function filterLogs() {
                const dbFilter = document.getElementById('dbFilter').value;
                const statusFilter = document.getElementById('statusFilter').value;
                const rows = document.querySelectorAll('#logsTable tbody tr');
                
                rows.forEach(row => {
                    const db = row.getAttribute('data-database');
                    const status = row.getAttribute('data-status');
                    
                    let show = true;
                    if (dbFilter && db !== dbFilter) show = false;
                    if (statusFilter && status !== statusFilter) show = false;
                    
                    row.style.display = show ? '' : 'none';
                });
            }
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


# ========================================
# UI Routes
# ========================================
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root(request: Request):
    """Render integrated UI homepage"""
    if not os.path.exists("templates"):
        return HTMLResponse(content="""
        <html>
            <head><title>Oracle SQL API</title></head>
            <body>
                <h1>Oracle SQL API - Multi-Database</h1>
                <p>UI templates not found. API is available at <a href="/api/docs">/api/docs</a></p>
            </body>
        </html>
        """)
    
    # Get database information
    databases_info = {}
    for db_name in app.state.connection_manager.get_available_databases():
        db_config = app.state.settings.get_database(db_name)
        databases_info[db_name] = {
            "host": db_config.host,
            "operations": db_config.allowed_operations,
            "auth_type": "CyberArk" if db_config.use_cyberark else "Direct"
        }
    
    # Get API keys for template
    databases = app.state.settings.get_databases()
    api_keys_map = {}
    for db_name, db_config in databases.items():
        api_keys_map[db_name] = db_config.get_api_keys_list()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "databases": databases_info,
        "databases_api_keys": api_keys_map,
        "app_version": app.state.settings.APP_VERSION,
        "environment": app.state.settings.ENVIRONMENT
    })


# ========================================
# Configuration API Endpoints
# ========================================
@app.get("/api/v1/config/api-keys", tags=["Configuration"])
async def get_api_keys_config():
    """
    Get API keys for all databases
    Used by frontend to display and auto-select API keys
    """
    api_keys_map = {}
    databases = app.state.settings.get_databases()
    
    for db_name, db_config in databases.items():
        api_keys = db_config.get_api_keys_list()
        api_keys_map[db_name] = api_keys
    
    return {
        "api_keys": api_keys_map,
        "total_databases": len(api_keys_map),
        "note": "These API keys are read from environment variables"
    }


@app.get("/api/v1/config/environment", tags=["Configuration"])
async def get_environment_info():
    """Get current environment configuration"""
    return {
        "environment": app.state.settings.ENVIRONMENT,
        "version": app.state.settings.APP_VERSION,
        "debug": app.state.settings.DEBUG,
        "audit_enabled": app.state.settings.ENABLE_AUDIT_LOG,
        "cyberark_enabled": app.state.settings.CYBERARK_ENABLED
    }


# ========================================
# Audit API Endpoints
# ========================================
@app.get("/api/v1/audit/logs", tags=["Audit"])
async def query_audit_logs(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    database: Optional[str] = Query(None, description="Filter by database name"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    status: Optional[str] = Query(None, description="Filter by status (success/failed)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records")
):
    """Query audit logs from CQE_NFT database"""
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    results = app.state.audit_logger.query_audit_logs(
        start_date=start_dt,
        end_date=end_dt,
        database=database,
        event_type=event_type,
        status=status,
        limit=limit
    )
    
    return {
        "total_records": len(results),
        "filters": {
            "start_date": start_date,
            "end_date": end_date,
            "database": database,
            "event_type": event_type,
            "status": status
        },
        "records": results
    }


@app.get("/api/v1/audit/statistics", tags=["Audit"])
async def get_audit_statistics(
    start_date: Optional[str] = Query(None, description="Start date for statistics"),
    end_date: Optional[str] = Query(None, description="End date for statistics")
):
    """Get statistical summary of audit logs"""
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    stats = app.state.audit_logger.get_audit_statistics(
        start_date=start_dt,
        end_date=end_dt
    )
    
    return {
        "period": {
            "start_date": start_date or "all time",
            "end_date": end_date or "now"
        },
        "statistics": stats
    }


@app.get("/api/v1/audit/recent", tags=["Audit"])
async def get_recent_audit_events(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to look back"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of records")
):
    """Get most recent audit events"""
    start_date = datetime.now() - timedelta(hours=hours)
    
    results = app.state.audit_logger.query_audit_logs(
        start_date=start_date,
        limit=limit
    )
    
    return {
        "lookback_hours": hours,
        "total_records": len(results),
        "records": results
    }


# ========================================
# Global Health Endpoint
# ========================================
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def global_health_check():
    """Global health check for all databases"""
    
    databases_status = {}
    
    for db_name in app.state.connection_manager.get_available_databases():
        pool = app.state.connection_manager.get_pool(db_name)
        db_config = app.state.settings.get_database(db_name)
        
        try:
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM DUAL")
                cursor.fetchone()
                cursor.close()
            
            databases_status[db_name] = {
                "status": "healthy",
                "host": db_config.host,
                "operations": db_config.allowed_operations,
                "pool_status": pool.get_pool_status()
            }
        except Exception as e:
            databases_status[db_name] = {
                "status": "unhealthy",
                "error": str(e)
            }
    
    # Add failed databases
    for db_name, error in app.state.connection_manager.failed_databases.items():
        databases_status[db_name] = {
            "status": "failed",
            "error": error
        }
    
    # Determine overall status
    all_healthy = all(db.get("status") == "healthy" for db in databases_status.values())
    overall_status = "healthy" if all_healthy else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now().isoformat(),
        version=app.state.settings.APP_VERSION,
        environment=app.state.settings.ENVIRONMENT,
        databases=databases_status
    )


# ========================================
# Database-Specific Health Endpoints
# ========================================
@app.get("/api/v1/{db_name}/health", tags=["Health"])
async def database_health_check(db_name: str = Depends(verify_database_access)):
    """Health check for specific database"""
    
    pool = app.state.connection_manager.get_pool(db_name)
    db_config = app.state.settings.get_database(db_name)
    
    try:
        with pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SYSDATE, USER FROM DUAL")
            result = cursor.fetchone()
            cursor.close()
        
        return {
            "database": db_name,
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "server_time": str(result[0]),
            "connected_as": result[1],
            "host": db_config.host,
            "service": db_config.service_name,
            "allowed_operations": db_config.allowed_operations,
            "pool_status": pool.get_pool_status()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database health check failed: {str(e)}"
        )


# ========================================
# SQL Execution Endpoints
# ========================================
@app.post("/api/v1/{db_name}/execute", response_model=SQLExecuteResponse, tags=["SQL Execution"])
async def execute_sql(
    db_name: str,
    request: SQLExecuteRequest,
    http_request: Request,
    executor: SQLExecutor = Depends(get_database_executor),
    api_key: str = Depends(get_api_key_header)
):
    """Execute SQL query on specific database with enhanced audit logging"""
    
    db_config = app.state.settings.get_database(db_name)
    start_time = datetime.now()
    
    # Get client IP
    client_ip = http_request.client.host if http_request.client else "unknown"
    
    # Validate SQL against allowed operations
    is_valid, error_msg = SQLValidator.validate_sql(
        request.sql,
        db_config.allowed_operations
    )
    
    if not is_valid:
        # Log unauthorized attempt
        if app.state.audit_logger:
            app.state.audit_logger.log_event(
                event_type="sql_validation_failed",
                database=db_name,
                username=db_config.username,
                sql=request.sql[:200],
                error=error_msg,
                api_key=api_key[-8:] if len(api_key) >= 8 else "***",
                client_ip=client_ip,
                status="failed"
            )
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_msg
        )
    
    try:
        # Execute SQL
        result = executor.execute_query(
            sql=request.sql,
            params=request.params,
            fetch_size=request.fetch_size
        )
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Log successful execution with full details
        if app.state.audit_logger:
            app.state.audit_logger.log_event(
                event_type="sql_executed",
                database=db_name,
                username=db_config.username,
                sql=request.sql,
                rows_affected=result.get("rows_affected"),
                execution_time_ms=execution_time,
                status="success",
                api_key=api_key[-8:] if len(api_key) >= 8 else "***",
                client_ip=client_ip,
                fetch_size=request.fetch_size
            )
        
        return SQLExecuteResponse(
            database=db_name,
            success=True,
            message="Query executed successfully",
            rows_affected=result.get("rows_affected"),
            data=result.get("data"),
            columns=result.get("columns"),
            execution_time_ms=execution_time,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Log failed execution
        if app.state.audit_logger:
            app.state.audit_logger.log_event(
                event_type="sql_execution_failed",
                database=db_name,
                username=db_config.username,
                sql=request.sql,
                execution_time_ms=execution_time,
                status="failed",
                error=str(e),
                api_key=api_key[-8:] if len(api_key) >= 8 else "***",
                client_ip=client_ip
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SQL execution failed: {str(e)}"
        )


@app.post("/api/v1/{db_name}/execute-file", tags=["SQL Execution"])
async def execute_sql_file(
    db_name: str,
    http_request: Request,
    file: UploadFile = File(...),
    executor: SQLExecutor = Depends(get_database_executor),
    api_key: str = Depends(get_api_key_header)
):
    """Execute multiple SQL queries from uploaded file"""
    
    db_config = app.state.settings.get_database(db_name)
    client_ip = http_request.client.host if http_request.client else "unknown"
    
    # Validate file size
    max_size = app.state.settings.MAX_SQL_FILE_SIZE_MB * 1024 * 1024
    content = await file.read()
    
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {app.state.settings.MAX_SQL_FILE_SIZE_MB}MB"
        )
    
    # Parse SQL statements
    sql_content = content.decode('utf-8')
    statements = [s.strip() for s in sql_content.split(';') if s.strip()]
    
    # Validate all statements first
    is_valid, error_msg, failed = SQLValidator.validate_multiple_sql(
        statements,
        db_config.allowed_operations
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"SQL validation failed:\n{error_msg}"
        )
    
    # Execute all statements
    results = []
    for i, sql in enumerate(statements, 1):
        try:
            result = executor.execute_query(sql)
            results.append({
                "statement_number": i,
                "success": True,
                "rows_affected": result.get("rows_affected"),
                "message": "Success"
            })
        except Exception as e:
            results.append({
                "statement_number": i,
                "success": False,
                "error": str(e)
            })
    
    # Log file execution
    if app.state.audit_logger:
        app.state.audit_logger.log_event(
            event_type="sql_file_executed",
            database=db_name,
            username=db_config.username,
            filename=file.filename,
            statements_count=len(statements),
            successful=sum(1 for r in results if r["success"]),
            failed=sum(1 for r in results if not r["success"]),
            api_key=api_key[-8:] if len(api_key) >= 8 else "***",
            client_ip=client_ip,
            status="success" if all(r["success"] for r in results) else "partial"
        )
    
    return {
        "database": db_name,
        "filename": file.filename,
        "total_statements": len(statements),
        "successful": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "results": results,
        "timestamp": datetime.now().isoformat()
    }


# ========================================
# Database Information Endpoints
# ========================================
@app.get("/api/v1/databases", tags=["Database Info"])
async def list_databases():
    """List all configured databases and their status"""
    
    databases = []
    
    for db_name in app.state.connection_manager.get_available_databases():
        db_config = app.state.settings.get_database(db_name)
        databases.append({
            "name": db_name,
            "status": "available",
            "host": db_config.host,
            "port": db_config.port,
            "service": db_config.service_name,
            "allowed_operations": db_config.allowed_operations,
            "auth_type": "CyberArk" if db_config.use_cyberark else "Direct"
        })
    
    for db_name, error in app.state.connection_manager.failed_databases.items():
        db_config = app.state.settings.get_database(db_name)
        databases.append({
            "name": db_name,
            "status": "unavailable",
            "error": error,
            "host": db_config.host if db_config else "Unknown",
            "allowed_operations": db_config.allowed_operations if db_config else []
        })
    
    return {
        "total_databases": len(databases),
        "available": len(app.state.connection_manager.get_available_databases()),
        "failed": len(app.state.connection_manager.failed_databases),
        "databases": databases
    }


# ========================================
# Include AppDynamics Router - FIXED LOCATION
# ========================================
app.include_router(
    appd_router,
    prefix="/api/v1/monitoring/appd",
    tags=["AppDynamics Monitoring"]
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")