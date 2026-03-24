# ============================================================
# HOW TO ADD TO YOUR EXISTING main.py
# Add these lines in the correct locations — do NOT replace
# your existing main.py, just insert the marked blocks.
# ============================================================

# ── 1. IMPORT (add near top with other router imports) ──────
from reports.routes import router as reports_router, init_reports_routes


# ── 2. REGISTER ROUTER (add with other app.include_router calls) ──
app.include_router(reports_router, prefix="/api/v1")
# Result: endpoints available at /api/v1/reports/save
#                                /api/v1/reports/list
#                                /api/v1/reports/view/{report_id}
#                                /api/v1/reports/{report_id}  (DELETE)


# ── 3. INITIALISE on startup (add inside your @app.on_event("startup") handler) ──
@app.on_event("startup")
async def startup():
    # ... your existing startup code ...

    # Add this line — uses the same CQE_NFT pool as the rest of monitoring
    pool = connection_manager.get_pool('CQE_NFT')
    init_reports_routes(pool)


# ============================================================
# FOLDER STRUCTURE — create reports/ alongside monitoring/
# ============================================================
# app/
# ├── main.py
# ├── monitoring/
# │   ├── appd/
# │   ├── awr/
# │   └── pc/
# └── reports/             ← NEW
#     ├── __init__.py
#     ├── database.py
#     └── routes.py
# ============================================================
