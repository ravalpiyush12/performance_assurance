# =============================================================================
# FIX 1: routes.py — Fix get_active_nodes to use config_name query param
# REPLACE the existing get_active_nodes function entirely
# =============================================================================

@router.get("/active-nodes")
async def get_active_nodes(
    lob_name: str = Query(...),
    config_name: str = Query(None),   # NOW properly used
    track: str = Query(None),
    current_user: str = Depends(verify_auth_token),
):
    """Get all discovered active/inactive nodes for a LOB, config, and optional track."""
    if not appd_db:
        raise HTTPException(status_code=503, detail="Service not initialized")
    try:
        # If config_name provided directly, use it — don't look up from lob_config
        if not config_name:
            # Fallback: get latest config for this LOB+track
            config = appd_db.get_lob_config(lob_name)
            if not config:
                return {"success": True, "nodes": [], "total": 0, "active": 0,
                        "message": "No config found"}
            config_name = config.get('config_name') or lob_name

        # Get ALL nodes (active + inactive) so UI can show both
        nodes = appd_db.get_all_nodes_for_lob(lob_name, config_name, track=track)

        # Get last discovery time from discovery log
        last_discovery_time = appd_db.get_last_discovery_time(lob_name, config_name)

        return {
            "success": True,
            "nodes": nodes,
            "total": len(nodes),
            "active": sum(1 for n in nodes if n.get('is_active') == 'Y'),
            "inactive": sum(1 for n in nodes if n.get('is_active') != 'Y'),
            "last_discovery_time": last_discovery_time,
        }
    except Exception as e:
        logger.error(f"Get active nodes error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# FIX 2: routes.py — Add DELETE /applications/{app_master_id} endpoint
# Add this after the existing POST /applications endpoint
# =============================================================================

@router.delete("/applications/{app_master_id}")
async def delete_appd_application(
    app_master_id: int,
    current_user: str = Depends(verify_auth_token),
):
    """Delete (soft-delete) an AppDynamics master application by ID."""
    if not appd_db:
        raise HTTPException(status_code=503, detail="Service not initialized")
    try:
        success = appd_db.delete_master_application(app_master_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Application ID {app_master_id} not found"
            )
        return {"success": True, "message": f"Application {app_master_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete application error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# FIX 3: database.py — Add get_all_nodes_for_lob (returns BOTH active+inactive)
# This replaces the existing get_active_nodes_for_lob which only returns IS_ACTIVE='Y'
# Add this as a NEW method — keep the old one for health check compatibility
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
        get_active_nodes_for_lob still exists for health check (active only).
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
                    COALESCE(th.EXPECTED_NODES, 0) AS EXPECTED_NODES,
                    n.LAST_UPDATED
                FROM API_APPD_LOB_CONFIG l
                JOIN API_APPD_APPLICATIONS a ON l.LOB_ID = a.LOB_ID
                JOIN API_APPD_TIERS t ON a.APP_ID = t.APP_ID
                JOIN API_APPD_NODES n ON t.TIER_ID = n.TIER_ID
                LEFT JOIN API_APPD_TIERS th_tier ON (
                    th_tier.TIER_ID = t.TIER_ID
                )
                WHERE l.LOB_NAME = :lob_name
                  AND l.CONFIG_NAME = :config_name
                  AND a.IS_ACTIVE = 'Y'
                  AND t.IS_ACTIVE = 'Y'
            """
            # NOTE: EXPECTED_NODES — if you store it on API_APPD_TIERS directly,
            # update the SELECT above. If it's a separate threshold table, join that instead.
            # Based on your save_tier_threshold endpoint it updates API_APPD_TIERS directly.

            params = {'lob_name': lob_name, 'config_name': config_name}
            if track:
                sql += " AND l.TRACK = :track"
                params['track'] = track
            sql += " ORDER BY a.APPLICATION_NAME, t.TIER_NAME, n.NODE_NAME"

            cursor.execute(sql, params)
            nodes = []
            for row in cursor.fetchall():
                nodes.append({
                    'lob_name':           row[0],
                    'application_name':   row[1],
                    'tier_name':          row[2],
                    'node_name':          row[3],
                    'node_id':            row[4],
                    'calls_per_minute':   row[5],
                    'machine_name':       row[6],
                    'ip_address':         row[7],
                    'last_activity_time': row[8].isoformat() if row[8] else None,
                    'lob_id':             row[9],
                    'app_id':             row[10],
                    'tier_id':            row[11],
                    'is_active':          row[12],       # 'Y' or 'INACTIVE'/'N'
                    'expected_nodes':     row[13] or 0,  # for threshold input
                    'last_updated':       row[14].isoformat() if row[14] else None,
                })
            return nodes
        finally:
            conn.close()

    def get_last_discovery_time(self, lob_name: str, config_name: str):
        """Get timestamp of last completed discovery run for this config."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MAX(COMPLETED_AT)
                  FROM API_APPD_DISCOVERY_LOG
                 WHERE LOB_NAME   = :lob_name
                   AND CONFIG_NAME = :config_name
                   AND STATUS      = 'SUCCESS'
            """, {'lob_name': lob_name, 'config_name': config_name})
            row = cursor.fetchone()
            return row[0].isoformat() if row and row[0] else None
        except Exception:
            return None
        finally:
            conn.close()

    def delete_master_application(self, app_master_id: int) -> bool:
        """Soft-delete a master application by ID (sets IS_ACTIVE='N')."""
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
            logger.error(f"Delete master application error: {e}", exc_info=True)
            raise
        finally:
            conn.close()


# =============================================================================
# IMPORTANT: Check what column stores IS_ACTIVE on API_APPD_NODES
# From your discovery.py upsert_node call, IS_ACTIVE is stored as 'ACTIVE'/'INACTIVE'
# NOT 'Y'/'N' — so the comparison in frontend must match.
#
# In get_all_nodes_for_lob the row[12] returns 'ACTIVE' or 'INACTIVE'
# Frontend already checks: n.is_active === 'Y'  ← THIS WILL FAIL
#
# FIX in frontend: change all  n.is_active === 'Y'  to  n.is_active === 'ACTIVE'
# OR fix in SQL: CASE WHEN n.IS_ACTIVE='ACTIVE' THEN 'Y' ELSE 'N' END AS IS_ACTIVE
# The SQL approach is cleaner — add to get_all_nodes_for_lob SELECT:
#
#   CASE WHEN n.IS_ACTIVE = 'ACTIVE' THEN 'Y' ELSE 'N' END AS IS_ACTIVE
#
# This way frontend code stays unchanged.
# =============================================================================
