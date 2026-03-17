"""
NFT Platform API Routes
All endpoints for: User LOB Access, AppD/Kibana/Splunk/MongoDB/PC/DB configs,
Track Templates, and Release Reports.

Matches exact style of monitoring/appd/routes.py:
  - Global db instance initialized by init_nft_routes()
  - HTTPException for all error cases
  - try/except/raise pattern
  - Depends(verify_auth_token) on all endpoints
"""
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import HTMLResponse

from .database import NFTPlatformDatabase
from .models import (
    UserLobGrantRequest, UserLobRevokeRequest, UserLobAccessResponse,
    AppdConfigRequest, AppdConfigResponse,
    KibanaConfigRequest, KibanaConfigResponse,
    SplunkConfigRequest, SplunkConfigResponse,
    MongoDbConfigRequest, MongoDbConfigResponse,
    PcConfigRequest, PcConfigResponse,
    DbConfigRequest, DbConfigResponse,
    TrackTemplateRequest, TrackTemplateResponse,
    ReleaseReportSaveRequest, ReleaseReportSaveResponse,
    TestConnectionResponse
)

# Auth dependency — same as used in appd/routes.py and pc/routes.py
from Auth import get_current_user as verify_auth_token

logger = logging.getLogger(__name__)

router = APIRouter()

# Global database instance — initialized by init_nft_routes()
nft_db: Optional[NFTPlatformDatabase] = None


def init_nft_routes(oracle_connection_pool) -> None:
    """Initialize NFT routes with Oracle connection pool.
    Called from main.py startup event, same pattern as init_appd_components()
    and init_pc_routes().

    Args:
        oracle_connection_pool: Oracle pool from connection_manager.get_pool('CQE_NFT')
    """
    global nft_db
    nft_db = NFTPlatformDatabase(oracle_connection_pool)
    logger.info("NFT platform routes initialized")


# =============================================================================
# USER LOB ACCESS ENDPOINTS
# Prefix: /api/v1/nft/user-lob-access
# =============================================================================

@router.post("/user-lob-access/grant", response_model=UserLobAccessResponse)
async def grant_user_lob_access(
    request: UserLobGrantRequest,
    current_user: str = Depends(verify_auth_token)
):
    """Grant a user access to a LOB.
    Admin only — allows PE/test_lead users to see this LOB after login.
    """
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        result = nft_db.grant_user_lob_access(
            username=request.username,
            lob_name=request.lob_name,
            granted_by=request.granted_by
        )
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error'))
        return UserLobAccessResponse(
            success=True,
            message=result['message'],
            access_id=result.get('access_id'),
            username=request.username,
            lob_name=request.lob_name
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to grant LOB access: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to grant access: {str(e)}")


@router.post("/user-lob-access/revoke", response_model=UserLobAccessResponse)
async def revoke_user_lob_access(
    request: UserLobRevokeRequest,
    current_user: str = Depends(verify_auth_token)
):
    """Revoke a user's access to a LOB (soft delete)."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        result = nft_db.revoke_user_lob_access(
            username=request.username,
            lob_name=request.lob_name,
            revoked_by=request.revoked_by
        )
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error'))
        return UserLobAccessResponse(
            success=True,
            message=result['message'],
            username=request.username,
            lob_name=request.lob_name
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke LOB access: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to revoke access: {str(e)}")


@router.get("/user-lob-access/{username}")
async def get_user_lob_access(
    username: str,
    current_user: str = Depends(verify_auth_token)
):
    """Get all LOBs accessible to a user."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        lobs = nft_db.get_user_lobs(username)
        return {"success": True, "username": username,
                "total": len(lobs), "lobs": lobs}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user LOBs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get user LOBs: {str(e)}")


@router.get("/user-lob-access")
async def list_all_user_lob_access(
    lob_name: Optional[str] = None,
    current_user: str = Depends(verify_auth_token)
):
    """List all user-LOB access records. Optionally filter by LOB."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        records = nft_db.list_all_user_lob_access(lob_name=lob_name)
        return {"success": True, "total": len(records), "records": records}
    except Exception as e:
        logger.error(f"Failed to list user LOB access: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list access: {str(e)}")


# =============================================================================
# APPD CONFIG ENDPOINTS
# Prefix: /api/v1/nft/config/appd
# =============================================================================

@router.post("/config/appd", response_model=AppdConfigResponse)
async def create_appd_config(
    request: AppdConfigRequest,
    current_user: str = Depends(verify_auth_token)
):
    """Create AppDynamics config for a LOB/Track.
    TOKEN_ENV_VAR must be the environment variable NAME, never the actual token.
    """
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        # Check if config already exists for this LOB/Track
        existing = nft_db.get_appd_config(request.lob_name, request.track)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"AppD config already exists for {request.lob_name}/{request.track}. Use PUT to update."
            )
        result = nft_db.save_appd_config(
            lob_name=request.lob_name,
            track=request.track,
            controller_url=request.controller_url,
            account_name=request.account_name,
            token_env_var=request.token_env_var,
            application_names=request.application_names,
            tier_filter=request.tier_filter,
            node_filter=request.node_filter,
            collection_interval=request.collection_interval,
            created_by=request.created_by
        )
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error'))
        return AppdConfigResponse(
            success=True,
            message=f"AppD config saved for {request.lob_name}/{request.track}",
            config_id=result['config_id'],
            lob_name=request.lob_name,
            track=request.track
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create AppD config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save AppD config: {str(e)}")


@router.get("/config/appd/{lob_name}/{track}")
async def get_appd_config(
    lob_name: str,
    track: str,
    current_user: str = Depends(verify_auth_token)
):
    """Get AppD config for a LOB/Track."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        config = nft_db.get_appd_config(lob_name, track)
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"AppD config not found for {lob_name}/{track}"
            )
        return {"success": True, "config": config}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get AppD config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get AppD config: {str(e)}")


