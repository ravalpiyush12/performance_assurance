# =============================================================================
# FIX: routes.py — execute_update_nodes_task
# Error: create_discovery_log() takes 2 positional arguments but 4 were given
#
# Your existing create_discovery_log signature is:
#   def create_discovery_log(self, lob_id, config_name)   ← only 2 args
#
# I passed 4: (lob_id, lob_name, config_name) — WRONG
# Fix: match your existing signature exactly
# =============================================================================

async def execute_update_nodes_task(
    task_id: str,
    lob_id: int,
    lob_name: str,
    config_name: str,
    applications: List[str],
):
    """Background task: refresh CPM + re-classify active/inactive for existing nodes."""
    # FIX: only pass lob_id and config_name — matches your existing signature
    log_id = appd_db.create_discovery_log(lob_id, config_name)
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
# Also check execute_discovery_task in your existing routes.py —
# it likely calls create_discovery_log the same way.
# Make sure all calls match: appd_db.create_discovery_log(lob_id, config_name)
# =============================================================================
