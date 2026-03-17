"""
MAIN.PY ADDITIONS — Kibana monitoring module
============================================
Add these to your existing main.py in 3 places.
"""

# STEP 1 — Add import (alongside existing monitoring imports)
# ---------------------------------------------------------------------------
from monitoring.kibana.routes import router as kibana_router, init_kibana_routes

# STEP 2 — Register router (alongside appd_router, pc_router, awr_router)
# ---------------------------------------------------------------------------
app.include_router(kibana_router, prefix="/api/v1/monitoring", tags=["Kibana Monitoring"])

# STEP 3 — Initialize in startup (alongside init_appd_components, init_pc_routes, init_awr_routes)
# ---------------------------------------------------------------------------
# In your @app.on_event("startup") function, inside the try block, add:
init_kibana_routes(oracle_pool.pool)
logger.info("✓ Kibana monitoring routes initialized")

# STEP 4 — Health check (optional, alongside existing health checks)
# ---------------------------------------------------------------------------
@app.get("/api/health/kibana", tags=["Health"])
async def health_check_kibana():
    """Kibana monitoring health check."""
    from monitoring.kibana.routes import kibana_db
    if kibana_db:
        return {"status": "ok", "service": "kibana_monitoring"}
    return {"status": "degraded", "service": "kibana_monitoring",
            "detail": "Kibana DB not initialized"}


# =============================================================================
# SUMMARY OF ALL ROUTES AFTER ADDING KIBANA:
# =============================================================================
# /api/v1/monitoring/appd/*     ← existing AppDynamics
# /api/v1/monitoring/awr/*      ← existing AWR
# /api/v1/monitoring/pc/*       ← existing PC
# /api/v1/monitoring/kibana/test-connection   ← NEW
# /api/v1/monitoring/kibana/fetch             ← NEW
# /api/v1/monitoring/kibana/metrics/{run_id}  ← NEW
# /api/v1/monitoring/kibana/metrics/{run_id}/summary ← NEW
# /api/v1/monitoring/appd/metrics/{run_id}    ← NEW (from appd_routes_additions)
# /api/v1/monitoring/appd/metrics/{run_id}/summary ← NEW
# /api/v1/monitoring/appd/nodes/{run_id}      ← NEW
# /api/v1/nft/*                 ← existing NFT platform
# =============================================================================