@router.delete("/config/appd/{config_id}")
async def delete_appd_config(
    config_id: int,
    updated_by: str,
    current_user: str = Depends(verify_auth_token)
):
    """Soft delete AppD config (IS_ACTIVE = N)."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        result = nft_db.delete_appd_config(config_id, updated_by)
        if not result['success']:
            raise HTTPException(status_code=404, detail=result.get('error', 'Config not found'))
        return {"success": True,
                "message": f"AppD config {config_id} deactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete AppD config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete AppD config: {str(e)}")


@router.post("/config/appd/{config_id}/test-connection",
             response_model=TestConnectionResponse)
async def test_appd_connection(
    config_id: int,
    current_user: str = Depends(verify_auth_token)
):
    """Test AppDynamics connection using stored config.
    Reads token from environment variable. Returns contact_app_team=True if no data found.
    """
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        config = nft_db.get_appd_config_by_id(config_id)
        if not config:
            raise HTTPException(status_code=404, detail=f"Config {config_id} not found")
        # Get actual token from environment variable
        token = os.getenv(config['token_env_var'])
        if not token:
            nft_db.update_appd_test_status(config_id, 'FAIL')
            return TestConnectionResponse(
                success=False,
                message=f"Environment variable '{config['token_env_var']}' not set",
                status='FAIL'
            )
        # Attempt a lightweight API call to AppDynamics
        try:
            import requests
            headers = {"Authorization": f"Bearer {token}",
                       "Content-Type": "application/json"}
            resp = requests.get(
                f"{config['controller_url']}/controller/rest/applications",
                headers=headers,
                params={"output": "JSON"},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                has_data = isinstance(data, list) and len(data) > 0
                status = 'PASS' if has_data else 'PASS'
                nft_db.update_appd_test_status(config_id, status)
                return TestConnectionResponse(
                    success=True,
                    message=f"Connected successfully. Found {len(data)} applications.",
                    status='PASS',
                    contact_app_team=not has_data
                )
            else:
                nft_db.update_appd_test_status(config_id, 'FAIL')
                return TestConnectionResponse(
                    success=False,
                    message=f"AppDynamics returned HTTP {resp.status_code}",
                    status='FAIL'
                )
        except Exception as conn_err:
            nft_db.update_appd_test_status(config_id, 'FAIL')
            return TestConnectionResponse(
                success=False,
                message=f"Connection failed: {str(conn_err)}",
                status='FAIL'
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test AppD connection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Test connection failed: {str(e)}")


# =============================================================================
# KIBANA CONFIG ENDPOINTS
# Prefix: /api/v1/nft/config/kibana
# =============================================================================

@router.post("/config/kibana", response_model=KibanaConfigResponse)
async def create_kibana_config(
    request: KibanaConfigRequest,
    current_user: str = Depends(verify_auth_token)
):
    """Create Kibana config for a LOB/Track."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        existing = nft_db.get_kibana_config(request.lob_name, request.track)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Kibana config already exists for {request.lob_name}/{request.track}"
            )
        result = nft_db.save_kibana_config(
            lob_name=request.lob_name,
            track=request.track,
            kibana_url=request.kibana_url,
            dashboard_id=request.dashboard_id,
            display_name=request.display_name,
            index_pattern=request.index_pattern,
            token_env_var=request.token_env_var,
            time_field=request.time_field,
            default_time_range=request.default_time_range,
            custom_filters=request.custom_filters,
            created_by=request.created_by
        )
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error'))
        return KibanaConfigResponse(
            success=True,
            message=f"Kibana config saved for {request.lob_name}/{request.track}",
            config_id=result['config_id'],
            lob_name=request.lob_name,
            track=request.track
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create Kibana config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save Kibana config: {str(e)}")


@router.get("/config/kibana/{lob_name}/{track}")
async def get_kibana_config(
    lob_name: str,
    track: str,
    current_user: str = Depends(verify_auth_token)
):
    """Get Kibana config for a LOB/Track."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        config = nft_db.get_kibana_config(lob_name, track)
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Kibana config not found for {lob_name}/{track}"
            )
        return {"success": True, "config": config}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Kibana config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get Kibana config: {str(e)}")


@router.delete("/config/kibana/{config_id}")
async def delete_kibana_config(
    config_id: int,
    updated_by: str,
    current_user: str = Depends(verify_auth_token)
):
    """Soft delete Kibana config."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        result = nft_db.delete_kibana_config(config_id, updated_by)
        if not result['success']:
            raise HTTPException(status_code=404, detail=result.get('error'))
        return {"success": True, "message": f"Kibana config {config_id} deactivated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete Kibana config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete Kibana config: {str(e)}")


@router.post("/config/kibana/{config_id}/test-connection",
             response_model=TestConnectionResponse)
async def test_kibana_connection(
    config_id: int,
    current_user: str = Depends(verify_auth_token)
):
    """Test Kibana connection using stored config."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        config = nft_db.get_kibana_config_by_id(config_id)
        if not config:
            raise HTTPException(status_code=404, detail=f"Config {config_id} not found")
        token = os.getenv(config['token_env_var']) if config.get('token_env_var') else None
        try:
            import requests
            headers = {"Content-Type": "application/json", "kbn-xsrf": "true"}
            if token:
                headers["Authorization"] = f"ApiKey {token}"
            resp = requests.get(
                f"{config['kibana_url']}/api/status",
                headers=headers,
                timeout=10
            )
            if resp.status_code == 200:
                nft_db.update_kibana_test_status(config_id, 'PASS')
                return TestConnectionResponse(
                    success=True,
                    message="Kibana connection successful",
                    status='PASS'
                )
            else:
                nft_db.update_kibana_test_status(config_id, 'FAIL')
                return TestConnectionResponse(
                    success=False,
                    message=f"Kibana returned HTTP {resp.status_code}",
                    status='FAIL'
                )
        except Exception as conn_err:
            nft_db.update_kibana_test_status(config_id, 'FAIL')
            return TestConnectionResponse(
                success=False, message=f"Connection failed: {str(conn_err)}", status='FAIL'
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test Kibana connection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Test connection failed: {str(e)}")


# =============================================================================
# SPLUNK CONFIG ENDPOINTS
# =============================================================================

@router.post("/config/splunk", response_model=SplunkConfigResponse)
async def create_splunk_config(
    request: SplunkConfigRequest,
    current_user: str = Depends(verify_auth_token)
):
    """Create Splunk config for a LOB/Track."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        existing = nft_db.get_splunk_config(request.lob_name, request.track)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Splunk config already exists for {request.lob_name}/{request.track}"
            )
        result = nft_db.save_splunk_config(
            lob_name=request.lob_name,
            track=request.track,
            splunk_url=request.splunk_url,
            token_env_var=request.token_env_var,
            default_index=request.default_index,
            saved_search_name=request.saved_search_name,
            spl_query=request.spl_query,
            search_type=request.search_type,
            dashboard_name=request.dashboard_name,
            time_range=request.time_range,
            error_patterns=request.error_patterns,
            created_by=request.created_by
        )
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error'))
        return SplunkConfigResponse(
            success=True,
            message=f"Splunk config saved for {request.lob_name}/{request.track}",
            config_id=result['config_id'],
            lob_name=request.lob_name,
            track=request.track
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create Splunk config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save Splunk config: {str(e)}")


@router.get("/config/splunk/{lob_name}/{track}")
async def get_splunk_config(
    lob_name: str,
    track: str,
    current_user: str = Depends(verify_auth_token)
):
    """Get Splunk config for a LOB/Track."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        config = nft_db.get_splunk_config(lob_name, track)
        if not config:
            raise HTTPException(status_code=404,
                                detail=f"Splunk config not found for {lob_name}/{track}")
        return {"success": True, "config": config}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Splunk config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get Splunk config: {str(e)}")


@router.delete("/config/splunk/{config_id}")
async def delete_splunk_config(
    config_id: int,
    updated_by: str,
    current_user: str = Depends(verify_auth_token)
):
    """Soft delete Splunk config."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        result = nft_db.delete_splunk_config(config_id, updated_by)
        if not result['success']:
            raise HTTPException(status_code=404, detail=result.get('error'))
        return {"success": True, "message": f"Splunk config {config_id} deactivated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete Splunk config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete Splunk config: {str(e)}")


@router.post("/config/splunk/{config_id}/test-connection",
             response_model=TestConnectionResponse)
async def test_splunk_connection(
    config_id: int,
    current_user: str = Depends(verify_auth_token)
):
    """Test Splunk connection using stored config."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        config = nft_db.get_splunk_config(None, None)  # Will be fetched by id below
        # Direct DB call since we have id
        with nft_db.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT CONFIG_ID, SPLUNK_URL, TOKEN_ENV_VAR, DEFAULT_INDEX
                    FROM API_NFT_SPLUNK_CONFIG WHERE CONFIG_ID = :config_id
                """, {'config_id': config_id})
                row = cursor.fetchone()
            finally:
                cursor.close()
        if not row:
            raise HTTPException(status_code=404, detail=f"Config {config_id} not found")
        splunk_url, token_env_var, default_index = row[1], row[2], row[3]
        token = os.getenv(token_env_var)
        if not token:
            nft_db.update_splunk_test_status(config_id, 'FAIL')
            return TestConnectionResponse(
                success=False,
                message=f"Environment variable '{token_env_var}' not set",
                status='FAIL'
            )
        try:
            import requests
            headers = {"Authorization": f"Bearer {token}"}
            resp = requests.get(
                f"{splunk_url}/services/search/jobs",
                headers=headers,
                verify=False,
                timeout=10
            )
            if resp.status_code in [200, 201]:
                nft_db.update_splunk_test_status(config_id, 'PASS')
                return TestConnectionResponse(
                    success=True, message="Splunk connection successful", status='PASS'
                )
            else:
                nft_db.update_splunk_test_status(config_id, 'FAIL')
                return TestConnectionResponse(
                    success=False,
                    message=f"Splunk returned HTTP {resp.status_code}",
                    status='FAIL'
                )
        except Exception as conn_err:
            nft_db.update_splunk_test_status(config_id, 'FAIL')
            return TestConnectionResponse(
                success=False, message=f"Connection failed: {str(conn_err)}", status='FAIL'
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test Splunk connection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Test connection failed: {str(e)}")


# =============================================================================
# MONGODB CONFIG ENDPOINTS
# =============================================================================

@router.post("/config/mongodb", response_model=MongoDbConfigResponse)
async def create_mongodb_config(
    request: MongoDbConfigRequest,
    current_user: str = Depends(verify_auth_token)
):
    """Create MongoDB config for a LOB/Track."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        existing = nft_db.get_mongodb_config(request.lob_name, request.track)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"MongoDB config already exists for {request.lob_name}/{request.track}"
            )
        result = nft_db.save_mongodb_config(
            lob_name=request.lob_name,
            track=request.track,
            uri_env_var=request.uri_env_var,
            database_name=request.database_name,
            collection_names=request.collection_names,
            replica_set=request.replica_set,
            auth_db=request.auth_db,
            slow_query_ms=request.slow_query_ms,
            created_by=request.created_by
        )
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error'))
        return MongoDbConfigResponse(
            success=True,
            message=f"MongoDB config saved for {request.lob_name}/{request.track}",
            config_id=result['config_id'],
            lob_name=request.lob_name,
            track=request.track
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create MongoDB config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save MongoDB config: {str(e)}")


@router.get("/config/mongodb/{lob_name}/{track}")
async def get_mongodb_config(
    lob_name: str,
    track: str,
    current_user: str = Depends(verify_auth_token)
):
    """Get MongoDB config for a LOB/Track."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        config = nft_db.get_mongodb_config(lob_name, track)
        if not config:
            raise HTTPException(status_code=404,
                                detail=f"MongoDB config not found for {lob_name}/{track}")
        return {"success": True, "config": config}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get MongoDB config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get MongoDB config: {str(e)}")


@router.delete("/config/mongodb/{config_id}")
async def delete_mongodb_config(
    config_id: int,
    updated_by: str,
    current_user: str = Depends(verify_auth_token)
):
    """Soft delete MongoDB config."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        result = nft_db.delete_mongodb_config(config_id, updated_by)
        if not result['success']:
            raise HTTPException(status_code=404, detail=result.get('error'))
        return {"success": True, "message": f"MongoDB config {config_id} deactivated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete MongoDB config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete MongoDB config: {str(e)}")


@router.post("/config/mongodb/{config_id}/test-connection",
             response_model=TestConnectionResponse)
async def test_mongodb_connection(
    config_id: int,
    current_user: str = Depends(verify_auth_token)
):
    """Test MongoDB connection using stored config."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        config = nft_db.get_mongodb_config(None, None)
        # Fetch directly by id
        with nft_db.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT URI_ENV_VAR, DATABASE_NAME
                    FROM API_NFT_MONGODB_CONFIG WHERE CONFIG_ID = :config_id
                """, {'config_id': config_id})
                row = cursor.fetchone()
            finally:
                cursor.close()
        if not row:
            raise HTTPException(status_code=404, detail=f"Config {config_id} not found")
        uri = os.getenv(row[0])
        if not uri:
            nft_db.update_mongodb_test_status(config_id, 'FAIL')
            return TestConnectionResponse(
                success=False,
                message=f"Environment variable '{row[0]}' not set",
                status='FAIL'
            )
        try:
            from pymongo import MongoClient
            client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            client.server_info()
            db = client[row[1]]
            collections = db.list_collection_names()
            has_data = len(collections) > 0
            nft_db.update_mongodb_test_status(config_id, 'PASS')
            return TestConnectionResponse(
                success=True,
                message=f"MongoDB connected. Found {len(collections)} collections.",
                status='PASS',
                contact_app_team=not has_data
            )
        except Exception as conn_err:
            nft_db.update_mongodb_test_status(config_id, 'FAIL')
            return TestConnectionResponse(
                success=False, message=f"Connection failed: {str(conn_err)}", status='FAIL'
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test MongoDB connection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Test connection failed: {str(e)}")


# =============================================================================
# PC CONFIG ENDPOINTS
# =============================================================================

@router.post("/config/pc", response_model=PcConfigResponse)
async def create_pc_config(
    request: PcConfigRequest,
    current_user: str = Depends(verify_auth_token)
):
    """Create Performance Center config for a LOB/Track."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        existing = nft_db.get_pc_config(request.lob_name, request.track)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"PC config already exists for {request.lob_name}/{request.track}"
            )
        result = nft_db.save_pc_config(
            lob_name=request.lob_name,
            track=request.track,
            pc_url=request.pc_url,
            pc_domain=request.pc_domain,
            pc_project=request.pc_project,
            username=request.username,
            password_env_var=request.password_env_var,
            duration_format=request.duration_format,
            cookie_flag=request.cookie_flag,
            default_timeout_min=request.default_timeout_min,
            created_by=request.created_by
        )
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error'))
        return PcConfigResponse(
            success=True,
            message=f"PC config saved for {request.lob_name}/{request.track}",
            config_id=result['config_id'],
            lob_name=request.lob_name,
            track=request.track
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create PC config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save PC config: {str(e)}")


@router.get("/config/pc/{lob_name}/{track}")
async def get_pc_config(
    lob_name: str,
    track: str,
    current_user: str = Depends(verify_auth_token)
):
    """Get PC config for a LOB/Track."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        config = nft_db.get_pc_config(lob_name, track)
        if not config:
            raise HTTPException(status_code=404,
                                detail=f"PC config not found for {lob_name}/{track}")
        return {"success": True, "config": config}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get PC config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get PC config: {str(e)}")


@router.delete("/config/pc/{config_id}")
async def delete_pc_config(
    config_id: int,
    updated_by: str,
    current_user: str = Depends(verify_auth_token)
):
    """Soft delete PC config."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        result = nft_db.delete_pc_config(config_id, updated_by)
        if not result['success']:
            raise HTTPException(status_code=404, detail=result.get('error'))
        return {"success": True, "message": f"PC config {config_id} deactivated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete PC config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete PC config: {str(e)}")


@router.post("/config/pc/{config_id}/test-connection",
             response_model=TestConnectionResponse)
async def test_pc_connection(
    config_id: int,
    current_user: str = Depends(verify_auth_token)
):
    """Test PC connection using existing PerformanceCenterClient."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        config = nft_db.get_pc_config(None, None)
        with nft_db.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT PC_URL, PC_DOMAIN, PC_PROJECT, USERNAME, PASSWORD_ENV_VAR
                    FROM API_NFT_PC_CONFIG WHERE CONFIG_ID = :config_id
                """, {'config_id': config_id})
                row = cursor.fetchone()
            finally:
                cursor.close()
        if not row:
            raise HTTPException(status_code=404, detail=f"Config {config_id} not found")
        password = os.getenv(row[4])
        if not password:
            nft_db.update_pc_test_status(config_id, 'FAIL')
            return TestConnectionResponse(
                success=False,
                message=f"Environment variable '{row[4]}' not set",
                status='FAIL'
            )
        try:
            # Reuse existing PerformanceCenterClient from monitoring/pc/client.py
            from monitoring.pc.client import PerformanceCenterClient
            client = PerformanceCenterClient(
                base_url=f"{row[0]}:{80}",
                username=row[3],
                password=password,
                domain=row[1],
                project=row[2]
            )
            client.authenticate()
            client.logout()
            nft_db.update_pc_test_status(config_id, 'PASS')
            return TestConnectionResponse(
                success=True, message="PC connection successful", status='PASS'
            )
        except Exception as conn_err:
            nft_db.update_pc_test_status(config_id, 'FAIL')
            return TestConnectionResponse(
                success=False, message=f"PC connection failed: {str(conn_err)}", status='FAIL'
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test PC connection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Test connection failed: {str(e)}")


# =============================================================================
# DB CONFIG ENDPOINTS
# =============================================================================

@router.post("/config/db", response_model=DbConfigResponse)
async def create_db_config(
    request: DbConfigRequest,
    current_user: str = Depends(verify_auth_token)
):
    """Create Oracle DB config for AWR target database."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        existing = nft_db.get_db_config(request.lob_name, request.track)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"DB config already exists for {request.lob_name}/{request.track}"
            )
        result = nft_db.save_db_config(
            lob_name=request.lob_name,
            track=request.track,
            db_alias=request.db_alias,
            host=request.host,
            port=request.port,
            service_name=request.service_name,
            username=request.username,
            password_env_var=request.password_env_var,
            use_cyberark=request.use_cyberark,
            cyberark_safe=request.cyberark_safe,
            cyberark_object=request.cyberark_object,
            created_by=request.created_by
        )
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error'))
        return DbConfigResponse(
            success=True,
            message=f"DB config saved for {request.lob_name}/{request.track}",
            config_id=result['config_id'],
            lob_name=request.lob_name,
            track=request.track
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create DB config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save DB config: {str(e)}")


@router.get("/config/db/{lob_name}/{track}")
async def get_db_config(
    lob_name: str,
    track: str,
    current_user: str = Depends(verify_auth_token)
):
    """Get Oracle DB config for a LOB/Track."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        config = nft_db.get_db_config(lob_name, track)
        if not config:
            raise HTTPException(status_code=404,
                                detail=f"DB config not found for {lob_name}/{track}")
        return {"success": True, "config": config}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get DB config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get DB config: {str(e)}")


@router.delete("/config/db/{config_id}")
async def delete_db_config(
    config_id: int,
    updated_by: str,
    current_user: str = Depends(verify_auth_token)
):
    """Soft delete DB config."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        result = nft_db.delete_db_config(config_id, updated_by)
        if not result['success']:
            raise HTTPException(status_code=404, detail=result.get('error'))
        return {"success": True, "message": f"DB config {config_id} deactivated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete DB config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete DB config: {str(e)}")


@router.post("/config/db/{config_id}/test-connection",
             response_model=TestConnectionResponse)
async def test_db_connection(
    config_id: int,
    current_user: str = Depends(verify_auth_token)
):
    """Test Oracle DB connection using stored config."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        with nft_db.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT HOST, PORT, SERVICE_NAME, USERNAME,
                           PASSWORD_ENV_VAR, USE_CYBERARK
                    FROM API_NFT_DB_CONFIG WHERE CONFIG_ID = :config_id
                """, {'config_id': config_id})
                row = cursor.fetchone()
            finally:
                cursor.close()
        if not row:
            raise HTTPException(status_code=404, detail=f"Config {config_id} not found")
        password = os.getenv(row[4])
        if not password:
            nft_db.update_db_test_status(config_id, 'FAIL')
            return TestConnectionResponse(
                success=False,
                message=f"Environment variable '{row[4]}' not set",
                status='FAIL'
            )
        try:
            import oracledb
            dsn = f"{row[0]}:{row[1]}/{row[2]}"
            test_conn = oracledb.connect(user=row[3], password=password, dsn=dsn)
            test_cursor = test_conn.cursor()
            test_cursor.execute("SELECT 1 FROM DUAL")
            test_cursor.close()
            test_conn.close()
            nft_db.update_db_test_status(config_id, 'PASS')
            return TestConnectionResponse(
                success=True,
                message=f"Oracle DB connected successfully to {row[2]}",
                status='PASS'
            )
        except Exception as conn_err:
            nft_db.update_db_test_status(config_id, 'FAIL')
            return TestConnectionResponse(
                success=False, message=f"DB connection failed: {str(conn_err)}", status='FAIL'
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test DB connection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Test connection failed: {str(e)}")


# =============================================================================
# TRACK TEMPLATE ENDPOINTS
# =============================================================================

@router.post("/track-template", response_model=TrackTemplateResponse)
async def create_track_template(
    request: TrackTemplateRequest,
    current_user: str = Depends(verify_auth_token)
):
    """Create track template linking all tool configs for a LOB/Track."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        existing = nft_db.get_track_template(request.lob_name, request.track)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Track template already exists for {request.lob_name}/{request.track}"
            )
        result = nft_db.save_track_template(
            lob_name=request.lob_name,
            track=request.track,
            appd_config_ids=request.appd_config_ids,
            kibana_config_ids=request.kibana_config_ids,
            splunk_config_ids=request.splunk_config_ids,
            mongodb_config_ids=request.mongodb_config_ids,
            pc_config_ids=request.pc_config_ids,
            db_config_ids=request.db_config_ids,
            created_by=request.created_by
        )
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error'))
        return TrackTemplateResponse(
            success=True,
            message=f"Track template saved for {request.lob_name}/{request.track}",
            template_id=result['template_id'],
            lob_name=request.lob_name,
            track=request.track
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create track template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save track template: {str(e)}")


@router.get("/track-template/{lob_name}/{track}")
async def get_track_template(
    lob_name: str,
    track: str,
    current_user: str = Depends(verify_auth_token)
):
    """Get track template for a LOB/Track."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        template = nft_db.get_track_template(lob_name, track)
        if not template:
            raise HTTPException(status_code=404,
                                detail=f"Track template not found for {lob_name}/{track}")
        return {"success": True, "template": template}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get track template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get track template: {str(e)}")


@router.get("/track-template")
async def list_track_templates(
    lob_name: Optional[str] = None,
    current_user: str = Depends(verify_auth_token)
):
    """List all track templates, optionally filtered by LOB."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        templates = nft_db.list_track_templates(lob_name=lob_name)
        return {"success": True, "total": len(templates), "templates": templates}
    except Exception as e:
        logger.error(f"Failed to list track templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list templates: {str(e)}")


@router.delete("/track-template/{lob_name}/{track}")
async def delete_track_template(
    lob_name: str,
    track: str,
    updated_by: str,
    current_user: str = Depends(verify_auth_token)
):
    """Soft delete track template."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        result = nft_db.delete_track_template(lob_name, track, updated_by)
        if not result['success']:
            raise HTTPException(status_code=404, detail=result.get('error'))
        return {"success": True, "message": result['message']}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete track template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete template: {str(e)}")


# =============================================================================
# RELEASE REPORTS ENDPOINTS
# =============================================================================

@router.post("/release-reports", response_model=ReleaseReportSaveResponse)
async def save_release_report(
    request: ReleaseReportSaveRequest,
    current_user: str = Depends(verify_auth_token)
):
    """Save final test report HTML as CLOB to Oracle.
    Callable from frontend 'Save Report' button.
    """
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        # Calculate retain_until date
        retain_until = None
        if request.retain_months:
            retain_until = datetime.now() + timedelta(days=request.retain_months * 30)

        result = nft_db.save_release_report(
            run_id=request.run_id,
            lob_name=request.lob_name,
            track=request.track,
            test_name=request.test_name,
            test_type=request.test_type,
            pc_run_id=request.pc_run_id,
            report_title=request.report_title,
            report_html=request.report_html,
            generated_by=request.generated_by,
            retain_until=retain_until,
            notes=request.notes
        )
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error'))
        logger.info(f"Release report saved: run_id={request.run_id} "
                    f"size={result.get('report_size_kb')}KB")
        return ReleaseReportSaveResponse(
            success=True,
            message=f"Report saved successfully. Size: {result.get('report_size_kb')}KB",
            report_id=result['report_id'],
            report_size_kb=result.get('report_size_kb')
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save release report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save report: {str(e)}")


@router.get("/release-reports")
async def list_release_reports(
    lob_name: Optional[str] = None,
    limit: int = 50,
    current_user: str = Depends(verify_auth_token)
):
    """List release reports (metadata only, no HTML content)."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        reports = nft_db.list_release_reports(lob_name=lob_name, limit=limit)
        return {"success": True, "total": len(reports), "reports": reports}
    except Exception as e:
        logger.error(f"Failed to list release reports: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list reports: {str(e)}")


@router.get("/release-reports/{report_id}/view",
            response_class=HTMLResponse)
async def view_release_report(
    report_id: int,
    current_user: str = Depends(verify_auth_token)
):
    """Return full HTML report for rendering in browser.
    Returns HTMLResponse so browser renders it directly.
    """
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        report = nft_db.get_release_report(report_id)
        if not report:
            raise HTTPException(status_code=404,
                                detail=f"Report {report_id} not found")
        if not report.get('report_html'):
            raise HTTPException(status_code=404,
                                detail=f"Report {report_id} has no HTML content")
        return HTMLResponse(content=report['report_html'])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve report {report_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve report: {str(e)}")


@router.get("/release-reports/{report_id}")
async def get_release_report_metadata(
    report_id: int,
    current_user: str = Depends(verify_auth_token)
):
    """Get report metadata without HTML content."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        report = nft_db.get_release_report(report_id)
        if not report:
            raise HTTPException(status_code=404,
                                detail=f"Report {report_id} not found")
        # Strip HTML for metadata endpoint
        report_meta = {k: v for k, v in report.items() if k != 'report_html'}
        return {"success": True, "report": report_meta}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get report metadata: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get report: {str(e)}")
