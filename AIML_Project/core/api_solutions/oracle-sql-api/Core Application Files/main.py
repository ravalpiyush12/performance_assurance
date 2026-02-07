"""
Main FastAPI Application
Oracle SQL API with security, monitoring, and audit logging
"""
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import uuid
from datetime import datetime
import structlog

from config import get_settings, Settings
from oracle_handler import OracleConnectionPool, SQLExecutor
from security import SecurityManager, verify_api_key_dependency, get_request_identifier
from audit import AuditLogger

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Oracle SQL API",
    description="Secure API for executing SQL operations on Oracle Database",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class SQLExecuteRequest(BaseModel):
    """SQL execution request"""
    sql_content: str = Field(..., description="SQL statements to execute")
    username: str = Field(..., description="Username executing the SQL")
    description: Optional[str] = Field(None, description="Description of the operation")


class SQLExecuteResponse(BaseModel):
    """SQL execution response"""
    request_id: str
    status: str
    operation_type: str
    rows_affected: int
    data: List[Dict[str, Any]] = []
    columns: List[str] = []
    execution_time_seconds: float
    timestamp: str
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str
    environment: str
    database_status: Dict[str, Any]
    pool_status: Dict[str, Any]


class TokenRequest(BaseModel):
    """Token generation request"""
    username: str
    api_key: str


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# Application Startup
@app.on_event("startup")
async def startup_event():
    """Initialize application resources"""
    logger.info("Starting Oracle SQL API...")
    
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
        # Don't fail startup - allow health checks to report the issue
    
    # Initialize SQL executor
    app.state.sql_executor = SQLExecutor(app.state.oracle_pool, settings)
    
    logger.info(f"Application started successfully in {settings.ENVIRONMENT} environment")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup application resources"""
    logger.info("Shutting down Oracle SQL API...")
    
    # Close connection pool
    if hasattr(app.state, 'oracle_pool'):
        app.state.oracle_pool.close()
    
    logger.info("Application shutdown complete")


# API Endpoints

@app.get("/", tags=["General"])
async def root():
    """Root endpoint"""
    return {
        "service": "Oracle SQL API",
        "version": app.state.settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check():
    """
    Health check endpoint
    Verifies database connectivity and pool status
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
    
    overall_status = "healthy" if db_status["status"] == "healthy" else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now().isoformat(),
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        database_status=db_status,
        pool_status=pool_status
    )


@app.post("/api/v1/auth/token", response_model=TokenResponse, tags=["Authentication"])
async def generate_token(request: TokenRequest):
    """
    Generate JWT access token
    Requires valid API key for authentication
    """
    security_manager: SecurityManager = app.state.security_manager
    settings: Settings = app.state.settings
    audit_logger: AuditLogger = app.state.audit_logger
    
    # Verify API key
    try:
        security_manager.verify_api_key(request.api_key)
    except HTTPException:
        audit_logger.log_authentication(
            username=request.username,
            api_key=request.api_key,
            success=False,
            reason="Invalid API key"
        )
        raise
    
    # Generate token
    token_data = {
        "sub": request.username,
        "api_key": request.api_key
    }
    
    access_token = security_manager.token_manager.create_access_token(token_data)
    
    audit_logger.log_authentication(
        username=request.username,
        api_key=request.api_key,
        success=True
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@app.post("/api/v1/sql/execute", response_model=SQLExecuteResponse, tags=["SQL Operations"])
async def execute_sql(
    request: SQLExecuteRequest,
    api_key: str = Depends(verify_api_key_dependency),
    req: Request = None
):
    """
    Execute SQL statement
    
    Supports both DQL (SELECT) and DML (INSERT, UPDATE, DELETE, MERGE) operations.
    Returns query results for SELECT, rows affected for DML.
    
    Requires valid API key in X-API-Key header.
    """
    settings: Settings = app.state.settings
    sql_executor: SQLExecutor = app.state.sql_executor
    audit_logger: AuditLogger = app.state.audit_logger
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    
    # Get client IP
    client_ip = req.client.host if req and req.client else None
    
    logger.info(f"[{request_id}] SQL execution request from {request.username}")
    
    # Validate SQL
    is_valid, error_msg, operation_type = sql_executor.validate_sql(request.sql_content)
    
    if not is_valid:
        logger.warning(f"[{request_id}] SQL validation failed: {error_msg}")
        
        audit_logger.log_request(
            request_id=request_id,
            username=request.username,
            api_key=api_key,
            operation_type=operation_type,
            sql_preview=request.sql_content[:500],
            client_ip=client_ip,
            metadata={"description": request.description, "validation_error": error_msg}
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SQL validation failed: {error_msg}"
        )
    
    # Log request
    audit_logger.log_request(
        request_id=request_id,
        username=request.username,
        api_key=api_key,
        operation_type=operation_type,
        sql_preview=request.sql_content[:500],
        client_ip=client_ip,
        metadata={"description": request.description}
    )
    
    # Execute SQL
    result = sql_executor.execute_sql(
        sql_content=request.sql_content,
        operation_type=operation_type,
        request_id=request_id,
        username=request.username
    )
    
    # Log response
    audit_logger.log_response(
        request_id=request_id,
        status=result["status"],
        rows_affected=result.get("rows_affected", 0),
        execution_time=result["execution_time_seconds"],
        error=result.get("error")
    )
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "SQL execution failed")
        )
    
    return SQLExecuteResponse(**result)


