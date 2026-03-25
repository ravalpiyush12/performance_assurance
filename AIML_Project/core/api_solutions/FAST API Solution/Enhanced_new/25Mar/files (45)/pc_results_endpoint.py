# =============================================================================
# UPDATE: monitoring/pc/database.py — get_pc_results_by_run_id()
#
# Adds TEST_DURATION_MINUTES from API_RUN_MASTER join.
# Also adds LOB_NAME, TRACK to the response from RUN_MASTER
# (needed so save report always has lob_name even before PC data loads).
# =============================================================================

    def get_pc_results_by_run_id(self, run_id: str) -> dict:
        """
        Fetch PC test run + LR transactions + RUN_MASTER metadata for one run_id.
        """
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                # ── 1. PC Test run row ─────────────────────────────────────
                cursor.execute("""
                    SELECT p.PC_TEST_ID, p.RUN_ID, p.PC_RUN_ID,
                           p.PC_URL, p.DOMAIN, p.PROJECT,
                           p.TEST_STATUS, p.COLLATION_STATUS,
                           p.TEST_SET_NAME, p.TEST_INSTANCE_ID,
                           p.TOTAL_TRANSACTIONS, p.PASSED_TRANSACTIONS,
                           p.FAILED_TRANSACTIONS, p.AVERAGE_RESPONSE_TIME,
                           p.REPORT_FETCHED, p.CREATED_DATE,
                           r.LOB_NAME, r.TRACK, r.TEST_NAME,
                           r.TEST_DURATION_MINUTES,
                           r.TEST_START_TIME, r.TEST_END_TIME
                    FROM   API_PC_TEST_RUNS p
                    LEFT JOIN API_RUN_MASTER r ON p.RUN_ID = r.RUN_ID
                    WHERE  p.RUN_ID = :run_id
                    ORDER  BY p.CREATED_DATE DESC
                    FETCH  FIRST 1 ROW ONLY
                """, {'run_id': run_id})

                row = cursor.fetchone()
                if not row:
                    return None

                run = {
                    'pc_test_id':           int(row[0]) if row[0] else None,
                    'run_id':               row[1],
                    'pc_run_id':            str(row[2]) if row[2] else '',
                    'pc_url':               row[3] or '',
                    'domain':               row[4] or '',
                    'project':              row[5] or '',
                    'test_status':          row[6] or '',
                    'collation_status':     row[7] or '',
                    'test_set_name':        row[8] or '',
                    'test_instance_id':     row[9] or '',
                    'total_transactions':   int(row[10]) if row[10] else 0,
                    'passed_transactions':  int(row[11]) if row[11] else 0,
                    'failed_transactions':  int(row[12]) if row[12] else 0,
                    'average_response_time':float(row[13]) if row[13] else 0.0,
                    'report_fetched':       row[14],
                    'created_date':         row[15].isoformat() if row[15] else None,
                    # RUN_MASTER fields
                    'lob_name':             row[16] or '',
                    'track':                row[17] or '',
                    'test_name':            row[18] or '',
                    'duration_minutes':     float(row[19]) if row[19] else None,
                    'test_duration_minutes':float(row[19]) if row[19] else None,
                    'start_time':           row[20].isoformat() if row[20] else None,
                    'end_time':             row[21].isoformat() if row[21] else None,
                }

                # ── 2. Transactions ────────────────────────────────────────
                cursor.execute("""
                    SELECT TRANSACTION_ID, TRANSACTION_NAME,
                           MINIMUM_TIME, AVERAGE_TIME, MAXIMUM_TIME,
                           STD_DEVIATION,
                           PERCENTILE_90, PERCENTILE_95, PERCENTILE_99,
                           PASS_COUNT, FAIL_COUNT, STOP_COUNT, TOTAL_COUNT,
                           PASS_PERCENTAGE, THROUGHPUT_TPS
                    FROM   API_LR_TRANSACTION_RESULTS
                    WHERE  RUN_ID = :run_id
                    ORDER  BY TRANSACTION_NAME
                """, {'run_id': run_id})

                transactions = []
                for r in cursor.fetchall():
                    t = {
                        'transaction_id':   int(r[0])    if r[0]  is not None else None,
                        'transaction_name': r[1]         or '—',
                        'minimum_time':     float(r[2])  if r[2]  is not None else 0.0,
                        'average_time':     float(r[3])  if r[3]  is not None else 0.0,
                        'maximum_time':     float(r[4])  if r[4]  is not None else 0.0,
                        'std_deviation':    float(r[5])  if r[5]  is not None else 0.0,
                        'percentile_90':    float(r[6])  if r[6]  is not None else 0.0,
                        'percentile_95':    float(r[7])  if r[7]  is not None else None,  # keep None if null
                        'percentile_99':    float(r[8])  if r[8]  is not None else None,
                        'pass_count':       int(r[9])    if r[9]  is not None else 0,
                        'fail_count':       int(r[10])   if r[10] is not None else 0,
                        'stop_count':       int(r[11])   if r[11] is not None else 0,
                        'total_count':      int(r[12])   if r[12] is not None else 0,
                        'pass_percentage':  float(r[13]) if r[13] is not None else None,
                        'throughput_tps':   float(r[14]) if r[14] is not None else None,  # keep None if null
                    }
                    transactions.append(t)

                # ── 3. Summary stats ───────────────────────────────────────
                total   = len(transactions)
                passed  = sum(1 for t in transactions
                              if (t['pass_percentage'] or 0) >= 95.0
                              and t['fail_count'] == 0)
                failed  = sum(1 for t in transactions if t['fail_count'] > 0)
                avg_rt  = (sum(t['average_time'] for t in transactions) / total
                           if total else 0.0)
                p95_vals = [t['percentile_95'] for t in transactions if t['percentile_95'] is not None]
                max_p95  = max(p95_vals) if p95_vals else 0.0

                return {
                    'success':               True,
                    'run_id':                run['run_id'],
                    'pc_run_id':             run['pc_run_id'],
                    'lob_name':              run['lob_name'],
                    'track':                 run['track'],
                    'test_name':             run['test_name'],
                    'test_status':           run['test_status'],
                    'collation_status':      run['collation_status'],
                    'project':               run['project'],
                    'duration_minutes':      run['duration_minutes'],
                    'test_duration_minutes': run['test_duration_minutes'],
                    'start_time':            run['start_time'],
                    'end_time':              run['end_time'],
                    'total_transactions':    total,
                    'passed_transactions':   passed,
                    'failed_transactions':   failed,
                    'average_response_time': round(avg_rt, 3),
                    'max_p95':               round(max_p95, 3) if max_p95 else 0.0,
                    'transactions':          transactions,
                }

            except Exception as e:
                logger.error(f"get_pc_results_by_run_id error {run_id}: {e}", exc_info=True)
                return None
            finally:
                cursor.close()


# =============================================================================
# ROUTE (unchanged — already exists, just ensure it calls the updated method)
# =============================================================================

@router.get("/results/{run_id}")
async def get_pc_results(run_id: str):
    """
    GET /api/v1/monitoring/pc/results/{run_id}
    Returns PC test + LR transactions + duration from API_RUN_MASTER.
    """
    if not pc_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        result = pc_db.get_pc_results_by_run_id(run_id)
        if not result:
            raise HTTPException(status_code=404,
                detail=f"No PC results found for run_id: {run_id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_pc_results error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
