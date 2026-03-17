"""
Kibana Monitoring API Routes
Follows exact pattern of appd/routes.py and awr/routes.py:
  - Global db instance initialized at startup
  - try/except HTTPException/Exception pattern
  - logger.error with exc_info=True
  - current_user from get_current_user dependency
"""
import logging
import os
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel

from .database import KibanaDatabase
from .client import KibanaMonitoringClient
from Auth.routes_fixed import get_current_user as verify_auth_token

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Kibana Monitoring"])

# Global DB instance — initialized at startup via init_kibana_routes()
kibana_db: Optional[KibanaDatabase] = None


def init_kibana_routes(oracle_pool) -> None:
    """Initialize Kibana routes with Oracle connection pool. Called from main.py startup."""
    global kibana_db
    kibana_db = KibanaDatabase(connection_pool=oracle_pool)
    logger.info("Kibana monitoring routes initialized with Oracle pool")


# ─── Request / Response Models ────────────────────────────────────────────────

class KibanaFetchRequest(BaseModel):
    run_id: str
    lob_name: str
    dashboard_id: str
    dashboard_name: str
    kibana_url: str
    token_env_var: str
    username: Optional[str] = None
    auth_type: str = 'apikey'
    time_range_minutes: int = 10

    class Config:
        schema_extra = {
            "example": {
                "run_id": "NFT-DT-CDV3-20260317-001",
                "lob_name": "Digital Technology",
                "dashboard_id": "abc12345-def6-7890-abcd-kib01",
                "dashboard_name": "API Performance — CDV3",
                "kibana_url": "https://kibana.corp.internal:5601",
                "token_env_var": "KIBANA_TOKEN_DIGTECH",
                "time_range_minutes": 10
            }
        }


class KibanaTestConnectionRequest(BaseModel):
    kibana_url: str
    token_env_var: str
    username: Optional[str] = None
    auth_type: str = 'apikey'

    class Config:
        schema_extra = {
            "example": {
                "kibana_url": "https://kibana.corp.internal:5601",
                "token_env_var": "KIBANA_TOKEN_DIGTECH",
            }
        }


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/kibana/test-connection")
async def test_kibana_connection(
    request: KibanaTestConnectionRequest,
    current_user: str = Depends(verify_auth_token)
):
    """Test Kibana connection using credentials from environment variable."""
    try:
        client = KibanaMonitoringClient(
            kibana_url=request.kibana_url,
            username=request.username,
            token_env_var=request.token_env_var,
            auth_type=request.auth_type,
        )
        result = client.test_connection()
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Kibana test connection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Test connection failed: {str(e)}")


@router.post("/kibana/fetch")
async def fetch_kibana_metrics(
    request: KibanaFetchRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(verify_auth_token)
):
    """
    Collect Kibana dashboard metrics for a monitoring run.
    Fetches API endpoint metrics and stores them in API_KIBANA_METRICS.
    """
    if not kibana_db:
        raise HTTPException(status_code=503, detail="Kibana database not initialized")
    try:
        client = KibanaMonitoringClient(
            kibana_url=request.kibana_url,
            username=request.username,
            token_env_var=request.token_env_var,
            auth_type=request.auth_type,
        )
        result = client.collect_dashboard_metrics(
            dashboard_id=request.dashboard_id,
            time_range_minutes=request.time_range_minutes,
        )

        if result.get('success') and result.get('status') == 'PASS':
            metrics_list = result.get('metrics', [])
            if metrics_list:
                inserted = kibana_db.insert_kibana_metrics_batch(
                    run_id=request.run_id,
                    dashboard_id=request.dashboard_id,
                    dashboard_name=request.dashboard_name,
                    metrics_list=metrics_list,
                )
                result['stored_count'] = inserted
            else:
                result['stored_count'] = 0

        return {
            'success': result.get('success', False),
            'run_id': request.run_id,
            'dashboard_id': request.dashboard_id,
            'dashboard_name': request.dashboard_name,
            'status': result.get('status'),
            'message': result.get('message'),
            'record_count': result.get('record_count', 0),
            'error_rate': result.get('error_rate', 0),
            'p95_ms': result.get('p95_ms', 0),
            'stored_count': result.get('stored_count', 0),
            'last_data_point': result.get('last_data_point'),
            'contact_app_team': result.get('contact_app_team', False),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Kibana fetch error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Kibana fetch failed: {str(e)}")


@router.get("/kibana/metrics/{run_id}")
async def get_kibana_metrics(
    run_id: str,
    current_user: str = Depends(verify_auth_token)
):
    """
    Retrieve all stored Kibana metrics for a run_id.
    Used by test-report.html to populate the Kibana Analysis tab.
    """
    if not kibana_db:
        raise HTTPException(status_code=503, detail="Kibana database not initialized")
    try:
        metrics = kibana_db.get_metrics_by_run_id(run_id)
        summary = kibana_db.get_summary_by_run_id(run_id)
        return {
            'success': True,
            'run_id': run_id,
            'summary': summary,
            'metrics': metrics,
            'total_records': len(metrics),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get Kibana metrics error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")


@router.get("/kibana/metrics/{run_id}/summary")
async def get_kibana_summary(
    run_id: str,
    current_user: str = Depends(verify_auth_token)
):
    """Get aggregated summary of Kibana metrics for a run."""
    if not kibana_db:
        raise HTTPException(status_code=503, detail="Kibana database not initialized")
    try:
        summary = kibana_db.get_summary_by_run_id(run_id)
        if not summary:
            raise HTTPException(status_code=404, detail=f"No Kibana metrics found for run_id '{run_id}'")
        return {'success': True, 'run_id': run_id, 'summary': summary}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get Kibana summary error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve summary: {str(e)}")
