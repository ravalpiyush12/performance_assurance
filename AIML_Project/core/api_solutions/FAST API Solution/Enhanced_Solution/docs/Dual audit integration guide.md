# Dual Audit System Integration Guide

## Overview

The enhanced audit system supports **dual logging**:
1. **JSONL Files** - Fast, append-only logging to `/app/logs/audit/`
2. **Oracle Database** - Structured logging to `AUDIT_LOG` table in CQE_NFT

## Features

### JSONL File Audit
- ✅ One JSON object per line (JSONL format)
- ✅ Daily rotation (`audit_YYYYMMDD.jsonl`)
- ✅ Fast writes, no database overhead
- ✅ Easy parsing with standard tools

### Oracle Database Audit
- ✅ Structured table with indexes
- ✅ Queryable via SQL and API
- ✅ Full SQL statements stored (not truncated)
- ✅ Statistics and analytics
- ✅ Automatic cleanup of old records

## Database Schema

The `AUDIT_LOG` table in CQE_NFT:

```sql
CREATE TABLE AUDIT_LOG (
    AUDIT_ID NUMBER PRIMARY KEY,              -- Unique ID (from sequence)
    EVENT_TIMESTAMP TIMESTAMP,                 -- When event occurred
    EVENT_TYPE VARCHAR2(100),                  -- Type of event
    DATABASE_NAME VARCHAR2(100),               -- Which database
    USERNAME VARCHAR2(100),                    -- Database user
    SQL_STATEMENT CLOB,                        -- Full SQL (not truncated)
    ROWS_AFFECTED NUMBER,                      -- Rows modified/returned
    EXECUTION_TIME_MS NUMBER,                  -- Execution time
    STATUS VARCHAR2(50),                       -- success/failed/error
    ERROR_MESSAGE VARCHAR2(4000),              -- Error details if failed
    API_KEY_HASH VARCHAR2(100),                -- Last 8 chars of API key
    CLIENT_IP VARCHAR2(50),                    -- Client IP address
    ENVIRONMENT VARCHAR2(50),                  -- dev/staging/prod
    ADDITIONAL_DATA CLOB,                      -- Extra data as JSON
    CREATED_DATE DATE DEFAULT SYSDATE         -- Record creation date
);

-- Indexes for performance
CREATE INDEX IDX_AUDIT_LOG_TIMESTAMP ON AUDIT_LOG(EVENT_TIMESTAMP);
CREATE INDEX IDX_AUDIT_LOG_DATABASE ON AUDIT_LOG(DATABASE_NAME);
```

## Integration Steps

### Step 1: Update Imports in main.py

Replace the audit import:

```python
# OLD:
# from utils.audit import AuditLogger

# NEW:
from utils.audit import AuditLogger  # Use the new audit_dual.py as audit.py
```

### Step 2: Update Initialization in main.py

Update the audit logger initialization to pass CQE_NFT pool:

```python
# In the global initialization section (before @app.on_event)

try:
    # ... existing initialization code ...
    
    # Initialize connection manager
    _connection_manager = ConnectionManager(_settings)
    _connection_manager.initialize_all()
    
    # Get CQE_NFT pool for audit logging
    cqe_nft_pool = _connection_manager.get_pool("CQE_NFT")
    
    # Initialize audit logger with CQE_NFT pool
    print("\nInitializing audit logger...", flush=True)
    _audit_logger = AuditLogger(_settings, cqe_nft_pool=cqe_nft_pool)
    print("✓ Audit logger initialized", flush=True)
    print(f"  File audit: {'Enabled' if _audit_logger.file_audit_enabled else 'Disabled'}", flush=True)
    print(f"  DB audit: {'Enabled' if _audit_logger.db_audit_enabled else 'Disabled'}", flush=True)
    sys.stdout.flush()
    
    # ... rest of initialization ...
    
except Exception as e:
    print(f"\n✗ INITIALIZATION FAILED: {e}", flush=True)
    # ...
```

### Step 3: Add Audit API Endpoints

Add audit query endpoints to main.py:

