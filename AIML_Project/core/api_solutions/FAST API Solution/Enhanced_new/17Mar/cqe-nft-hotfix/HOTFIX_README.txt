HOTFIX - 5 bugs from first login test
======================================
BACKEND (restart uvicorn after replacing):
  monitoring/nft/database.py  - get_connection() -> acquire() (35 fixes) + 5 new methods
  monitoring/nft/routes.py    - POST /user-lob-access/revoke-all added

FRONTEND (no restart needed):
  pages/monitoring/login.html       - totp_code null fixed
  pages/admin/user-management.html - role update non-blocking

PERMANENT FIX for ORA-00904 UPDATED_BY:
  In authentication_fixed.py update_user_role(), remove UPDATED_BY
  from the UPDATE SQL. API_AUTH_USERS has no UPDATED_BY column.
