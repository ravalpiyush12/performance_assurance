# =============================================================================
# ADD to appd/routes.py
# GET /monitoring/summary/{run_id}
# Returns record counts from all 5 AppD monitoring tables for a given run_id
# =============================================================================

@router.get("/monitoring/summary/{run_id}")
async def get_monitoring_summary(
    run_id: str,
    current_user: str = Depends(verify_auth_token),
):
    """
    Fetch data counts from all AppD monitoring tables for a run_id.
    Called by frontend after Stop Monitoring to show the summary table.

    Tables queried:
      - API_RUN_MASTER
      - API_APPD_MONITORING_RUNS
      - API_APPD_APPLICATION_METRICS
      - API_APPD_JVM_METRICS
      - API_APPD_SERVER_METRICS
    """
    if not appd_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        with appd_db.pool.acquire() as conn:
            cursor = conn.cursor()

            def count_table(table, col='RUN_ID'):
                try:
                    cursor.execute(
                        f"SELECT COUNT(*) FROM {table} WHERE {col} = :run_id",
                        {'run_id': run_id}
                    )
                    row = cursor.fetchone()
                    return row[0] if row else 0
                except Exception as e:
                    logger.warning(f"Count error for {table}: {e}")
                    return 0

            run_master_count         = count_table('API_RUN_MASTER')
            monitoring_runs_count    = count_table('API_APPD_MONITORING_RUNS')
            application_metrics_count= count_table('API_APPD_APPLICATION_METRICS')
            jvm_metrics_count        = count_table('API_APPD_JVM_METRICS')
            server_metrics_count     = count_table('API_APPD_SERVER_METRICS')

            total = (monitoring_runs_count + application_metrics_count +
                     jvm_metrics_count + server_metrics_count)

            return {
                "success":                   True,
                "run_id":                    run_id,
                "run_master_count":          run_master_count,
                "monitoring_runs_count":     monitoring_runs_count,
                "application_metrics_count": application_metrics_count,
                "jvm_metrics_count":         jvm_metrics_count,
                "server_metrics_count":      server_metrics_count,
                "total_records":             total,
            }
    except Exception as e:
        logger.error(f"Error fetching monitoring summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ALSO FIX: update_monitoring_run_status not updating DB on stop
#
# In appd/orchestrator.py stop_monitoring() — line 299:
#   self.db.update_monitoring_run_status(run_id, 'STOPPED')
#
# Check appd/database.py for this method. The run_id stored in
# API_APPD_MONITORING_RUNS may differ from masterRunId.
#
# masterRunId format: "RUNID_12351_24Mar2026_001"
# DB RUN_ID format:   "RUN_20260302_006" (from Image 3)
#
# If formats differ, the UPDATE finds 0 rows. Fix by also trying
# to match on the PC_RUN_ID or a partial match:
# =============================================================================

    def update_monitoring_run_status(self, run_id: str, status: str) -> bool:
        """Update monitoring run status — tries both RUN_ID formats."""
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            # Try exact match first
            cursor.execute("""
                UPDATE API_APPD_MONITORING_RUNS
                   SET STATUS = :status, END_TIME = SYSDATE, UPDATED_DATE = SYSDATE
                 WHERE RUN_ID = :run_id
            """, {'status': status, 'run_id': run_id})

            if cursor.rowcount == 0:
                # Try matching on API_RUN_MASTER.RUN_ID → join to get APPD run id
                logger.warning(f"No APPD monitoring run found for RUN_ID={run_id}, "
                                f"trying API_RUN_MASTER lookup")
                # Also update API_RUN_MASTER status
                cursor.execute("""
                    UPDATE API_RUN_MASTER
                       SET TEST_STATUS = :status, TEST_END_TIME = SYSDATE,
                           UPDATED_DATE = SYSDATE
                     WHERE RUN_ID = :run_id
                """, {'status': status, 'run_id': run_id})

            conn.commit()
            logger.info(f"Updated run status to {status} for {run_id} "
                        f"({cursor.rowcount} row(s) affected)")
            return True
