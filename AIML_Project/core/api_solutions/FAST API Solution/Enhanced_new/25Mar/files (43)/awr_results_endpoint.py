# =============================================================================
# CHANGE 1: monitoring/awr/database.py
# Add get_full_results_by_run_id() to AWR database class
# =============================================================================

    def get_full_results_by_run_id(self, run_id: str) -> dict:
        """
        Fetch all AWR data for a run_id across 4 tables + RUN_MASTER metadata.
        Used by GET /monitoring/awr/results/{run_id} → pc_report.html AWR section.

        Returns:
        {
          "run_id": "...", "lob_name": "...", "track": "...",
          "analyses": [{ summary + concerns + top_sql + wait_events }]
        }
        """
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                # ── 1. RUN_MASTER for LOB + Track ──────────────────────────
                cursor.execute("""
                    SELECT LOB_NAME, TRACK, TEST_NAME, TEST_STATUS,
                           TEST_START_TIME, TEST_END_TIME, PC_RUN_ID
                    FROM   API_RUN_MASTER
                    WHERE  RUN_ID = :run_id
                """, {'run_id': run_id})
                master_row = cursor.fetchone()
                master = {}
                if master_row:
                    master = {
                        'lob_name':   master_row[0],
                        'track':      master_row[1],
                        'test_name':  master_row[2],
                        'test_status':master_row[3],
                        'start_time': master_row[4].isoformat() if master_row[4] else None,
                        'end_time':   master_row[5].isoformat() if master_row[5] else None,
                        'pc_run_id':  str(master_row[6]) if master_row[6] else '',
                    }

                # ── 2. AWR Analysis Results (one per DB) ───────────────────
                cursor.execute("""
                    SELECT ANALYSIS_ID, RUN_ID, DATABASE_NAME,
                           BEGIN_SNAP_ID, END_SNAP_ID,
                           BEGIN_TIME, END_TIME,
                           DURATION_MINUTES, DB_TIME_SECONDS,
                           CPU_TIME_SECONDS, BUFFER_CACHE_HIT_PCT,
                           HARD_PARSES_PER_SEC, SOFT_PARSES_PER_SEC,
                           EXECUTIONS_PER_SEC, TRANSACTIONS_PER_SEC,
                           PHYSICAL_READS_PER_SEC, DB_BLOCK_CHANGES_PER_SEC,
                           REDO_SIZE_PER_SEC, TOTAL_SQL_COUNT,
                           CREATED_DATE
                    FROM   API_AWR_ANALYSIS_RESULTS
                    WHERE  RUN_ID = :run_id
                    ORDER  BY DATABASE_NAME
                """, {'run_id': run_id})

                analysis_cols = [
                    'analysis_id','run_id','database_name',
                    'begin_snap_id','end_snap_id',
                    'begin_time','end_time',
                    'duration_minutes','db_time_seconds',
                    'cpu_time_seconds','buffer_cache_hit_pct',
                    'hard_parses_per_sec','soft_parses_per_sec',
                    'executions_per_sec','transactions_per_sec',
                    'physical_reads_per_sec','db_block_changes_per_sec',
                    'redo_size_per_sec','total_sql_count',
                    'created_date'
                ]
                analyses_raw = []
                for row in cursor.fetchall():
                    d = dict(zip(analysis_cols, row))
                    for f in ['begin_time','end_time','created_date']:
                        if d.get(f) and hasattr(d[f], 'isoformat'):
                            d[f] = d[f].isoformat()
                    for f in ['duration_minutes','db_time_seconds','cpu_time_seconds',
                              'buffer_cache_hit_pct','hard_parses_per_sec']:
                        if d.get(f) is not None:
                            d[f] = float(d[f])
                    analyses_raw.append(d)

                if not analyses_raw:
                    return None  # No AWR data for this run

                # ── 3. Concerns ────────────────────────────────────────────
                cursor.execute("""
                    SELECT CONCERN_ID, ANALYSIS_ID, RUN_ID, SEVERITY,
                           CONCERN_TITLE, CONCERN_DESCRIPTION,
                           METRIC_NAME, METRIC_VALUE, THRESHOLD_VALUE,
                           RECOMMENDATION, SQL_ID
                    FROM   API_AWR_CONCERNS
                    WHERE  RUN_ID = :run_id
                    ORDER  BY DECODE(SEVERITY,'CRITICAL',1,'WARNING',2,'INFO',3,4), ANALYSIS_ID
                """, {'run_id': run_id})
                concern_cols = ['concern_id','analysis_id','run_id','severity',
                                'concern_title','concern_description',
                                'metric_name','metric_value','threshold_value',
                                'recommendation','sql_id']
                all_concerns = []
                for row in cursor.fetchall():
                    d = dict(zip(concern_cols, row))
                    for f in ['metric_value','threshold_value']:
                        if d.get(f) is not None: d[f] = float(d[f])
                    # Read CLOB fields
                    for f in ['concern_description','recommendation']:
                        if d.get(f) and hasattr(d[f], 'read'):
                            d[f] = d[f].read()
                    all_concerns.append(d)

                # ── 4. Top SQL ─────────────────────────────────────────────
                cursor.execute("""
                    SELECT TOP_SQL_ID, ANALYSIS_ID, RUN_ID, SQL_ID,
                           SQL_TEXT, EXECUTIONS,
                           ELAPSED_TIME_SECONDS, CPU_TIME_SECONDS,
                           BUFFER_GETS, DISK_READS, ROWS_PROCESSED,
                           ELAPSED_PER_EXEC, RANK_BY_ELAPSED
                    FROM   API_AWR_TOP_SQL
                    WHERE  RUN_ID = :run_id
                    ORDER  BY RANK_BY_ELAPSED NULLS LAST, ELAPSED_TIME_SECONDS DESC NULLS LAST
                    FETCH  FIRST 50 ROWS ONLY
                """, {'run_id': run_id})
                sql_cols = ['top_sql_id','analysis_id','run_id','sql_id',
                            'sql_text','executions',
                            'elapsed_time_seconds','cpu_time_seconds',
                            'buffer_gets','disk_reads','rows_processed',
                            'elapsed_per_exec','rank_by_elapsed']
                all_top_sql = []
                for row in cursor.fetchall():
                    d = dict(zip(sql_cols, row))
                    for f in ['elapsed_time_seconds','cpu_time_seconds','elapsed_per_exec']:
                        if d.get(f) is not None: d[f] = float(d[f])
                    for f in ['executions','buffer_gets','disk_reads','rows_processed']:
                        if d.get(f) is not None: d[f] = int(d[f])
                    if d.get('sql_text') and hasattr(d['sql_text'], 'read'):
                        d['sql_text'] = d['sql_text'].read()
                    all_top_sql.append(d)

                # ── 5. Wait Events ─────────────────────────────────────────
                cursor.execute("""
                    SELECT WAIT_EVENT_ID, ANALYSIS_ID, RUN_ID,
                           EVENT_NAME, EVENT_CLASS,
                           TOTAL_WAITS, TIME_WAITED_SECONDS,
                           AVG_WAIT_MS, PCT_DB_TIME,
                           MAX_WAIT_MS
                    FROM   API_AWR_WAIT_EVENTS
                    WHERE  RUN_ID = :run_id
                    ORDER  BY PCT_DB_TIME DESC NULLS LAST
                    FETCH  FIRST 30 ROWS ONLY
                """, {'run_id': run_id})
                wait_cols = ['wait_event_id','analysis_id','run_id',
                             'event_name','event_class',
                             'total_waits','time_waited_seconds',
                             'avg_wait_ms','pct_db_time','max_wait_ms']
                all_waits = []
                for row in cursor.fetchall():
                    d = dict(zip(wait_cols, row))
                    for f in ['time_waited_seconds','avg_wait_ms','pct_db_time','max_wait_ms']:
                        if d.get(f) is not None: d[f] = float(d[f])
                    if d.get('total_waits') is not None: d['total_waits'] = int(d['total_waits'])
                    all_waits.append(d)

                # ── 6. Attach concerns/sql/waits to each analysis ──────────
                for a in analyses_raw:
                    aid = a['analysis_id']
                    a['concerns']    = [c for c in all_concerns if c['analysis_id'] == aid]
                    a['top_sql']     = [s for s in all_top_sql  if s['analysis_id'] == aid]
                    a['wait_events'] = [w for w in all_waits    if w['analysis_id'] == aid]

                return {
                    'run_id':   run_id,
                    'lob_name': master.get('lob_name',''),
                    'track':    master.get('track',''),
                    'test_name':master.get('test_name',''),
                    'pc_run_id':master.get('pc_run_id',''),
                    'analyses': analyses_raw,
                    'total_concerns':    len(all_concerns),
                    'total_sql':         len(all_top_sql),
                    'total_wait_events': len(all_waits),
                }

            except Exception as e:
                logger.error(f"get_full_results_by_run_id error {run_id}: {e}", exc_info=True)
                return None
            finally:
                cursor.close()


# =============================================================================
# CHANGE 2: monitoring/awr/routes.py
# Add GET /results/{run_id}  (replace existing /summary/{run_id} or add alongside)
# =============================================================================

@router.get("/results/{run_id}")
async def get_awr_results(run_id: str):
    """
    GET /api/v1/monitoring/awr/results/{run_id}
    Returns full AWR data: analysis summary + concerns + top SQL + wait events.
    Includes LOB/Track from API_RUN_MASTER.
    Used by pc_report.html AWR section.
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
