"""
APPD DATABASE ADDITIONS
=======================
Add these methods to your existing AppDynamicsDatabase class in appd/database.py.

These methods retrieve stored metrics for a given run_id — used by the
test-report.html page to show real AppD data.
"""

# ─── ADD THESE METHODS to AppDynamicsDatabase class ───────────────────────────

def get_application_metrics_by_run(self, run_id: str) -> list:
    """
    Get all API_APPD_APPLICATION_METRICS rows for a run_id.
    Joins to nodes/tiers/apps for display names.
    """
    conn = self._get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT
                m.METRIC_ID,
                a.APPLICATION_NAME,
                t.TIER_NAME,
                n.NODE_NAME,
                m.COLLECTION_TIME,
                m.CALLS_PER_MINUTE,
                m.CALLS_TOTAL,
                m.RESPONSE_TIME_AVG_MS,
                m.RESPONSE_TIME_MIN_MS,
                m.RESPONSE_TIME_MAX_MS,
                m.RESPONSE_TIME_P90_MS,
                m.RESPONSE_TIME_P95_MS,
                m.RESPONSE_TIME_P99_MS,
                m.ERRORS_PER_MINUTE,
                m.ERROR_RATE_PERCENT,
                m.ERRORS_TOTAL,
                m.BT_NORMAL_COUNT,
                m.BT_SLOW_COUNT,
                m.BT_VERY_SLOW_COUNT,
                m.BT_STALLED_COUNT,
                m.BT_ERROR_COUNT,
                m.APDEX_SCORE
            FROM API_APPD_APPLICATION_METRICS m
            JOIN API_APPD_NODES n     ON m.NODE_ID = n.NODE_ID
            JOIN API_APPD_TIERS t     ON m.TIER_ID = t.TIER_ID
            JOIN API_APPD_APPLICATIONS a ON m.APP_ID = a.APP_ID
            WHERE m.RUN_ID = :run_id
            ORDER BY a.APPLICATION_NAME, t.TIER_NAME, m.COLLECTION_TIME
        """, {'run_id': run_id})
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


def get_server_metrics_by_run(self, run_id: str) -> list:
    """
    Get all API_APPD_SERVER_METRICS for a run_id.
    Joins to node/tier/app for display names.
    """
    conn = self._get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT
                s.METRIC_ID,
                n.NODE_NAME,
                n.MACHINE_NAME,
                t.TIER_NAME,
                a.APPLICATION_NAME,
                s.COLLECTION_TIME,
                s.CPU_BUSY_PERCENT,
                s.CPU_IDLE_PERCENT,
                s.MEMORY_TOTAL_MB,
                s.MEMORY_USED_MB,
                s.MEMORY_USED_PERCENT,
                s.NETWORK_INCOMING_KB,
                s.NETWORK_OUTGOING_KB,
                s.DISK_READS_PER_SEC,
                s.DISK_WRITES_PER_SEC,
                s.DISK_USED_PERCENT
            FROM API_APPD_SERVER_METRICS s
            JOIN API_APPD_NODES n     ON s.NODE_ID = n.NODE_ID
            JOIN API_APPD_TIERS t     ON n.TIER_ID = t.TIER_ID
            JOIN API_APPD_APPLICATIONS a ON t.APP_ID = a.APP_ID
            WHERE s.RUN_ID = :run_id
            ORDER BY a.APPLICATION_NAME, t.TIER_NAME, n.NODE_NAME, s.COLLECTION_TIME
        """, {'run_id': run_id})
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


