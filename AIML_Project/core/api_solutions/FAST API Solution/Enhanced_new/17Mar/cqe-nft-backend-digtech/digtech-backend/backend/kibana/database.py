"""
Kibana Database Operations
All CRUD for API_KIBANA_METRICS table.
Follows exact AppDynamicsDatabase pattern from appd/database.py.
"""
import logging
import json
from typing import List, Dict, Optional
from datetime import datetime
import oracledb

logger = logging.getLogger(__name__)


class KibanaDatabase:
    """Database operations for Kibana monitoring."""

    def __init__(self, connection_pool=None):
        self.connection_pool = connection_pool

    def _get_connection(self):
        if self.connection_pool:
            return self.connection_pool.acquire()
        raise RuntimeError("Database connection pool is not initialized.")

    # =========================================================================
    # Metrics Operations
    # =========================================================================

    def insert_kibana_metrics(self, run_id: str, dashboard_id: str,
                               dashboard_name: str, metrics: Dict) -> int:
        """Insert Kibana API endpoint metrics for a monitoring run."""
        conn = self._get_connection()
        cursor = conn.cursor()
        metric_id_var = cursor.var(oracledb.NUMBER)
        try:
            cursor.execute("""
                INSERT INTO API_KIBANA_METRICS (
                    METRIC_ID, RUN_ID, DASHBOARD_ID, DASHBOARD_NAME,
                    API_ENDPOINT, API_NAME, COLLECTION_TIME,
                    TOTAL_REQUESTS, TOTAL_COUNT,
                    PASS_COUNT, FAIL_COUNT,
                    MIN_RESPONSE_TIME_MS, AVG_RESPONSE_TIME_MS,
                    MAX_RESPONSE_TIME_MS, P90_RESPONSE_TIME_MS,
                    P95_RESPONSE_TIME_MS, ADDITIONAL_METRICS
                ) VALUES (
                    API_KIBANA_METRICS_SEQ.NEXTVAL, :run_id, :dashboard_id, :dashboard_name,
                    :api_endpoint, :api_name, SYSTIMESTAMP,
                    :total_requests, :total_count,
                    :pass_count, :fail_count,
                    :min_rt, :avg_rt,
                    :max_rt, :p90_rt,
                    :p95_rt, :additional
                ) RETURNING METRIC_ID INTO :metric_id_out
            """, {
                'run_id':        run_id,
                'dashboard_id':  dashboard_id,
                'dashboard_name': dashboard_name,
                'api_endpoint':  metrics.get('api_endpoint'),
                'api_name':      metrics.get('api_name', metrics.get('api_endpoint')),
                'total_requests': metrics.get('total_requests', 0),
                'total_count':   metrics.get('total_count', metrics.get('total_requests', 0)),
                'pass_count':    metrics.get('pass_count', 0),
                'fail_count':    metrics.get('fail_count', 0),
                'min_rt':        metrics.get('min_response_time', 0),
                'avg_rt':        metrics.get('avg_response_time', 0),
                'max_rt':        metrics.get('max_response_time', 0),
                'p90_rt':        metrics.get('p90_response_time', 0),
                'p95_rt':        metrics.get('p95_response_time', 0),
                'additional':    json.dumps(metrics.get('additional', {})),
                'metric_id_out': metric_id_var,
            })
            conn.commit()
            return int(metric_id_var.getvalue()[0])
        finally:
            cursor.close()
            conn.close()

    def insert_kibana_metrics_batch(self, run_id: str, dashboard_id: str,
                                     dashboard_name: str,
                                     metrics_list: List[Dict]) -> int:
        """Insert multiple Kibana endpoint metrics in one connection. Returns count inserted."""
        if not metrics_list:
            return 0
        conn = self._get_connection()
        cursor = conn.cursor()
        count = 0
        try:
            for metrics in metrics_list:
                cursor.execute("""
                    INSERT INTO API_KIBANA_METRICS (
                        METRIC_ID, RUN_ID, DASHBOARD_ID, DASHBOARD_NAME,
                        API_ENDPOINT, API_NAME, COLLECTION_TIME,
                        TOTAL_REQUESTS, TOTAL_COUNT,
                        PASS_COUNT, FAIL_COUNT,
                        MIN_RESPONSE_TIME_MS, AVG_RESPONSE_TIME_MS,
                        MAX_RESPONSE_TIME_MS, P90_RESPONSE_TIME_MS,
                        P95_RESPONSE_TIME_MS, ADDITIONAL_METRICS
                    ) VALUES (
                        API_KIBANA_METRICS_SEQ.NEXTVAL, :run_id, :dashboard_id, :dashboard_name,
                        :api_endpoint, :api_name, SYSTIMESTAMP,
                        :total_requests, :total_count,
                        :pass_count, :fail_count,
                        :min_rt, :avg_rt,
                        :max_rt, :p90_rt,
                        :p95_rt, :additional
                    )
                """, {
                    'run_id':        run_id,
                    'dashboard_id':  dashboard_id,
                    'dashboard_name': dashboard_name,
                    'api_endpoint':  metrics.get('api_endpoint'),
                    'api_name':      metrics.get('api_name', metrics.get('api_endpoint')),
                    'total_requests': metrics.get('total_requests', 0),
                    'total_count':   metrics.get('total_count', metrics.get('total_requests', 0)),
                    'pass_count':    metrics.get('pass_count', 0),
                    'fail_count':    metrics.get('fail_count', 0),
                    'min_rt':        metrics.get('min_response_time', 0),
                    'avg_rt':        metrics.get('avg_response_time', 0),
                    'max_rt':        metrics.get('max_response_time', 0),
                    'p90_rt':        metrics.get('p90_response_time', 0),
                    'p95_rt':        metrics.get('p95_response_time', 0),
                    'additional':    json.dumps(metrics.get('additional', {})),
                })
                count += 1
            conn.commit()
            return count
        except Exception as e:
            conn.rollback()
            logger.error(f"Batch insert error: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    def get_metrics_by_run_id(self, run_id: str) -> List[Dict]:
        """Get all Kibana metrics for a run_id, aggregated by dashboard."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT
                    METRIC_ID, RUN_ID, DASHBOARD_ID, DASHBOARD_NAME,
                    API_ENDPOINT, API_NAME, COLLECTION_TIME,
                    TOTAL_REQUESTS, TOTAL_COUNT,
                    PASS_COUNT, FAIL_COUNT,
                    MIN_RESPONSE_TIME_MS, AVG_RESPONSE_TIME_MS,
                    MAX_RESPONSE_TIME_MS, P90_RESPONSE_TIME_MS,
                    P95_RESPONSE_TIME_MS, ADDITIONAL_METRICS,
                    CREATED_DATE
                FROM API_KIBANA_METRICS
                WHERE RUN_ID = :run_id
                ORDER BY DASHBOARD_NAME, API_NAME, COLLECTION_TIME
            """, {'run_id': run_id})
            columns = [col[0].lower() for col in cursor.description]
            rows = cursor.fetchall()
            metrics = []
            for row in rows:
                m = dict(zip(columns, row))
                # Parse CLOB additional_metrics
                if m.get('additional_metrics'):
                    addl = m['additional_metrics']
                    if hasattr(addl, 'read'):
                        addl = addl.read()
                    try:
                        m['additional_metrics'] = json.loads(str(addl))
                    except Exception:
                        m['additional_metrics'] = {}
                # Serialize datetimes
                for k in ('collection_time', 'created_date'):
                    if m.get(k) and hasattr(m[k], 'isoformat'):
                        m[k] = m[k].isoformat()
                metrics.append(m)
            return metrics
        finally:
            cursor.close()
            conn.close()

    def get_summary_by_run_id(self, run_id: str) -> Dict:
        """Get aggregated summary of Kibana metrics for a run."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT
                    COUNT(DISTINCT API_ENDPOINT)    AS total_endpoints,
                    SUM(TOTAL_REQUESTS)             AS total_requests,
                    SUM(PASS_COUNT)                 AS total_pass,
                    SUM(FAIL_COUNT)                 AS total_fail,
                    ROUND(AVG(AVG_RESPONSE_TIME_MS), 2) AS avg_rt_ms,
                    ROUND(AVG(P90_RESPONSE_TIME_MS), 2) AS avg_p90_ms,
                    ROUND(AVG(P95_RESPONSE_TIME_MS), 2) AS avg_p95_ms,
                    COUNT(DISTINCT DASHBOARD_ID)    AS total_dashboards
                FROM API_KIBANA_METRICS
                WHERE RUN_ID = :run_id
            """, {'run_id': run_id})
            row = cursor.fetchone()
            if not row:
                return {}
            total_req = row[1] or 0
            total_pass = row[2] or 0
            pass_rate = round((total_pass / total_req * 100), 2) if total_req > 0 else 0
            return {
                'total_endpoints':  row[0] or 0,
                'total_requests':   total_req,
                'total_pass':       total_pass,
                'total_fail':       row[3] or 0,
                'pass_rate_percent': pass_rate,
                'avg_response_time_ms': row[4] or 0,
                'avg_p90_ms':       row[5] or 0,
                'avg_p95_ms':       row[6] or 0,
                'total_dashboards': row[7] or 0,
            }
        finally:
            cursor.close()
            conn.close()

    def get_metrics_by_dashboard(self, run_id: str, dashboard_id: str) -> List[Dict]:
        """Get all endpoint metrics for a specific dashboard in a run."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT
                    API_ENDPOINT, API_NAME, TOTAL_REQUESTS, PASS_COUNT, FAIL_COUNT,
                    MIN_RESPONSE_TIME_MS, AVG_RESPONSE_TIME_MS, MAX_RESPONSE_TIME_MS,
                    P90_RESPONSE_TIME_MS, P95_RESPONSE_TIME_MS, COLLECTION_TIME
                FROM API_KIBANA_METRICS
                WHERE RUN_ID = :run_id AND DASHBOARD_ID = :dashboard_id
                ORDER BY TOTAL_REQUESTS DESC
            """, {'run_id': run_id, 'dashboard_id': dashboard_id})
            columns = [col[0].lower() for col in cursor.description]
            rows = cursor.fetchall()
            result = []
            for row in rows:
                m = dict(zip(columns, row))
                if m.get('collection_time') and hasattr(m['collection_time'], 'isoformat'):
                    m['collection_time'] = m['collection_time'].isoformat()
                result.append(m)
            return result
        finally:
            cursor.close()
            conn.close()

    def delete_metrics_by_run_id(self, run_id: str) -> int:
        """Delete all Kibana metrics for a run_id. Returns deleted count."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM API_KIBANA_METRICS WHERE RUN_ID = :run_id",
                {'run_id': run_id}
            )
            deleted = cursor.rowcount
            conn.commit()
            return deleted
        finally:
            cursor.close()
            conn.close()
