"""
============================================================
MAIN.PY ADDITIONS — CQE NFT Platform Integration
============================================================
This file shows EXACTLY what to add to your existing main.py.
It is NOT a replacement — it is a targeted diff.

Search for each "FIND THIS" block in your main.py and
add the corresponding "ADD THIS" block immediately after/before.
============================================================
"""

# ============================================================
# STEP 1 — ADD IMPORT (after existing monitoring imports)
# ============================================================
# FIND THIS in your main.py:
#   from monitoring.pc.routes import router as pc_router, init_pc_routes
#   from monitoring.awr.routes import router as awr_router, init_awr_routes
#
# ADD THIS immediately after:
#
#   from monitoring.nft.routes import router as nft_router, init_nft_routes
#
# ============================================================


# ============================================================
# STEP 2 — REGISTER ROUTER (after existing app.include_router calls)
# ============================================================
# FIND THIS in your main.py:
#   app.include_router(
#       auth_router,
#       prefix="/api/v1/auth",
#       tags=["Authentication"]
#   )
#
# ADD THIS immediately after (before the startup event):
#
#   app.include_router(
#       nft_router,
#       prefix="/api/v1/nft",
#       tags=["NFT Platform"]
#   )
#
# ============================================================


# ============================================================
# STEP 3 — INITIALIZE IN STARTUP EVENT
# ============================================================
# FIND THIS in your @app.on_event("startup") function:
#   # Initialize AppDynamics monitoring
#   print("\nInitializing AppDynamics monitoring...", flush=True)
#   try:
#       oracle_pool = app.state.connection_manager.get_pool('CQE_NFT')
#       if oracle_pool:
#           initialize_appd_components(oracle_pool.pool)
#           init_pc_routes(oracle_pool.pool)
#           init_awr_routes(oracle_pool.pool)
#           print("✓ AppDynamics, Performance Center & AWR monitoring initialized", flush=True)
#       else:
#           print("⚠ Oracle pool not available for AppDynamics", flush=True)
#   except Exception as e:
#       print(f"✗ AppDynamics initialization failed: {e}", flush=True)
#
# REPLACE that block with (just add init_nft_routes to the try block):
#
#   print("\nInitializing AppDynamics monitoring...", flush=True)
#   try:
#       oracle_pool = app.state.connection_manager.get_pool('CQE_NFT')
#       if oracle_pool:
#           initialize_appd_components(oracle_pool.pool)
#           init_pc_routes(oracle_pool.pool)
#           init_awr_routes(oracle_pool.pool)
#           init_nft_routes(oracle_pool.pool)           # <-- ADD THIS LINE
#           print("✓ AppDynamics, PC, AWR & NFT Platform initialized", flush=True)
#       else:
#           print("⚠ Oracle pool not available", flush=True)
#   except Exception as e:
#       import traceback
#       print(f"✗ Initialization failed: {e}", flush=True)
#       traceback.print_exc(file=sys.stdout)
#
# ============================================================


# ============================================================
# STEP 4 — HEALTH CHECK (add to existing health endpoints)
# ============================================================
# FIND THIS in your main.py (near the other health checks):
#   @app.get("/api/health/test", tags=["Health"])
#   async def health_check_test():
#       """Test health check"""
#       return {"status": "ok", "service": "test"}
#
# ADD THIS immediately after:
#
#   @app.get("/api/health/nft", tags=["Health"])
#   async def health_check_nft():
#       """NFT Platform health check"""
#       from monitoring.nft.routes import nft_db
#       if nft_db:
#           return {"status": "ok", "service": "nft_platform"}
#       return {"status": "degraded", "service": "nft_platform",
#               "message": "Database not initialized"}
#
# ============================================================