def get_jvm_metrics_by_run(self, run_id: str) -> list:
    """Get JVM metrics for a run_id with node/app names."""
    conn = self._get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT
                j.METRIC_ID,
                n.NODE_NAME,
                t.TIER_NAME,
                a.APPLICATION_NAME,
                j.COLLECTION_TIME,
                j.HEAP_USED_MB,
                j.HEAP_MAX_MB,
                j.HEAP_USED_PERCENT,
                j.GC_TIME_MS,
                j.GC_MAJOR_COLLECTION_COUNT,
                j.GC_MINOR_COLLECTION_COUNT,
                j.THREAD_COUNT,
                j.THREAD_BLOCKED,
                j.EXCEPTION_COUNT,
                j.SLOW_CALLS_COUNT,
                j.VERY_SLOW_CALLS_COUNT
            FROM API_APPD_JVM_METRICS j
            JOIN API_APPD_NODES n     ON j.NODE_ID = n.NODE_ID
            JOIN API_APPD_TIERS t     ON n.TIER_ID = t.TIER_ID
            JOIN API_APPD_APPLICATIONS a ON t.APP_ID = a.APP_ID
            WHERE j.RUN_ID = :run_id
            ORDER BY a.APPLICATION_NAME, n.NODE_NAME, j.COLLECTION_TIME
        """, {'run_id': run_id})
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


def get_run_summary(self, run_id: str) -> dict:
    """
    Aggregated AppD summary for a run_id.
    Used by test-report.html summary cards.
    """
    conn = self._get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT
                COUNT(DISTINCT m.NODE_ID)               AS active_nodes,
                COUNT(DISTINCT m.APP_ID)                AS total_apps,
                COUNT(DISTINCT m.TIER_ID)               AS total_tiers,
                ROUND(AVG(m.RESPONSE_TIME_AVG_MS), 2)  AS avg_rt_ms,
                ROUND(AVG(m.RESPONSE_TIME_P90_MS), 2)  AS avg_p90_ms,
                ROUND(AVG(m.RESPONSE_TIME_P95_MS), 2)  AS avg_p95_ms,
                ROUND(AVG(m.ERROR_RATE_PERCENT), 2)    AS avg_error_rate,
                SUM(m.CALLS_TOTAL)                      AS total_calls,
                SUM(m.ERRORS_TOTAL)                     AS total_errors,
                ROUND(AVG(m.APDEX_SCORE), 3)           AS avg_apdex,
                ROUND(AVG(s.CPU_BUSY_PERCENT), 2)      AS avg_cpu_percent,
                ROUND(AVG(s.MEMORY_USED_PERCENT), 2)   AS avg_memory_percent
            FROM API_APPD_APPLICATION_METRICS m
            LEFT JOIN API_APPD_SERVER_METRICS s
                ON m.RUN_ID = s.RUN_ID AND m.NODE_ID = s.NODE_ID
            WHERE m.RUN_ID = :run_id
        """, {'run_id': run_id})
        row = cursor.fetchone()
        if not row:
            return {}
        return {
            'active_nodes':      row[0] or 0,
            'total_apps':        row[1] or 0,
            'total_tiers':       row[2] or 0,
            'avg_rt_ms':         row[3] or 0,
            'avg_p90_ms':        row[4] or 0,
            'avg_p95_ms':        row[5] or 0,
            'avg_error_rate':    row[6] or 0,
            'total_calls':       row[7] or 0,
            'total_errors':      row[8] or 0,
            'avg_apdex':         row[9] or 0,
            'avg_cpu_percent':   row[10] or 0,
            'avg_memory_percent': row[11] or 0,
        }
    finally:
        cursor.close()
        conn.close()


