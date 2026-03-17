"""
NFT DATABASE ADDITIONS
======================
Add these methods to your existing NFTPlatformDatabase class in monitoring/nft/database.py.
These are needed by the real test-connection implementations.
"""

# ─── ADD THESE METHODS to NFTPlatformDatabase class ───────────────────────────

def get_kibana_config_by_id(self, kibana_config_id: int):
    """Get a single Kibana config by primary key."""
    conn = self._get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT KIBANA_CONFIG_ID, LOB_NAME, TRACK_NAME, KIBANA_URL,
                   USERNAME, TOKEN_ENV_VAR, AUTH_TYPE,
                   DASHBOARD_ID, DISPLAY_NAME, TIME_FIELD,
                   LAST_TEST_STATUS, CREATED_DATE
            FROM API_NFT_KIBANA_CONFIG
            WHERE KIBANA_CONFIG_ID = :config_id
        """, {'config_id': kibana_config_id})
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'kibana_config_id': row[0],
            'lob_name':         row[1],
            'track_name':       row[2],
            'kibana_url':       row[3],
            'username':         row[4],
            'token_env_var':    row[5],
            'auth_type':        row[6] or 'apikey',
            'dashboard_id':     row[7],
            'display_name':     row[8],
            'time_field':       row[9] or '@timestamp',
            'last_test_status': row[10],
            'created_date':     row[11].isoformat() if row[11] else None,
        }
    finally:
        cursor.close()
        conn.close()


def get_pc_config_by_id(self, pc_config_id: int):
    """Get a single PC config by primary key."""
    conn = self._get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT PC_CONFIG_ID, LOB_NAME, TRACK_NAME, PC_URL, PC_PORT,
                   USERNAME, PASS_ENV_VAR, DOMAIN, PROJECT_NAME,
                   DISPLAY_NAME, DURATION_FORMAT, COOKIE_FLAG,
                   REPORT_TIMEOUT_SEC, LAST_RUN_ID, LAST_TEST_STATUS
            FROM API_NFT_PC_CONFIG
            WHERE PC_CONFIG_ID = :config_id
        """, {'config_id': pc_config_id})
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'pc_config_id':      row[0],
            'lob_name':          row[1],
            'track_name':        row[2],
            'pc_url':            row[3],
            'pc_port':           row[4] or 443,
            'username':          row[5],
            'pass_env_var':      row[6],
            'domain':            row[7] or 'DEFAULT',
            'project_name':      row[8],
            'display_name':      row[9],
            'duration_format':   row[10] or 'HM',
            'cookie_flag':       row[11] or '-b',
            'report_timeout_sec': row[12] or 300,
            'last_run_id':       row[13],
            'last_test_status':  row[14],
        }
    finally:
        cursor.close()
        conn.close()


def get_db_config_by_id(self, db_config_id: int):
    """Get a single Oracle DB config by primary key."""
    conn = self._get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT DB_CONFIG_ID, LOB_NAME, DISPLAY_NAME,
                   HOST, PORT, SERVICE_NAME, USERNAME, PASS_ENV_VAR,
                   USE_CYBERARK, ALLOWED_OPERATIONS
            FROM API_NFT_DB_CONFIG
            WHERE DB_CONFIG_ID = :config_id
        """, {'config_id': db_config_id})
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'db_config_id':       row[0],
            'lob_name':           row[1],
            'display_name':       row[2],
            'host':               row[3],
            'port':               row[4] or 1521,
            'service_name':       row[5],
            'username':           row[6],
            'pass_env_var':       row[7],
            'use_cyberark':       row[8] == 'Y',
            'allowed_operations': row[9],
        }
    finally:
        cursor.close()
        conn.close()


def get_appd_config_by_lob(self, lob_name: str):
    """Get AppD config for a LOB — used by AppD test-connection."""
    conn = self._get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT APPD_CONFIG_ID, LOB_NAME, CONTROLLER_URL, ACCOUNT_NAME,
                   TOKEN_ENV_VAR, DEFAULT_NODE_COUNT, LAST_TEST_STATUS
            FROM API_NFT_APPD_CONFIG
            WHERE LOB_NAME = :lob_name
              AND IS_ACTIVE = 'Y'
            ORDER BY CREATED_DATE DESC
            FETCH FIRST 1 ROW ONLY
        """, {'lob_name': lob_name})
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'appd_config_id':    row[0],
            'lob_name':          row[1],
            'controller_url':    row[2],
            'account_name':      row[3],
            'token_env_var':     row[4],
            'default_node_count': row[5] or 3,
            'last_test_status':  row[6],
        }
    finally:
        cursor.close()
        conn.close()


def update_config_test_status(self, table: str, pk_col: str,
                               pk_val: int, status: str) -> None:
    """
    Update LAST_TEST_STATUS on any NFT config table.
    table: 'API_NFT_KIBANA_CONFIG' | 'API_NFT_PC_CONFIG' | 'API_NFT_DB_CONFIG'
    status: 'PASS' | 'FAIL' | 'NOT_TESTED'
    """
    conn = self._get_connection()
    cursor = conn.cursor()
    try:
        sql = f"""
            UPDATE {table}
            SET LAST_TEST_STATUS = :status, UPDATED_DATE = SYSDATE
            WHERE {pk_col} = :pk_val
        """
        cursor.execute(sql, {'status': status, 'pk_val': pk_val})
        conn.commit()
    finally:
        cursor.close()
        conn.close()
