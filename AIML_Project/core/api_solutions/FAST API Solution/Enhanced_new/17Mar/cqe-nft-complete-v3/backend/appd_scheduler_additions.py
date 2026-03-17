"""
APPD SCHEDULER ADDITIONS
=========================
Add these to main.py to run AppD discovery daily via FastAPI background scheduler.

Uses APScheduler (add to requirements.txt: apscheduler>=3.10.0)
"""

# ─── STEP 1: Add to requirements.txt ─────────────────────────────────────────
# apscheduler>=3.10.0

# ─── STEP 2: Add imports to main.py ──────────────────────────────────────────
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

scheduler = AsyncIOScheduler()

# ─── STEP 3: Add this function to main.py ─────────────────────────────────────
async def run_daily_appd_discovery():
    """
    Daily batch: runs AppD discovery for ALL active LOBs.
    Fetches apps/tiers/nodes from AppD API.
    Marks nodes active/inactive based on CPM threshold.
    Scheduled at 2:00 AM daily.
    """
    logger = logging.getLogger("scheduler")
    logger.info("=" * 60)
    logger.info("DAILY APPD DISCOVERY BATCH STARTING")
    logger.info("=" * 60)

    try:
        from monitoring.appd.database import AppDynamicsDatabase
        from monitoring.appd.orchestrator import DiscoveryOrchestrator

        oracle_pool = app.state.connection_manager.get_pool('CQE_NFT')
        if not oracle_pool:
            logger.error("Oracle pool not available — skipping batch")
            return

        appd_database = AppDynamicsDatabase(connection_pool=oracle_pool.pool)

        # Get all active LOB configs
        configs = appd_database.list_configs(active_only=True)
        logger.info(f"Found {len(configs)} active AppD configs")

        for config in configs:
            config_name = config.get('config_name')
            lob_name = config.get('lob_name')
            logger.info(f"Running discovery for: {config_name} ({lob_name})")
            try:
                # Use existing DiscoveryOrchestrator — it handles everything
                orchestrator = DiscoveryOrchestrator(oracle_pool.pool)
                result = await orchestrator.run_discovery(
                    config_name=config_name,
                    triggered_by='scheduler'
                )
                logger.info(
                    f"  ✓ {config_name}: {result.get('nodes_discovered', 0)} nodes, "
                    f"{result.get('active_nodes', 0)} active"
                )
            except Exception as e:
                logger.error(f"  ✗ {config_name} failed: {e}", exc_info=True)

        logger.info("DAILY APPD DISCOVERY BATCH COMPLETE")

    except Exception as e:
        logger.error(f"Daily batch error: {e}", exc_info=True)


# ─── STEP 4: Add to startup event in main.py ─────────────────────────────────
# Inside @app.on_event("startup"), after existing init code, add:

scheduler.add_job(
    run_daily_appd_discovery,
    CronTrigger(hour=2, minute=0),     # 2:00 AM daily
    id='daily_appd_discovery',
    replace_existing=True,
    misfire_grace_time=3600            # Allow up to 1hr late start
)
scheduler.start()
logger.info("✓ AppD discovery scheduler started (daily @ 2:00 AM)")


# ─── STEP 5: Add to shutdown event in main.py ────────────────────────────────
# Inside @app.on_event("shutdown"), add:
scheduler.shutdown()


# ─── STEP 6: Add manual trigger endpoint ─────────────────────────────────────
# Add to main.py or appd/routes.py:

@app.post("/api/v1/monitoring/appd/discovery/trigger-batch", tags=["AppDynamics"])
async def trigger_appd_batch(current_user: dict = Depends(verify_auth_token)):
    """Manually trigger AppD discovery for all LOBs (admin only)."""
    import asyncio
    asyncio.create_task(run_daily_appd_discovery())
    return {"success": True, "message": "Discovery batch started in background"}


# ─── STEP 7: Add tier threshold endpoint to appd/routes.py ───────────────────
# (Saves expected node count per tier — used by config UI after discovery)

@router.post("/tier-threshold")
async def save_tier_threshold(
    request: dict,
    current_user: str = Depends(verify_auth_token)
):
    """Save expected active node count for a tier (admin override)."""
    if not appd_db:
        raise HTTPException(status_code=503, detail="Service not initialized")
    try:
        lob_name = request.get('lob_name')
        application_name = request.get('application_name')
        tier_name = request.get('tier_name')
        expected_nodes = int(request.get('expected_nodes', 1))

        # Update ACTIVE_THRESHOLD in API_APPD_TIERS
        with appd_db.connection_pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE API_APPD_TIERS t
                    SET ACTIVE_THRESHOLD = :threshold,
                        UPDATED_DATE = SYSDATE
                    WHERE TIER_NAME = :tier_name
                      AND APP_ID IN (
                          SELECT APP_ID FROM API_APPD_APPLICATIONS
                          WHERE APPLICATION_NAME = :app_name
                            AND LOB_ID IN (
                                SELECT LOB_ID FROM API_APPD_LOB_CONFIG
                                WHERE LOB_NAME = :lob_name AND IS_ACTIVE = 'Y'
                            )
                      )
                """, {
                    'threshold': expected_nodes,
                    'tier_name': tier_name,
                    'app_name': application_name,
                    'lob_name': lob_name,
                })
                updated = cursor.rowcount
                conn.commit()
                return {
                    "success": True,
                    "updated_rows": updated,
                    "tier_name": tier_name,
                    "expected_nodes": expected_nodes,
                }
            finally:
                cursor.close()

    except Exception as e:
        logger.error(f"Tier threshold error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── STEP 8: Add active nodes endpoint to appd/routes.py ─────────────────────

@router.get("/active-nodes")
async def get_active_nodes(
    lob_name: str = Query(...),
    current_user: str = Depends(verify_auth_token)
):
    """Get all discovered active/inactive nodes for a LOB (for config UI)."""
    if not appd_db:
        raise HTTPException(status_code=503, detail="Service not initialized")
    try:
        # Get config name for this LOB
        config = appd_db.get_lob_config(lob_name)
        if not config:
            return {"success": True, "nodes": [], "message": "No config found"}

        config_name = config.get('config_name') or lob_name
        nodes = appd_db.get_active_nodes_for_lob(lob_name, config_name)
        return {"success": True, "nodes": nodes, "total": len(nodes),
                "active": sum(1 for n in nodes if n.get('is_active') == 'Y')}
    except Exception as e:
        logger.error(f"Get active nodes error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── STEP 9: Add master applications endpoint ────────────────────────────────

@router.get("/master-applications")
async def get_master_applications(
    lob_name: str = Query(None),
    track: str = Query(None),
    current_user: str = Depends(verify_auth_token)
):
    """Get applications from APPD_APPLICATIONS_MASTER filtered by LOB/Track."""
    if not appd_db:
        raise HTTPException(status_code=503, detail="Service not initialized")
    try:
        apps = appd_db.get_master_applications(lob_name=lob_name, track=track)
        return {"success": True, "applications": apps, "total": len(apps)}
    except Exception as e:
        logger.error(f"Get master applications error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
