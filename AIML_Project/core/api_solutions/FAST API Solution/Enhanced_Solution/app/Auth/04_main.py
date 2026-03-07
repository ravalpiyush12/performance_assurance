"""
Main Application Integration
Updated for python-oracledb 2.0.0 (Thin Mode)

Key Changes from cx_Oracle:
- import oracledb instead of cx_Oracle
- Use oracledb.create_pool() instead of SessionPool
- Thin mode = No Oracle Instant Client required!
- pool.acquire() / pool.release() instead of with pool.acquire()
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import oracledb  # NEW: python-oracledb 2.0.0
import logging

# Import authentication components
from authentication import AuthenticationManager
from routes import router as auth_router, init_auth_routes, get_current_user, require_permission

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==========================================
# Database Configuration
# ==========================================

DB_CONFIG = {
    'user': 'your_db_user',
    'password': 'your_db_password',
    'dsn': 'localhost:1521/ORCL',  # Or use Easy Connect: 'host:port/service_name'
    'min': 2,
    'max': 10,
    'increment': 1
}

# IMPORTANT: For oracledb 2.0.0, you can also use:
# dsn = 'host/service_name'  (default port 1521)
# dsn = 'host:port/service_name'
# dsn = TNS name from tnsnames.ora

# Create database connection pool
db_pool = None

def init_database():
    """
    Initialize Oracle database connection pool
    
    Using python-oracledb 2.0.0 Thin Mode:
    - No Oracle Instant Client required!
    - Pure Python implementation
    - Faster connection pooling
    """
    global db_pool
    try:
        # OPTION 1: Thin Mode (No Instant Client - Recommended)
        # This is the default mode in oracledb 2.0.0
        db_pool = oracledb.create_pool(
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            dsn=DB_CONFIG['dsn'],
            min=DB_CONFIG['min'],
            max=DB_CONFIG['max'],
            increment=DB_CONFIG['increment'],
            # Thin mode specific options
            events=True,  # Enable event handling
            threaded=True  # Enable threading support
        )
        
        logger.info("✓ Database connection pool created (Thin Mode - No Instant Client)")
        logger.info(f"  Pool: {DB_CONFIG['min']}-{DB_CONFIG['max']} connections")
        logger.info(f"  DSN: {DB_CONFIG['dsn']}")
        
        # OPTION 2: Thick Mode (with Oracle Instant Client)
        # Only use if you need features not in Thin mode
        # oracledb.init_oracle_client(lib_dir="/path/to/instantclient")
        # Then create pool as above
        
        return db_pool
        
    except oracledb.Error as e:
        error_obj, = e.args
        logger.error(f"Failed to create database pool:")
        logger.error(f"  Error: {error_obj.message}")
        logger.error(f"  Code: {error_obj.code}")
        raise
    except Exception as e:
        logger.error(f"Failed to create database pool: {e}")
        raise

# ==========================================
# FastAPI Application
# ==========================================

app = FastAPI(
    title="Monitoring System with TOTP Authentication",
    description="Secure monitoring system with two-factor authentication (oracledb 2.0.0)",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# Startup Events
# ==========================================

@app.on_event("startup")
async def startup_event():
    """Initialize database and authentication on startup"""
    logger.info("Starting application...")
    logger.info(f"Using python-oracledb {oracledb.__version__}")
    
    # Initialize database
    init_database()
    
    # Initialize authentication routes
    init_auth_routes(db_pool, session_expiry_minutes=60)
    
    logger.info("✓ Application started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down application...")
    
    if db_pool:
        db_pool.close()
        logger.info("✓ Database pool closed")

# ==========================================
# Include Routers
# ==========================================

# Include authentication routes
app.include_router(auth_router)

# Include your existing routes here
# Example:
# from monitoring.awr.routes import router as awr_router
# app.include_router(awr_router)
# from monitoring.appd.routes import router as appd_router
# app.include_router(appd_router)
# from monitoring.pc.routes import router as pc_router
# app.include_router(pc_router)

# ==========================================
# Example: Protecting Existing Endpoints
# ==========================================

# Example 1: Protect AWR upload endpoint
@app.post("/api/v1/monitoring/awr/upload")
async def upload_awr_report(
    user: dict = Depends(require_permission("write"))
):
    """
    Upload AWR report - requires 'write' permission
    
    The user dict contains:
    - user_id: User ID
    - username: Username
    - email: Email
    - role: User role
    - permissions: List of permissions
    """
    logger.info(f"AWR upload by {user['username']} (Role: {user['role']})")
    
    # Example: Set Oracle session context with actual username
    conn = db_pool.acquire()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            BEGIN
                DBMS_SESSION.SET_IDENTIFIER(:username);
                DBMS_APPLICATION_INFO.SET_CLIENT_INFO(:username);
            END;
        """, {'username': user['username']})
        conn.commit()
        logger.info(f"  Oracle session set for: {user['username']}")
    finally:
        cursor.close()
        db_pool.release(conn)
    
    # Your existing AWR upload logic here
    # All database writes will be tagged with user['username']
    
    return {
        'success': True,
        'uploaded_by': user['username'],
        'message': 'AWR report uploaded successfully'
    }

# Example 2: Protect test registration endpoint
@app.post("/api/v1/pc/test-run/register")
async def register_test(
    user: dict = Depends(require_permission("register_test"))
):
    """
    Register test run - requires 'register_test' permission
    """
    logger.info(f"Test registration by {user['username']}")
    
    # Your existing test registration logic
    # Log who registered the test
    
    return {
        'success': True,
        'registered_by': user['username']
    }

# Example 3: Admin-only endpoint
@app.get("/api/v1/admin/system-config")
async def get_system_config(
    user: dict = Depends(require_permission("configure"))
):
    """
    Get system configuration - admin only
    """
    return {
        'config': {...},
        'accessed_by': user['username']
    }

# Example 4: Public endpoint (no authentication)
@app.get("/api/v1/health")
async def health_check():
    """Public health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'monitoring-system',
        'database': 'oracledb 2.0.0 (Thin Mode)'
    }

# ==========================================
# Root Endpoint
# ==========================================

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        'name': 'Monitoring System API',
        'version': '1.0.0',
        'authentication': 'TOTP (Two-Factor Authentication)',
        'database': f'python-oracledb {oracledb.__version__} (Thin Mode)',
        'endpoints': {
            'auth': '/api/v1/auth/login',
            'docs': '/docs',
            'health': '/api/v1/health'
        }
    }

# ==========================================
# Run Application
# ==========================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Set to False in production
        log_level="info"
    )
