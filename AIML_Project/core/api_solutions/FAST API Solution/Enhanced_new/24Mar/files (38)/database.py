"""
reports/database.py
Database operations for NFT Release Reports (API_NFT_RELEASE_REPORTS).
"""
import logging
from typing import Optional, Dict, Any, List
import oracledb

logger = logging.getLogger(__name__)


class ReportsDatabase:
    """Handles all Oracle operations for NFT_RELEASE_REPORTS."""

    def __init__(self, pool):
        self.pool = pool

    # ──────────────────────────────────────────────────────────────
    # SAVE
    # ──────────────────────────────────────────────────────────────
    def save_release_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert a new release report row.

        Expected keys in data:
          run_id, pc_run_id, lob_name, release_name, test_type,
          test_name, track_name, report_html,
          overall_status, pass_rate_pct, peak_vusers,
          avg_response_ms, p95_response_ms,
          total_transactions, failed_transactions,
          saved_by, notes
        """
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                html = data.get('report_html', '') or ''
                html_size_kb = round(len(html.encode('utf-8')) / 1024, 2)

                # oracledb 2.x: use a CLOB variable for large text
                clob_var = cursor.var(oracledb.DB_TYPE_CLOB)
                clob_var.setvalue(0, html)

                out_id = cursor.var(oracledb.NUMBER)

                cursor.execute("""
                    INSERT INTO API_NFT_RELEASE_REPORTS (
                        RUN_ID, PC_RUN_ID, LOB_NAME, RELEASE_NAME, TEST_TYPE,
                        TEST_NAME, TRACK_NAME, REPORT_HTML, REPORT_SIZE_KB,
                        OVERALL_STATUS, PASS_RATE_PCT, PEAK_VUSERS,
                        AVG_RESPONSE_MS, P95_RESPONSE_MS,
                        TOTAL_TRANSACTIONS, FAILED_TRANSACTIONS,
                        SAVED_BY, NOTES, IS_ACTIVE
                    ) VALUES (
                        :run_id, :pc_run_id, :lob_name, :release_name, :test_type,
                        :test_name, :track_name, :report_html, :report_size_kb,
                        :overall_status, :pass_rate_pct, :peak_vusers,
                        :avg_response_ms, :p95_response_ms,
                        :total_transactions, :failed_transactions,
                        :saved_by, :notes, 'Y'
                    )
                    RETURNING REPORT_ID INTO :out_id
                """, {
                    'run_id':               data.get('run_id', ''),
                    'pc_run_id':            str(data.get('pc_run_id', '')),
                    'lob_name':             data.get('lob_name', ''),
                    'release_name':         data.get('release_name', ''),
                    'test_type':            data.get('test_type', 'LOAD'),
                    'test_name':            data.get('test_name', ''),
                    'track_name':           data.get('track_name', ''),
                    'report_html':          clob_var,
                    'report_size_kb':       html_size_kb,
                    'overall_status':       data.get('overall_status', ''),
                    'pass_rate_pct':        data.get('pass_rate_pct'),
                    'peak_vusers':          data.get('peak_vusers'),
                    'avg_response_ms':      data.get('avg_response_ms'),
                    'p95_response_ms':      data.get('p95_response_ms'),
                    'total_transactions':   data.get('total_transactions'),
                    'failed_transactions':  data.get('failed_transactions'),
                    'saved_by':             data.get('saved_by', 'system'),
                    'notes':                data.get('notes', ''),
                    'out_id':               out_id,
                })
                conn.commit()
                report_id = int(out_id.getvalue()[0])
                logger.info(f"Saved release report ID={report_id}, run={data.get('run_id')}, size={html_size_kb} KB")
                return {
                    'success': True,
                    'report_id': report_id,
                    'report_size_kb': html_size_kb,
                    'message': f"Report saved successfully (ID: {report_id}, {html_size_kb} KB)"
                }

            except oracledb.IntegrityError as e:
                conn.rollback()
                err = str(e)
                if 'unique constraint' in err.lower() or 'ORA-00001' in err:
                    return {
                        'success': False,
                        'error': f"A {data.get('test_type','LOAD')} report for run '{data.get('run_id')}' is already saved. "
                                 f"Use a different test type or delete the existing report first."
                    }
                logger.error(f"IntegrityError saving report: {e}")
                return {'success': False, 'error': str(e)}

            except Exception as e:
                conn.rollback()
                logger.error(f"Error saving release report: {e}", exc_info=True)
                return {'success': False, 'error': str(e)}

            finally:
                cursor.close()

    # ──────────────────────────────────────────────────────────────
    # LIST
    # ──────────────────────────────────────────────────────────────
    def get_release_reports(
        self,
        lob_name: str,
        release_name: Optional[str] = None,
        test_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """List saved reports (no HTML content — metadata only)."""
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                params: Dict[str, Any] = {'lob_name': lob_name, 'limit': limit}
                sql = """
                    SELECT REPORT_ID, RUN_ID, PC_RUN_ID, LOB_NAME,
                           RELEASE_NAME, TEST_TYPE, TEST_NAME, TRACK_NAME,
                           REPORT_SIZE_KB, OVERALL_STATUS, PASS_RATE_PCT,
                           PEAK_VUSERS, AVG_RESPONSE_MS, P95_RESPONSE_MS,
                           TOTAL_TRANSACTIONS, FAILED_TRANSACTIONS,
                           SAVED_BY, SAVED_DATE, NOTES
                    FROM   API_NFT_RELEASE_REPORTS
                    WHERE  LOB_NAME = :lob_name
                    AND    IS_ACTIVE = 'Y'
                """
                if release_name:
                    sql += " AND RELEASE_NAME = :release_name"
                    params['release_name'] = release_name
                if test_type:
                    sql += " AND TEST_TYPE = :test_type"
                    params['test_type'] = test_type
                sql += " ORDER BY SAVED_DATE DESC FETCH FIRST :limit ROWS ONLY"

                cursor.execute(sql, params)
                cols = [
                    'report_id', 'run_id', 'pc_run_id', 'lob_name',
                    'release_name', 'test_type', 'test_name', 'track_name',
                    'report_size_kb', 'overall_status', 'pass_rate_pct',
                    'peak_vusers', 'avg_response_ms', 'p95_response_ms',
                    'total_transactions', 'failed_transactions',
                    'saved_by', 'saved_date', 'notes'
                ]
                result = []
                for row in cursor.fetchall():
                    d = dict(zip(cols, row))
                    d['saved_date'] = d['saved_date'].isoformat() if d['saved_date'] else None
                    result.append(d)
                return result
            except Exception as e:
                logger.error(f"Error listing release reports: {e}")
                return []
            finally:
                cursor.close()

    # ──────────────────────────────────────────────────────────────
    # FETCH HTML (for viewing a saved report)
    # ──────────────────────────────────────────────────────────────
    def get_report_html(self, report_id: int) -> Optional[str]:
        """Fetch the full CLOB HTML for one report."""
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT REPORT_HTML
                    FROM   API_NFT_RELEASE_REPORTS
                    WHERE  REPORT_ID = :report_id
                    AND    IS_ACTIVE = 'Y'
                """, {'report_id': report_id})
                row = cursor.fetchone()
                if not row:
                    return None
                clob = row[0]
                return clob.read() if clob else None
            except Exception as e:
                logger.error(f"Error fetching report HTML {report_id}: {e}")
                return None
            finally:
                cursor.close()

    # ──────────────────────────────────────────────────────────────
    # SOFT DELETE
    # ──────────────────────────────────────────────────────────────
    def delete_report(self, report_id: int) -> bool:
        """Soft-delete a report (sets IS_ACTIVE = 'N')."""
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE API_NFT_RELEASE_REPORTS
                    SET    IS_ACTIVE = 'N'
                    WHERE  REPORT_ID = :report_id
                """, {'report_id': report_id})
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                conn.rollback()
                logger.error(f"Error deleting report {report_id}: {e}")
                return False
            finally:
                cursor.close()
