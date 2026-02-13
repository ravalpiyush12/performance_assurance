# Diagnostic Startup Event - Find Exact Failure Point

## 🎯 Replace Your Startup Event with This Diagnostic Version

This will print after EVERY step so you can see exactly where it fails.

```python
import sys
import traceback
from datetime import datetime

@app.on_event("startup")
async def startup_event():
    """
    Diagnostic startup event
    Prints after every step to find exact failure point
    """
    
    print("\n" + "=" * 80, flush=True)
    print(f"STARTUP DIAGNOSTIC - {datetime.now().isoformat()}", flush=True)
    print("=" * 80 + "\n", flush=True)
    sys.stdout.flush()
    
    # ========================================
    # STEP 1: Import Check
    # ========================================
    print("STEP 1: Checking imports...", flush=True)
    sys.stdout.flush()
    
    try:
        from config import get_settings, Settings
        print("  ✓ config imported", flush=True)
    except Exception as e:
        print(f"  ✗ config import FAILED: {e}", flush=True)
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
        raise
    
    try:
        from security import SecurityManager, verify_api_key_dependency
        print("  ✓ security imported", flush=True)
    except Exception as e:
        print(f"  ✗ security import FAILED: {e}", flush=True)
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
        raise
    
    try:
        from oracle_handler import OracleConnectionPool, SQLExecutor
        print("  ✓ oracle_handler imported", flush=True)
    except Exception as e:
        print(f"  ✗ oracle_handler import FAILED: {e}", flush=True)
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
        raise
    
    try:
        from audit import AuditLogger
        print("  ✓ audit imported", flush=True)
    except Exception as e:
        print(f"  ✗ audit import FAILED: {e}", flush=True)
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
        raise
    
    print("  ✓ All imports successful\n", flush=True)
    sys.stdout.flush()
    
    # ========================================
    # STEP 2: Load Settings
    # ========================================
    print("STEP 2: Loading settings...", flush=True)
    sys.stdout.flush()
    
    try:
        settings = get_settings()
        print(f"  ✓ Settings object created", flush=True)
        print(f"    Type: {type(settings)}", flush=True)
        sys.stdout.flush()
    except Exception as e:
        print(f"  ✗ get_settings() FAILED: {e}", flush=True)
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
        raise
    
    try:
        app.state.settings = settings
        print(f"  ✓ Settings assigned to app.state", flush=True)
        print(f"    Environment: {settings.ENVIRONMENT}", flush=True)
        print(f"    Version: {settings.APP_VERSION}", flush=True)
        print(f"    Oracle Host: {settings.ORACLE_HOST}", flush=True)
        print(f"    Oracle Port: {settings.ORACLE_PORT}", flush=True)
        print(f"    Oracle Service: {settings.ORACLE_SERVICE_NAME}\n", flush=True)
        sys.stdout.flush()
    except Exception as e:
        print(f"  ✗ Assigning to app.state FAILED: {e}", flush=True)
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
        raise
    
    # ========================================
    # STEP 3: Initialize Security Manager
    # ========================================
    print("STEP 3: Initializing security manager...", flush=True)
    sys.stdout.flush()
    
    try:
        security_manager = SecurityManager(settings)
        print(f"  ✓ SecurityManager object created", flush=True)
        sys.stdout.flush()
    except Exception as e:
        print(f"  ✗ SecurityManager() FAILED: {e}", flush=True)
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
        raise
    
    try:
        app.state.security_manager = security_manager
        print(f"  ✓ SecurityManager assigned to app.state\n", flush=True)
        sys.stdout.flush()
    except Exception as e:
        print(f"  ✗ Assigning SecurityManager to app.state FAILED: {e}", flush=True)
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
        raise
    
    # ========================================
    # STEP 4: Initialize Audit Logger
    # ========================================
    print("STEP 4: Initializing audit logger...", flush=True)
    sys.stdout.flush()
    
    try:
        audit_logger = AuditLogger(settings)
        print(f"  ✓ AuditLogger object created", flush=True)
        sys.stdout.flush()
    except Exception as e:
        print(f"  ✗ AuditLogger() FAILED: {e}", flush=True)
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
        # Don't raise - audit is not critical
        audit_logger = None
        print(f"  ⚠ Continuing without audit logger\n", flush=True)
        sys.stdout.flush()
    
    try:
        app.state.audit_logger = audit_logger
        print(f"  ✓ AuditLogger assigned to app.state\n", flush=True)
        sys.stdout.flush()
    except Exception as e:
        print(f"  ✗ Assigning AuditLogger to app.state FAILED: {e}", flush=True)
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
        raise
    
    # ========================================
    # STEP 5: Initialize Oracle Connection Pool
    # ========================================
    print("STEP 5: Initializing Oracle connection pool...", flush=True)
    print(f"  Target: {settings.ORACLE_HOST}:{settings.ORACLE_PORT}/{settings.ORACLE_SERVICE_NAME}", flush=True)
    sys.stdout.flush()
    
    try:
        print("  Creating OracleConnectionPool object...", flush=True)
        sys.stdout.flush()
        
        oracle_pool = OracleConnectionPool(settings)
        print(f"  ✓ OracleConnectionPool object created", flush=True)
        sys.stdout.flush()
        
    except Exception as e:
        print(f"  ✗ OracleConnectionPool() FAILED: {e}", flush=True)
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
        app.state.oracle_pool = None
        app.state.sql_executor = None
        print(f"  ⚠ Continuing without Oracle (pool=None)\n", flush=True)
        sys.stdout.flush()
        # Don't raise - continue without Oracle
        oracle_pool = None
    
    if oracle_pool:
        try:
            print("  Initializing connection pool...", flush=True)
            sys.stdout.flush()
            
            oracle_pool.initialize()
            print(f"  ✓ Connection pool initialized", flush=True)
            sys.stdout.flush()
            
        except Exception as e:
            print(f"  ✗ pool.initialize() FAILED: {e}", flush=True)
            print(f"    Error type: {type(e).__name__}", flush=True)
            traceback.print_exc(file=sys.stdout)
            sys.stdout.flush()
            oracle_pool = None
            print(f"  ⚠ Continuing without Oracle (pool=None)\n", flush=True)
            sys.stdout.flush()
    
    try:
        app.state.oracle_pool = oracle_pool
        print(f"  ✓ Oracle pool assigned to app.state (value: {'Available' if oracle_pool else 'None'})\n", flush=True)
        sys.stdout.flush()
    except Exception as e:
        print(f"  ✗ Assigning oracle_pool to app.state FAILED: {e}", flush=True)
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
        raise
    
    # ========================================
    # STEP 6: Initialize SQL Executor
    # ========================================
    if oracle_pool:
        print("STEP 6: Initializing SQL executor...", flush=True)
        sys.stdout.flush()
        
        try:
            sql_executor = SQLExecutor(oracle_pool, settings)
            print(f"  ✓ SQLExecutor object created", flush=True)
            sys.stdout.flush()
        except Exception as e:
            print(f"  ✗ SQLExecutor() FAILED: {e}", flush=True)
            traceback.print_exc(file=sys.stdout)
            sys.stdout.flush()
            sql_executor = None
            print(f"  ⚠ Continuing without SQL executor\n", flush=True)
            sys.stdout.flush()
        
        try:
            app.state.sql_executor = sql_executor
            print(f"  ✓ SQLExecutor assigned to app.state\n", flush=True)
            sys.stdout.flush()
        except Exception as e:
            print(f"  ✗ Assigning sql_executor to app.state FAILED: {e}", flush=True)
            traceback.print_exc(file=sys.stdout)
            sys.stdout.flush()
            raise
    else:
        print("STEP 6: Skipping SQL executor (no Oracle pool)\n", flush=True)
        app.state.sql_executor = None
        sys.stdout.flush()
    
    # ========================================
    # STEP 7: Test Database Connection (if pool exists)
    # ========================================
    if oracle_pool:
        print("STEP 7: Testing database connection...", flush=True)
        sys.stdout.flush()
        
        try:
            with oracle_pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT SYSDATE, USER FROM DUAL")
                result = cursor.fetchone()
                cursor.close()
                print(f"  ✓ Database connection successful", flush=True)
                print(f"    Server time: {result[0]}", flush=True)
                print(f"    Connected as: {result[1]}\n", flush=True)
                sys.stdout.flush()
        except Exception as e:
            print(f"  ✗ Database connection test FAILED: {e}", flush=True)
            traceback.print_exc(file=sys.stdout)
            sys.stdout.flush()
            print(f"  ⚠ Pool created but connection test failed\n", flush=True)
            sys.stdout.flush()
    else:
        print("STEP 7: Skipping connection test (no pool)\n", flush=True)
        sys.stdout.flush()
    
    # ========================================
    # Startup Complete
    # ========================================
    print("=" * 80, flush=True)
    print("✓ STARTUP COMPLETED SUCCESSFULLY", flush=True)
    print("=" * 80, flush=True)
    print(f"Environment: {settings.ENVIRONMENT}", flush=True)
    print(f"Version: {settings.APP_VERSION}", flush=True)
    print(f"Oracle: {'✓ Connected' if oracle_pool else '✗ Not available'}", flush=True)
    print(f"app.state.settings: {'✓ Set' if hasattr(app.state, 'settings') else '✗ Missing'}", flush=True)
    print(f"app.state.oracle_pool: {'✓ Set' if hasattr(app.state, 'oracle_pool') else '✗ Missing'}", flush=True)
    print("=" * 80 + "\n", flush=True)
    sys.stdout.flush()
```

