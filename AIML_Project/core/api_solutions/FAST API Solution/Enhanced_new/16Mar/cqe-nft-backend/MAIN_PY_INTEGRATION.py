# =============================================================================
# main.py INTEGRATION — ADD THESE LINES TO YOUR EXISTING main.py
# =============================================================================
# All additions follow the exact same pattern as your existing appd/pc/awr routes.
# Only 3 places to edit in main.py:
#   1. Imports section (top of file)
#   2. startup event (inside @app.on_event("startup"))
#   3. Router registration (after existing app.include_router calls)
# =============================================================================


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: ADD TO IMPORTS SECTION
# Place alongside existing monitoring imports:
#   from monitoring.appd.routes import router as appd_router, initialize_appd_components
#   from monitoring.pc.routes import router as pc_router, init_pc_routes
#   from monitoring.awr.routes import router as awr_router, init_awr_routes
# ─────────────────────────────────────────────────────────────────────────────

from monitoring.nft.routes import router as nft_router, init_nft_routes


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: ADD TO STARTUP EVENT
# Inside your existing @app.on_event("startup") async def startup_event():
# Place after init_awr_routes(oracle_pool.pool) line:
# ─────────────────────────────────────────────────────────────────────────────

# Initialize NFT Platform routes
print("\nInitializing NFT Platform routes...", flush=True)
try:
    oracle_pool = app.state.connection_manager.get_pool('CQE_NFT')
    if oracle_pool:
        init_nft_routes(oracle_pool.pool)
        print("✓ NFT Platform routes initialized", flush=True)
    else:
        print("⚠ Oracle pool not available for NFT Platform", flush=True)
except Exception as e:
    print(f"✗ NFT Platform initialization failed: {e}", flush=True)
    import traceback
    traceback.print_exc(file=sys.stdout)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: ADD ROUTER REGISTRATION
# Place alongside existing app.include_router calls:
#   app.include_router(appd_router, prefix="/api/v1/monitoring/appd", ...)
#   app.include_router(pc_router,   prefix="/api/v1/monitoring/pc",   ...)
#   app.include_router(awr_router,  prefix="/api/v1/monitoring",      ...)
# ─────────────────────────────────────────────────────────────────────────────

app.include_router(
    nft_router,
    prefix="/api/v1/nft",
    tags=["NFT Platform"]
)


# =============================================================================
# COMPLETE API ENDPOINT REFERENCE AFTER INTEGRATION
# =============================================================================
#
# USER LOB ACCESS
#   POST   /api/v1/nft/user-lob-access/grant
#   POST   /api/v1/nft/user-lob-access/revoke
#   GET    /api/v1/nft/user-lob-access/{username}
#   GET    /api/v1/nft/user-lob-access?lob_name=
#
# APPD CONFIG
#   POST   /api/v1/nft/config/appd
#   GET    /api/v1/nft/config/appd/{lob_name}/{track}
#   DELETE /api/v1/nft/config/appd/{config_id}?updated_by=
#   POST   /api/v1/nft/config/appd/{config_id}/test-connection
#
# KIBANA CONFIG
#   POST   /api/v1/nft/config/kibana
#   GET    /api/v1/nft/config/kibana/{lob_name}/{track}
#   DELETE /api/v1/nft/config/kibana/{config_id}?updated_by=
#   POST   /api/v1/nft/config/kibana/{config_id}/test-connection
#
# SPLUNK CONFIG
#   POST   /api/v1/nft/config/splunk
#   GET    /api/v1/nft/config/splunk/{lob_name}/{track}
#   DELETE /api/v1/nft/config/splunk/{config_id}?updated_by=
#   POST   /api/v1/nft/config/splunk/{config_id}/test-connection
#
# MONGODB CONFIG
#   POST   /api/v1/nft/config/mongodb
#   GET    /api/v1/nft/config/mongodb/{lob_name}/{track}
#   DELETE /api/v1/nft/config/mongodb/{config_id}?updated_by=
#   POST   /api/v1/nft/config/mongodb/{config_id}/test-connection
#
# PC CONFIG
#   POST   /api/v1/nft/config/pc
#   GET    /api/v1/nft/config/pc/{lob_name}/{track}
#   DELETE /api/v1/nft/config/pc/{config_id}?updated_by=
#   POST   /api/v1/nft/config/pc/{config_id}/test-connection
#
# DB (ORACLE AWR TARGET) CONFIG
#   POST   /api/v1/nft/config/db
#   GET    /api/v1/nft/config/db/{lob_name}/{track}
#   DELETE /api/v1/nft/config/db/{config_id}?updated_by=
#   POST   /api/v1/nft/config/db/{config_id}/test-connection
#
# TRACK TEMPLATES
#   POST   /api/v1/nft/track-template
#   GET    /api/v1/nft/track-template/{lob_name}/{track}
#   GET    /api/v1/nft/track-template?lob_name=
#   DELETE /api/v1/nft/track-template/{lob_name}/{track}?updated_by=
#
# RELEASE REPORTS
#   POST   /api/v1/nft/release-reports
#   GET    /api/v1/nft/release-reports?lob_name=&limit=
#   GET    /api/v1/nft/release-reports/{report_id}
#   GET    /api/v1/nft/release-reports/{report_id}/view    ← HTMLResponse
#
# =============================================================================
