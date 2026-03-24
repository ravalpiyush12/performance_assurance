# =============================================================================
# ADD to auth/routes.py or nft/routes.py
#
# GET /auth/lob-config/databases?lob_name=
# Returns DB_MONITORING entries from API_LOB_MASTER for the AWR database dropdown
#
# From Image 5, API_LOB_MASTER columns:
#   ID, LOB_NAME, TRACK_NAME, DATABASE_NAME, IS_ACTIVE,
#   CREATED_BY, CREATED_DATE, UPDATED_BY, UPDATED_DATE
#
# DB_MONITORING rows have DATABASE_NAME values like:
#   CQE_NFT, CD_PTE_READ, CAS_PTE_READ, PORTAL_PTE_READ,
#   CD_PTE_WRITE, CAS_PTE_WRITE, PORTAL_PTE_WRITE
# =============================================================================

@auth_router.get("/lob-config/databases")
async def get_lob_databases(
    lob_name: str = Query(None),
    current_user: str = Depends(verify_auth_token),
):
    """
    Get Oracle database names for a LOB from API_LOB_MASTER.
    Returns entries where TRACK_NAME = 'DB_MONITORING'.
    Used to populate the AWR database dropdown in upload-reports.html.
    """
    try:
        with oracle_pool.acquire() as conn:
            cursor = conn.cursor()
            sql = """
                SELECT ID, LOB_NAME, TRACK_NAME, DATABASE_NAME, IS_ACTIVE
                  FROM API_LOB_MASTER
                 WHERE TRACK_NAME = 'DB_MONITORING'
                   AND IS_ACTIVE = 'Y'
            """
            params = {}
            if lob_name:
                sql += " AND LOB_NAME = :lob_name"
                params['lob_name'] = lob_name
            sql += " ORDER BY DATABASE_NAME"
            cursor.execute(sql, params)

            databases = []
            for row in cursor.fetchall():
                databases.append({
                    'id':            row[0],
                    'lob_name':      row[1],
                    'track_name':    row[2],
                    'database_name': row[3],
                    'name':          row[3],  # alias for frontend convenience
                    'is_active':     row[4],
                })
            return {
                "success":   True,
                "lob_name":  lob_name,
                "databases": databases,
                "total":     len(databases),
            }
    except Exception as e:
        logger.error(f"Error getting LOB databases: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# AWR UPLOAD RESPONSE — ensure awr/routes.py returns these fields
# so upload-reports.html can show correct table counts:
#
# Return from POST /awr/upload:
# {
#   "success": true,
#   "run_id": "...",
#   "awr_run_id": "...",
#   "database_name": "CAS_PTE_READ",
#   "total_concerns": 5,         ← maps to API_AWR_CONCERNS count
#   "critical_concerns": 2,
#   "warning_concerns": 3,
#   "top_sql_count": 10,         ← maps to API_AWR_TOP_SQL count
#   "wait_events_count": 8,      ← maps to API_AWR_WAIT_EVENTS count
#   "message": "AWR analysis completed successfully."
# }
#
# These field names are what upload-reports.html now reads:
#   awrData.total_concerns      → API_AWR_CONCERNS
#   awrData.top_sql_count       → API_AWR_TOP_SQL
#   awrData.wait_events_count   → API_AWR_WAIT_EVENTS
# =============================================================================
