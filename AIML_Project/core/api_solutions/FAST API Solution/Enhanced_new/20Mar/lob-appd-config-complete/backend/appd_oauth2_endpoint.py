"""
ADD TO: monitoring/appd/routes.py
-----------------------------------
OAuth2 test-connection endpoint for AppDynamics.
Also adds the applications save endpoint.
"""

# ── POST /appd/test-connection ────────────────────────────────────────────────
@router.post("/test-connection")
async def test_appd_connection(
    request: Request,
    current_user: str = Depends(verify_auth_token)
):
    """
    Test AppDynamics controller connection.
    Supports oauth (client_id+secret), basic, token auth.
    Credentials always via env vars — never stored in DB.
    """
    body = await request.json()
    controller_url = body.get('controller_url', '').rstrip('/')
    account_name   = body.get('account_name', '')
    auth_type      = body.get('auth_type', 'oauth')

    if not controller_url or not account_name:
        raise HTTPException(status_code=400,
            detail="controller_url and account_name are required")

    import os, requests as req_lib
    from requests.auth import HTTPBasicAuth

    try:
        session = req_lib.Session()
        session.verify = False  # Corp certs

        if auth_type == 'oauth':
            client_id_env     = body.get('client_id_env_var', '')
            client_secret_env = body.get('client_secret_env_var', '')
            client_id     = os.environ.get(client_id_env, '')
            client_secret = os.environ.get(client_secret_env, '')
            if not client_id or not client_secret:
                raise HTTPException(status_code=400,
                    detail=f"Env vars '{client_id_env}' or '{client_secret_env}' not set on server")

            # OAuth2 token request
            token_url = f"{controller_url}/controller/api/oauth/access_token"
            token_resp = session.post(token_url, data={
                'grant_type':    'client_credentials',
                'client_id':     f"{client_id}@{account_name}",
                'client_secret': client_secret,
            }, timeout=15)

            if token_resp.status_code != 200:
                return {"success": False, "status": "FAIL",
                        "message": f"OAuth2 token request failed: HTTP {token_resp.status_code}. "
                                   f"Check client ID/secret env vars."}
            token = token_resp.json().get('access_token', '')
            session.headers.update({'Authorization': f'Bearer {token}'})

        elif auth_type == 'basic':
            username  = body.get('username', '')
            pass_env  = body.get('pass_env_var', '')
            password  = os.environ.get(pass_env, '')
            if not password:
                raise HTTPException(status_code=400,
                    detail=f"Env var '{pass_env}' not set on server")
            user_at = f"{username}@{account_name}"
            session.auth = HTTPBasicAuth(user_at, password)

        else:  # token
            token_env = body.get('token_env_var', '')
            token     = os.environ.get(token_env, '')
            if not token:
                raise HTTPException(status_code=400,
                    detail=f"Env var '{token_env}' not set on server")
            session.headers.update({'Authorization': f'Bearer {token}'})

        # Test by calling /controller/rest/applications
        test_url = f"{controller_url}/controller/rest/applications?output=JSON"
        resp = session.get(test_url, timeout=15)

        if resp.status_code == 200:
            apps = resp.json() if resp.content else []
            return {
                "success": True,
                "status":  "ok",
                "message": f"Connected to AppDynamics controller. "
                           f"Found {len(apps)} accessible application(s).",
                "accessible_apps": len(apps),
                "controller_url":  controller_url,
                "account_name":    account_name,
            }
        elif resp.status_code == 401:
            return {"success": False, "status": "FAIL",
                    "message": "Authentication failed (401). Check credentials."}
        else:
            return {"success": False, "status": "FAIL",
                    "message": f"Controller returned HTTP {resp.status_code}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AppD test-connection error: {e}", exc_info=True)
        return {"success": False, "status": "FAIL", "message": str(e)}


# ── POST /appd/applications ───────────────────────────────────────────────────
@router.post("/applications")
async def save_appd_application(
    request: Request,
    current_user: str = Depends(verify_auth_token)
):
    """
    Save an AppDynamics application to APPD_APPLICATIONS_MASTER.
    Used by AppD Config admin page when admin adds applications.
    """
    if not appd_db:
        raise HTTPException(status_code=503, detail="AppDynamics service not initialized")
    try:
        body = await request.json()
        lob_name  = body.get('lob_name', '')
        track     = body.get('track', '')
        app_name  = body.get('application_name', '').strip()
        app_id    = body.get('application_id', '').strip()
        freq      = body.get('discovery_frequency', 'daily')
        is_active = body.get('is_active', 'Y')

        if not app_name or not app_id:
            raise HTTPException(status_code=400,
                detail="application_name and application_id are required")

        # Upsert into APPD_APPLICATIONS_MASTER
        with appd_db.connection_pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    MERGE INTO APPD_APPLICATIONS_MASTER t
                    USING (SELECT :app_name AS an FROM DUAL) s
                    ON (t.APPLICATION_NAME = s.an)
                    WHEN MATCHED THEN
                        UPDATE SET LOB_NAME             = :lob_name,
                                   TRACK                = :track,
                                   APPLICATION_ID_APPD  = :app_id,
                                   DISCOVERY_FREQUENCY  = :freq,
                                   IS_ACTIVE            = :is_active,
                                   UPDATED_DATE         = SYSDATE
                    WHEN NOT MATCHED THEN
                        INSERT (APPLICATION_NAME, LOB_NAME, TRACK,
                                APPLICATION_ID_APPD, DISCOVERY_FREQUENCY,
                                IS_ACTIVE, CREATED_DATE)
                        VALUES (:app_name, :lob_name, :track,
                                :app_id, :freq, :is_active, SYSDATE)
                """, {
                    'app_name':  app_name,
                    'lob_name':  lob_name,
                    'track':     track,
                    'app_id':    app_id,
                    'freq':      freq,
                    'is_active': is_active,
                })
                conn.commit()
                return {"success": True, "application_name": app_name,
                        "message": f"Application '{app_name}' saved"}
            except Exception as e:
                conn.rollback()
                raise HTTPException(status_code=500, detail=str(e))
            finally:
                cursor.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Save application error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── DELETE /appd/config/{config_name} ────────────────────────────────────────
@router.delete("/config/{config_name}")
async def delete_appd_config(
    config_name: str,
    current_user: str = Depends(verify_auth_token)
):
    """Deactivate (soft delete) an AppD discovery config."""
    if not appd_db:
        raise HTTPException(status_code=503, detail="AppDynamics service not initialized")
    try:
        appd_db.deactivate_config(config_name)
        return {"success": True, "config_name": config_name,
                "message": f"Config '{config_name}' deactivated"}
    except Exception as e:
        logger.error(f"Delete config error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
