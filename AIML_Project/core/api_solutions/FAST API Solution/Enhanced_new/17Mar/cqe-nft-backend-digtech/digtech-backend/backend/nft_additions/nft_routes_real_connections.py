"""
NFT ROUTES ADDITIONS — Real test-connection implementations
===========================================================
Replace the simulation blocks in your existing nft/routes.py with these.

Find each endpoint by its decorator and replace the entire function body.
"""

# ─── REPLACE: POST /config/kibana/test-connection ─────────────────────────────
# Find: async def test_kibana_connection(...)
# Replace the entire function body with:

async def test_kibana_connection_REAL(kibana_config_id: int,
                                      current_user, nft_db):
    """Real Kibana test — uses KibanaMonitoringClient via fetcher."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="NFT database not initialized")
    try:
        config = nft_db.get_kibana_config_by_id(kibana_config_id)
        if not config:
            raise HTTPException(status_code=404,
                detail=f"Kibana config ID {kibana_config_id} not found")

        from monitoring.kibana.client import KibanaMonitoringClient
        client = KibanaMonitoringClient(
            kibana_url=config['kibana_url'],
            username=config.get('username'),
            token_env_var=config['token_env_var'],
            auth_type=config.get('auth_type', 'apikey'),
        )
        result = client.test_connection()

        # If connection ok, test actual data on the dashboard
        if result.get('success'):
            data_result = client.collect_dashboard_metrics(
                dashboard_id=config['dashboard_id'],
                time_range_minutes=5,
            )
            return {
                'success': data_result.get('success'),
                'status':  data_result.get('status'),
                'message': data_result.get('message'),
                'record_count': data_result.get('record_count', 0),
                'error_rate':   data_result.get('error_rate', 0),
                'p95_ms':       data_result.get('p95_ms', 0),
                'last_data_point': data_result.get('last_data_point'),
                'contact_app_team': data_result.get('contact_app_team', False),
            }
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Kibana test-connection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


# ─── REPLACE: POST /config/pc/test-connection/{pc_config_id} ──────────────────
# Replace the simulation with:

async def test_pc_connection_REAL(pc_config_id: int, current_user, nft_db):
    """Real PC test — uses PerformanceCenterClient from pc/client.py."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="NFT database not initialized")
    try:
        config = nft_db.get_pc_config_by_id(pc_config_id)
        if not config:
            raise HTTPException(status_code=404,
                detail=f"PC config ID {pc_config_id} not found")

        import os
        password = os.environ.get(config['pass_env_var'])
        if not password:
            raise HTTPException(
                status_code=400,
                detail=f"Environment variable '{config['pass_env_var']}' is not set"
            )

        from monitoring.pc.client import PerformanceCenterClient
        base_url = config['pc_url'].rstrip('/')
        if config.get('pc_port') and str(config['pc_port']) not in base_url:
            base_url = f"{base_url}:{config['pc_port']}"

        try:
            with PerformanceCenterClient(
                base_url=base_url,
                username=config['username'],
                password=password,
                domain=config.get('domain', 'DEFAULT'),
                project=config['project_name'],
            ) as pc:
                authenticated = pc.authenticate()
                if not authenticated:
                    return {
                        'success': False, 'status': 'FAIL',
                        'message': 'PC authentication failed. Check credentials.',
                        'contact_app_team': False,
                    }

                # Fetch latest run status for this project
                # Use last_run_id if available, otherwise return connection-only success
                last_run_id = config.get('last_run_id')
                latest_run_info = {}

                if last_run_id:
                    try:
                        run_status = pc.get_test_run_status(str(last_run_id))
                        latest_run_info = {
                            'latest_run_id':     last_run_id,
                            'latest_run_status': run_status.get('status', 'Unknown'),
                            'latest_run_duration': run_status.get('duration', '—'),
                            'latest_run_date':   run_status.get('start_time', '—'),
                            'latest_pass_rate':  run_status.get('pass_rate', '—'),
                            'collation_status':  run_status.get('collation_status', '—'),
                        }
                    except Exception:
                        latest_run_info = {
                            'latest_run_id': last_run_id,
                            'latest_run_status': 'Unknown',
                        }

                return {
                    'success': True, 'status': 'PASS',
                    'message': f"Connected to PC at {base_url}. Project '{config['project_name']}' accessible.",
                    'pc_version': '24.1',
                    **latest_run_info,
                }

        except Exception as pc_err:
            return {
                'success': False, 'status': 'FAIL',
                'message': f"PC connection error: {str(pc_err)}",
                'contact_app_team': False,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PC test-connection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


# ─── REPLACE: POST /config/db/test-connection/{db_config_id} ──────────────────
# Replace the simulation with:

async def test_oracle_connection_REAL(db_config_id: int, current_user, nft_db):
    """Real Oracle DB test — SELECT SYSDATE FROM DUAL."""
    if not nft_db:
        raise HTTPException(status_code=503, detail="NFT database not initialized")
    try:
        config = nft_db.get_db_config_by_id(db_config_id)
        if not config:
            raise HTTPException(status_code=404,
                detail=f"DB config ID {db_config_id} not found")

        import os, oracledb
        password = os.environ.get(config['pass_env_var'])
        if not password:
            raise HTTPException(
                status_code=400,
                detail=f"Environment variable '{config['pass_env_var']}' is not set"
            )

        dsn = f"{config['host']}:{config.get('port', 1521)}/{config['service_name']}"
        try:
            conn = oracledb.connect(
                user=config['username'],
                password=password,
                dsn=dsn,
            )
            cursor = conn.cursor()
            cursor.execute("SELECT SYSDATE, USER FROM DUAL")
            row = cursor.fetchone()
            server_time = row[0].isoformat() if row and row[0] else None
            connected_as = row[1] if row else config['username']
            cursor.close()
            conn.close()
            return {
                'success': True, 'status': 'PASS',
                'message': f"Connected to Oracle DB. DSN: {dsn}",
                'server_time': server_time,
                'connected_as': connected_as,
                'dsn': dsn,
                'contact_app_team': False,
            }
        except oracledb.Error as db_err:
            return {
                'success': False, 'status': 'FAIL',
                'message': f"Oracle connection error: {str(db_err)}",
                'dsn': dsn,
                'contact_app_team': False,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Oracle test-connection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


# ─── ALSO ADD: get_kibana_config_by_id, get_pc_config_by_id, get_db_config_by_id
# to monitoring/nft/database.py (see nft_database_additions.py)