```python
# After all your database routes, add audit routes
from fastapi import APIRouter, Query
from datetime import timedelta

# Audit API Router
audit_router = APIRouter(prefix="/api/v1/audit", tags=["Audit"])

@audit_router.get("/logs")
async def query_audit_logs(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    database: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000)
):
    """Query audit logs from database"""
    from datetime import datetime
    
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
        "records": results
    }

@audit_router.get("/statistics")
async def get_audit_statistics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get audit statistics"""
    from datetime import datetime
    
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    stats = app.state.audit_logger.get_audit_statistics(
        start_date=start_dt,
        end_date=end_dt
    )
    
    return {"statistics": stats}

@audit_router.get("/recent")
async def get_recent_audit(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(50, ge=1, le=500)
):
    """Get recent audit events"""
    from datetime import datetime
    
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

# Include audit router
app.include_router(audit_router)
```

### Step 4: Update SQL Execution to Include More Audit Data

Enhance the audit logging in your execute_sql endpoint:

```python
@app.post("/api/v1/{db_name}/execute")
async def execute_sql(
    db_name: str,
    request: SQLExecuteRequest,
    executor: SQLExecutor = Depends(get_database_executor),
    api_key: str = Depends(get_api_key_header),
    http_request: Request  # Add this to get client IP
):
    """Execute SQL with enhanced audit logging"""
    
    db_config = app.state.settings.get_database(db_name)
    start_time = datetime.now()
    
    # ... existing validation code ...
    
    try:
        # Execute SQL
        result = executor.execute_query(...)
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Enhanced audit logging with client IP
        if app.state.audit_logger:
            app.state.audit_logger.log_event(
                event_type="sql_executed",
                database=db_name,
                username=db_config.username,  # Add username
                sql=request.sql,  # Full SQL for DB, truncated for file
                rows_affected=result.get("rows_affected"),
                execution_time_ms=execution_time,
                status="success",
                api_key=api_key[-8:],  # Last 8 chars only
                client_ip=http_request.client.host,  # Client IP
                fetch_size=request.fetch_size  # Additional data
            )
        
        # ... return response ...
        
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Log failure
        if app.state.audit_logger:
            app.state.audit_logger.log_event(
                event_type="sql_execution_failed",
                database=db_name,
                username=db_config.username,
                sql=request.sql,
                execution_time_ms=execution_time,
                status="failed",
                error=str(e),
                api_key=api_key[-8:],
                client_ip=http_request.client.host
            )
        
        raise HTTPException(...)
```

## API Usage Examples

### Query Recent Audit Logs
```bash
# Get last 24 hours
curl "http://localhost:8000/api/v1/audit/recent?hours=24&limit=50"

# Response:
{
  "lookback_hours": 24,
  "total_records": 45,
  "records": [
    {
      "audit_id": 12345,
      "event_timestamp": "2024-02-13T10:30:00",
      "event_type": "sql_executed",
      "database_name": "CQE_NFT",
      "username": "cqe_user",
      "sql_statement": "SELECT * FROM users WHERE status = 'active'",
      "rows_affected": 150,
      "execution_time_ms": 45.2,
      "status": "success",
      "api_key_hash": "***key***",
      "client_ip": "192.168.1.100",
      "environment": "prod"
    }
  ]
}
```

### Query with Filters
```bash
# Get CQE_NFT executions from last week
curl "http://localhost:8000/api/v1/audit/logs?\
database=CQE_NFT&\
start_date=2024-02-06T00:00:00&\
end_date=2024-02-13T23:59:59&\
status=success&\
limit=200"
```

### Get Statistics
```bash
# Get overall statistics
curl "http://localhost:8000/api/v1/audit/statistics"

# Response:
{
  "statistics": {
    "total_events": 1523,
    "successful_events": 1498,
    "failed_events": 25,
    "avg_execution_time_ms": 42.3,
    "max_execution_time_ms": 1250.5,
    "total_rows_affected": 45678,
    "event_types": {
      "sql_executed": 1450,
      "sql_execution_failed": 25,
      "sql_file_executed": 48
    },
    "databases": {
      "CQE_NFT": 856,
      "CD_PTE_READ": 345,
      "CAS_PTE_READ": 322
    }
  }
}
```

