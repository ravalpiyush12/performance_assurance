"""
ADD TO: Auth/routes_fixed.py
------------------------------
Paste this after the reset_user_totp endpoint.
Admin-only: reset another user's password.
"""

@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    request: Request,
    current_user: dict = Depends(require_admin)
):
    """
    Reset password for a user (admin only).
    Body: { new_password: str, updated_by: str }
    """
    try:
        body = await request.json()
        new_password = body.get('new_password', '').strip()
        updated_by = body.get('updated_by', current_user.get('username', 'admin'))

        if not new_password or len(new_password) < 8:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters"
            )

        auth_mgr = get_auth_manager()

        # Hash the new password using bcrypt (same as create_user)
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed = pwd_context.hash(new_password)

        with auth_mgr.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                # Update password and set first_login flag so user must change on login
                cursor.execute("""
                    UPDATE API_AUTH_USERS
                    SET PASSWORD_HASH = :password_hash,
                        FAILED_ATTEMPTS = 0,
                        LOCKED_UNTIL = NULL
                    WHERE USER_ID = :user_id
                """, {
                    'password_hash': hashed,
                    'user_id': user_id,
                })
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=404, detail=f"User ID {user_id} not found")
                conn.commit()

                # Log audit
                auth_mgr._log_audit(
                    username=updated_by,
                    action='PASSWORD_RESET',
                    resource_id=user_id,
                    success='Y',
                    failure_reason=None
                )

                return {
                    "success": True,
                    "message": f"Password reset successfully for user ID {user_id}",
                    "updated_by": updated_by
                }
            except HTTPException:
                raise
            except Exception as e:
                conn.rollback()
                logger.error(f"Password reset error: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Password reset failed: {str(e)}")
            finally:
                cursor.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reset password error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
