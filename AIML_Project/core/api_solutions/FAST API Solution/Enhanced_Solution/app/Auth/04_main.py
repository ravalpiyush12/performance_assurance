"""
Main Application Integration
Shows how to integrate TOTP authentication into your FastAPI app
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import cx_Oracle
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
    'dsn': 'localhost:1521/ORCL',  # Change to your Oracle DSN
    'min': 2,
    'max': 10,
    'increment': 1
}

# Create database connection pool
db_pool = None

def init_database():
    """Initialize Oracle database connection pool"""
    global db_pool
    try:
        db_pool = cx_Oracle.SessionPool(
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            dsn=DB_CONFIG['dsn'],
            min=DB_CONFIG['min'],
            max=DB_CONFIG['max'],
            increment=DB_CONFIG['increment'],
            threaded=True
        )
        logger.info("✓ Database connection pool created")
        return db_pool
    except Exception as e:
        logger.error(f"Failed to create database pool: {e}")
        raise

# ==========================================
# FastAPI Application
# ==========================================

app = FastAPI(
    title="Monitoring System with TOTP Authentication",
    description="Secure monitoring system with two-factor authentication",
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
        'service': 'monitoring-system'
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
