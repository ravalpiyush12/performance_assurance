# =============================================================================
# OPTION B — Backend changes for pc_config_id credential loading
#
# Two changes needed:
#   1. monitoring/pc/models.py  — add pc_config_id to PCConnectionRequest
#   2. monitoring/pc/routes.py  — update fetch_pc_results to load creds from DB
#
# No changes needed to PCConnectionRequest's existing fields —
# they remain Optional so existing callers don't break.
# =============================================================================


# =============================================================================
# CHANGE 1: monitoring/pc/models.py
# Add pc_config_id field to PCConnectionRequest
# =============================================================================
#
# FIND this class:
#
#   class PCConnectionRequest(BaseModel):
#       run_id:           str
#       pc_run_id:        str
#       pc_url:           str
#       pc_port:          int = Field(default=8080, ...)
#       pc_domain:        str
#       pc_project:       str
#       username:         str
#       password:         str
#       test_set_name:    Optional[str]
#       test_instance_id: Optional[str]
#       lob_name:         str
#       track:            Optional[str]
#       test_name:        Optional[str]
#
# REPLACE with:

class PCConnectionRequest(BaseModel):
    """Request to connect to Performance Center and fetch results"""
    run_id:           str   = Field(...,    description="Master run ID from RUN_MASTER")
    pc_run_id:        str   = Field(...,    description="Performance Center run ID")
    lob_name:         str   = Field(...,    description="Line of Business")

    # ── Option B: supply config ID so backend loads creds itself ──
    pc_config_id:     Optional[int]  = Field(None, description="PC config ID — if supplied, backend loads credentials from DB")

    # ── Legacy fields — still accepted but ignored when pc_config_id is set ──
    pc_url:           Optional[str]  = Field(None, description="PC URL (ignored if pc_config_id set)")
    pc_port:          Optional[int]  = Field(8080, description="PC port")
    pc_domain:        Optional[str]  = Field(None, description="PC domain")
    pc_project:       Optional[str]  = Field(None, description="PC project")
    username:         Optional[str]  = Field(None, description="PC username (ignored if pc_config_id set)")
    password:         Optional[str]  = Field(None, description="PC password (ignored if pc_config_id set)")

    # ── Optional metadata ──
    track:            Optional[str]  = Field(None)
    test_set_name:    Optional[str]  = Field(None)
    test_instance_id: Optional[str]  = Field(None)
    test_name:        Optional[str]  = Field(None)


# =============================================================================
# CHANGE 2: monitoring/pc/routes.py
# Update fetch_pc_results to load credentials from DB when pc_config_id given
# =============================================================================
#
# ADD this import at the top of monitoring/pc/routes.py (if not already there):
import os

# Also ensure nft_db is accessible. In your routes.py, pc_db is the
# MonitoringDatabase / PCDatabase instance. You need access to the NFT
# platform DB to call get_pc_config_by_id.
# If nft_db is not already imported, add:
#
#   from app.main import app   # ← only if nft_db is on app.state
# OR pass it in via init_pc_routes(pool, nft_pool) — see note at bottom.
#
# SIMPLEST approach: since API_NFT_PC_CONFIG lives in CQE_NFT (same pool
# as the rest of monitoring), add get_pc_config_by_id directly to
# your PCDatabase class (monitoring/pc/database.py). See CHANGE 3 below.


