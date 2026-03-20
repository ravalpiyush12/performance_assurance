"""
ADD TO: Auth/routes_fixed.py
------------------------------
Endpoints for LOB Config admin page.
All require admin auth via get_current_user.
"""

# ── POST /lob-config  (add a LOB+Track row) ──────────────────────────────────
@router.post("/lob-config")
async def add_lob_config(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Add or update a LOB/Track entry in API_LOB_MASTER."""
    body = await request.json()
    lob_name   = body.get('lob_name', '').strip()
    track_name = body.get('track_name', '').strip()
    db_name    = body.get('database_name', 'CQE_NFT').strip()
    is_active  = body.get('is_active', 'Y')

    if not lob_name or not track_name:
        raise HTTPException(status_code=400, detail="lob_name and track_name are required")

    auth_mgr = get_auth_manager()
    with auth_mgr.pool.acquire() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                MERGE INTO API_LOB_MASTER t
                USING (SELECT :lob_name AS ln, :track_name AS tn FROM DUAL) s
                ON (t.LOB_NAME = s.ln AND t.TRACK_NAME = s.tn)
                WHEN MATCHED THEN
                    UPDATE SET DATABASE_NAME = :db_name,
                               IS_ACTIVE     = :is_active,
                               UPDATED_BY    = :updated_by,
                               UPDATED_DATE  = SYSDATE
                WHEN NOT MATCHED THEN
                    INSERT (LOB_NAME, TRACK_NAME, DATABASE_NAME, IS_ACTIVE,
                            CREATED_BY, CREATED_DATE)
                    VALUES (:lob_name, :track_name, :db_name, :is_active,
                            :updated_by, SYSDATE)
            """, {
                'lob_name':   lob_name,
                'track_name': track_name,
                'db_name':    db_name,
                'is_active':  is_active,
                'updated_by': current_user.get('username', 'admin'),
            })
            conn.commit()
            return {"success": True, "lob_name": lob_name,
                    "track_name": track_name, "message": "LOB/Track saved"}
        except Exception as e:
            conn.rollback()
            logger.error(f"Add LOB config error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            cursor.close()


# ── DELETE /lob-config/{lob_name}/{track_name} ───────────────────────────────
@router.delete("/lob-config/{lob_name}/{track_name}")
async def delete_lob_track(
    lob_name: str,
    track_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a specific track from a LOB."""
    auth_mgr = get_auth_manager()
    with auth_mgr.pool.acquire() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                DELETE FROM API_LOB_MASTER
                WHERE LOB_NAME = :lob_name AND TRACK_NAME = :track_name
            """, {'lob_name': lob_name, 'track_name': track_name})
            deleted = cursor.rowcount
            conn.commit()
            if deleted == 0:
                raise HTTPException(status_code=404,
                    detail=f"Track '{track_name}' not found in LOB '{lob_name}'")
            return {"success": True, "deleted": deleted,
                    "message": f"Track '{track_name}' removed from '{lob_name}'"}
        except HTTPException:
            raise
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            cursor.close()


# ── PUT /lob-config/{lob_name}/status ────────────────────────────────────────
@router.put("/lob-config/{lob_name}/status")
async def update_lob_status(
    lob_name: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Enable or disable all tracks for a LOB."""
    body = await request.json()
    is_active = body.get('is_active', 'Y')
    auth_mgr = get_auth_manager()
    with auth_mgr.pool.acquire() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE API_LOB_MASTER
                SET IS_ACTIVE = :is_active, UPDATED_DATE = SYSDATE
                WHERE LOB_NAME = :lob_name
            """, {'is_active': is_active, 'lob_name': lob_name})
            conn.commit()
            return {"success": True, "lob_name": lob_name, "is_active": is_active}
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            cursor.close()
