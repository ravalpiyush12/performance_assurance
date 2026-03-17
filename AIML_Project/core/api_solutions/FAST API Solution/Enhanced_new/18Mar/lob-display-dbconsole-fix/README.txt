LOB Display Fix + DB Console Improvements
==========================================

ROOT CAUSE of LOB showing 'ALL':
  database.py get_user_lob_access() was querying 'ID' and 'CREATED_DATE'
  but actual table has 'ACCESS_ID' and 'GRANTED_DATE' → returned empty rows
  Frontend saw empty LOB list → fell back to showing 'ALL'

FRONTEND (no restart):
  admin/user-management.html
    Fetches LOB access per-user concurrently using Promise.allSettled
    Correctly reads lob_access[].lob_name from response
    Shows actual LOB names e.g. 'Digital Technology, Payments'

  admin/db-console.html
    API Key shown (read-only, first 6 chars + masked)
    Warning shown if selected DB is read-only (DQL only)
    Upload SQL button — load .sql file into editor, then click Execute
    Multi-statement execution works as before

BACKEND (restart uvicorn after):
  monitoring/nft/database.py
    get_user_lob_access() fixed: ACCESS_ID, GRANTED_DATE
    list_users_with_lob_access() fixed: ACCESS_ID
    grant/revoke already fixed in previous zip