### Get Failed Operations
```bash
# Troubleshoot failures in last 48 hours
curl "http://localhost:8000/api/v1/audit/logs?status=failed&limit=50"
```

## Direct SQL Queries

You can also query the audit table directly:

```sql
-- Get today's audit summary
SELECT 
    DATABASE_NAME,
    STATUS,
    COUNT(*) as count,
    ROUND(AVG(EXECUTION_TIME_MS), 2) as avg_time_ms
FROM AUDIT_LOG
WHERE TRUNC(EVENT_TIMESTAMP) = TRUNC(SYSDATE)
GROUP BY DATABASE_NAME, STATUS
ORDER BY DATABASE_NAME, STATUS;

-- Get slowest queries today
SELECT 
    EVENT_TIMESTAMP,
    DATABASE_NAME,
    SUBSTR(SQL_STATEMENT, 1, 100) as sql_preview,
    EXECUTION_TIME_MS,
    ROWS_AFFECTED
FROM AUDIT_LOG
WHERE TRUNC(EVENT_TIMESTAMP) = TRUNC(SYSDATE)
ORDER BY EXECUTION_TIME_MS DESC
FETCH FIRST 10 ROWS ONLY;

-- Get error summary
SELECT 
    DATABASE_NAME,
    ERROR_MESSAGE,
    COUNT(*) as error_count,
    MAX(EVENT_TIMESTAMP) as last_occurrence
FROM AUDIT_LOG
WHERE STATUS = 'failed'
AND EVENT_TIMESTAMP >= SYSDATE - 7
GROUP BY DATABASE_NAME, ERROR_MESSAGE
ORDER BY error_count DESC;
```

## Maintenance

### Cleanup Old Logs

Automatically cleanup logs older than 90 days:

```bash
# Via API
curl -X POST "http://localhost:8000/api/v1/audit/cleanup?days_to_keep=90"

# Or schedule in cron
0 2 * * 0 curl -X POST "http://localhost:8000/api/v1/audit/cleanup?days_to_keep=90"
```

### Monitor Audit Table Size

```sql
-- Check audit table size
SELECT 
    SEGMENT_NAME,
    ROUND(BYTES/1024/1024, 2) as SIZE_MB,
    NUM_ROWS
FROM USER_SEGMENTS
JOIN USER_TABLES USING (TABLE_NAME)
WHERE SEGMENT_NAME = 'AUDIT_LOG';
```

## Benefits

### JSONL Files
- ✅ Fast writes (no database overhead)
- ✅ Works even if CQE_NFT is unavailable
- ✅ Easy to ship to log aggregators (ELK, Splunk)
- ✅ Simple grep/parsing with standard tools

### Oracle Database
- ✅ Powerful SQL queries
- ✅ Join with other business data
- ✅ Statistics and analytics
- ✅ Retention policies
- ✅ API access for dashboards

## Troubleshooting

### Audit Table Not Created
```bash
# Check if CQE_NFT pool exists
kubectl logs <pod> | grep "CQE_NFT"

# Manually create table if needed
sqlplus cqe_user/password@CQE_NFT @create_audit_table.sql
```

### No Database Audit Logs
Check initialization:
```python
# In logs, you should see:
# ✓ Audit table initialized in CQE_NFT
# File audit: Enabled
# DB audit: Enabled
```

### High Audit Table Growth
Adjust retention:
```sql
-- Cleanup more aggressively
DELETE FROM AUDIT_LOG WHERE EVENT_TIMESTAMP < SYSDATE - 30;
COMMIT;
```

## File Locations

- **JSONL Files**: `/app/logs/audit/audit_YYYYMMDD.jsonl`
- **Database Table**: `CQE_NFT.AUDIT_LOG`
- **Python Module**: `app/utils/audit.py` (use audit_dual.py as audit.py)

---

**Your audit system is now enterprise-grade with dual logging!** 🎯