def get_nodes_for_run(self, run_id: str) -> list:
    """
    Get nodes involved in a run with their latest metric snapshot.
    Used for the node-level summary table in test-report.html.
    """
    conn = self._get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT
                n.NODE_NAME,
                n.MACHINE_NAME,
                n.IP_ADDRESS,
                n.NODE_TYPE,
                n.IS_ACTIVE,
                t.TIER_NAME,
                a.APPLICATION_NAME,
                n.CALLS_PER_MINUTE,
                n.AGENT_VERSION,
                n.LAST_ACTIVITY_TIME,
                AVG(s.CPU_BUSY_PERCENT)   AS avg_cpu,
                AVG(s.MEMORY_USED_PERCENT) AS avg_mem
            FROM API_APPD_NODES n
            JOIN API_APPD_TIERS t         ON n.TIER_ID = t.TIER_ID
            JOIN API_APPD_APPLICATIONS a  ON t.APP_ID = a.APP_ID
            LEFT JOIN API_APPD_SERVER_METRICS s
                ON s.NODE_ID = n.NODE_ID AND s.RUN_ID = :run_id
            WHERE n.NODE_ID IN (
                SELECT DISTINCT NODE_ID FROM API_APPD_APPLICATION_METRICS
                WHERE RUN_ID = :run_id
            )
            GROUP BY
                n.NODE_NAME, n.MACHINE_NAME, n.IP_ADDRESS, n.NODE_TYPE,
                n.IS_ACTIVE, t.TIER_NAME, a.APPLICATION_NAME,
                n.CALLS_PER_MINUTE, n.AGENT_VERSION, n.LAST_ACTIVITY_TIME
            ORDER BY a.APPLICATION_NAME, t.TIER_NAME, n.NODE_NAME
        """, {'run_id': run_id})
        columns = [col[0].lower() for col in cursor.description]
        rows = cursor.fetchall()
        result = []
        for row in rows:
            m = dict(zip(columns, row))
            if m.get('last_activity_time') and hasattr(m['last_activity_time'], 'isoformat'):
                m['last_activity_time'] = m['last_activity_time'].isoformat()
            m['avg_cpu'] = round(m.get('avg_cpu') or 0, 2)
            m['avg_mem'] = round(m.get('avg_mem') or 0, 2)
            result.append(m)
        return result
    finally:
        cursor.close()
        conn.close()


def get_monitoring_sessions(self, run_id: str = None, lob_name: str = None) -> list:
    """
    Overloaded: can filter by run_id OR lob_name.
    Existing method only filters by lob_name — this adds run_id filtering.
    """
    conn = self._get_connection()
    cursor = conn.cursor()
    try:
        if run_id:
            query = """
                SELECT RUN_ID, LOB_ID, LOB_NAME, TRACK, TEST_NAME,
                       START_TIME, END_TIME, STATUS,
                       COLLECTION_INTERVAL_SECONDS, DURATION_MINUTES,
                       APPLICATIONS, NVL(TOTAL_COLLECTIONS, 0),
                       NVL(SUCCESSFUL_COLLECTIONS, 0), NVL(FAILED_COLLECTIONS, 0),
                       LAST_COLLECTION_TIME, PC_RUN_ID, APPD_RUN_ID,
                       ERROR_MESSAGE, CREATED_DATE, UPDATED_DATE
                FROM API_APPD_MONITORING_RUNS
                WHERE RUN_ID = :run_id
            """
            params = {'run_id': run_id}
        else:
            query = """
                SELECT RUN_ID, LOB_ID, LOB_NAME, TRACK, TEST_NAME,
                       START_TIME, END_TIME, STATUS,
                       COLLECTION_INTERVAL_SECONDS, DURATION_MINUTES,
                       APPLICATIONS, NVL(TOTAL_COLLECTIONS, 0),
                       NVL(SUCCESSFUL_COLLECTIONS, 0), NVL(FAILED_COLLECTIONS, 0),
                       LAST_COLLECTION_TIME, PC_RUN_ID, APPD_RUN_ID,
                       ERROR_MESSAGE, CREATED_DATE, UPDATED_DATE
                FROM API_APPD_MONITORING_RUNS
                WHERE LOB_NAME = :lob_name
                ORDER BY START_TIME DESC
            """
            params = {'lob_name': lob_name}
        cursor.execute(query, params)
        import json as _json
        sessions = []
        for row in cursor.fetchall():
            # APPLICATIONS column is JSON CLOB
            applications = []
            if row[10]:
                apps_clob = row[10]
                if hasattr(apps_clob, 'read'):
                    apps_clob = apps_clob.read()
                try:
                    applications = _json.loads(str(apps_clob))
                except Exception:
                    applications = []
            session = {
                'run_id':            row[0],
                'lob_id':            row[1],
                'lob_name':          row[2],
                'track':             row[3],
                'config_name':       row[4],   # TEST_NAME maps to config_name
                'start_time':        row[5].isoformat() if row[5] else None,
                'end_time':          row[6].isoformat() if row[6] else None,
                'status':            row[7],
                'interval_seconds':  row[8],
                'duration_minutes':  row[9],
                'applications':      applications,
                'total_collections': row[11],
                'successful_collections': row[12],
                'failed_collections': row[13],
                'last_collection':   row[14].isoformat() if row[14] else None,
                'pc_run_id':         row[15],
                'appd_run_id':       row[16],
                'error_message':     row[17],
                'created_date':      row[18].isoformat() if row[18] else None,
                'updated_date':      row[19].isoformat() if row[19] else None,
            }
            sessions.append(session)
        return sessions
    finally:
        cursor.close()
        conn.close()
