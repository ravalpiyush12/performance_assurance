# =============================================================================
# STEP 1: Oracle DDL — Create track template table (run once in SQL Developer)
# =============================================================================

CREATE TABLE API_NFT_TRACK_TEMPLATE (
    TEMPLATE_ID    NUMBER         NOT NULL,
    LOB_NAME       VARCHAR2(100)  NOT NULL,
    TRACK          VARCHAR2(50)   NOT NULL,
    APPD_APPS      CLOB,          -- JSON array: ["app1","app2"]
    AWR_DATABASES  CLOB,          -- JSON array: ["CQE_NFT","CD_PTE_READ"]
    PC_PROJECTS    CLOB,          -- JSON array: ["project1"]
    CREATED_BY     VARCHAR2(100),
    CREATED_DATE   DATE DEFAULT SYSDATE,
    UPDATED_DATE   DATE DEFAULT SYSDATE,
    IS_ACTIVE      CHAR(1) DEFAULT 'Y',
    CONSTRAINT PK_TRACK_TEMPLATE PRIMARY KEY (TEMPLATE_ID),
    CONSTRAINT UQ_TRACK_TEMPLATE UNIQUE (LOB_NAME, TRACK)
);

CREATE SEQUENCE SEQ_TRACK_TEMPLATE START WITH 1 INCREMENT BY 1;

-- PC config projects table
CREATE TABLE API_NFT_PC_CONFIG (
    CONFIG_ID       NUMBER         NOT NULL,
    LOB_NAME        VARCHAR2(100)  NOT NULL,
    TRACK           VARCHAR2(50),
    PROJECT_NAME    VARCHAR2(200)  NOT NULL,
    TEST_PLAN_NAME  VARCHAR2(200),
    DISPLAY_NAME    VARCHAR2(200),
    PC_URL          VARCHAR2(500),
    PC_PORT         NUMBER,
    USERNAME        VARCHAR2(100),
    PASS_ENV_VAR    VARCHAR2(200),
    PC_DOMAIN       VARCHAR2(100) DEFAULT 'DEFAULT',
    TIMEOUT_SECONDS NUMBER DEFAULT 300,
    IS_ACTIVE       CHAR(1) DEFAULT 'Y',
    CREATED_DATE    DATE DEFAULT SYSDATE,
    UPDATED_DATE    DATE DEFAULT SYSDATE,
    CONSTRAINT PK_PC_CONFIG PRIMARY KEY (CONFIG_ID),
    CONSTRAINT UQ_PC_CONFIG UNIQUE (LOB_NAME, PROJECT_NAME)
);

CREATE SEQUENCE SEQ_PC_CONFIG START WITH 1 INCREMENT BY 1;


# =============================================================================
# STEP 2: Add these endpoints to your NFT router (routes_fixed.py or main.py)
# These are the endpoints the frontend calls via /api/v1/nft/...
# =============================================================================

import json
from fastapi import APIRouter, Depends, HTTPException, Request

# ── GET /nft/track-template ───────────────────────────────────────────────────
@nft_router.get("/track-template")
async def get_track_template(
    lob_name: str = Query(...),
    track:    str = Query(...),
    current_user: str = Depends(verify_auth_token),
):
    """Get track template for a LOB+Track combination."""
    try:
        with oracle_pool.acquire() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT APPD_APPS, AWR_DATABASES, PC_PROJECTS, UPDATED_DATE
                  FROM API_NFT_TRACK_TEMPLATE
                 WHERE LOB_NAME = :lob_name AND TRACK = :track AND IS_ACTIVE = 'Y'
            """, {'lob_name': lob_name, 'track': track})
            row = cursor.fetchone()
            if not row:
                return {"template": None}
            return {
                "template": {
                    "lob_name":          lob_name,
                    "track":             track,
                    "appd_applications": json.loads(row[0] or '[]'),
                    "awr_databases":     json.loads(row[1] or '[]'),
                    "pc_projects":       json.loads(row[2] or '[]'),
                    "updated_date":      row[3].isoformat() if row[3] else None,
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── POST /nft/track-template ──────────────────────────────────────────────────
@nft_router.post("/track-template")
async def save_track_template(
    request: Request,
    current_user: str = Depends(verify_auth_token),
):
    """Save (upsert) a track template."""
    body = await request.json()
    lob_name  = body.get('lob_name')
    track     = body.get('track')
    appd_apps = json.dumps(body.get('appd_applications', []))
    awr_dbs   = json.dumps(body.get('awr_databases', []))
    pc_projs  = json.dumps(body.get('pc_projects', []))
    created_by= body.get('created_by', 'admin')

    if not lob_name or not track:
        raise HTTPException(status_code=400, detail="lob_name and track required")
    try:
        with oracle_pool.acquire() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                MERGE INTO API_NFT_TRACK_TEMPLATE t
                USING DUAL ON (t.LOB_NAME = :lob_name AND t.TRACK = :track)
                WHEN MATCHED THEN UPDATE SET
                    t.APPD_APPS     = :appd_apps,
                    t.AWR_DATABASES = :awr_dbs,
                    t.PC_PROJECTS   = :pc_projs,
                    t.UPDATED_DATE  = SYSDATE
                WHEN NOT MATCHED THEN INSERT
                    (TEMPLATE_ID, LOB_NAME, TRACK, APPD_APPS, AWR_DATABASES,
                     PC_PROJECTS, CREATED_BY, IS_ACTIVE)
                VALUES
                    (SEQ_TRACK_TEMPLATE.NEXTVAL, :lob_name, :track, :appd_apps,
                     :awr_dbs, :pc_projs, :created_by, 'Y')
            """, {
                'lob_name': lob_name, 'track': track,
                'appd_apps': appd_apps, 'awr_dbs': awr_dbs, 'pc_projs': pc_projs,
                'created_by': created_by,
            })
            conn.commit()
        return {"success": True, "lob_name": lob_name, "track": track}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /nft/track-template/list ─────────────────────────────────────────────
