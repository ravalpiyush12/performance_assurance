CQE NFT PLATFORM — v3 Complete Build
======================================

FRONTEND — Replace these 6 files (no restart needed):
  admin/user-management.html  — fully wired: create/edit/delete/toggle/reset MFA
  admin/appd-config.html      — new design: connection + discovery batch + node view
  admin/kibana-config.html    — token OR username/password auth, save+test dashboards
  admin/track-management.html — loads real configs, save templates to API
  monitoring/login.html       — QR code on demand, fixed forgot password
  monitoring/pre-login.html   — no more 401 spam, static LOB list

BACKEND — Add to existing code (restart uvicorn after):
  backend/monitoring/nft/database.py  — replace (get_connection→acquire + new methods)
  backend/monitoring/nft/routes.py    — replace (revoke-all endpoint added)
  backend/appd_scheduler_additions.py — follow instructions inside to add:
    1. pip install apscheduler>=3.10.0
    2. Daily 2AM AppD discovery batch (AsyncIOScheduler)
    3. POST /appd/discovery/trigger-batch  (manual trigger)
    4. POST /appd/tier-threshold           (save expected node count)
    5. GET  /appd/active-nodes             (fetch discovered nodes for UI)
    6. GET  /appd/master-applications      (fetch apps for track template dropdowns)

SQL — If not already run:
  ALTER TABLE API_APPD_LOB_CONFIG ADD (AUTH_TYPE VARCHAR2(20), USERNAME VARCHAR2(200), PASS_ENV_VAR VARCHAR2(200));
  Run this before restarting backend.
