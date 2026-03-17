"""
ADD TO: Auth/routes_fixed.py
------------------------------
Paste this block BEFORE the existing get_lob_config() function.
Uses exact same DB pattern as all other routes in this file.
No auth dependency — safe to expose (only LOB names, no sensitive data).
"""

@router.get("/lob-config/public", summary="Get active LOBs - no auth required")
async def get_lob_config_public():
    """
    Public endpoint — no authentication required.
    Returns active LOBs + tracks from API_LOB_MASTER.
    Used by pre-login page to show LOB selector before login.
    """
    try:
        auth_mgr = get_auth_manager()
        with auth_mgr.pool.acquire() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("""
                    SELECT
                        LOB_NAME,
                        LISTAGG(TRACK_NAME, ',')
                            WITHIN GROUP (ORDER BY TRACK_NAME) AS TRACKS,
                        COUNT(*)        AS TRACK_COUNT,
                        MAX(DATABASE_NAME) AS DATABASE_NAME
                    FROM API_LOB_MASTER
                    WHERE IS_ACTIVE = 'Y'
                    GROUP BY LOB_NAME
                    ORDER BY LOB_NAME
                """)
                rows = cursor.fetchall()
                lobs = []
                for row in rows:
                    tracks = [t.strip() for t in (row[1] or '').split(',') if t.strip()]
                    lobs.append({
                        'name':        row[0],
                        'tracks':      tracks,
                        'track_count': row[2] or 0,
                        'database':    row[3] or '',
                    })
                return {'success': True, 'lobs': lobs, 'total': len(lobs)}
            finally:
                cursor.close()
    except Exception as e:
        logger.error(f"Public LOB config error: {e}", exc_info=True)
        return {'success': False, 'lobs': [], 'total': 0, 'detail': str(e)}
