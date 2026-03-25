# =============================================================================
# monitoring/awr/database.py — Add this method to AWRDatabase class
# monitoring/awr/routes.py   — Add GET /results/{run_id}
#
# Uses EXACT column names confirmed from table describe (Images 1-2)
# =============================================================================

# ── database.py method ────────────────────────────────────────────────────────

    def get_full_results_by_run_id(self, run_id: str) -> dict:
        """
        Fetch all AWR data for a run_id joined across 5 tables.
        Returns None if no AWR analysis exists for this run.
        """
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                # ── 1. RUN_MASTER — LOB, Track, Test metadata ───────────────
                cursor.execute("""
                    SELECT LOB_NAME, TRACK, TEST_NAME, TEST_STATUS,
                           TEST_START_TIME, TEST_END_TIME, PC_RUN_ID
                    FROM   API_RUN_MASTER
                    WHERE  RUN_ID = :run_id
                """, {'run_id': run_id})
                row = cursor.fetchone()
                master = {}
                if row:
                    master = {
                        'lob_name':   row[0] or '',
                        'track':      row[1] or '',
                        'test_name':  row[2] or '',
                        'test_status':row[3] or '',
                        'start_time': row[4].isoformat() if row[4] else None,
                        'end_time':   row[5].isoformat() if row[5] else None,
                        'pc_run_id':  str(row[6]) if row[6] else '',
                    }

                # ── 2. AWR Analysis Results — one row per database ──────────
                cursor.execute("""
                    SELECT
                        ANALYSIS_ID, RUN_ID, AWR_RUN_ID,
                        DATABASE_NAME, INSTANCE_NAME, HOST_NAME,
                        SNAPSHOT_BEGIN, SNAPSHOT_END,
                        SNAPSHOT_BEGIN_TIME, SNAPSHOT_END_TIME,
                        ELAPSED_TIME_MINUTES, DB_TIME_MINUTES, DB_CPU_MINUTES,
                        TOTAL_CONCERNS, CRITICAL_CONCERNS,
                        WARNING_CONCERNS, INFO_CONCERNS, ANALYSIS_STATUS
                    FROM   API_AWR_ANALYSIS_RESULTS
                    WHERE  RUN_ID = :run_id
                    ORDER  BY DATABASE_NAME
                """, {'run_id': run_id})

                analyses_raw = []
                for r in cursor.fetchall():
                    a = {
                        'analysis_id':          int(r[0]) if r[0] else None,
                        'run_id':               r[1],
                        'awr_run_id':           r[2],
                        'database_name':        r[3] or '',
                        'instance_name':        r[4] or '',
                        'host_name':            r[5] or '',
                        'snapshot_begin':       int(r[6]) if r[6] else None,
                        'snapshot_end':         int(r[7]) if r[7] else None,
                        'snapshot_begin_time':  r[8].isoformat()  if r[8]  else None,
                        'snapshot_end_time':    r[9].isoformat()  if r[9]  else None,
                        'elapsed_time_minutes': float(r[10]) if r[10] else None,
                        'db_time_minutes':      float(r[11]) if r[11] else None,
                        'db_cpu_minutes':       float(r[12]) if r[12] else None,
                        'total_concerns':       int(r[13])   if r[13] else 0,
                        'critical_concerns':    int(r[14])   if r[14] else 0,
                        'warning_concerns':     int(r[15])   if r[15] else 0,
                        'info_concerns':        int(r[16])   if r[16] else 0,
                        'analysis_status':      r[17] or '',
                    }
                    analyses_raw.append(a)

                if not analyses_raw:
                    return None

                # ── 3. Concerns ─────────────────────────────────────────────
                cursor.execute("""
                    SELECT
                        CONCERN_ID, ANALYSIS_ID, RUN_ID, AWR_RUN_ID,
                        CONCERN_CATEGORY, CONCERN_TYPE, SEVERITY, CONCERN_TITLE,
                        CONCERN_DESCRIPTION, METRIC_NAME, METRIC_VALUE,
                        THRESHOLD_VALUE, RECOMMENDATION, SQL_ID, CREATED_DATE
                    FROM   API_AWR_CONCERNS
                    WHERE  RUN_ID = :run_id
                    ORDER  BY
                        DECODE(SEVERITY,'CRITICAL',1,'WARNING',2,'INFO',3,4),
                        ANALYSIS_ID
                """, {'run_id': run_id})

                all_concerns = []
                for r in cursor.fetchall():
                    c = {
                        'concern_id':          int(r[0]) if r[0] else None,
                        'analysis_id':         int(r[1]) if r[1] else None,
                        'run_id':              r[2],
                        'awr_run_id':          r[3],
                        'concern_category':    r[4] or '',
                        'concern_type':        r[5] or '',
                        'severity':            r[6] or '',
                        'concern_title':       r[7] or '',
                        'concern_description': r[8].read() if (r[8] and hasattr(r[8],'read')) else (r[8] or ''),
                        'metric_name':         r[9] or '',
                        'metric_value':        float(r[10]) if r[10] else None,
                        'threshold_value':     float(r[11]) if r[11] else None,
                        'recommendation':      r[12].read() if (r[12] and hasattr(r[12],'read')) else (r[12] or ''),
                        'sql_id':              r[13] or '',
                        'created_date':        r[14].isoformat() if r[14] else None,
                    }
                    all_concerns.append(c)

                # ── 4. Top SQL ───────────────────────────────────────────────
                cursor.execute("""
                    SELECT
                        ANALYSIS_ID, RUN_ID, SQL_ID, SQL_TEXT,
                        EXECUTIONS, ELAPSED_TIME_SECONDS, CPU_TIME_SECONDS,
                        BUFFER_GETS, DISK_READS, ROWS_PROCESSED,
                        ELAPSED_PER_EXEC_MS, CPU_PER_EXEC_MS,
                        RANK_BY_ELAPSED, RANK_BY_CPU, RANK_BY_READS,
                        CREATED_DATE
                    FROM   API_AWR_TOP_SQL
                    WHERE  RUN_ID = :run_id
                    ORDER  BY RANK_BY_ELAPSED NULLS LAST, ELAPSED_TIME_SECONDS DESC NULLS LAST
                    FETCH  FIRST 50 ROWS ONLY
                """, {'run_id': run_id})

                all_top_sql = []
                for r in cursor.fetchall():
                    s = {
                        'analysis_id':        int(r[0]) if r[0] else None,
                        'run_id':             r[1],
                        'sql_id':             r[2] or '',
                        'sql_text':           r[3].read() if (r[3] and hasattr(r[3],'read')) else (r[3] or ''),
                        'executions':         int(r[4])   if r[4] else 0,
                        'elapsed_time_seconds': float(r[5]) if r[5] else 0.0,
                        'cpu_time_seconds':   float(r[6])  if r[6] else 0.0,
                        'buffer_gets':        int(r[7])    if r[7] else 0,
                        'disk_reads':         int(r[8])    if r[8] else 0,
                        'rows_processed':     int(r[9])    if r[9] else 0,
                        'elapsed_per_exec_ms':float(r[10]) if r[10] else 0.0,
                        'cpu_per_exec_ms':    float(r[11]) if r[11] else 0.0,
                        'rank_by_elapsed':    int(r[12])   if r[12] else None,
                        'rank_by_cpu':        int(r[13])   if r[13] else None,
                        'rank_by_reads':      int(r[14])   if r[14] else None,
                        'created_date':       r[15].isoformat() if r[15] else None,
                    }
                    all_top_sql.append(s)

                # ── 5. Wait Events ───────────────────────────────────────────
                # NOTE: API_AWR_WAIT_EVENTS does NOT have EVENT_NAME or EVENT_CLASS
                # Columns: ANALYSIS_ID, RUN_ID, WAITS, TOTAL_WAIT_TIME_SECONDS,
                #          AVG_WAIT_TIME_MS, PERCENT_DB_TIME, RANK_POSITION, CREATED_DATE
                # AWR_RUN_ID links back to analysis row for event name if stored there
                # We query and display what we have
                cursor.execute("""
                    SELECT
                        ANALYSIS_ID, RUN_ID, AWR_RUN_ID,
                        WAITS, TOTAL_WAIT_TIME_SECONDS,
                        AVG_WAIT_TIME_MS, PERCENT_DB_TIME,
                        RANK_POSITION, CREATED_DATE
                    FROM   API_AWR_WAIT_EVENTS
                    WHERE  RUN_ID = :run_id
                    ORDER  BY PERCENT_DB_TIME DESC NULLS LAST
                    FETCH  FIRST 30 ROWS ONLY
                """, {'run_id': run_id})

                all_waits = []
                for r in cursor.fetchall():
                    w = {
                        'analysis_id':           int(r[0]) if r[0] else None,
                        'run_id':                r[1],
                        'awr_run_id':            r[2] or '',
                        'waits':                 int(r[3])    if r[3] else 0,
                        'total_wait_time_seconds': float(r[4]) if r[4] else 0.0,
                        'avg_wait_time_ms':      float(r[5])  if r[5] else 0.0,
                        'percent_db_time':       float(r[6])  if r[6] else 0.0,
                        'rank_position':         int(r[7])    if r[7] else None,
                        'created_date':          r[8].isoformat() if r[8] else None,
                        # Derive a display label from awr_run_id or rank
                        'event_label':           f"Wait Event #{r[7] or '?'}",
                    }
                    all_waits.append(w)

                # ── 6. Attach children to each analysis ──────────────────────
                for a in analyses_raw:
                    aid = a['analysis_id']
                    a['concerns']    = [c for c in all_concerns if c['analysis_id'] == aid]
                    a['top_sql']     = [s for s in all_top_sql  if s['analysis_id'] == aid]
                    a['wait_events'] = [w for w in all_waits    if w['analysis_id'] == aid]

                return {
                    'run_id':            run_id,
                    'lob_name':          master.get('lob_name', ''),
                    'track':             master.get('track', ''),
                    'test_name':         master.get('test_name', ''),
                    'pc_run_id':         master.get('pc_run_id', ''),
                    'test_status':       master.get('test_status', ''),
                    'analyses':          analyses_raw,
                    'total_analyses':    len(analyses_raw),
                    'total_concerns':    len(all_concerns),
                    'total_sql':         len(all_top_sql),
                    'total_wait_events': len(all_waits),
                }

            except Exception as e:
                logger.error(f"AWR get_full_results error {run_id}: {e}", exc_info=True)
                raise
            finally:
                cursor.close()


# ── routes.py endpoint ────────────────────────────────────────────────────────

@router.get("/results/{run_id}")
async def get_awr_results(run_id: str):
    """
    GET /api/v1/monitoring/awr/results/{run_id}
    Full AWR data: analysis summary + concerns + top SQL + wait events.
    LOB/Track pulled from API_RUN_MASTER.
    """
    if not awr_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        result = awr_db.get_full_results_by_run_id(run_id)
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"No AWR analysis found for run_id: {run_id}"
            )
        return {"success": True, **result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_awr_results error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
