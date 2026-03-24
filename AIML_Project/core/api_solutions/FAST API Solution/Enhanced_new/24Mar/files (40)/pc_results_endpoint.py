# =============================================================================
# CHANGE 1 — monitoring/pc/database.py
# Add this method to your PCDatabase class.
# =============================================================================

    def get_pc_results_by_run_id(self, run_id: str) -> dict:
        """
        Fetch PC test run + all LR transactions for one master RUN_ID.
        Returns None if not found.
        """
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                # ── Test run row ─────────────────────────────────────────────
                cursor.execute("""
                    SELECT PC_TEST_ID, RUN_ID, PC_RUN_ID,
                           PC_URL, DOMAIN, PROJECT,
                           TEST_STATUS, COLLATION_STATUS,
                           TEST_SET_NAME, TEST_INSTANCE_ID,
                           TOTAL_TRANSACTIONS, PASSED_TRANSACTIONS,
                           FAILED_TRANSACTIONS, AVERAGE_RESPONSE_TIME,
                           REPORT_FETCHED, CREATED_DATE
                    FROM   API_PC_TEST_RUNS
                    WHERE  RUN_ID = :run_id
                    ORDER  BY CREATED_DATE DESC
                    FETCH  FIRST 1 ROW ONLY
                """, {'run_id': run_id})

                row = cursor.fetchone()
                if not row:
                    return None

                run = {
                    'pc_test_id':            row[0],
                    'run_id':                row[1],
                    'pc_run_id':             str(row[2]) if row[2] else '',
                    'pc_url':                row[3],
                    'domain':                row[4],
                    'project':               row[5],
                    'test_status':           row[6],
                    'collation_status':      row[7],
                    'test_set_name':         row[8],
                    'test_instance_id':      row[9],
                    'total_transactions':    int(row[10]) if row[10] else 0,
                    'passed_transactions':   int(row[11]) if row[11] else 0,
                    'failed_transactions':   int(row[12]) if row[12] else 0,
                    'average_response_time': float(row[13]) if row[13] else 0.0,
                    'report_fetched':        row[14],
                    'created_date':          row[15].isoformat() if row[15] else None,
                }

                # ── Transactions ─────────────────────────────────────────────
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
                        'transaction_id':   r[0],
                        'transaction_name': r[1],
                        'minimum_time':     float(r[2])  if r[2]  is not None else 0.0,
                        'average_time':     float(r[3])  if r[3]  is not None else 0.0,
                        'maximum_time':     float(r[4])  if r[4]  is not None else 0.0,
                        'std_deviation':    float(r[5])  if r[5]  is not None else 0.0,
                        'percentile_90':    float(r[6])  if r[6]  is not None else 0.0,
                        'percentile_95':    float(r[7])  if r[7]  is not None else 0.0,
                        'percentile_99':    float(r[8])  if r[8]  is not None else 0.0,
                        'pass_count':       int(r[9])    if r[9]  is not None else 0,
                        'fail_count':       int(r[10])   if r[10] is not None else 0,
                        'stop_count':       int(r[11])   if r[11] is not None else 0,
                        'total_count':      int(r[12])   if r[12] is not None else 0,
                        'pass_percentage':  float(r[13]) if r[13] is not None else 0.0,
                        'throughput_tps':   float(r[14]) if r[14] is not None else 0.0,
                    }
                    transactions.append(t)

                return {'run': run, 'transactions': transactions}

            except Exception as e:
                logger.error(f"get_pc_results_by_run_id error {run_id}: {e}", exc_info=True)
                return None
            finally:
                cursor.close()


# =============================================================================
# CHANGE 2 — monitoring/pc/routes.py
# Replace your existing GET /results/{run_id} with this.
# =============================================================================

@router.get("/results/{run_id}")
async def get_pc_results(run_id: str):
    """
    GET /api/v1/monitoring/pc/results/{run_id}
    Returns PC test run + LR transactions for a master RUN_ID.
    Used by upload-reports.html and pc_report.html.
    """
    if not pc_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        result = pc_db.get_pc_results_by_run_id(run_id)
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"No PC results found for run_id: {run_id}"
            )
        run = result['run']
        transactions = result['transactions']

        # Calculate summary stats
        total  = len(transactions)
        passed = sum(1 for t in transactions if t['pass_percentage'] >= 95.0)
        failed = total - passed
        avg_rt = (
            sum(t['average_time'] for t in transactions) / total
            if total else 0.0
        )
        max_p95 = max((t['percentile_95'] for t in transactions), default=0.0)

        return {
            "success":              True,
            "run_id":               run['run_id'],
            "pc_run_id":            run['pc_run_id'],
            "status":               run['test_status'],
            "collation_status":     run['collation_status'],
            "project":              run['project'],
            "domain":               run['domain'],
            "test_set_name":        run['test_set_name'],
            "created_date":         run['created_date'],
            "total_transactions":   total,
            "passed_transactions":  passed,
            "failed_transactions":  failed,
            "average_response_time": round(avg_rt, 3),
            "max_p95":              round(max_p95, 3),
            "transactions":         transactions,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_pc_results error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