@nft_router.get("/track-template/list")
async def list_track_templates(
    lob_name: str = Query(None),
    current_user: str = Depends(verify_auth_token),
):
    """List all saved track templates, optionally filtered by LOB."""
    try:
        with oracle_pool.acquire() as conn:
            cursor = conn.cursor()
            sql = """
                SELECT LOB_NAME, TRACK, APPD_APPS, AWR_DATABASES,
                       PC_PROJECTS, UPDATED_DATE
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
                templates.append({
                    'lob_name':          row[0],
                    'track':             row[1],
                    'appd_applications': json.loads(row[2] or '[]'),
                    'awr_databases':     json.loads(row[3] or '[]'),
                    'pc_projects':       json.loads(row[4] or '[]'),
                    'updated_date':      row[5].isoformat() if row[5] else None,
                })
            return {"templates": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── DELETE /nft/track-template ────────────────────────────────────────────────
@nft_router.delete("/track-template")
async def delete_track_template(
    lob_name: str = Query(...),
    track:    str = Query(...),
    current_user: str = Depends(verify_auth_token),
):
    """Soft-delete a track template."""
    try:
        with oracle_pool.acquire() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE API_NFT_TRACK_TEMPLATE
                   SET IS_ACTIVE = 'N', UPDATED_DATE = SYSDATE
                 WHERE LOB_NAME = :lob_name AND TRACK = :track
            """, {'lob_name': lob_name, 'track': track})
            conn.commit()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /nft/config/pc/projects ───────────────────────────────────────────────
