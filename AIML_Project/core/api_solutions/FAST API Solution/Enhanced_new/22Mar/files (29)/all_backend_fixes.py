# =============================================================================
# STEP 1: Run this DDL in Oracle SQL Developer
# Add EXPECTED_NODES to API_APPD_TIERS
# =============================================================================

ALTER TABLE API_APPD_TIERS
ADD EXPECTED_NODES NUMBER DEFAULT 0;

COMMENT ON COLUMN API_APPD_TIERS.EXPECTED_NODES IS
'Admin-defined expected active node count for health alerting. 0 = use ACTIVE_NODES from last discovery.';

-- Seed with current ACTIVE_NODES as default so existing data is meaningful
UPDATE API_APPD_TIERS
   SET EXPECTED_NODES = ACTIVE_NODES
 WHERE EXPECTED_NODES IS NULL OR EXPECTED_NODES = 0;

COMMIT;


# =============================================================================
# STEP 2: database.py — fix get_master_applications
# Add APP_ID to SELECT so frontend can use it for DELETE
# =============================================================================

# Find the get_master_applications method. Based on your schema it queries
# API_APPD_APPLICATIONS. Update the SQL and row mapping:

def get_master_applications(self, lob_name: str, track: str) -> List[Dict]:
    """Get all AppDynamics applications filtered by LOB and Track."""
    conn = self._get_connection()
    try:
        cursor = conn.cursor()
        sql = """
            SELECT
                a.APP_ID,                    -- ADD: needed for frontend DELETE
                a.APPLICATION_NAME,
                a.LOB_ID,
                a.APPLICATION_ID,            -- AppD numeric app ID
                a.TOTAL_TIERS,
                a.TOTAL_NODES,
                a.ACTIVE_NODES,
                a.INACTIVE_NODES,
                a.DISCOVERY_DATE,
                a.IS_ACTIVE,
                a.CREATED_DATE,
                a.UPDATED_DATE,
                l.LOB_NAME,
                l.TRACK
            FROM API_APPD_APPLICATIONS a
            JOIN API_APPD_LOB_CONFIG l ON a.LOB_ID = l.LOB_ID
            WHERE l.LOB_NAME = :lob_name
              AND l.TRACK    = :track
              AND a.IS_ACTIVE = 'Y'
            ORDER BY a.APPLICATION_NAME
        """
        cursor.execute(sql, {'lob_name': lob_name, 'track': track})
        apps = []
        for row in cursor.fetchall():
            apps.append({
                'app_master_id':    row[0],   # APP_ID — used by frontend for DELETE
                'application_name': row[1],
                'lob_id':           row[2],
                'application_id':   row[3],   # AppD numeric ID (app_id_appd)
                'total_tiers':      row[4],
                'total_nodes':      row[5],
                'active_nodes':     row[6],
                'inactive_nodes':   row[7],
                'discovery_date':   row[8].isoformat() if row[8] else None,
                'is_active':        row[9],
                'created_date':     row[10].isoformat() if row[10] else None,
                'updated_date':     row[11].isoformat() if row[11] else None,
                'lob_name':         row[12],
                'track':            row[13],
                'description':      None,     # Add DESCRIPTION col to table if needed
            })
        return apps
    except Exception as e:
        logger.error(f"Get master applications error: {e}", exc_info=True)
        raise
    finally:
        conn.close()


# =============================================================================
# STEP 3: database.py — fix get_all_nodes_for_lob
# Fix the LEFT JOIN (self-join on th_tier was wrong), use EXPECTED_NODES from tier
# Also fix IS_ACTIVE comparison — nodes store 'ACTIVE'/'INACTIVE' not 'Y'/'N'
# =============================================================================