# ============================================================
# COMPLETE STARTUP SECTION FOR REFERENCE
# ============================================================
# After all additions, your startup section should look like:
#
# @app.on_event("startup")
# async def startup_event():
#     """Assign pre-initialized objects to app.state"""
#     print("FastAPI startup: Assigning app.state", flush=True)
#
#     app.state.settings           = _settings
#     app.state.connection_manager = _connection_manager
#     app.state.security_managers  = _security_managers
#     app.state.audit_logger       = _audit_logger
#     app.state.sql_executors      = _sql_executors
#
#     # Initialize AppDynamics / PC / AWR / NFT
#     print("\nInitializing monitoring components...", flush=True)
#     try:
#         oracle_pool = app.state.connection_manager.get_pool('CQE_NFT')
#         if oracle_pool:
#             initialize_appd_components(oracle_pool.pool)
#             init_pc_routes(oracle_pool.pool)
#             init_awr_routes(oracle_pool.pool)
#             init_nft_routes(oracle_pool.pool)           # <-- NFT Platform
#             print("✓ AppDynamics, PC, AWR & NFT Platform initialized", flush=True)
#         else:
#             print("⚠ Oracle pool not available", flush=True)
#     except Exception as e:
#         import traceback
#         print(f"✗ Initialization failed: {e}", flush=True)
#         traceback.print_exc(file=sys.stdout)
#
#
# ============================================================
# ROUTER REGISTRATION — final order in main.py:
# ============================================================
#
#   app.include_router(pc_router,  prefix="/api/v1/monitoring/pc",   tags=["Performance Center"])
#   app.include_router(awr_router, prefix="/api/v1/monitoring",       tags=["AWR Analysis"])
#   app.include_router(auth_router, prefix="/api/v1/auth",            tags=["Authentication"])
#   app.include_router(nft_router,  prefix="/api/v1/nft",             tags=["NFT Platform"])
#                      ^^^^^^^^^^   ^^^^^^^^^^^^^^^^                   ^^^^^^^^^^^^^^^^^^^^
#                      ADD THIS
#
# ============================================================
# COMPLETE API ENDPOINT LIST AFTER INTEGRATION:
# ============================================================
#
# NFT PLATFORM — /api/v1/nft/
#
# User LOB Access:
#   GET    /api/v1/nft/user-lob-access                         List all users + LOBs
#   GET    /api/v1/nft/user-lob-access/{username}              Get user LOBs
#   POST   /api/v1/nft/user-lob-access/grant                   Grant LOB access
#   POST   /api/v1/nft/user-lob-access/revoke                  Revoke LOB access
#
# Tool Configs:
#   POST   /api/v1/nft/config/appd                             Save AppD config
#   GET    /api/v1/nft/config/appd/{lob_name}                  Get AppD config
#
#   POST   /api/v1/nft/config/kibana                           Add Kibana dashboard
#   GET    /api/v1/nft/config/kibana/{lob_name}                List Kibana configs
#   POST   /api/v1/nft/config/kibana/test-connection           Test Kibana
#   DELETE /api/v1/nft/config/kibana/{id}                      Delete Kibana config
#
#   POST   /api/v1/nft/config/splunk                           Add Splunk search
#   GET    /api/v1/nft/config/splunk/{lob_name}                List Splunk configs
#   POST   /api/v1/nft/config/splunk/test-connection/{id}      Test Splunk
#   DELETE /api/v1/nft/config/splunk/{id}                      Delete Splunk config
#
#   POST   /api/v1/nft/config/mongodb                          Add MongoDB collection
#   GET    /api/v1/nft/config/mongodb/{lob_name}               List MongoDB configs
#   POST   /api/v1/nft/config/mongodb/test-connection/{id}     Test MongoDB
#   DELETE /api/v1/nft/config/mongodb/{id}                     Delete MongoDB config
#
#   POST   /api/v1/nft/config/pc                               Add PC project config
#   GET    /api/v1/nft/config/pc/{lob_name}                    List PC configs
#   POST   /api/v1/nft/config/pc/test-connection/{id}          Test PC connection
#   DELETE /api/v1/nft/config/pc/{id}                          Delete PC config
#
#   POST   /api/v1/nft/config/db                               Add DB config
#   GET    /api/v1/nft/config/db/{lob_name}                    List DB configs
#   POST   /api/v1/nft/config/db/test-connection/{id}          Test DB connection
#   DELETE /api/v1/nft/config/db/{id}                          Delete DB config
#
# Track Template:
#   POST   /api/v1/nft/track-template                          Save/update template
#   GET    /api/v1/nft/track-template/{lob_name}               List templates for LOB
#   GET    /api/v1/nft/track-template/{lob_name}/{track}       Get specific template
#   DELETE /api/v1/nft/track-template/{lob_name}/{track}       Delete template
#
# Test Registration:
#   POST   /api/v1/nft/test-registration                       Register new test
#   GET    /api/v1/nft/test-registration/recent                Recent registrations
#   GET    /api/v1/nft/test-registration/{run_id}              Get by run ID
#
# Release Reports:
#   POST   /api/v1/nft/release-reports                         Save HTML report
#   GET    /api/v1/nft/release-reports/{lob_name}              List reports (no HTML)
#   GET    /api/v1/nft/release-reports/view/{report_id}        View full HTML report
#
# Health:
#   GET    /api/health/nft                                     NFT platform health
#
# ============================================================