# =============================================================================
# CHANGE 2 continued — fetch_pc_results function
# Replace ONLY the credential-building block inside the try: body.
# =============================================================================
#
# FIND this section in your current fetch_pc_results:
#
#   # Create PC client
#   pc_url_full = f"{request.pc_url}:{request.pc_port}"
#   ...
#   pc_client = PerformanceCenterClient(
#       base_url=pc_url_full,
#       username=request.username,
#       password=request.password,
#       domain=request.pc_domain,
#       project=request.pc_project
#   )
#
# REPLACE that block with:

        # ── Resolve credentials ───────────────────────────────────────────────
        if request.pc_config_id:
            # Option B: load from DB — frontend never needs to send passwords
            logger.info(f"Loading PC credentials from config ID: {request.pc_config_id}")
            cfg = pc_db.get_pc_config_by_id(request.pc_config_id)
            if not cfg:
                raise HTTPException(
                    status_code=404,
                    detail=f"PC config ID {request.pc_config_id} not found. "
                           f"Configure it in Admin → PC Config first."
                )
            pc_url      = cfg.get('pc_url')      or cfg.get('base_url', '')
            pc_port     = cfg.get('pc_port')      or cfg.get('port', 8080)
            pc_domain   = cfg.get('domain')       or cfg.get('pc_domain', 'DEFAULT')
            pc_project  = cfg.get('project_name') or cfg.get('pc_project', '')
            username    = cfg.get('username', '')

            # Password stored as env var name — resolve from environment
            pass_env_var = cfg.get('pass_env_var', '')
            password = os.environ.get(pass_env_var, '') if pass_env_var else ''
            if not password:
                raise HTTPException(
                    status_code=500,
                    detail=f"PC password env var '{pass_env_var}' is not set on the server. "
                           f"Set the environment variable and restart."
                )
        else:
            # Legacy path: credentials passed directly in request body
            pc_url     = request.pc_url     or ''
            pc_port    = request.pc_port    or 8080
            pc_domain  = request.pc_domain  or 'DEFAULT'
            pc_project = request.pc_project or ''
            username   = request.username   or ''
            password   = request.password   or ''

        if not pc_url:
            raise HTTPException(status_code=400, detail="PC URL is required (pc_url or pc_config_id).")
        if not username:
            raise HTTPException(status_code=400, detail="PC username is required.")
        if not password:
            raise HTTPException(status_code=400, detail="PC password is required.")

        # ── Build client (unchanged from your existing code) ─────────────────
        pc_url_full = f"{pc_url}:{pc_port}"
        pc_client = PerformanceCenterClient(
            base_url=pc_url_full,
            username=username,
            password=password,
            domain=pc_domain,
            project=pc_project
        )
        # ... rest of your function continues unchanged from here ...


# =============================================================================
# CHANGE 3: monitoring/pc/database.py
# Add get_pc_config_by_id method to your PCDatabase class
# =============================================================================
#
# ADD this method to the PCDatabase class:

    def get_pc_config_by_id(self, pc_config_id: int) -> dict:
        """
        Fetch a single PC config row by PC_CONFIG_ID from API_NFT_PC_CONFIG.
        Returns dict with pc_url, pc_port, domain, project_name,
        username, pass_env_var — or None if not found.
        """
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT PC_CONFIG_ID, LOB_NAME, TRACK_NAME,
                           PC_URL, PC_PORT, DOMAIN, PROJECT_NAME,
                           USERNAME, PASS_ENV_VAR, DISPLAY_NAME,
                           DURATION_FORMAT, COOKIE_FLAG, REPORT_TIMEOUT_SEC
                    FROM   API_NFT_PC_CONFIG
                    WHERE  PC_CONFIG_ID = :pc_config_id
                    AND    IS_ACTIVE = 'Y'
                """, {'pc_config_id': pc_config_id})
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'pc_config_id':      row[0],
                    'lob_name':          row[1],
                    'track_name':        row[2],
                    'pc_url':            row[3],
                    'pc_port':           row[4],
                    'domain':            row[5],
                    'project_name':      row[6],
                    'username':          row[7],
                    'pass_env_var':      row[8],
                    'display_name':      row[9],
                    'duration_format':   row[10],
                    'cookie_flag':       row[11],
                    'report_timeout_sec': row[12],
                }
            except Exception as e:
                logger.error(f"Error fetching PC config {pc_config_id}: {e}")
                return None
            finally:
                cursor.close()
