# =============================================================================
# CHANGE 1: monitoring/appd/database.py
# Add get_full_results_by_run_id() to AppDynamicsDatabase class
# =============================================================================

    def get_full_results_by_run_id(self, run_id: str) -> dict:
        """
        Fetch AppD monitoring summary for a run_id.
        Joins APPLICATION_METRICS → NODES → TIERS → APPLICATIONS.
        Also gets run metadata from API_RUN_MASTER.
        Used by GET /monitoring/appd/results/{run_id} → pc_report.html AppD section.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                # ── 1. RUN_MASTER metadata ──────────────────────────────────
                cursor.execute("""
                    SELECT LOB_NAME, TRACK, TEST_NAME, PC_RUN_ID
                    FROM   API_RUN_MASTER
                    WHERE  RUN_ID = :run_id
                """, {'run_id': run_id})
                master_row = cursor.fetchone()
                master = {}
                if master_row:
                    master = {
                        'lob_name': master_row[0],
                        'track':    master_row[1],
                        'test_name':master_row[2],
                        'pc_run_id':str(master_row[3]) if master_row[3] else '',
                    }

                # ── 2. Monitoring runs count + status ───────────────────────
                cursor.execute("""
                    SELECT COUNT(*), MIN(START_TIME), MAX(END_TIME),
                           SUM(METRICS_COLLECTED)
                    FROM   API_APPD_MONITORING_RUNS
                    WHERE  RUN_ID = :run_id
                """, {'run_id': run_id})
                run_row = cursor.fetchone()
                monitoring_runs    = int(run_row[0]) if run_row[0] else 0
                monitoring_start   = run_row[1].isoformat() if run_row[1] else None
                monitoring_end     = run_row[2].isoformat() if run_row[2] else None
                metrics_collected  = int(run_row[3]) if run_row[3] else 0

                if monitoring_runs == 0:
                    return None  # No AppD data for this run

                # ── 3. Application metrics — aggregated by tier/app ─────────
                cursor.execute("""
                    SELECT
                        aa.APPLICATION_NAME,
                        at2.TIER_NAME,
                        COUNT(DISTINCT an.NODE_ID)          AS node_count,
                        COUNT(m.METRIC_ID)                  AS sample_count,
                        ROUND(AVG(m.RESPONSE_TIME_AVG_MS),2) AS avg_rt_ms,
                        ROUND(MAX(m.RESPONSE_TIME_MAX_MS),2) AS max_rt_ms,
                        ROUND(AVG(m.CALLS_PER_MINUTE),2)    AS avg_cpm,
                        ROUND(AVG(m.ERROR_RATE_PERCENT),3)  AS avg_err_pct,
                        ROUND(AVG(m.APDEX_SCORE),3)         AS avg_apdex,
                        SUM(m.ERRORS_TOTAL)                 AS total_errors,
                        SUM(m.BT_SLOW_COUNT + m.BT_VERY_SLOW_COUNT) AS slow_calls
                    FROM   API_APPD_APPLICATION_METRICS m
                    JOIN   API_APPD_NODES         an  ON m.NODE_ID  = an.NODE_ID
                    JOIN   API_APPD_TIERS         at2 ON m.TIER_ID  = at2.TIER_ID
                    JOIN   API_APPD_APPLICATIONS  aa  ON m.APP_ID   = aa.APP_ID
                    WHERE  m.RUN_ID = :run_id
                    GROUP  BY aa.APPLICATION_NAME, at2.TIER_NAME
                    ORDER  BY AVG(m.RESPONSE_TIME_AVG_MS) DESC NULLS LAST
                """, {'run_id': run_id})
                tier_cols = ['application_name','tier_name','node_count','sample_count',
                             'avg_rt_ms','max_rt_ms','avg_cpm','avg_err_pct',
                             'avg_apdex','total_errors','slow_calls']
                tier_summary = []
                for row in cursor.fetchall():
                    d = dict(zip(tier_cols, row))
                    for f in ['avg_rt_ms','max_rt_ms','avg_cpm','avg_err_pct','avg_apdex']:
                        if d.get(f) is not None: d[f] = float(d[f])
                    for f in ['node_count','sample_count','total_errors','slow_calls']:
                        if d.get(f) is not None: d[f] = int(d[f])
                    tier_summary.append(d)

                # ── 4. Node-level summary (top nodes by RT) ─────────────────
                cursor.execute("""
                    SELECT
                        an.NODE_NAME,
                        at2.TIER_NAME,
                        aa.APPLICATION_NAME,
                        ROUND(AVG(m.RESPONSE_TIME_AVG_MS),2) AS avg_rt_ms,
                        ROUND(MAX(m.RESPONSE_TIME_MAX_MS),2) AS max_rt_ms,
                        ROUND(AVG(m.CALLS_PER_MINUTE),2)     AS avg_cpm,
                        ROUND(AVG(m.ERROR_RATE_PERCENT),3)   AS avg_err_pct,
                        SUM(m.ERRORS_TOTAL)                  AS total_errors,
                        ROUND(AVG(m.APDEX_SCORE),3)          AS avg_apdex
                    FROM   API_APPD_APPLICATION_METRICS m
                    JOIN   API_APPD_NODES        an  ON m.NODE_ID = an.NODE_ID
                    JOIN   API_APPD_TIERS        at2 ON m.TIER_ID = at2.TIER_ID
                    JOIN   API_APPD_APPLICATIONS aa  ON m.APP_ID  = aa.APP_ID
                    WHERE  m.RUN_ID = :run_id
                    GROUP  BY an.NODE_NAME, at2.TIER_NAME, aa.APPLICATION_NAME
                    ORDER  BY AVG(m.RESPONSE_TIME_AVG_MS) DESC NULLS LAST
                    FETCH  FIRST 20 ROWS ONLY
                """, {'run_id': run_id})
                node_cols = ['node_name','tier_name','application_name',
                             'avg_rt_ms','max_rt_ms','avg_cpm','avg_err_pct',
                             'total_errors','avg_apdex']
                node_summary = []
                for row in cursor.fetchall():
                    d = dict(zip(node_cols, row))
                    for f in ['avg_rt_ms','max_rt_ms','avg_cpm','avg_err_pct','avg_apdex']:
                        if d.get(f) is not None: d[f] = float(d[f])
                    if d.get('total_errors') is not None: d['total_errors'] = int(d['total_errors'])
                    node_summary.append(d)

                # ── 5. JVM metrics — aggregated ─────────────────────────────
                cursor.execute("""
                    SELECT
                        ROUND(AVG(j.HEAP_USED_PERCENT),2)    AS avg_heap_pct,
                        ROUND(MAX(j.HEAP_USED_PERCENT),2)    AS max_heap_pct,
                        ROUND(AVG(j.GC_TIME_SPENT_PERCENT),2) AS avg_gc_pct,
                        ROUND(AVG(j.THREAD_COUNT),0)         AS avg_threads,
                        SUM(j.EXCEPTION_COUNT)               AS total_exceptions,
                        SUM(j.ERROR_COUNT)                   AS total_errors
                    FROM   API_APPD_JVM_METRICS j
                    WHERE  j.RUN_ID = :run_id
                """, {'run_id': run_id})
                jvm_row = cursor.fetchone()
                jvm_summary = {}
                if jvm_row and jvm_row[0] is not None:
                    jvm_summary = {
                        'avg_heap_pct':    float(jvm_row[0]) if jvm_row[0] else 0,
                        'max_heap_pct':    float(jvm_row[1]) if jvm_row[1] else 0,
                        'avg_gc_pct':      float(jvm_row[2]) if jvm_row[2] else 0,
                        'avg_threads':     int(jvm_row[3])   if jvm_row[3] else 0,
                        'total_exceptions':int(jvm_row[4])   if jvm_row[4] else 0,
                        'total_errors':    int(jvm_row[5])   if jvm_row[5] else 0,
                    }

                # ── 6. Server metrics — aggregated ──────────────────────────
                cursor.execute("""
                    SELECT
                        ROUND(AVG(s.CPU_BUSY_PCT),2)         AS avg_cpu_pct,
                        ROUND(MAX(s.CPU_BUSY_PCT),2)         AS max_cpu_pct,
                        ROUND(AVG(s.MEMORY_USED_PCT),2)      AS avg_mem_pct,
                        ROUND(MAX(s.MEMORY_USED_PCT),2)      AS max_mem_pct,
                        COUNT(DISTINCT s.NODE_ID)            AS node_count
                    FROM   API_APPD_SERVER_METRICS s
                    WHERE  s.RUN_ID = :run_id
                """, {'run_id': run_id})
                srv_row = cursor.fetchone()
                server_summary = {}
                if srv_row and srv_row[0] is not None:
                    server_summary = {
                        'avg_cpu_pct': float(srv_row[0]) if srv_row[0] else 0,
                        'max_cpu_pct': float(srv_row[1]) if srv_row[1] else 0,
                        'avg_mem_pct': float(srv_row[2]) if srv_row[2] else 0,
                        'max_mem_pct': float(srv_row[3]) if srv_row[3] else 0,
                        'node_count':  int(srv_row[4])   if srv_row[4] else 0,
                    }

                # ── 7. Overall app-level summary ────────────────────────────
                cursor.execute("""
                    SELECT
                        ROUND(AVG(m.RESPONSE_TIME_AVG_MS),2) AS overall_avg_rt,
                        ROUND(AVG(m.CALLS_PER_MINUTE),2)     AS overall_cpm,
                        ROUND(AVG(m.ERROR_RATE_PERCENT),3)   AS overall_err_pct,
                        COUNT(DISTINCT m.NODE_ID)            AS active_nodes,
                        COUNT(DISTINCT m.APP_ID)             AS app_count
                    FROM   API_APPD_APPLICATION_METRICS m
                    WHERE  m.RUN_ID = :run_id
                """, {'run_id': run_id})
                overall_row = cursor.fetchone()
                overall = {}
                if overall_row:
                    overall = {
                        'overall_avg_rt_ms': float(overall_row[0]) if overall_row[0] else 0,
                        'overall_cpm':       float(overall_row[1]) if overall_row[1] else 0,
                        'overall_err_pct':   float(overall_row[2]) if overall_row[2] else 0,
                        'active_nodes':      int(overall_row[3])   if overall_row[3] else 0,
                        'app_count':         int(overall_row[4])   if overall_row[4] else 0,
                    }

                return {
                    'run_id':            run_id,
                    'lob_name':          master.get('lob_name',''),
                    'track':             master.get('track',''),
                    'test_name':         master.get('test_name',''),
                    'pc_run_id':         master.get('pc_run_id',''),
                    'monitoring_runs':   monitoring_runs,
                    'monitoring_start':  monitoring_start,
                    'monitoring_end':    monitoring_end,
                    'metrics_collected': metrics_collected,
                    'overall':           overall,
                    'tier_summary':      tier_summary,
                    'node_summary':      node_summary,
                    'jvm_summary':       jvm_summary,
                    'server_summary':    server_summary,
                }

            except Exception as e:
                logger.error(f"AppD get_full_results_by_run_id error {run_id}: {e}", exc_info=True)
                return None
            finally:
                cursor.close()


# =============================================================================
# CHANGE 2: monitoring/appd/routes.py
# Add GET /results/{run_id}
# =============================================================================

@router.get("/results/{run_id}")
async def get_appd_results(run_id: str):
    """
    GET /api/v1/monitoring/appd/results/{run_id}
    Returns full AppD data: tier/node summaries, JVM, server metrics.
    Used by pc_report.html AppD section.
    """
    if not appd_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        result = appd_db.get_full_results_by_run_id(run_id)
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"No AppD monitoring data found for run_id: {run_id}. "
                       f"Run AppD monitoring via Start Monitoring to collect data."
            )
        return {"success": True, **result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_appd_results error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
