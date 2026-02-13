🎯 Root Cause: FastAPI Lifespan Issue
The startup event isn't running. This is likely because:

Gunicorn is starting multiple workers before startup completes
FastAPI lifespan context is not being used
The startup decorator isn't being recognized


⚡ Immediate Fix
Option 1: Use Lifespan Context (FastAPI 0.93+)
Replace your @app.on_event("startup") with the new lifespan pattern:
pythonfrom contextlib import asynccontextmanager
from fastapi import FastAPI
import sys

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager - replaces startup/shutdown events
    """
    # STARTUP
    print("=" * 80, flush=True)
    print("LIFESPAN STARTUP", flush=True)
    print("=" * 80, flush=True)
    sys.stdout.flush()
    
    try:
        from config import get_settings
        from security import SecurityManager
        from oracle_handler import OracleConnectionPool, SQLExecutor
        from audit import AuditLogger
        
        # Load settings
        print("Loading settings...", flush=True)
        settings = get_settings()
        app.state.settings = settings
        print(f"✓ Settings: {settings.ENVIRONMENT}", flush=True)
        sys.stdout.flush()
        
        # Initialize security
        print("Initializing security...", flush=True)
        app.state.security_manager = SecurityManager(settings)
        print("✓ Security initialized", flush=True)
        sys.stdout.flush()
        
        # Initialize audit
        print("Initializing audit...", flush=True)
        app.state.audit_logger = AuditLogger(settings)
        print("✓ Audit initialized", flush=True)
        sys.stdout.flush()
        
        # Initialize Oracle (allow to fail)
        print("Initializing Oracle...", flush=True)
        try:
            app.state.oracle_pool = OracleConnectionPool(settings)
            app.state.oracle_pool.initialize()
            app.state.sql_executor = SQLExecutor(app.state.oracle_pool, settings)
            print("✓ Oracle initialized", flush=True)
        except Exception as e:
            print(f"✗ Oracle failed: {e}", flush=True)
            app.state.oracle_pool = None
            app.state.sql_executor = None
        
        sys.stdout.flush()
        print("=" * 80, flush=True)
        print("✓ STARTUP COMPLETE", flush=True)
        print("=" * 80, flush=True)
        sys.stdout.flush()
        
    except Exception as e:
        print(f"✗ STARTUP FAILED: {e}", flush=True)
        import traceback
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
        raise
    
    # Application is running
    yield
    
    # SHUTDOWN
    print("=" * 80, flush=True)
    print("LIFESPAN SHUTDOWN", flush=True)
    print("=" * 80, flush=True)
    if hasattr(app.state, 'oracle_pool') and app.state.oracle_pool:
        app.state.oracle_pool.close()
    sys.stdout.flush()


# Create FastAPI app with lifespan
app = FastAPI(
    title="Oracle SQL API",
    lifespan=lifespan  # ← Use lifespan parameter
)

# Remove @app.on_event("startup") - not needed with lifespan

Option 2: Force Startup with Preload
If lifespan doesn't work, use Gunicorn preload:
Update gunicorn.conf.py:
pythonimport multiprocessing

bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
accesslog = "-"
errorlog = "-"
loglevel = "info"

# CRITICAL: Preload app before forking workers
preload_app = True  # ← Add this
Then add startup code directly in main.py (not in event handler):
pythonimport sys
from fastapi import FastAPI

app = FastAPI(title="Oracle SQL API")

# INITIALIZE IMMEDIATELY (not in startup event)
print("=" * 80, flush=True)
print("INITIALIZING APP (preload)", flush=True)
print("=" * 80, flush=True)
sys.stdout.flush()

try:
    from config import get_settings
    from security import SecurityManager
    from oracle_handler import OracleConnectionPool, SQLExecutor
    from audit import AuditLogger
    
    # Load settings
    settings = get_settings()
    app.state.settings = settings
    print(f"✓ Settings: {settings.ENVIRONMENT}", flush=True)
    
    # Initialize components
    app.state.security_manager = SecurityManager(settings)
    print("✓ Security initialized", flush=True)
    
    app.state.audit_logger = AuditLogger(settings)
    print("✓ Audit initialized", flush=True)
    
    # Oracle (allow to fail)
    try:
        app.state.oracle_pool = OracleConnectionPool(settings)
        app.state.oracle_pool.initialize()
        app.state.sql_executor = SQLExecutor(app.state.oracle_pool, settings)
        print("✓ Oracle initialized", flush=True)
    except Exception as e:
        print(f"✗ Oracle failed: {e}", flush=True)
        app.state.oracle_pool = None
        app.state.sql_executor = None
    
    sys.stdout.flush()
    print("✓ INITIALIZATION COMPLETE", flush=True)
    sys.stdout.flush()
    
except Exception as e:
    print(f"✗ INITIALIZATION FAILED: {e}", flush=True)
    import traceback
    traceback.print_exc(file=sys.stdout)
    sys.stdout.flush()
    raise

# Your endpoints below...

Option 3: Single Worker (Simplest)
Update gunicorn.conf.py:
pythonbind = "0.0.0.0:8000"
workers = 1  # ← Change to 1
worker_class = "uvicorn.workers.UvicornWorker"
accesslog = "-"
errorlog = "-"
loglevel = "info"
capture_output = True
This ensures startup runs once and app.state is shared.

🚀 I Recommend: Option 1 (Lifespan)
Replace your main.py structure with:
pythonimport sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan - handles startup and shutdown"""
    
    # STARTUP
    print("\n" + "=" * 80, flush=True)
    print("LIFESPAN STARTUP", flush=True)
    print("=" * 80 + "\n", flush=True)
    sys.stdout.flush()
    
    from config import get_settings
    from security import SecurityManager
    from oracle_handler import OracleConnectionPool, SQLExecutor
    from audit import AuditLogger
    
    # Settings
    settings = get_settings()
    app.state.settings = settings
    print(f"✓ Settings: {settings.ENVIRONMENT} v{settings.APP_VERSION}", flush=True)
    
    # Security
    app.state.security_manager = SecurityManager(settings)
    print("✓ Security initialized", flush=True)
    
    # Audit
    app.state.audit_logger = AuditLogger(settings)
    print("✓ Audit initialized", flush=True)
    
    # Oracle
    try:
        app.state.oracle_pool = OracleConnectionPool(settings)
        app.state.oracle_pool.initialize()
        app.state.sql_executor = SQLExecutor(app.state.oracle_pool, settings)
        print("✓ Oracle connected", flush=True)
    except Exception as e:
        print(f"⚠ Oracle unavailable: {e}", flush=True)
        app.state.oracle_pool = None
        app.state.sql_executor = None
    
    sys.stdout.flush()
    
    yield  # App runs here
    
    # SHUTDOWN
    print("\nShutting down...", flush=True)
    if hasattr(app.state, 'oracle_pool') and app.state.oracle_pool:
        app.state.oracle_pool.close()
    sys.stdout.flush()

# Create app with lifespan
app = FastAPI(title="Oracle SQL API", lifespan=lifespan)

# Your routes go here...
@app.get("/health")
async def health_check():
    # ... your health check code ...
```

**Deploy and you'll see:**
```
================================================================================
LIFESPAN STARTUP
================================================================================

✓ Settings: dev v1.0.0
✓ Security initialized
✓ Audit initialized
✓ Oracle connected
Then your health endpoint will work! 🎯
Which option do you want to try first?