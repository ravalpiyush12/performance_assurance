FIXES: User Management + DB Console
=====================================

FRONTEND — replace these files (no restart):
  admin/user-management.html
    - LOB chips now load from /lob-config/public (shows all real LOBs)
    - Reset Password button added per user
    - Reset MFA button label corrected

  admin/db-console.html
    - DB health from GET /api/v1/{db}/health (real status + error reason)
    - DB list from GET /api/v1/databases
    - SQL console: select DB → API key auto-shown (masked)
    - Multiple statements split by ; — each executed individually
    - Each statement shows: rows returned / rows affected / error message
    - Summary: X succeeded, Y failed
    - Export CSV button for SELECT results

BACKEND — add these to Auth/routes_fixed.py (restart uvicorn after):
  reset_password_endpoint.py
    Paste AFTER the reset_user_totp endpoint
    New: POST /api/v1/auth/users/{user_id}/reset-password
    Body: { new_password, updated_by }
    Admin only. Hashes with bcrypt. Resets failed_attempts + locked_until.
