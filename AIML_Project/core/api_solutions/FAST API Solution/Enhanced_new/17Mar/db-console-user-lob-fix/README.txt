DB Console + User Management LOB Filter Fix
=============================================

FRONTEND (no restart):
  admin/db-console.html
    - Uses GET /api/v1/admin/db-health (Bearer auth, no API key in browser)
    - Uses POST /api/v1/admin/db-execute (Bearer auth, server selects API key)
    - Shows real connect status + error reason + server time
    - Multi-statement SQL split by ; with per-statement result

  admin/user-management.html
    - Filters users by selected LOB from sessionStorage
    - Shows count: '3 users for Digital Technology (12 total)'
    - 'Show all users' link to bypass filter
    - Loads real LOB assignments per user from API_NFT_USER_LOB_ACCESS

BACKEND (restart uvicorn after):
  backend/admin_db_endpoints.py
    Paste both endpoints into main.py:
    - GET  /api/v1/admin/db-health  (proxy health check, Bearer auth)
    - POST /api/v1/admin/db-execute (proxy SQL execute, Bearer auth)
    These use server-side pool — no API keys exposed to browser.

SQL (run once in SQL Developer):
  alter_user_lob_access.sql
    Creates view V_AUTH_USERS_WITH_LOB
    Joins API_AUTH_USERS + API_NFT_USER_LOB_ACCESS
    Optional but useful for admin queries.