@app.post("/api/v1/sql/execute-file", response_model=SQLExecuteResponse, tags=["SQL Operations"])
async def execute_sql_file(
    file: UploadFile = File(..., description="SQL file to execute (.sql)"),
    username: str = Field(..., description="Username executing the SQL"),
    description: Optional[str] = Field(None, description="Description of the operation"),
    api_key: str = Depends(verify_api_key_dependency),
    req: Request = None
):
    """
    Execute SQL from uploaded file
    
    Accepts .sql file containing SQL statements.
    Validates and executes the SQL content.
    
    Requires valid API key in X-API-Key header.
    """
    settings: Settings = app.state.settings
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    
    logger.info(f"[{request_id}] SQL file upload from {username}: {file.filename}")
    
    # Validate file extension
    if not file.filename.endswith('.sql'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .sql files are allowed"
        )
    
    # Check file size
    contents = await file.read()
    file_size_mb = len(contents) / (1024 * 1024)
    
    if file_size_mb > settings.MAX_SQL_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size {file_size_mb:.2f}MB exceeds maximum {settings.MAX_SQL_FILE_SIZE_MB}MB"
        )
    
    # Decode SQL content
    try:
        sql_content = contents.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be UTF-8 encoded"
        )
    
    # Create execute request
    execute_request = SQLExecuteRequest(
        sql_content=sql_content,
        username=username,
        description=description or f"File: {file.filename}"
    )
    
    # Use the execute_sql endpoint logic
    return await execute_sql(execute_request, api_key, req)


@app.get("/api/v1/audit/summary", tags=["Monitoring"])
async def get_audit_summary(
    date: Optional[str] = None,
    api_key: str = Depends(verify_api_key_dependency)
):
    """
    Get audit log summary
    
    Provides statistics on SQL operations for a specific date.
    Date format: YYYYMMDD (default: today)
    
    Requires valid API key.
    """
    audit_logger: AuditLogger = app.state.audit_logger
    
    summary = audit_logger.get_audit_summary(date)
    
    return summary


@app.get("/api/v1/rate-limit/status", tags=["Monitoring"])
async def get_rate_limit_status(
    request: Request,
    api_key: str = Depends(verify_api_key_dependency)
):
    """
    Get rate limit status
    
    Returns current rate limit information for the API key.
    """
    security_manager: SecurityManager = app.state.security_manager
    identifier = await get_request_identifier(request)
    
    rate_limit_info = security_manager.get_rate_limit_info(identifier)
    
    return {
        "identifier": identifier,
        **rate_limit_info
    }


@app.get("/api/v1/pool/status", tags=["Monitoring"])
async def get_pool_status(api_key: str = Depends(verify_api_key_dependency)):
    """
    Get Oracle connection pool status
    
    Returns current pool statistics.
    """
    pool: OracleConnectionPool = app.state.oracle_pool
    
    return pool.get_pool_status()


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc) if app.state.settings.DEBUG else None,
            "timestamp": datetime.now().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )