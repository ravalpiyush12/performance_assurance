# =============================================================================
# monitoring/appd/database.py — Add this method to AppDynamicsDatabase class
# monitoring/appd/routes.py   — Add GET /results/{run_id}
#
# Uses EXACT column names confirmed from table describe (Images 3-4)
#
# KEY NOTES from images:
# - API_APPD_APPLICATION_METRICS has NO RUN_ID column directly visible —
#   it joins via NODE_ID → API_APPD_MONITORING_RUNS.APPD_RUN_ID
#   Actually looking at Image 3 right: first visible col is NODE_ID, TIER_ID, APP_ID
#   The RUN_ID link is through API_APPD_MONITORING_RUNS which has APPD_RUN_ID
#   APPLICATION_METRICS likely has METRIC_ID + RUN_ID at top (cut off in image)
#   We query APPLICATION_METRICS with RUN_ID directly (standard pattern)
# - API_APPD_SERVER_METRICS: CPU_BUSY_PERCENT, CPU_IDLE_PERCENT, CPU_STOLEN_PERCENT,
#   MEMORY_TOTAL_MB, MEMORY_USED_MB, MEMORY_FREE_MB, MEMORY_USED_PERCENT,
#   NETWORK_INCOMING_KB, NETWORK_OUTGOING_KB, DISK_READS_PER_SEC
# =============================================================================