@nft_router.get("/config/pc/projects")
async def get_pc_projects(
    lob_name: str = Query(None),
    track:    str = Query(None),
    current_user: str = Depends(verify_auth_token),
):
    """Get PC project configurations, optionally filtered by LOB/Track."""
    try:
        with oracle_pool.acquire() as conn:
            cursor = conn.cursor()
            sql = """
                SELECT CONFIG_ID, LOB_NAME, TRACK, PROJECT_NAME,
                       TEST_PLAN_NAME, DISPLAY_NAME, IS_ACTIVE, UPDATED_DATE
                  FROM API_NFT_PC_CONFIG WHERE IS_ACTIVE = 'Y'
            """
            params = {}
            if lob_name: sql += " AND LOB_NAME = :lob_name"; params['lob_name'] = lob_name
            if track:    sql += " AND TRACK = :track";       params['track'] = track
            cursor.execute(sql, params)
            projects = []
            for row in cursor.fetchall():
                projects.append({
                    'config_id':    row[0], 'lob_name': row[1],
                    'track':        row[2], 'project_name': row[3],
                    'test_plan_name': row[4], 'display_name': row[5],
                    'is_active':    row[6],
                    'updated_date': row[7].isoformat() if row[7] else None,
                })
            return {"projects": projects, "total": len(projects)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── POST /nft/config/pc/projects ─────────────────────────────────────────────
@nft_router.post("/config/pc/projects")
async def save_pc_project(
    request: Request,
    current_user: str = Depends(verify_auth_token),
):
    """Save (upsert) a PC project config."""
    body = await request.json()
    lob_name     = body.get('lob_name')
    project_name = body.get('project_name')
    if not lob_name or not project_name:
        raise HTTPException(status_code=400, detail="lob_name and project_name required")
    try:
        with oracle_pool.acquire() as conn:
            cursor = conn.cursor()
            config_id_var = cursor.var(int)
            cursor.execute("""
                MERGE INTO API_NFT_PC_CONFIG c
                USING DUAL ON (c.LOB_NAME = :lob_name AND c.PROJECT_NAME = :project_name)
                WHEN MATCHED THEN UPDATE SET
                    c.TRACK          = :track,
                    c.TEST_PLAN_NAME = :test_plan,
                    c.DISPLAY_NAME   = :display,
                    c.IS_ACTIVE      = :is_active,
                    c.UPDATED_DATE   = SYSDATE
                WHEN NOT MATCHED THEN INSERT
                    (CONFIG_ID, LOB_NAME, TRACK, PROJECT_NAME, TEST_PLAN_NAME,
                     DISPLAY_NAME, IS_ACTIVE)
                VALUES
                    (SEQ_PC_CONFIG.NEXTVAL, :lob_name, :track, :project_name,
                     :test_plan, :display, :is_active)
            """, {
                'lob_name':     lob_name,
                'project_name': project_name,
                'track':        body.get('track', ''),
                'test_plan':    body.get('test_plan_name', ''),
                'display':      body.get('display_name', project_name),
                'is_active':    body.get('is_active', 'Y'),
            })
            # Get the ID
            cursor.execute("""
                SELECT CONFIG_ID FROM API_NFT_PC_CONFIG
                 WHERE LOB_NAME = :lob and PROJECT_NAME = :proj
            """, {'lob': lob_name, 'proj': project_name})
            row = cursor.fetchone()
            conn.commit()
            return {"success": True, "config_id": row[0] if row else None,
                    "project_name": project_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── DELETE /nft/config/pc/projects/{config_id} ────────────────────────────────
@nft_router.delete("/config/pc/projects/{config_id}")
async def delete_pc_project(
    config_id: int,
    current_user: str = Depends(verify_auth_token),
):
    try:
        with oracle_pool.acquire() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE API_NFT_PC_CONFIG SET IS_ACTIVE='N', UPDATED_DATE=SYSDATE
                 WHERE CONFIG_ID = :id
            """, {'id': config_id})
            conn.commit()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SUMMARY OF ALL ENDPOINTS NEEDED
# =============================================================================
#
# Track Management page calls:
#   GET  /api/v1/auth/lob-config/public               ← already exists
#   GET  /api/v1/monitoring/appd/master-applications  ← already exists
#   GET  /api/v1/nft/config/databases                 ← add if not exists
#   GET  /api/v1/nft/config/pc/projects               ← ADD (above)
#   GET  /api/v1/nft/track-template                   ← ADD (above)
#   POST /api/v1/nft/track-template                   ← ADD (above)
#   GET  /api/v1/nft/track-template/list              ← ADD (above)
#   DELETE /api/v1/nft/track-template                 ← ADD (above)
#
# PC Config page calls:
#   GET  /api/v1/auth/lob-config/public               ← already exists
#   GET  /api/v1/nft/config/pc/{lob_name}             ← already exists (connection settings)
#   POST /api/v1/nft/config/pc                        ← already exists (save connection)
#   POST /api/v1/monitoring/pc/test-connection        ← add if not exists
#   GET  /api/v1/nft/config/pc/projects               ← ADD (above)
#   POST /api/v1/nft/config/pc/projects               ← ADD (above)
#   DELETE /api/v1/nft/config/pc/projects/{id}        ← ADD (above)
#   GET  /api/v1/monitoring/pc/health/{lob_name}      ← already exists
#
# Upload Reports page calls:
#   GET  /api/v1/auth/lob-config/public               ← already exists
#   GET  /api/v1/nft/config/databases                 ← add if not exists
#   GET  /api/v1/nft/config/pc/projects               ← ADD (above)
#   POST /api/v1/monitoring/pc/test-run/register      ← already exists
#   POST /api/v1/monitoring/awr/upload                ← already exists
#   POST /api/v1/monitoring/pc/fetch-results          ← already exists
#
# Start Monitoring page calls:
#   GET  /api/v1/auth/lob-config/public               ← already exists
#   GET  /api/v1/nft/track-template                   ← ADD (above)
#   GET  /api/v1/monitoring/appd/health/{lob}         ← already exists
#   GET  /api/v1/monitoring/pc/health/{lob}           ← already exists
#   POST /api/v1/monitoring/pc/test-run/register      ← already exists
#   POST /api/v1/monitoring/appd/monitoring/start     ← already exists
#   POST /api/v1/monitoring/appd/monitoring/stop/{id} ← already exists
# =============================================================================
