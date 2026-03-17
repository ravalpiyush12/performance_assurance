LOB Access Column Name Fix (from DESCRIBE output)
===================================================

ROOT CAUSE:
  API_NFT_USER_LOB_ACCESS actual columns:
    ACCESS_ID (NUMBER, needs API_NFT_ULA_SEQ)
    GRANTED_DATE (not CREATED_DATE)
    REVOKED_BY, REVOKED_DATE (new columns we missed)

STEP 1 — SQL (run first in SQL Developer):
  sql/backfill_user_lob_access_v2.sql
    Creates API_NFT_ULA_SEQ if missing
    Grants ALL LOBs to all users with zero LOB access
    Uses correct column names throughout

STEP 2 — Backend (restart uvicorn after):
  backend/part1_authentication_fixed_v2.py
    Replace create_user() in Auth/authentication_fixed.py
    Uses ACCESS_ID/API_NFT_ULA_SEQ, GRANTED_DATE, REVOKED_BY/DATE

  backend/monitoring/nft/database.py
    Replace grant_user_lob_access() — correct INSERT/UPDATE columns
    Replace revoke — adds REVOKED_BY, REVOKED_DATE

  backend/monitoring/nft/routes.py
    revoke-all endpoint — adds REVOKED_BY, REVOKED_DATE
