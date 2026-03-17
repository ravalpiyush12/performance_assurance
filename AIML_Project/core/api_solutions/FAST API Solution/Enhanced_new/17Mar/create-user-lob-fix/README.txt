Auto LOB Grant on User Creation — Deep Fix
============================================

STEP 1 — Run SQL (immediate fix for existing users):
  sql/backfill_user_lob_access.sql
  Grants ALL active LOBs to every user who currently has ZERO LOB access.
  Safe to re-run (uses MERGE). Fixes admin + any other existing users.

STEP 2 — Backend fix (restart uvicorn after):
  backend/part1_authentication_fixed.py
    Replace create_user() in Auth/authentication_fixed.py
    Now auto-grants LOBs inside same transaction as user creation.
    lob_names=None → grants ALL active LOBs from API_LOB_MASTER
    lob_names=['X','Y'] → grants only those specific LOBs
    Uses MERGE so it is safe to call multiple times

  backend/part2_routes_fixed.py
    1-line change in POST /create-user endpoint
    Pass lob_names from request body to create_user()

RESULT:
  Every new user created via Admin UI or API will automatically get
  LOB access in API_NFT_USER_LOB_ACCESS in the same DB transaction.
  If the LOB grant fails for any reason, it logs a warning but
  does NOT roll back the user creation.
