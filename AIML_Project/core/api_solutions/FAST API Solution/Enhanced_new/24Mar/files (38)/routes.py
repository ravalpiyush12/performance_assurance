"""
reports/routes.py
FastAPI routes for NFT Release Report storage.

Mount in main.py:
    from reports.routes import router as reports_router, init_reports_routes
    init_reports_routes(connection_manager.get_pool('CQE_NFT'))
    app.include_router(reports_router, prefix="/api/v1")
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .database import ReportsDatabase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reports", tags=["Reports"])

_db: Optional[ReportsDatabase] = None


def init_reports_routes(pool):
    global _db
    _db = ReportsDatabase(pool)
    logger.info("Reports routes initialised")


def get_db() -> ReportsDatabase:
    if _db is None:
        raise HTTPException(status_code=503, detail="Reports database not initialised")
    return _db


# ── Request / Response models ──────────────────────────────────────────────────

class SaveReportRequest(BaseModel):
    run_id:               str
    pc_run_id:            str
    lob_name:             str
    release_name:         str
    test_type:            str = "LOAD"       # LOAD | STRESS | ENDURANCE
    test_name:            Optional[str] = None
    track_name:           Optional[str] = None
    report_html:          str                # full HTML string from frontend
    overall_status:       Optional[str] = None
    pass_rate_pct:        Optional[float] = None
    peak_vusers:          Optional[int]   = None
    avg_response_ms:      Optional[float] = None
    p95_response_ms:      Optional[float] = None
    total_transactions:   Optional[int]   = None
    failed_transactions:  Optional[int]   = None
    saved_by:             Optional[str]   = "system"
    notes:                Optional[str]   = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/save")
async def save_report(
    payload: SaveReportRequest,
    db: ReportsDatabase = Depends(get_db)
):
    """
    POST /api/v1/reports/save
    Save rendered report HTML to Oracle API_NFT_RELEASE_REPORTS (CLOB).
    Called by pc_report.html Save modal (Oracle BLOB option).
    """
    if not payload.report_html or len(payload.report_html) < 100:
        raise HTTPException(status_code=400, detail="report_html is empty or too short")

    if payload.test_type not in ('LOAD', 'STRESS', 'ENDURANCE'):
        raise HTTPException(status_code=400, detail="test_type must be LOAD, STRESS, or ENDURANCE")

    result = db.save_release_report(payload.dict())

    if not result['success']:
        # Surface duplicate or DB error back as 409 / 500
        status = 409 if 'already saved' in result.get('error', '') else 500
        raise HTTPException(status_code=status, detail=result['error'])

    return {
        "success": True,
        "report_id":     result['report_id'],
        "report_size_kb": result['report_size_kb'],
        "message":       result['message']
    }


@router.get("/list")
async def list_reports(
    lob_name:     str,
    release_name: Optional[str] = None,
    test_type:    Optional[str] = None,
    limit:        int = 50,
    db: ReportsDatabase = Depends(get_db)
):
    """
    GET /api/v1/reports/list?lob_name=Digital+Technology&release_name=Release+2.5
    Returns report metadata (no HTML content).
    """
    reports = db.get_release_reports(lob_name, release_name, test_type, limit)
    return {
        "success": True,
        "count":   len(reports),
        "reports": reports
    }


@router.get("/view/{report_id}", response_class=HTMLResponse)
async def view_report(
    report_id: int,
    db: ReportsDatabase = Depends(get_db)
):
    """
    GET /api/v1/reports/view/{report_id}
    Returns the full HTML of a saved report — browser renders it directly.
    """
    html = db.get_report_html(report_id)
    if html is None:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    return HTMLResponse(content=html)


@router.delete("/{report_id}")
async def delete_report(
    report_id: int,
    db: ReportsDatabase = Depends(get_db)
):
    """
    DELETE /api/v1/reports/{report_id}
    Soft-deletes a report (IS_ACTIVE = 'N').
    """
    ok = db.delete_report(report_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found or already deleted")
    return {"success": True, "message": f"Report {report_id} deleted"}
