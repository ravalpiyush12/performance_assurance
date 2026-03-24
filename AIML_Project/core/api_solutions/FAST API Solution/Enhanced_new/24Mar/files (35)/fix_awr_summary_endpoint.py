# =============================================================================
# 1. ADD to awr/routes.py
#    GET /awr/summary/{run_id}
#    Returns row counts from all 4 AWR tables for a run_id
# =============================================================================

@router.get("/summary/{run_id}")
async def get_awr_summary(
    run_id: str,
    current_user: str = Depends(verify_auth_token),
):
    """
    Get record counts from all 4 AWR tables for a given run_id.
    Called by upload-reports.html after AWR upload completes.

    Tables:
      - API_AWR_ANALYSIS_RESULTS  (1 row per upload)
      - API_AWR_CONCERNS          (N rows — critical/warning concerns)
      - API_AWR_TOP_SQL           (N rows — top SQL statements)
      - API_AWR_WAIT_EVENTS       (N rows — wait events)
    """
    if not awr_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        with awr_db.pool.acquire() as conn:
            cursor = conn.cursor()

            def count_table(table):
                try:
                    cursor.execute(
                        f"SELECT COUNT(*) FROM {table} WHERE RUN_ID = :run_id",
                        {'run_id': run_id}
                    )
                    row = cursor.fetchone()
                    return row[0] if row else 0
                except Exception as e:
                    logger.warning(f"Count error for {table}: {e}")
                    return 0

            analysis_results_count = count_table('API_AWR_ANALYSIS_RESULTS')
            concerns_count         = count_table('API_AWR_CONCERNS')
            top_sql_count          = count_table('API_AWR_TOP_SQL')
            wait_events_count      = count_table('API_AWR_WAIT_EVENTS')
            total                  = (analysis_results_count + concerns_count +
                                      top_sql_count + wait_events_count)

            return {
                "success":                 True,
                "run_id":                  run_id,
                "analysis_results_count":  analysis_results_count,
                "concerns_count":          concerns_count,
                "top_sql_count":           top_sql_count,
                "wait_events_count":       wait_events_count,
                "total_records":           total,
            }
    except Exception as e:
        logger.error(f"Error fetching AWR summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 2. ADD to nft/routes.py
#    GET /nft/lob-config/databases?lob_name=
#    Returns DB_MONITORING entries from API_LOB_MASTER
#    Used by upload-reports.html for AWR database dropdown
# =============================================================================

@nft_router.get("/lob-config/databases")
async def get_lob_databases(
    lob_name: str = Query(None),
    current_user: str = Depends(verify_auth_token),
):
    """
    Get Oracle database names for AWR from API_LOB_MASTER.
    Returns rows where TRACK_NAME = 'DB_MONITORING' for the given LOB.

    API_LOB_MASTER columns used:
      ID, LOB_NAME, TRACK_NAME, DATABASE_NAME, IS_ACTIVE
    """
    _check_db()
    try:
        with nft_db.pool.acquire() as conn:
            cursor = conn.cursor()
            sql = """
                SELECT ID, LOB_NAME, TRACK_NAME, DATABASE_NAME
                  FROM API_LOB_MASTER
                 WHERE TRACK_NAME = 'DB_MONITORING'
                   AND IS_ACTIVE  = 'Y'
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
                    'name':          row[3],   # alias
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
# SUMMARY OF WHAT UI NOW CALLS AFTER AWR UPLOAD:
#
# 1. POST /api/v1/monitoring/awr/upload   → upload & parse AWR file
#    Response should include: total_concerns, top_sql_count, wait_events_count,
#    run_id, awr_run_id, database_name
#
# 2. GET  /api/v1/monitoring/awr/summary/{run_id}  ← NEW endpoint above
#    Response: {analysis_results_count, concerns_count, top_sql_count,
#               wait_events_count, total_records}
#
# UI shows all 4 rows in the results table with real counts from Oracle.
# =============================================================================
