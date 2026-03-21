# =============================================================================
# database.py — corrected update_node_cpm using TIER_ID (not TIER_NAME)
# =============================================================================

    def update_node_cpm(
        self,
        lob_id: int,
        app_name: str,
        tier_name: str,
        node_name: str,
        calls_per_minute: float,
        is_active: str,
    ) -> bool:
        """
        Update ONLY calls_per_minute + is_active for an existing node.
        Looks up TIER_ID from API_APPD_TIERS via lob_id + tier_name + app_name.
        Does NOT insert — if node doesn't exist, silently skips.
        """
        sql = """
            UPDATE API_APPD_NODES
               SET CALLS_PER_MINUTE = :cpm,
                   IS_ACTIVE        = :is_active,
                   LAST_UPDATED     = SYSDATE
             WHERE LOB_ID   = :lob_id
               AND NODE_NAME = :node_name
               AND TIER_ID  = (
                   SELECT t.TIER_ID
                     FROM API_APPD_TIERS t
                     JOIN API_APPD_APPLICATIONS a
                       ON a.APP_ID  = t.APP_ID
                      AND a.LOB_ID  = :lob_id
                      AND a.APPLICATION_NAME = :app_name
                    WHERE t.TIER_NAME = :tier_name
                      AND t.LOB_ID   = :lob_id
                      AND ROWNUM     = 1
               )
        """
        try:
            with self.connection_pool.acquire() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, {
                    'cpm':       calls_per_minute,
                    'is_active': is_active,
                    'lob_id':    lob_id,
                    'node_name': node_name,
                    'tier_name': tier_name,
                    'app_name':  app_name,
                })
                updated_rows = cursor.rowcount
                conn.commit()
                if updated_rows == 0:
                    logger.warning(
                        f"[UpdateNodeCPM] Node not found in DB — skipped: "
                        f"{app_name}/{tier_name}/{node_name}"
                    )
                return updated_rows > 0
        except Exception as e:
            logger.error(f"[UpdateNodeCPM] DB error: {e}", exc_info=True)
            raise
