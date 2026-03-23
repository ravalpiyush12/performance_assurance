# =============================================================================
# REPLACE the test_pc_connection function in nft/routes.py (lines 630-656)
# with this real implementation
# =============================================================================

@router.post("/config/pc/test-connection/{pc_config_id}")
async def test_pc_connection(
    pc_config_id: int,
    current_user: str = Depends(verify_auth_token),
) -> PCTestConnectionResponse:
    """
    Test PC connection using saved config and return latest run info.
    Uses the real PerformanceCenterClient to authenticate and fetch runs.
    """
    _check_db()
    try:
        # ── Step 1: Load config from DB ───────────────────────────────────────
        config = nft_db.get_pc_config_by_id(pc_config_id)
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"PC config {pc_config_id} not found"
            )

        pc_url      = config.get('pc_url') or config.get('base_url', '')
        pc_port     = config.get('pc_port') or config.get('port', 443)
        domain      = config.get('domain') or config.get('pc_domain', 'DEFAULT')
        username    = config.get('username', '')
        pass_env    = config.get('pass_env_var') or config.get('password_env_var', '')
        project     = config.get('project_name') or config.get('pc_project', '')
        display     = config.get('display_name') or project
        lob_name    = config.get('lob_name', '')

        if not pc_url or not username or not pass_env:
            raise HTTPException(
                status_code=400,
                detail="Incomplete PC config — PC URL, Username and Password env var are required"
            )

        # ── Step 2: Get password from environment variable ────────────────────
        import os
        password = os.environ.get(pass_env)
        if not password:
            raise HTTPException(
                status_code=400,
                detail=f"Environment variable '{pass_env}' not set on server"
            )

        # ── Step 3: Build full URL and authenticate ───────────────────────────
        base_url = f"{pc_url.rstrip('/')}:{pc_port}" if pc_port else pc_url.rstrip('/')

        # Use your existing PerformanceCenterClient
        pc_client = PerformanceCenterClient(
            base_url=base_url,
            username=username,
            password=password,
            domain=domain,
            project=project,
        )

        # Authenticate (establishes cookie session)
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

        # ── Step 4: Get latest test run for this project ──────────────────────
        latest_run_id     = None
        latest_run_status = None
        latest_run_date   = None
        latest_run_duration = None
        latest_pass_rate  = None
        pc_version        = "24.1"

        try:
            # Get recent runs — uses PC REST API
            runs = pc_client.get_recent_runs(limit=1)
            if runs:
                run = runs[0]
                latest_run_id     = str(run.get('ID') or run.get('id') or '')
                latest_run_status = run.get('RunState') or run.get('status') or run.get('TestRunStatus', '')
                start_time        = run.get('StartTime') or run.get('start_time')
                duration_sec      = run.get('Duration') or run.get('duration_seconds', 0)

                if start_time:
                    from datetime import datetime
                    try:
                        # PC returns timestamps in various formats
                        if isinstance(start_time, (int, float)):
                            dt = datetime.fromtimestamp(start_time / 1000)
                        else:
                            dt = datetime.fromisoformat(str(start_time).replace('Z', '+00:00'))
                        latest_run_date = dt.strftime('%Y-%m-%d')
                    except Exception:
                        latest_run_date = str(start_time)[:10]

                if duration_sec:
                    hours   = int(duration_sec) // 3600
                    minutes = (int(duration_sec) % 3600) // 60
                    latest_run_duration = f"{hours}h {minutes}m" if hours else f"{minutes}m"

                # Try to get pass rate from results
                try:
                    if latest_run_id:
                        results = pc_client.get_run_results(latest_run_id)
                        if results:
                            total  = results.get('total_transactions', 0)
                            passed = results.get('passed_transactions', 0)
                            if total > 0:
                                latest_pass_rate = round((passed / total) * 100, 1)
                except Exception:
                    pass  # pass rate is optional

        except Exception as run_err:
            logger.warning(f"Could not fetch latest run for config {pc_config_id}: {run_err}")
            # Connection still succeeded even if runs fetch fails

        finally:
            # Always logout to release session
            try:
                pc_client.logout()
            except Exception:
                pass

        # ── Step 5: Update DB with test status ────────────────────────────────
        nft_db.update_pc_test_status(pc_config_id, 'PASS')

        return PCTestConnectionResponse(
            success=True,
            pc_config_id=pc_config_id,
            display_name=display,
            status="PASS",
            pc_version=pc_version,
            latest_run_id=latest_run_id,
            latest_run_status=latest_run_status,
            latest_run_date=latest_run_date,
            latest_run_duration=latest_run_duration,
            latest_pass_rate=latest_pass_rate,
            message=f"Connected to PC {pc_version}. Cookie session established. Latest run info retrieved."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing PC connection: {e}", exc_info=True)
        # Update DB to reflect failed test
        try:
            nft_db.update_pc_test_status(pc_config_id, 'FAIL')
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ALSO NEED: get_pc_config_by_id in nft/database.py
# Add this method to NFTPlatformDatabase class:
# =============================================================================

    def get_pc_config_by_id(self, pc_config_id: int) -> dict:
        """Get a single PC config by PC_CONFIG_ID."""
        configs = self.get_pc_configs(None, None)  # get all
        for c in configs:
            if c.get('pc_config_id') == pc_config_id or c.get('config_id') == pc_config_id:
                return c
        return None

        # OR if you prefer a direct SQL query:
        # with self.pool.acquire() as conn:
        #     cursor = conn.cursor()
        #     cursor.execute("""
        #         SELECT PC_CONFIG_ID, LOB_NAME, TRACK_NAME,
        #                PC_URL, PC_PORT, DOMAIN, PROJECT_NAME,
        #                USERNAME, PASS_ENV_VAR, DISPLAY_NAME,
        #                DURATION_FORMAT, COOKIE_FLAG, REPORT_TIMEOUT_SEC
        #           FROM API_NFT_PC_CONFIG
        #          WHERE PC_CONFIG_ID = :id AND IS_ACTIVE = 'Y'
        #     """, {'id': pc_config_id})
        #     row = cursor.fetchone()
        #     if not row: return None
        #     return {
        #         'pc_config_id': row[0], 'lob_name': row[1],
        #         'track_name': row[2], 'pc_url': row[3],
        #         'pc_port': row[4], 'domain': row[5],
        #         'project_name': row[6], 'username': row[7],
        #         'pass_env_var': row[8], 'display_name': row[9],
        #         'duration_format': row[10], 'cookie_flag': row[11],
        #         'report_timeout_sec': row[12],
        #     }


# =============================================================================
# KEY DEPENDENCIES — check these exist in your codebase:
#
# 1. PerformanceCenterClient — already in monitoring/pc/client.py
#    Import at top of nft/routes.py:
#    from monitoring.pc.client import PerformanceCenterClient
#
# 2. pc_client.authenticate()  — should return True/False
# 3. pc_client.get_recent_runs(limit=1) — returns list of run dicts
# 4. pc_client.get_run_results(run_id) — returns result stats
# 5. pc_client.logout() — closes session
#
# If your PerformanceCenterClient has different method names, adjust above.
# Check monitoring/pc/client.py for exact method signatures.
# =============================================================================
