"""
Audit API Endpoints
Add these endpoints to your main.py for querying audit logs
"""

from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta
from typing import Optional

# Create router for audit endpoints
audit_router = APIRouter(prefix="/api/v1/audit", tags=["Audit"])


@audit_router.get("/logs", summary="Query audit logs from database")
async def query_audit_logs(
    start_date: Optional[str] = Query(None, description="Start date (ISO format: 2024-02-13T00:00:00)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format: 2024-02-13T23:59:59)"),
    database: Optional[str] = Query(None, description="Filter by database name"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    status: Optional[str] = Query(None, description="Filter by status (success/failed)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records")
):
    """
    Query audit logs from CQE_NFT database
    
    Returns audit records with filtering options
    """
    # Parse dates if provided
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    # Query from audit logger
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


@audit_router.get("/statistics", summary="Get audit log statistics")
async def get_audit_statistics(
    start_date: Optional[str] = Query(None, description="Start date for statistics"),
    end_date: Optional[str] = Query(None, description="End date for statistics")
):
    """
    Get statistical summary of audit logs
    
    Returns:
    - Total events
    - Success/failure counts
    - Average execution time
    - Event type breakdown
    - Database breakdown
    """
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


@audit_router.get("/recent", summary="Get recent audit events")
async def get_recent_audit_events(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to look back"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of records")
):
    """
    Get most recent audit events
    
    Convenient endpoint for monitoring recent activity
    """
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


@audit_router.get("/by-database/{database}", summary="Get audit logs for specific database")
async def get_database_audit_logs(
    database: str,
    hours: int = Query(24, ge=1, le=168, description="Number of hours to look back"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records")
):
    """
    Get audit logs for a specific database
    """
    start_date = datetime.now() - timedelta(hours=hours)
    
    results = app.state.audit_logger.query_audit_logs(
        start_date=start_date,
        database=database.upper(),
        limit=limit
    )
    
    # Get stats for this database
    stats = app.state.audit_logger.get_audit_statistics(
        start_date=start_date
    )
    
    db_stats = {
        "total_events": stats.get("databases", {}).get(database.upper(), 0),
        "success_rate": 0
    }
    
    if db_stats["total_events"] > 0:
        success_count = sum(1 for r in results if r.get("status") == "success")
        db_stats["success_rate"] = (success_count / len(results)) * 100
    
    return {
        "database": database.upper(),
        "lookback_hours": hours,
        "total_records": len(results),
        "statistics": db_stats,
        "records": results
    }


@audit_router.get("/failed", summary="Get failed operations")
async def get_failed_operations(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to look back"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records")
):
    """
    Get all failed operations for troubleshooting
    """
    start_date = datetime.now() - timedelta(hours=hours)
    
    results = app.state.audit_logger.query_audit_logs(
        start_date=start_date,
        status="failed",
        limit=limit
    )
    
    return {
        "lookback_hours": hours,
        "total_failed": len(results),
        "records": results
    }


@audit_router.post("/cleanup", summary="Cleanup old audit logs")
async def cleanup_audit_logs(
    days_to_keep: int = Query(90, ge=30, le=365, description="Number of days to retain")
):
    """
    Delete audit logs older than specified days
    
    Requires admin privileges
    """
    app.state.audit_logger.cleanup_old_logs(days_to_keep=days_to_keep)
    
    return {
        "message": f"Cleanup initiated for logs older than {days_to_keep} days",
        "days_to_keep": days_to_keep
    }


# ========================================
# Add to main.py after creating app
# ========================================
# app.include_router(audit_router)


"""
USAGE EXAMPLES:

1. Get recent audit logs:
   GET /api/v1/audit/recent?hours=24&limit=50

2. Query with filters:
   GET /api/v1/audit/logs?database=CQE_NFT&status=success&limit=100

3. Get statistics:
   GET /api/v1/audit/statistics?start_date=2024-02-01T00:00:00

4. Get database-specific logs:
   GET /api/v1/audit/by-database/CQE_NFT?hours=48

5. Get failed operations:
   GET /api/v1/audit/failed?hours=24

6. Cleanup old logs:
   POST /api/v1/audit/cleanup?days_to_keep=90
"""