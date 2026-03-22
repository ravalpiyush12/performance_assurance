# =============================================================================
# ACTUAL TABLE: API_NFT_TRACK_TEMPLATE
# Stores CONFIG IDs (comma-separated) not application names
#
# TEMPLATE_ID    NUMBER        PK
# LOB_NAME       VARCHAR2(100) NOT NULL
# TRACK          VARCHAR2(50)  NOT NULL
# APPD_CONFIG_IDS VARCHAR2(500) -- e.g. "1,2,3"  (AppD LOB config IDs)
# KIBANA_CONFIG_IDS VARCHAR2(500)
# SPLUNK_CONFIG_IDS VARCHAR2(500)
# MONGODB_CONFIG_IDS VARCHAR2(500)
# PC_CONFIG_IDS  VARCHAR2(500) -- PC project config IDs
# DB_CONFIG_IDS  VARCHAR2(500) -- Oracle DB config IDs (for AWR)
# APPD_COUNT     NUMBER
# KIBANA_COUNT   NUMBER
# SPLUNK_COUNT   NUMBER
# MONGODB_COUNT  NUMBER
# PC_COUNT       NUMBER
# DB_COUNT       NUMBER
# IS_ACTIVE      CHAR(1)
# CREATED_BY     VARCHAR2(100)
# CREATED_DATE   DATE
# UPDATED_BY     VARCHAR2(100)
# UPDATED_DATE   DATE
# =============================================================================