## 🔍 What This Will Show

After deploying this, you'll see in logs EXACTLY where it fails:

### **If it's an import problem:**
```
STEP 1: Checking imports...
  ✓ config imported
  ✗ security import FAILED: ImportError: cannot import name 'RateLimiter'
[Stack trace]
```

### **If it's a settings problem:**
```
STEP 1: Checking imports...
  ✓ All imports successful

STEP 2: Loading settings...
  ✗ get_settings() FAILED: ValidationError: 2 validation errors
[Stack trace showing which env vars are missing]
```

### **If it's Oracle:**
```
STEP 5: Initializing Oracle connection pool...
  Creating OracleConnectionPool object...
  ✓ OracleConnectionPool object created
  Initializing connection pool...
  ✗ pool.initialize() FAILED: DatabaseError: ORA-12514
[Stack trace]
```

### **If it completes successfully:**
```
✓ STARTUP COMPLETED SUCCESSFULLY
Environment: dev
Version: 1.0.0
Oracle: ✓ Connected
app.state.settings: ✓ Set
app.state.oracle_pool: ✓ Set
```

## 🚀 Deploy This Diagnostic Version

```bash
# 1. Replace your startup event in main.py with the code above
# 2. Rebuild and deploy
docker build -t your-image:latest .
docker push your-image:latest

# 3. Restart
oc rollout restart deployment/oracle-sql-api

# 4. Watch logs
oc logs -f deployment/oracle-sql-api
```