# ── database.py method ────────────────────────────────────────────────────────

    def get_full_results_by_run_id(self, run_id: str) -> dict:
        """
        Fetch AppD monitoring summary for a run_id.
        Uses exact column names from API_APPD_* tables.
        Returns None if no AppD monitoring data for this run.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                # ── 1. RUN_MASTER — LOB, Track ──────────────────────────────
                cursor.execute("""
                    SELECT LOB_NAME, TRACK, TEST_NAME, PC_RUN_ID
                    FROM   API_RUN_MASTER
                    WHERE  RUN_ID = :run_id
                """, {'run_id': run_id})
                row = cursor.fetchone()
                master = {}
                if row:
                    master = {
                        'lob_name': row[0] or '',
                        'track':    row[1] or '',
                        'test_name':row[2] or '',
                        'pc_run_id':str(row[3]) if row[3] else '',
                    }

                # ── 2. MONITORING RUNS — run-level summary ───────────────────
                # API_APPD_MONITORING_RUNS columns (Image 3 left):
                # RUN_ID, LOB_ID, LOB_NAME, TRACK, TEST_NAME, START_TIME, END_TIME,
                # STATUS, COLLECTION_INTERVAL_SECONDS, APPLICATIONS, TOTAL_COLLECTIONS,
                # SUCCESSFUL_COLLECTIONS, FAILED_COLLECTIONS, LAST_COLLECTION_TIME,
                # ERROR_MESSAGE, CREATED_DATE, UPDATED_DATE, DURATION_MINUTES,
                # PC_RUN_ID, APPD_RUN_ID
                cursor.execute("""
                    SELECT
                        COUNT(*)                  AS run_count,
                        SUM(TOTAL_COLLECTIONS)    AS total_collections,
                        SUM(SUCCESSFUL_COLLECTIONS) AS successful_collections,
                        SUM(FAILED_COLLECTIONS)   AS failed_collections,
                        MIN(START_TIME)           AS first_start,
                        MAX(END_TIME)             AS last_end,
                        SUM(DURATION_MINUTES)     AS total_duration_min
                    FROM   API_APPD_MONITORING_RUNS
                    WHERE  RUN_ID = :run_id
                """, {'run_id': run_id})
                mr = cursor.fetchone()
                if not mr or int(mr[0] or 0) == 0:
                    return None  # No AppD data for this run

                monitoring_summary = {
                    'monitoring_runs':         int(mr[0] or 0),
                    'total_collections':       int(mr[1] or 0),
                    'successful_collections':  int(mr[2] or 0),
                    'failed_collections':      int(mr[3] or 0),
                    'first_start':             mr[4].isoformat() if mr[4] else None,
                    'last_end':                mr[5].isoformat() if mr[5] else None,
                    'total_duration_min':      float(mr[6] or 0),
                }

                # ── 3. APPLICATION METRICS — tier-level aggregation ──────────
                # Columns (Image 3 right): NODE_ID, TIER_ID, APP_ID, COLLECTION_TIME,
                # CALLS_PER_MINUTE, CALLS_TOTAL, RESPONSE_TIME_AVG_MS, RESPONSE_TIME_MIN_MS,
                # RESPONSE_TIME_MAX_MS, RESPONSE_TIME_P90_MS, RESPONSE_TIME_P95_MS,
                # RESPONSE_TIME_P99_MS, ERRORS_PER_MINUTE, ERROR_RATE_PERCENT,
                # ERRORS_TOTAL, BT_NORMAL_COUNT, BT_SLOW_COUNT, BT_VERY_SLOW_COUNT,
                # BT_STALLED_COUNT, BT_ERROR_COUNT, APDEX_SCORE
                cursor.execute("""
                    SELECT
                        aa.APPLICATION_NAME,
                        at2.TIER_NAME,
                        COUNT(DISTINCT m.NODE_ID)              AS node_count,
                        COUNT(m.NODE_ID)                       AS sample_count,
                        ROUND(AVG(m.RESPONSE_TIME_AVG_MS), 2)  AS avg_rt_ms,
                        ROUND(MAX(m.RESPONSE_TIME_MAX_MS), 2)  AS max_rt_ms,
                        ROUND(AVG(m.RESPONSE_TIME_P90_MS), 2)  AS avg_p90_ms,
                        ROUND(AVG(m.RESPONSE_TIME_P95_MS), 2)  AS avg_p95_ms,
                        ROUND(AVG(m.CALLS_PER_MINUTE), 2)      AS avg_cpm,
                        ROUND(AVG(m.ERROR_RATE_PERCENT), 3)    AS avg_err_pct,
                        ROUND(AVG(m.APDEX_SCORE), 3)           AS avg_apdex,
                        SUM(m.ERRORS_TOTAL)                    AS total_errors,
                        SUM(m.BT_SLOW_COUNT)                   AS slow_calls,
                        SUM(m.BT_VERY_SLOW_COUNT)              AS very_slow_calls,
                        SUM(m.BT_STALLED_COUNT)                AS stalled_calls,
                        SUM(m.CALLS_TOTAL)                     AS total_calls
                    FROM   API_APPD_APPLICATION_METRICS m
                    JOIN   API_APPD_NODES        an  ON m.NODE_ID  = an.NODE_ID
                    JOIN   API_APPD_TIERS        at2 ON m.TIER_ID  = at2.TIER_ID
                    JOIN   API_APPD_APPLICATIONS aa  ON m.APP_ID   = aa.APP_ID
                    WHERE  m.RUN_ID = :run_id
                    GROUP  BY aa.APPLICATION_NAME, at2.TIER_NAME
                    ORDER  BY AVG(m.RESPONSE_TIME_AVG_MS) DESC NULLS LAST
                """, {'run_id': run_id})

                tier_cols = ['application_name','tier_name','node_count','sample_count',
                             'avg_rt_ms','max_rt_ms','avg_p90_ms','avg_p95_ms',
                             'avg_cpm','avg_err_pct','avg_apdex',
                             'total_errors','slow_calls','very_slow_calls',
                             'stalled_calls','total_calls']
                tier_summary = []
                for r in cursor.fetchall():
                    d = dict(zip(tier_cols, r))
                    for f in ['avg_rt_ms','max_rt_ms','avg_p90_ms','avg_p95_ms',
                              'avg_cpm','avg_err_pct','avg_apdex']:
                        d[f] = float(d[f]) if d[f] is not None else 0.0
                    for f in ['node_count','sample_count','total_errors',
                              'slow_calls','very_slow_calls','stalled_calls','total_calls']:
                        d[f] = int(d[f]) if d[f] is not None else 0
                    tier_summary.append(d)

                # ── 4. NODE-LEVEL SUMMARY (top 20 by avg RT) ─────────────────
                cursor.execute("""
                    SELECT
                        an.NODE_NAME,
                        at2.TIER_NAME,
                        aa.APPLICATION_NAME,
                        ROUND(AVG(m.RESPONSE_TIME_AVG_MS), 2)  AS avg_rt_ms,
                        ROUND(MAX(m.RESPONSE_TIME_MAX_MS), 2)  AS max_rt_ms,
                        ROUND(AVG(m.CALLS_PER_MINUTE), 2)      AS avg_cpm,
                        ROUND(AVG(m.ERROR_RATE_PERCENT), 3)    AS avg_err_pct,
                        SUM(m.ERRORS_TOTAL)                    AS total_errors,
                        ROUND(AVG(m.APDEX_SCORE), 3)           AS avg_apdex,
                        ROUND(AVG(m.RESPONSE_TIME_P95_MS), 2)  AS avg_p95_ms
                    FROM   API_APPD_APPLICATION_METRICS m
                    JOIN   API_APPD_NODES        an  ON m.NODE_ID  = an.NODE_ID
                    JOIN   API_APPD_TIERS        at2 ON m.TIER_ID  = at2.TIER_ID
                    JOIN   API_APPD_APPLICATIONS aa  ON m.APP_ID   = aa.APP_ID
                    WHERE  m.RUN_ID = :run_id
                    GROUP  BY an.NODE_NAME, at2.TIER_NAME, aa.APPLICATION_NAME
                    ORDER  BY AVG(m.RESPONSE_TIME_AVG_MS) DESC NULLS LAST
                    FETCH  FIRST 20 ROWS ONLY
                """, {'run_id': run_id})

                node_cols = ['node_name','tier_name','application_name',
                             'avg_rt_ms','max_rt_ms','avg_cpm',
                             'avg_err_pct','total_errors','avg_apdex','avg_p95_ms']
                node_summary = []
                for r in cursor.fetchall():
                    d = dict(zip(node_cols, r))
                    for f in ['avg_rt_ms','max_rt_ms','avg_cpm','avg_err_pct','avg_apdex','avg_p95_ms']:
                        d[f] = float(d[f]) if d[f] is not None else 0.0
                    d['total_errors'] = int(d['total_errors']) if d['total_errors'] else 0
                    node_summary.append(d)

                # ── 5. OVERALL summary across all metrics ─────────────────────
                cursor.execute("""
                    SELECT
                        ROUND(AVG(m.RESPONSE_TIME_AVG_MS), 2) AS overall_avg_rt,
                        ROUND(AVG(m.CALLS_PER_MINUTE), 2)     AS overall_cpm,
                        ROUND(AVG(m.ERROR_RATE_PERCENT), 3)   AS overall_err_pct,
                        COUNT(DISTINCT m.NODE_ID)             AS active_nodes,
                        COUNT(DISTINCT m.APP_ID)              AS app_count,
                        SUM(m.ERRORS_TOTAL)                   AS total_errors,
                        ROUND(AVG(m.APDEX_SCORE), 3)          AS avg_apdex
                    FROM   API_APPD_APPLICATION_METRICS m
                    WHERE  m.RUN_ID = :run_id
                """, {'run_id': run_id})
                ov = cursor.fetchone()
                overall = {}
                if ov:
                    overall = {
                        'overall_avg_rt_ms': float(ov[0]) if ov[0] else 0.0,
                        'overall_cpm':       float(ov[1]) if ov[1] else 0.0,
                        'overall_err_pct':   float(ov[2]) if ov[2] else 0.0,
                        'active_nodes':      int(ov[3])   if ov[3] else 0,
                        'app_count':         int(ov[4])   if ov[4] else 0,
                        'total_errors':      int(ov[5])   if ov[5] else 0,
                        'avg_apdex':         float(ov[6]) if ov[6] else 0.0,
                    }

                # ── 6. JVM METRICS — aggregated ──────────────────────────────
                # Columns: HEAP_USED_PERCENT, GC_TIME_SPENT_PERCENT,
                # THREAD_COUNT, EXCEPTION_COUNT (Image 4 left)
                cursor.execute("""
                    SELECT
                        ROUND(AVG(HEAP_USED_PERCENT), 2)      AS avg_heap_pct,
                        ROUND(MAX(HEAP_USED_PERCENT), 2)      AS max_heap_pct,
                        ROUND(AVG(GC_TIME_SPENT_PERCENT), 2)  AS avg_gc_pct,
                        ROUND(AVG(THREAD_COUNT), 0)           AS avg_threads,
                        ROUND(MAX(THREAD_PEAK), 0)            AS max_thread_peak,
                        SUM(EXCEPTION_COUNT)                  AS total_exceptions,
                        ROUND(AVG(HEAP_USED_MB), 1)           AS avg_heap_mb,
                        ROUND(MAX(HEAP_USED_MB), 1)           AS max_heap_mb,
                        ROUND(AVG(HEAP_MAX_MB), 1)            AS avg_heap_max_mb
                    FROM   API_APPD_JVM_METRICS
                    WHERE  RUN_ID = :run_id
                """, {'run_id': run_id})
                jr = cursor.fetchone()
                jvm_summary = {}
                if jr and jr[0] is not None:
                    jvm_summary = {
                        'avg_heap_pct':     float(jr[0]) if jr[0] else 0.0,
                        'max_heap_pct':     float(jr[1]) if jr[1] else 0.0,
                        'avg_gc_pct':       float(jr[2]) if jr[2] else 0.0,
                        'avg_threads':      int(jr[3])   if jr[3] else 0,
                        'max_thread_peak':  int(jr[4])   if jr[4] else 0,
                        'total_exceptions': int(jr[5])   if jr[5] else 0,
                        'avg_heap_mb':      float(jr[6]) if jr[6] else 0.0,
                        'max_heap_mb':      float(jr[7]) if jr[7] else 0.0,
                        'avg_heap_max_mb':  float(jr[8]) if jr[8] else 0.0,
                    }

                # ── 7. SERVER METRICS — aggregated ───────────────────────────
                # Columns: CPU_BUSY_PERCENT, CPU_IDLE_PERCENT, CPU_STOLEN_PERCENT,
                # MEMORY_TOTAL_MB, MEMORY_USED_MB, MEMORY_FREE_MB, MEMORY_USED_PERCENT,
                # NETWORK_INCOMING_KB, NETWORK_OUTGOING_KB, DISK_READS_PER_SEC
                cursor.execute("""
                    SELECT
                        ROUND(AVG(CPU_BUSY_PERCENT), 2)    AS avg_cpu_pct,
                        ROUND(MAX(CPU_BUSY_PERCENT), 2)    AS max_cpu_pct,
                        ROUND(AVG(MEMORY_USED_PERCENT), 2) AS avg_mem_pct,
                        ROUND(MAX(MEMORY_USED_PERCENT), 2) AS max_mem_pct,
                        ROUND(AVG(MEMORY_USED_MB), 1)      AS avg_mem_mb,
                        ROUND(MAX(MEMORY_USED_MB), 1)      AS max_mem_mb,
                        COUNT(DISTINCT NODE_ID)            AS node_count,
                        ROUND(AVG(NETWORK_INCOMING_KB + NETWORK_OUTGOING_KB), 1) AS avg_net_kb
                    FROM   API_APPD_SERVER_METRICS
                    WHERE  RUN_ID = :run_id
                """, {'run_id': run_id})
                sr = cursor.fetchone()
                server_summary = {}
                if sr and sr[0] is not None:
                    server_summary = {
                        'avg_cpu_pct': float(sr[0]) if sr[0] else 0.0,
                        'max_cpu_pct': float(sr[1]) if sr[1] else 0.0,
                        'avg_mem_pct': float(sr[2]) if sr[2] else 0.0,
                        'max_mem_pct': float(sr[3]) if sr[3] else 0.0,
                        'avg_mem_mb':  float(sr[4]) if sr[4] else 0.0,
                        'max_mem_mb':  float(sr[5]) if sr[5] else 0.0,
                        'node_count':  int(sr[6])   if sr[6] else 0,
                        'avg_net_kb':  float(sr[7]) if sr[7] else 0.0,
                    }

                return {
                    'run_id':             run_id,
                    'lob_name':           master.get('lob_name', ''),
                    'track':              master.get('track', ''),
                    'test_name':          master.get('test_name', ''),
                    'pc_run_id':          master.get('pc_run_id', ''),
                    'monitoring_summary': monitoring_summary,
                    'overall':            overall,
                    'tier_summary':       tier_summary,
                    'node_summary':       node_summary,
                    'jvm_summary':        jvm_summary,
                    'server_summary':     server_summary,
                }

            except Exception as e:
                logger.error(f"AppD get_full_results error {run_id}: {e}", exc_info=True)
                raise
            finally:
                cursor.close()


# ── routes.py endpoint ────────────────────────────────────────────────────────

@router.get("/results/{run_id}")
async def get_appd_results(run_id: str):
    """
    GET /api/v1/monitoring/appd/results/{run_id}
    Returns AppD monitoring data: tier/node summary, JVM, server metrics.
    LOB/Track from API_RUN_MASTER.
    """
    if not appd_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        result = appd_db.get_full_results_by_run_id(run_id)
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"No AppD monitoring data for run_id: {run_id}. "
                       f"Run AppD monitoring via Start Monitoring first."
            )
        return {"success": True, **result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_appd_results error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