def get_all_nodes_for_lob(
    self,
    lob_name: str,
    config_name: str,
    track: Optional[str] = None,
) -> List[Dict]:
    """
    Get ALL nodes (active + inactive) for a LOB+config.
    Used by Discovery tab to show full node list with status.
    """
    conn = self._get_connection()
    try:
        cursor = conn.cursor()
        sql = """
            SELECT
                l.LOB_NAME,
                a.APPLICATION_NAME,
                t.TIER_NAME,
                n.NODE_NAME,
                n.NODE_ID,
                n.CALLS_PER_MINUTE,
                n.MACHINE_NAME,
                n.IP_ADDRESS,
                n.LAST_ACTIVITY_TIME,
                l.LOB_ID,
                a.APP_ID,
                t.TIER_ID,
                n.IS_ACTIVE,
                COALESCE(t.EXPECTED_NODES, t.ACTIVE_NODES, 0) AS EXPECTED_NODES,
                n.UPDATED_DATE
            FROM API_APPD_LOB_CONFIG l
            JOIN API_APPD_APPLICATIONS a
              ON l.LOB_ID = a.LOB_ID
             AND a.IS_ACTIVE = 'Y'
            JOIN API_APPD_TIERS t
              ON a.APP_ID = t.APP_ID
             AND t.IS_ACTIVE = 'Y'
            JOIN API_APPD_NODES n
              ON t.TIER_ID = n.TIER_ID
            WHERE l.LOB_NAME    = :lob_name
              AND l.CONFIG_NAME = :config_name
        """
        params = {'lob_name': lob_name, 'config_name': config_name}
        if track:
            sql += " AND l.TRACK = :track"
            params['track'] = track
        sql += " ORDER BY a.APPLICATION_NAME, t.TIER_NAME, n.NODE_NAME"

        cursor.execute(sql, params)
        nodes = []
        for row in cursor.fetchall():
            raw_active = row[12]  # 'ACTIVE', 'INACTIVE', 'Y', or 'N'
            # Normalize to 'Y'/'N' for consistent frontend handling
            is_active = 'Y' if raw_active in ('ACTIVE', 'Y') else 'N'
            nodes.append({
                'lob_name':           row[0],
                'application_name':   row[1],
                'tier_name':          row[2],
                'node_name':          row[3],
                'node_id':            row[4],
                'calls_per_minute':   row[5] or 0,
                'machine_name':       row[6],
                'ip_address':         row[7],
                'last_activity_time': row[8].isoformat() if row[8] else None,
                'lob_id':             row[9],
                'app_id':             row[10],
                'tier_id':            row[11],
                'is_active':          is_active,  # always 'Y' or 'N'
                'expected_nodes':     row[13] or 0,
                'last_updated':       row[14].isoformat() if row[14] else None,
            })
        return nodes
    except Exception as e:
        logger.error(f"Get all nodes error: {e}", exc_info=True)
        raise
    finally:
        conn.close()


# =============================================================================
# STEP 4: database.py — fix save_tier_threshold
# Now saves to EXPECTED_NODES on API_APPD_TIERS
# Find the existing save_tier_threshold and replace the UPDATE SQL:
# =============================================================================

def save_tier_threshold(
    self,
    lob_name: str,
    track: str,
    application_name: str,
    tier_name: str,
    expected_nodes: int,
) -> Dict:
    """Save expected active node count for a tier."""
    conn = self._get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE API_APPD_TIERS t
               SET t.EXPECTED_NODES = :expected_nodes,
                   t.UPDATED_DATE   = SYSDATE
             WHERE t.TIER_NAME = :tier_name
               AND t.APP_ID IN (
                   SELECT a.APP_ID
                     FROM API_APPD_APPLICATIONS a
                     JOIN API_APPD_LOB_CONFIG l ON a.LOB_ID = l.LOB_ID
                    WHERE l.LOB_NAME          = :lob_name
                      AND l.TRACK             = :track
                      AND a.APPLICATION_NAME  = :app_name
                      AND a.IS_ACTIVE         = 'Y'
               )
        """, {
            'expected_nodes': expected_nodes,
            'tier_name':      tier_name,
            'lob_name':       lob_name,
            'track':          track,
            'app_name':       application_name,
        })
        updated = cursor.rowcount
        conn.commit()
        return {
            'updated_rows':   updated,
            'tier_name':      tier_name,
            'expected_nodes': expected_nodes,
        }
    except Exception as e:
        conn.rollback()
        logger.error(f"Tier threshold error: {e}", exc_info=True)
        raise
    finally:
        conn.close()


# =============================================================================
# STEP 5: database.py — fix delete_master_application
# API_APPD_APPLICATIONS uses IS_ACTIVE VARCHAR2(1) — use 'N' not False
# =============================================================================

def delete_master_application(self, app_master_id: int) -> bool:
    """Soft-delete a master application by APP_ID."""
    conn = self._get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE API_APPD_APPLICATIONS
               SET IS_ACTIVE    = 'N',
                   UPDATED_DATE = SYSDATE
             WHERE APP_ID = :app_id
        """, {'app_id': app_master_id})
        updated = cursor.rowcount
        conn.commit()
        return updated > 0
    except Exception as e:
        conn.rollback()
        logger.error(f"Delete application error: {e}", exc_info=True)
        raise
    finally:
        conn.close()


# =============================================================================
# SUMMARY OF ALL CHANGES
# =============================================================================
#
# Oracle DDL (run once):
#   ALTER TABLE API_APPD_TIERS ADD EXPECTED_NODES NUMBER DEFAULT 0;
#   UPDATE API_APPD_TIERS SET EXPECTED_NODES = ACTIVE_NODES WHERE EXPECTED_NODES = 0;
#   COMMIT;
#
# database.py:
#   get_master_applications  → add APP_ID to SELECT → returns 'app_master_id'
#   get_all_nodes_for_lob    → fix LEFT JOIN, use t.EXPECTED_NODES, normalize IS_ACTIVE
#   save_tier_threshold      → update EXPECTED_NODES on API_APPD_TIERS
#   delete_master_application → soft delete using IS_ACTIVE = 'N'
#
# Frontend (already done in appd-config.html):
#   loadApplicationsList  → reads app.app_master_id
#   saveApp               → fetches app_master_id after save
#   removeApp             → calls DELETE /applications/{app_master_id}
#   loadDiscoveryResults  → isActive() handles both 'Y' and 'ACTIVE'
#   Threshold input       → pre-fills from node.expected_nodes
# =============================================================================
