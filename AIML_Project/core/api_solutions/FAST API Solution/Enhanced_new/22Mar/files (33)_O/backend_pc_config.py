# =============================================================================
# ACTUAL API_NFT_PC_CONFIG SCHEMA:
# PC_CONFIG_ID, LOB_NAME, TRACK_NAME, PC_URL, DOMAIN, PROJECT_NAME,
# USERNAME, PASS_ENV_VAR, DURATION_FORMAT, COOKIE_FLAG, REPORT_TIMEOUT_SEC,
# LAST_RUN_ID, IS_ACTIVE, LAST_TEST_STATUS, LAST_TEST_DATE,
# CREATED_BY, CREATED_DATE, UPDATED_BY, UPDATED_DATE, DISPLAY_NAME, PC_PORT
# =============================================================================

# ── GET /nft/config/pc/projects ───────────────────────────────────────────────
@nft_router.get("/config/pc/projects")
async def get_pc_projects(
    lob_name: str = Query(None),
    track:    str = Query(None),    # maps to TRACK_NAME
    current_user: str = Depends(verify_auth_token),
):
    """Get PC project configurations filtered by LOB and optional Track."""
    try:
        with oracle_pool.acquire() as conn:
            cursor = conn.cursor()
            sql = """
                SELECT PC_CONFIG_ID, LOB_NAME, TRACK_NAME,
                       PC_URL, PC_PORT, DOMAIN, PROJECT_NAME,
                       USERNAME, PASS_ENV_VAR,
                       DURATION_FORMAT, COOKIE_FLAG, REPORT_TIMEOUT_SEC,
                       LAST_RUN_ID, LAST_TEST_STATUS, LAST_TEST_DATE,
                       DISPLAY_NAME, IS_ACTIVE,
                       CREATED_BY, CREATED_DATE, UPDATED_DATE
                  FROM API_NFT_PC_CONFIG
                 WHERE IS_ACTIVE = 'Y'
            """
            params = {}
            if lob_name:
                sql += " AND LOB_NAME = :lob_name"
                params['lob_name'] = lob_name
            if track:
                sql += " AND TRACK_NAME = :track"
                params['track'] = track
            sql += " ORDER BY TRACK_NAME, PROJECT_NAME"
            cursor.execute(sql, params)

            projects = []
            for row in cursor.fetchall():
                projects.append({
                    'pc_config_id':       row[0],
                    'lob_name':           row[1],
                    'track_name':         row[2],
                    'pc_url':             row[3],
                    'pc_port':            row[4],
                    'domain':             row[5],
                    'project_name':       row[6],
                    'username':           row[7],
                    'pass_env_var':       row[8],
                    'duration_format':    row[9],
                    'cookie_flag':        row[10],
                    'report_timeout_sec': row[11],
                    'last_run_id':        row[12],
                    'last_test_status':   row[13],
                    'last_test_date':     row[14].isoformat() if row[14] else None,
                    'display_name':       row[15],
                    'is_active':          row[16],
                    'created_by':         row[17],
                    'created_date':       row[18].isoformat() if row[18] else None,
                    'updated_date':       row[19].isoformat() if row[19] else None,
                })
            return {"projects": projects, "total": len(projects)}
    except Exception as e:
        logger.error(f"Get PC projects error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── POST /nft/config/pc/projects ─────────────────────────────────────────────
@nft_router.post("/config/pc/projects")
async def save_pc_project(
    request: Request,
    current_user: str = Depends(verify_auth_token),
):
    """Save (upsert) a PC project. Matches on LOB_NAME + PROJECT_NAME."""
    body = await request.json()
    lob_name     = body.get('lob_name')
    project_name = body.get('project_name')
    if not lob_name or not project_name:
        raise HTTPException(status_code=400, detail="lob_name and project_name are required")

    try:
        with oracle_pool.acquire() as conn:
            cursor = conn.cursor()
            # Check if exists
            cursor.execute("""
                SELECT PC_CONFIG_ID FROM API_NFT_PC_CONFIG
                 WHERE LOB_NAME = :lob AND PROJECT_NAME = :proj
            """, {'lob': lob_name, 'proj': project_name})
            existing = cursor.fetchone()

            if existing:
                # UPDATE
                cursor.execute("""
                    UPDATE API_NFT_PC_CONFIG SET
                        TRACK_NAME         = :track_name,
                        PC_URL             = :pc_url,
                        PC_PORT            = :pc_port,
                        DOMAIN             = :domain,
                        USERNAME           = :username,
                        PASS_ENV_VAR       = :pass_env_var,
                        DURATION_FORMAT    = :duration_format,
                        COOKIE_FLAG        = :cookie_flag,
                        REPORT_TIMEOUT_SEC = :timeout,
                        DISPLAY_NAME       = :display_name,
                        IS_ACTIVE          = :is_active,
                        UPDATED_BY         = :updated_by,
                        UPDATED_DATE       = SYSDATE
                     WHERE LOB_NAME = :lob_name AND PROJECT_NAME = :project_name
                """, {
                    'track_name':      body.get('track_name', ''),
                    'pc_url':          body.get('pc_url', ''),
                    'pc_port':         body.get('pc_port', 443),
                    'domain':          body.get('domain', 'DEFAULT'),
                    'username':        body.get('username', ''),
                    'pass_env_var':    body.get('pass_env_var', ''),
                    'duration_format': body.get('duration_format', 'HM'),
                    'cookie_flag':     body.get('cookie_flag', '-b'),
                    'timeout':         body.get('report_timeout_sec', 300),
                    'display_name':    body.get('display_name', project_name),
                    'is_active':       body.get('is_active', 'Y'),
                    'updated_by':      current_user,
                    'lob_name':        lob_name,
                    'project_name':    project_name,
                })
                config_id = existing[0]
            else:
                # INSERT — get next sequence value
                cursor.execute("SELECT API_NFT_PC_CONFIG_SEQ.NEXTVAL FROM DUAL")
                config_id = cursor.fetchone()[0]
                cursor.execute("""
                    INSERT INTO API_NFT_PC_CONFIG (
                        PC_CONFIG_ID, LOB_NAME, TRACK_NAME,
                        PC_URL, PC_PORT, DOMAIN,
                        PROJECT_NAME, USERNAME, PASS_ENV_VAR,
                        DURATION_FORMAT, COOKIE_FLAG, REPORT_TIMEOUT_SEC,
                        DISPLAY_NAME, IS_ACTIVE,
                        CREATED_BY, CREATED_DATE
                    ) VALUES (
                        :config_id, :lob_name, :track_name,
                        :pc_url, :pc_port, :domain,
                        :project_name, :username, :pass_env_var,
                        :duration_format, :cookie_flag, :timeout,
                        :display_name, :is_active,
                        :created_by, SYSDATE
                    )
                """, {
                    'config_id':       config_id,
                    'lob_name':        lob_name,
                    'track_name':      body.get('track_name', ''),
                    'pc_url':          body.get('pc_url', ''),
                    'pc_port':         body.get('pc_port', 443),
                    'domain':          body.get('domain', 'DEFAULT'),
                    'project_name':    project_name,
                    'username':        body.get('username', ''),
                    'pass_env_var':    body.get('pass_env_var', ''),
                    'duration_format': body.get('duration_format', 'HM'),
                    'cookie_flag':     body.get('cookie_flag', '-b'),
                    'timeout':         body.get('report_timeout_sec', 300),
                    'display_name':    body.get('display_name', project_name),
                    'is_active':       body.get('is_active', 'Y'),
                    'created_by':      body.get('created_by', current_user),
                })

            conn.commit()
            return {
                "success":      True,
                "pc_config_id": config_id,
                "project_name": project_name,
                "message":      f"Project '{project_name}' saved"
            }
    except Exception as e:
        logger.error(f"Save PC project error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── DELETE /nft/config/pc/projects/{config_id} ────────────────────────────────
@nft_router.delete("/config/pc/projects/{config_id}")
async def delete_pc_project(
    config_id: int,
    current_user: str = Depends(verify_auth_token),
):
    """Soft-delete a PC project by PC_CONFIG_ID."""
    try:
        with oracle_pool.acquire() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE API_NFT_PC_CONFIG
                   SET IS_ACTIVE   = 'N',
                       UPDATED_BY  = :user,
                       UPDATED_DATE = SYSDATE
                 WHERE PC_CONFIG_ID = :config_id
            """, {'config_id': config_id, 'user': current_user})
            updated = cursor.rowcount
            conn.commit()
            if not updated:
                raise HTTPException(status_code=404, detail=f"Project ID {config_id} not found")
            return {"success": True, "message": f"Project {config_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── UPDATE LAST_RUN_ID / LAST_TEST_STATUS (called internally after fetch-results)
# Add this call inside your fetch_pc_results endpoint after storing results:
#
# UPDATE API_NFT_PC_CONFIG
#    SET LAST_RUN_ID      = :run_id,
#        LAST_TEST_STATUS = :status,
#        LAST_TEST_DATE   = SYSDATE,
#        UPDATED_DATE     = SYSDATE
#  WHERE LOB_NAME = :lob_name
#    AND PROJECT_NAME = :project_name
#    AND IS_ACTIVE = 'Y'
#
# =============================================================================
# NOTE ON SEQUENCE NAME:
# Check your actual sequence name with:
#   SELECT SEQUENCE_NAME FROM USER_SEQUENCES WHERE SEQUENCE_NAME LIKE '%PC_CONFIG%';
# Common names: API_NFT_PC_CONFIG_SEQ, PC_CONFIG_SEQ, SEQ_PC_CONFIG
# Replace API_NFT_PC_CONFIG_SEQ.NEXTVAL above with the correct name.
# =============================================================================