## 🎯 Also Check: Async/Await Issue

Sometimes the issue is that the startup event is `async` but calling **synchronous blocking code**. Try this alternative:

```python
# Change from:
@app.on_event("startup")
async def startup_event():
    # ... your code ...

# To:
@app.on_event("startup")
def startup_event():  # ← Remove 'async'
    # ... your code ...
```

Or wrap blocking calls properly:

```python
@app.on_event("startup")
async def startup_event():
    import asyncio
    
    # Run blocking operations in executor
    loop = asyncio.get_event_loop()
    
    # Load settings (blocking)
    settings = await loop.run_in_executor(None, get_settings)
    
    # Initialize Oracle (blocking)
    oracle_pool = await loop.run_in_executor(None, lambda: OracleConnectionPool(settings))
```

## 🔍 Check if Startup Event is Even Running

Add this at the **very top** of main.py before the app definition:

```python
import sys

print("\n" + "=" * 80, flush=True)
print("MAIN.PY IS BEING LOADED", flush=True)
print("=" * 80 + "\n", flush=True)
sys.stdout.flush()

from fastapi import FastAPI

print("Creating FastAPI app instance...", flush=True)
sys.stdout.flush()

app = FastAPI(title="Oracle SQL API")

print("FastAPI app created successfully", flush=True)
sys.stdout.flush()

# Then your startup event...
```

This will tell us if:
1. main.py is even being executed
2. FastAPI app is created
3. Startup event is registered

Share the output and we'll know EXACTLY what's failing! 🎯