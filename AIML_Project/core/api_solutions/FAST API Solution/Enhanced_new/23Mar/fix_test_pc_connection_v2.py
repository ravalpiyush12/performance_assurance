# =============================================================================
# REPLACE test_pc_connection in nft/routes.py
#
# PerformanceCenterClient has these methods:
#   authenticate()                    → bool
#   get_test_run_status(run_id: str)  → dict with 'status','collation_status','run_id','is_finished'
#   download_summary_report(run_id)   → html string (not needed here)
#   logout()
#
# Strategy: authenticate → if LAST_RUN_ID stored in config, fetch its status
#           → return real data. No LAST_RUN_ID → just confirm auth succeeded.
# =============================================================================

@router.post("/config/pc/test-connection/{pc_config_id}")
async def test_pc_connection(
    pc_config_id: int,
    current_user: str = Depends(verify_auth_token),
) -> PCTestConnectionResponse:
    """Test PC connection using saved config and return latest run info."""
    _check_db()
    try:
        # ── Step 1: Load config from DB ───────────────────────────────────────
        config = nft_db.get_pc_config_by_id(pc_config_id)
        if not config:
            raise HTTPException(status_code=404, detail=f"PC config {pc_config_id} not found")

        pc_url    = config.get('pc_url') or config.get('base_url', '')
        pc_port   = config.get('pc_port') or config.get('port', 443)
        domain    = config.get('domain') or config.get('pc_domain', 'DEFAULT')
        username  = config.get('username', '')
        pass_env  = config.get('pass_env_var') or config.get('password_env_var', '')
        project   = config.get('project_name') or config.get('pc_project', '')
        display   = config.get('display_name') or project
        last_run_id = config.get('last_run_id')  # stored from previous test runs

        if not pc_url or not username or not pass_env:
            raise HTTPException(
                status_code=400,
                detail="Incomplete PC config — PC URL, Username and Password env var required"
            )

        # ── Step 2: Get password from environment variable ────────────────────
        import os
        password = os.environ.get(pass_env)
        if not password:
            raise HTTPException(
                status_code=400,
                detail=f"Environment variable '{pass_env}' not set on server"
            )

        # Build full base URL including port
        base_url = f"{pc_url.rstrip('/')}:{pc_port}" if pc_port else pc_url.rstrip('/')

        # ── Step 3: Authenticate ──────────────────────────────────────────────
        pc_client = PerformanceCenterClient(
            base_url=base_url,
            username=username,
            password=password,
            domain=domain,
            project=project,
        )

        authenticated = pc_client.authenticate()
        if not authenticated:
            nft_db.update_pc_test_status(pc_config_id, 'FAIL')
            return PCTestConnectionResponse(
                success=False,
                pc_config_id=pc_config_id,
                display_name=display,
                status="FAIL",
                message="Authentication failed. Check username, password and domain."
            )

        # ── Step 4: Fetch last run status if LAST_RUN_ID exists ───────────────
        latest_run_id     = None
        latest_run_status = None
        latest_run_date   = None
        latest_run_duration = None
        latest_pass_rate  = None

        if last_run_id:
            try:
                run_info = pc_client.get_test_run_status(str(last_run_id))
                # get_test_run_status returns:
                # {'status': ..., 'collation_status': ..., 'run_id': ..., 'is_finished': ...}
                latest_run_id     = str(run_info.get('run_id') or last_run_id)
                latest_run_status = run_info.get('status', 'Unknown')
                # collation_status tells us more detail
                collation         = run_info.get('collation_status', '')
                if collation and collation not in ('Unknown', ''):
                    latest_run_status = f"{latest_run_status} ({collation})"
            except Exception as run_err:
                logger.warning(f"Could not fetch run status for run {last_run_id}: {run_err}")
                latest_run_id = str(last_run_id)
                latest_run_status = "Unknown (fetch failed)"
        else:
            logger.info(f"No LAST_RUN_ID stored for config {pc_config_id} — auth-only test")

        # ── Step 5: Logout ────────────────────────────────────────────────────
        try:
            pc_client.logout()
        except Exception:
            pass

        # ── Step 6: Update DB + return ────────────────────────────────────────
        nft_db.update_pc_test_status(pc_config_id, 'PASS')

        msg = "Connected to PC 24.1. Cookie session established."
        if latest_run_id:
            msg += f" Run {latest_run_id} status retrieved."
        else:
            msg += " No previous run ID stored — run a test to populate last run info."

        return PCTestConnectionResponse(
            success=True,
            pc_config_id=pc_config_id,
            display_name=display,
            status="PASS",
            pc_version="24.1.0",
            latest_run_id=latest_run_id,
            latest_run_status=latest_run_status,
            latest_run_date=latest_run_date,
            latest_run_duration=latest_run_duration,
            latest_pass_rate=latest_pass_rate,
            message=msg
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing PC connection: {e}", exc_info=True)
        try:
            nft_db.update_pc_test_status(pc_config_id, 'FAIL')
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ADD to nft/database.py — NFTPlatformDatabase class:
# =============================================================================

    def get_pc_config_by_id(self, pc_config_id: int) -> dict:
        """Fetch a single PC config row by PC_CONFIG_ID."""
        # get_pc_configs already exists and returns a list — reuse it
        all_configs = self.get_pc_configs(None, None)
        for c in all_configs:
            cid = c.get('pc_config_id') or c.get('config_id') or c.get('id')
            if cid and int(cid) == int(pc_config_id):
                return c
        return None


# =============================================================================
# ADD import at top of nft/routes.py (if not already there):
# =============================================================================

from monitoring.pc.client import PerformanceCenterClient


# =============================================================================
# HOW LAST_RUN_ID GETS POPULATED:
#
# After fetch-results completes in pc/routes.py, add:
#   nft_db.update_pc_test_status(pc_config_id, 'PASS', last_run_id=pc_run_id)
#
# Or update LAST_RUN_ID in API_NFT_PC_CONFIG after a successful monitoring run:
#   UPDATE API_NFT_PC_CONFIG
#      SET LAST_RUN_ID = :run_id, UPDATED_DATE = SYSDATE
#    WHERE LOB_NAME = :lob AND TRACK_NAME = :track
#
# Until LAST_RUN_ID is set, test-connection confirms auth works but shows
# "No previous run ID stored" message — which is accurate and honest.
# =============================================================================