# ── GET /nft/track-template ───────────────────────────────────────────────────
@nft_router.get("/track-template")
async def get_track_template(
    lob_name: str = Query(...),
    track:    str = Query(...),
    current_user: str = Depends(verify_auth_token),
):
    """
    Get track template for a LOB+Track.
    Returns config IDs AND resolves them to names for display.
    """
    try:
        with oracle_pool.acquire() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TEMPLATE_ID,
                       APPD_CONFIG_IDS, PC_CONFIG_IDS, DB_CONFIG_IDS,
                       APPD_COUNT, PC_COUNT, DB_COUNT,
                       CREATED_BY, CREATED_DATE, UPDATED_DATE
                  FROM API_NFT_TRACK_TEMPLATE
                 WHERE LOB_NAME = :lob_name
                   AND TRACK    = :track
                   AND IS_ACTIVE = 'Y'
            """, {'lob_name': lob_name, 'track': track})
            row = cursor.fetchone()
            if not row:
                return {"template": None}

            template_id     = row[0]
            appd_config_ids = [x.strip() for x in (row[1] or '').split(',') if x.strip()]
            pc_config_ids   = [x.strip() for x in (row[2] or '').split(',') if x.strip()]
            db_config_ids   = [x.strip() for x in (row[3] or '').split(',') if x.strip()]

            # Resolve AppD config IDs → application names (for display)
            appd_names = []
            if appd_config_ids:
                placeholders = ','.join([f':id{i}' for i in range(len(appd_config_ids))])
                params = {f'id{i}': v for i, v in enumerate(appd_config_ids)}
                cursor.execute(f"""
                    SELECT a.APPLICATION_NAME
                      FROM API_APPD_APPLICATIONS a
                      JOIN API_APPD_LOB_CONFIG l ON a.LOB_ID = l.LOB_ID
                     WHERE l.LOB_ID IN ({placeholders})
                       AND a.IS_ACTIVE = 'Y'
                     ORDER BY a.APPLICATION_NAME
                """, params)
                appd_names = [r[0] for r in cursor.fetchall()]

            # Resolve PC config IDs → project names (from API_NFT_PC_CONFIG)
            pc_names = []
            if pc_config_ids:
                placeholders = ','.join([f':id{i}' for i in range(len(pc_config_ids))])
                params = {f'id{i}': v for i, v in enumerate(pc_config_ids)}
                cursor.execute(f"""
                    SELECT DISPLAY_NAME, PROJECT_NAME
                      FROM API_NFT_PC_CONFIG
                     WHERE CONFIG_ID IN ({placeholders})
                       AND IS_ACTIVE = 'Y'
                """, params)
                pc_names = [r[0] or r[1] for r in cursor.fetchall()]

            # Resolve DB config IDs → DB names
            db_names = []
            if db_config_ids:
                # DB configs stored directly as names in many setups
                db_names = db_config_ids  # fallback: treat IDs as names

            return {
                "template": {
                    "template_id":       template_id,
                    "lob_name":          lob_name,
                    "track":             track,
                    # IDs (for saving back)
                    "appd_config_ids":   appd_config_ids,
                    "pc_config_ids":     pc_config_ids,
                    "db_config_ids":     db_config_ids,
                    # Resolved names (for display in frontend)
                    "appd_applications": appd_names,
                    "pc_projects":       pc_names,
                    "awr_databases":     db_names,
                    "updated_date":      row[9].isoformat() if row[9] else None,
                }
            }
    except Exception as e:
        logger.error(f"Get track template error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── POST /nft/track-template ──────────────────────────────────────────────────
@nft_router.post("/track-template")
async def save_track_template(
    request: Request,
    current_user: str = Depends(verify_auth_token),
):
    """
    Save (upsert) a track template.
    Frontend sends arrays of IDs for each tool.
    """
    body = await request.json()
    lob_name = body.get('lob_name')
    track    = body.get('track')
    if not lob_name or not track:
        raise HTTPException(status_code=400, detail="lob_name and track required")

    # Accept both ID arrays and name arrays (frontend sends names, resolve to IDs if needed)
    appd_ids = body.get('appd_config_ids', body.get('appd_applications', []))
    pc_ids   = body.get('pc_config_ids',   body.get('pc_projects', []))
    db_ids   = body.get('db_config_ids',   body.get('awr_databases', []))

    appd_str = ','.join(str(x) for x in appd_ids)
    pc_str   = ','.join(str(x) for x in pc_ids)
    db_str   = ','.join(str(x) for x in db_ids)

    try:
        with oracle_pool.acquire() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                MERGE INTO API_NFT_TRACK_TEMPLATE t
                USING DUAL
                   ON (t.LOB_NAME = :lob_name AND t.TRACK = :track)
                WHEN MATCHED THEN
                    UPDATE SET
                        t.APPD_CONFIG_IDS = :appd_ids,
                        t.PC_CONFIG_IDS   = :pc_ids,
                        t.DB_CONFIG_IDS   = :db_ids,
                        t.APPD_COUNT      = :appd_count,
                        t.PC_COUNT        = :pc_count,
                        t.DB_COUNT        = :db_count,
                        t.UPDATED_BY      = :updated_by,
                        t.UPDATED_DATE    = SYSDATE
                WHEN NOT MATCHED THEN
                    INSERT (TEMPLATE_ID, LOB_NAME, TRACK,
                            APPD_CONFIG_IDS, PC_CONFIG_IDS, DB_CONFIG_IDS,
                            APPD_COUNT, PC_COUNT, DB_COUNT,
                            IS_ACTIVE, CREATED_BY, CREATED_DATE)
                    VALUES (SEQ_TRACK_TEMPLATE.NEXTVAL, :lob_name, :track,
                            :appd_ids, :pc_ids, :db_ids,
                            :appd_count, :pc_count, :db_count,
                            'Y', :updated_by, SYSDATE)
            """, {
                'lob_name':   lob_name,
                'track':      track,
                'appd_ids':   appd_str,
                'pc_ids':     pc_str,
                'db_ids':     db_str,
                'appd_count': len(appd_ids),
                'pc_count':   len(pc_ids),
                'db_count':   len(db_ids),
                'updated_by': current_user,
            })
            conn.commit()
        return {"success": True, "lob_name": lob_name, "track": track,
                "message": f"Template for {lob_name}/{track} saved"}
    except Exception as e:
        logger.error(f"Save track template error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /nft/track-template/list ─────────────────────────────────────────────
@nft_router.get("/track-template/list")
async def list_track_templates(
    lob_name: str = Query(None),
    current_user: str = Depends(verify_auth_token),
):
    """List all saved track templates with counts."""
    try:
        with oracle_pool.acquire() as conn:
            cursor = conn.cursor()
            sql = """
                SELECT LOB_NAME, TRACK,
                       APPD_CONFIG_IDS, PC_CONFIG_IDS, DB_CONFIG_IDS,
                       APPD_COUNT, PC_COUNT, DB_COUNT,
                       CREATED_BY, UPDATED_DATE
                  FROM API_NFT_TRACK_TEMPLATE
                 WHERE IS_ACTIVE = 'Y'
            """
            params = {}
            if lob_name:
                sql += " AND LOB_NAME = :lob_name"
                params['lob_name'] = lob_name
            sql += " ORDER BY LOB_NAME, TRACK"
            cursor.execute(sql, params)

            templates = []
            for row in cursor.fetchall():
                appd_ids = [x.strip() for x in (row[2] or '').split(',') if x.strip()]
                pc_ids   = [x.strip() for x in (row[3] or '').split(',') if x.strip()]
                db_ids   = [x.strip() for x in (row[4] or '').split(',') if x.strip()]
                templates.append({
                    'lob_name':        row[0],
                    'track':           row[1],
                    'appd_config_ids': appd_ids,
                    'pc_config_ids':   pc_ids,
                    'db_config_ids':   db_ids,
                    # Use IDs as display names for list view (saves extra joins)
                    'appd_applications': appd_ids,
                    'pc_projects':       pc_ids,
                    'awr_databases':     db_ids,
                    'appd_count':      row[5] or 0,
                    'pc_count':        row[6] or 0,
                    'db_count':        row[7] or 0,
                    'created_by':      row[8],
                    'updated_date':    row[9].isoformat() if row[9] else None,
                })
            return {"templates": templates, "total": len(templates)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── DELETE /nft/track-template ────────────────────────────────────────────────
@nft_router.delete("/track-template")
async def delete_track_template(
    lob_name: str = Query(...),
    track:    str = Query(...),
    current_user: str = Depends(verify_auth_token),
):
    try:
        with oracle_pool.acquire() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE API_NFT_TRACK_TEMPLATE
                   SET IS_ACTIVE    = 'N',
                       UPDATED_BY   = :user,
                       UPDATED_DATE = SYSDATE
                 WHERE LOB_NAME = :lob_name AND TRACK = :track
            """, {'lob_name': lob_name, 'track': track, 'user': current_user})
            conn.commit()
        return {"success": True, "message": f"Template {lob_name}/{track} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# KEY INSIGHT FOR FRONTEND WIRING:
#
# The table stores CONFIG IDs, not names.
# But the frontend dropdowns show NAMES and need to store IDs.
#
# For AppD: APPD_CONFIG_IDS = LOB_ID values from API_APPD_LOB_CONFIG
#           The master-applications endpoint returns APP_ID
#           → Use APP_ID as the config ID stored in APPD_CONFIG_IDS
#
# For PC:   PC_CONFIG_IDS = CONFIG_ID values from API_NFT_PC_CONFIG
#           → Use config_id returned from save_pc_project
#
# For DB (AWR): DB_CONFIG_IDS = db names directly (VARCHAR)
#               since there's no separate DB config table with IDs
#               → Store names directly: "CQE_NFT,CD_PTE_READ"
#
# FRONTEND CHANGE NEEDED (track-management.html):
# When user selects AppD app from dropdown, store BOTH name (display)
# and ID (for saving). The select option value should be the APP_ID,
# not the name. See updated frontend below.
# =============================================================================
