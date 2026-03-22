# =============================================================================
# FIX: save_pc_project in nft/routes.py
#
# ERROR: ORA-00001: unique constraint (NFTDB.UK_NFT_PC_LOB_TRK) violated
# CAUSE: Unique constraint is on (LOB_NAME, TRACK_NAME) — one project per track.
#        My previous code matched on (LOB_NAME, PROJECT_NAME) — wrong.
#
# REPLACE your existing save_pc_project function with this:
# =============================================================================

@nft_router.post("/config/pc/projects")
async def save_pc_project(
    request: Request,
    current_user: str = Depends(verify_auth_token),
):
    """
    Save (upsert) a PC project config.
    Unique constraint is on (LOB_NAME, TRACK_NAME) — one config per LOB+Track.
    """
    body = await request.json()
    lob_name   = body.get('lob_name')
    track_name = body.get('track_name')

    if not lob_name or not track_name:
        raise HTTPException(status_code=400, detail="lob_name and track_name are required")

    try:
        with nft_db.pool.acquire() as conn:  # adjust .pool if needed
            cursor = conn.cursor()

            # Check if record exists for this LOB+TRACK (unique key)
            cursor.execute("""
                SELECT PC_CONFIG_ID
                  FROM API_NFT_PC_CONFIG
                 WHERE LOB_NAME   = :lob_name
                   AND TRACK_NAME = :track_name
            """, {'lob_name': lob_name, 'track_name': track_name})
            existing = cursor.fetchone()

            if existing:
                # UPDATE existing record
                config_id = existing[0]
                cursor.execute("""
                    UPDATE API_NFT_PC_CONFIG SET
                        PROJECT_NAME       = :project_name,
                        DISPLAY_NAME       = :display_name,
                        PC_URL             = :pc_url,
                        PC_PORT            = :pc_port,
                        DOMAIN             = :domain,
                        USERNAME           = :username,
                        PASS_ENV_VAR       = :pass_env_var,
                        DURATION_FORMAT    = :duration_format,
                        COOKIE_FLAG        = :cookie_flag,
                        REPORT_TIMEOUT_SEC = :timeout,
                        IS_ACTIVE          = :is_active,
                        UPDATED_BY         = :updated_by,
                        UPDATED_DATE       = SYSDATE
                     WHERE PC_CONFIG_ID = :config_id
                """, {
                    'project_name':    body.get('project_name', ''),
                    'display_name':    body.get('display_name', body.get('project_name', '')),
                    'pc_url':          body.get('pc_url', ''),
                    'pc_port':         body.get('pc_port', 443),
                    'domain':          body.get('domain', 'DEFAULT'),
                    'username':        body.get('username', ''),
                    'pass_env_var':    body.get('pass_env_var', ''),
                    'duration_format': body.get('duration_format', 'HM'),
                    'cookie_flag':     body.get('cookie_flag', '-b'),
                    'timeout':         body.get('report_timeout_sec', 300),
                    'is_active':       body.get('is_active', 'Y'),
                    'updated_by':      current_user,
                    'config_id':       config_id,
                })
            else:
                # INSERT new record
                # First get the next sequence value
                # Check sequence name: SELECT SEQUENCE_NAME FROM USER_SEQUENCES WHERE SEQUENCE_NAME LIKE '%PC%';
                cursor.execute("SELECT API_NFT_PC_CONFIG_SEQ.NEXTVAL FROM DUAL")
                config_id = cursor.fetchone()[0]

                cursor.execute("""
                    INSERT INTO API_NFT_PC_CONFIG (
                        PC_CONFIG_ID, LOB_NAME, TRACK_NAME,
                        PROJECT_NAME, DISPLAY_NAME,
                        PC_URL, PC_PORT, DOMAIN,
                        USERNAME, PASS_ENV_VAR,
                        DURATION_FORMAT, COOKIE_FLAG, REPORT_TIMEOUT_SEC,
                        IS_ACTIVE, CREATED_BY, CREATED_DATE
                    ) VALUES (
                        :config_id, :lob_name, :track_name,
                        :project_name, :display_name,
                        :pc_url, :pc_port, :domain,
                        :username, :pass_env_var,
                        :duration_format, :cookie_flag, :timeout,
                        :is_active, :created_by, SYSDATE
                    )
                """, {
                    'config_id':       config_id,
                    'lob_name':        lob_name,
                    'track_name':      track_name,
                    'project_name':    body.get('project_name', ''),
                    'display_name':    body.get('display_name', body.get('project_name', '')),
                    'pc_url':          body.get('pc_url', ''),
                    'pc_port':         body.get('pc_port', 443),
                    'domain':          body.get('domain', 'DEFAULT'),
                    'username':        body.get('username', ''),
                    'pass_env_var':    body.get('pass_env_var', ''),
                    'duration_format': body.get('duration_format', 'HM'),
                    'cookie_flag':     body.get('cookie_flag', '-b'),
                    'timeout':         body.get('report_timeout_sec', 300),
                    'is_active':       body.get('is_active', 'Y'),
                    'created_by':      body.get('created_by', current_user),
                })

            conn.commit()
            logger.info(f"PC project saved: {lob_name}/{track_name} config_id={config_id}")
            return {
                "success":      True,
                "pc_config_id": config_id,
                "lob_name":     lob_name,
                "track_name":   track_name,
                "message":      f"PC config for {lob_name}/{track_name} saved"
            }

    except Exception as e:
        logger.error(f"Save PC project error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# NOTE ON nft_db.pool:
# If you get 'NFTPlatformDatabase has no attribute pool', check your class:
#   grep "self\." app/monitoring/nft/database.py | head -10
# Then replace nft_db.pool with the correct attribute name.
#
# Your existing working GET endpoint at line 1270 uses the same pattern —
# copy exactly what it uses for the connection.
# =============================================================================
