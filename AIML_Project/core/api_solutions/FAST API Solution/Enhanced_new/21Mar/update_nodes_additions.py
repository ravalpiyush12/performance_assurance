# =============================================================================
# FILE 1: Add to monitoring/appd/routes.py
# =============================================================================
# Add this class near the other request models (top of file):

class UpdateNodesRequest(BaseModel):
    """Request model for updating node CPM/active status only - no structural changes"""
    lob_name: str
    track: str
    config_name: str
    applications: List[str]
    triggered_by: Optional[str] = None


# Add this endpoint after the existing run_discovery endpoint:

@router.post("/discovery/update-nodes")
async def update_nodes(request: UpdateNodesRequest,
                       background_tasks: BackgroundTasks,
                       current_user: str = Depends(verify_auth_token)):
    """
    Refresh CPM values and re-classify active/inactive for existing nodes only.
    Does NOT create new tiers or nodes — only updates CPM + is_active on nodes
    that already exist in APPD_NODES for this config.
    Much faster than full discovery.
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    if not appd_db:
        raise HTTPException(status_code=503, detail="Database not initialized")

    # Validate config exists
    config = appd_db.get_config_by_name(request.config_name)
    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Config '{request.config_name}' not found. Run full discovery first."
        )

    lob_id = config['lob_id']

    # Run in background (same pattern as run_discovery)
    task_id = str(uuid.uuid4())

    background_tasks.add_task(
        execute_update_nodes_task,
        task_id,
        lob_id,
        request.lob_name,
        request.config_name,
        request.applications,
    )

    return {
        "success": True,
        "task_id": task_id,
        "status": "initiated",
        "config_name": request.config_name,
        "lob_name": request.lob_name,
        "applications": request.applications,
        "message": "Node update started in background",
    }


async def execute_update_nodes_task(
    task_id: str,
    lob_id: int,
    lob_name: str,
    config_name: str,
    applications: List[str],
):
    """
    Background task: refresh CPM + re-classify active/inactive for existing nodes.
    """
    log_id = appd_db.create_discovery_log(lob_id, lob_name, config_name)
    stats = {'tiers': 0, 'nodes': 0, 'active_nodes': 0}

    try:
        logger.info(f"[UpdateNodes {task_id}] Starting for LOB: {lob_name}, config: {config_name}")

        for app_name in applications:
            try:
                app_stats = discovery_service.refresh_node_cpm(
                    lob_id=lob_id,
                    lob_name=lob_name,
                    app_name=app_name,
                )
                stats['tiers']        += app_stats.get('tiers_count', 0)
                stats['nodes']        += app_stats.get('nodes_count', 0)
                stats['active_nodes'] += app_stats.get('active_nodes_count', 0)
            except Exception as e:
                logger.error(f"[UpdateNodes {task_id}] Failed for app {app_name}: {e}",
                             exc_info=True)

        appd_db.complete_discovery_log(log_id, stats, status='SUCCESS')
        logger.info(
            f"[UpdateNodes {task_id}] Completed: "
            f"{stats['nodes']} nodes, {stats['active_nodes']} active"
        )

    except Exception as e:
        logger.error(f"[UpdateNodes {task_id}] Failed: {e}", exc_info=True)
        try:
            appd_db.complete_discovery_log(log_id, stats, status='FAILED', error=str(e))
        except Exception:
            pass


# =============================================================================
# FILE 2: Add to monitoring/appd/discovery.py  (AppDynamicsDiscoveryService)
# =============================================================================
# Add this method inside the AppDynamicsDiscoveryService class,
# after the existing discover_application() method:

    def refresh_node_cpm(self, lob_id: int, lob_name: str, app_name: str) -> Dict:
        """
        Refresh CPM and re-classify active/inactive for all EXISTING nodes
        of an application. Does NOT create new tiers or nodes.

        Only touches nodes already present in APPD_NODES for this app.
        Uses the same CPM threshold as full discovery.

        Returns:
            Dict with tiers_count, nodes_count, active_nodes_count
        """
        logger.info(f"[RefreshCPM] Refreshing nodes for app: {app_name}")

        tiers_count = 0
        nodes_count = 0
        active_nodes_count = 0

        try:
            # Get application from AppD to confirm it still exists
            app_data = self.client.get_application(app_name)
            if not app_data:
                logger.warning(f"[RefreshCPM] Application not found in AppD: {app_name}")
                return {'tiers_count': 0, 'nodes_count': 0, 'active_nodes_count': 0}

            # FIX: Handle list vs dict (same pattern as discover_application)
            if isinstance(app_data, list):
                app_data = app_data[0] if len(app_data) > 0 else {}

            app_id_appd = app_data.get('id')
            if not app_id_appd:
                logger.warning(f"[RefreshCPM] Could not get App ID for: {app_name}")
                return {'tiers_count': 0, 'nodes_count': 0, 'active_nodes_count': 0}

            # Get all tiers from AppD for this application
            tiers = self.client.get_tiers(app_name)
            if not tiers or not isinstance(tiers, list):
                logger.warning(f"[RefreshCPM] No tiers found for: {app_name}")
                return {'tiers_count': 0, 'nodes_count': 0, 'active_nodes_count': 0}

            for tier in tiers:
                if not isinstance(tier, dict):
                    continue

                tier_name = tier.get('name')
                if not tier_name:
                    continue

                tiers_count += 1

                # Get all nodes from AppD for this tier
                nodes = self.client.get_nodes(app_name, tier_name)
                if not nodes or not isinstance(nodes, list):
                    continue

                for node in nodes:
                    if not isinstance(node, dict):
                        continue

                    node_name = node.get('name')
                    node_id_appd = node.get('id')
                    if not node_name or not node_id_appd:
                        continue

                    try:
                        # Get fresh CPM from AppD
                        cpm = self.client.get_calls_per_minute(
                            app_name,
                            tier_name,
                            node_name,
                            self.config.APPD_DISCOVERY_LOOKBACK_MINUTES,
                        )
                        if cpm is None or not isinstance(cpm, (int, float)):
                            cpm = 0

                        # Re-classify: same threshold as full discovery
                        is_active = (
                            'ACTIVE'
                            if cpm >= self.config.APPD_ACTIVE_NODE_CPM_THRESHOLD
                            else 'INACTIVE'
                        )

                        nodes_count += 1
                        if is_active == 'ACTIVE':
                            active_nodes_count += 1

                        # Update ONLY cpm + is_active — do NOT touch tier/node structure
                        self.db.update_node_cpm(
                            lob_id=lob_id,
                            app_name=app_name,
                            tier_name=tier_name,
                            node_name=node_name,
                            calls_per_minute=cpm,
                            is_active=is_active,
                        )

                        logger.info(
                            f"[RefreshCPM] Node {node_name}: "
                            f"CPM={cpm:.2f}, Status={is_active}"
                        )

                    except Exception as e:
                        logger.error(
                            f"[RefreshCPM] Failed to refresh node {node_name}: {e}",
                            exc_info=True
                        )
                        continue

        except Exception as e:
            logger.error(f"[RefreshCPM] Failed for app {app_name}: {e}", exc_info=True)

        return {
            'tiers_count': tiers_count,
            'nodes_count': nodes_count,
            'active_nodes_count': active_nodes_count,
        }


# =============================================================================
# FILE 3: Add to monitoring/appd/database.py  (AppDynamicsDatabase)
# =============================================================================
# Add this method inside the AppDynamicsDatabase class:

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
        Matches by lob_id + app_name + tier_name + node_name.
        Does NOT insert — if node doesn't exist, silently skips.
        """
        sql = """
            UPDATE API_APPD_NODES
               SET CALLS_PER_MINUTE  = :cpm,
                   IS_ACTIVE         = :is_active,
                   LAST_UPDATED      = SYSDATE
             WHERE LOB_ID = :lob_id
               AND NODE_NAME  = :node_name
               AND TIER_NAME  = (
                       SELECT t.TIER_NAME
                         FROM API_APPD_TIERS t
                        WHERE t.LOB_ID    = :lob_id
                          AND t.TIER_NAME = :tier_name
                          AND t.APP_ID    IN (
                              SELECT a.APP_ID
                                FROM API_APPD_APPLICATIONS a
                               WHERE a.LOB_ID           = :lob_id
                                 AND a.APPLICATION_NAME = :app_name
                          )
                   )
        """
        # Simpler alternative if your schema stores app_name directly on nodes:
        sql_simple = """
            UPDATE API_APPD_NODES n
               SET n.CALLS_PER_MINUTE = :cpm,
                   n.IS_ACTIVE        = :is_active,
                   n.LAST_UPDATED     = SYSDATE
             WHERE n.LOB_ID    = :lob_id
               AND n.NODE_NAME = :node_name
               AND n.TIER_NAME = :tier_name
        """
        # NOTE: Use sql_simple if APPD_NODES has TIER_NAME + LOB_ID directly.
        # Use the subquery version if you need to join through APPD_TIERS.
        # Check your schema — pick whichever matches.

        try:
            with self.connection_pool.acquire() as conn:
                cursor = conn.cursor()
                cursor.execute(sql_simple, {
                    'cpm':       calls_per_minute,
                    'is_active': is_active,
                    'lob_id':    lob_id,
                    'node_name': node_name,
                    'tier_name': tier_name,
                })
                updated_rows = cursor.rowcount
                conn.commit()
                if updated_rows == 0:
                    logger.warning(
                        f"[UpdateNodeCPM] Node not found in DB — skipping: "
                        f"{app_name}/{tier_name}/{node_name}"
                    )
                return updated_rows > 0
        except Exception as e:
            logger.error(f"[UpdateNodeCPM] DB error: {e}", exc_info=True)
            raise


# =============================================================================
# SUMMARY — What to add where
# =============================================================================
#
# routes.py:
#   + class UpdateNodesRequest(BaseModel)          ← request model
#   + POST /discovery/update-nodes endpoint        ← calls background task
#   + async execute_update_nodes_task(...)         ← background worker
#
# discovery.py (AppDynamicsDiscoveryService):
#   + def refresh_node_cpm(self, ...)              ← fetches CPM, calls update_node_cpm
#
# database.py (AppDynamicsDatabase):
#   + def update_node_cpm(self, ...)               ← single UPDATE SQL, no INSERT
#
# NO changes needed to:
#   - main.py
#   - collectors.py
#   - orchestrator.py
#   - Any other file
#
# The endpoint response shape matches what the frontend expects:
# {
#   "success": true,
#   "active_nodes": N,    ← from stats after background task completes
#   "inactive_nodes": N,
# }
# NOTE: Since it runs in background, the immediate response returns task_id.
# The frontend polls or waits — same as run_discovery.
# If you want synchronous response, remove background_tasks and await directly.
# =============================================================================
