"""
AppDynamics Database Operations
All CRUD operations for the 9 AppD tables
"""
import oracledb
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


class AppDynamicsDatabase:
    """Database operations for AppDynamics monitoring"""
    
    def __init__(self, connection_pool):
        """
        Initialize with Oracle connection pool
        
        Args:
            connection_pool: Oracle connection pool from main app
        """
        self.pool = connection_pool
    
    def _get_connection(self):
        """Get connection from pool"""
        return self.pool.acquire()
    
    # ========================================
    # LOB Configuration Operations
    # ========================================
    
    def get_lob_config(self, lob_name: str) -> Optional[Dict]:
        """Get LOB configuration by name"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT LOB_ID, LOB_NAME, LOB_DESCRIPTION, APPLICATION_NAMES, 
                       LAST_DISCOVERY_RUN, DISCOVERY_SCHEDULE, IS_ACTIVE
                FROM APPD_LOB_CONFIG
                WHERE LOB_NAME = :lob_name
            """, {'lob_name': lob_name})
            
            row = cursor.fetchone()
            if row:
                return {
                    'lob_id': row[0],
                    'lob_name': row[1],
                    'lob_description': row[2],
                    'application_names': json.loads(row[3]) if row[3] else [],
                    'last_discovery_run': row[4],
                    'discovery_schedule': row[5],
                    'is_active': row[6]
                }
            return None
        finally:
            conn.close()
    
    def get_all_active_lobs(self) -> List[Dict]:
        """Get all active LOBs"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT LOB_ID, LOB_NAME, LOB_DESCRIPTION, APPLICATION_NAMES, 
                       LAST_DISCOVERY_RUN, DISCOVERY_SCHEDULE
                FROM APPD_LOB_CONFIG
                WHERE IS_ACTIVE = 'Y'
                ORDER BY LOB_NAME
            """)
            
            lobs = []
            for row in cursor.fetchall():
                lobs.append({
                    'lob_id': row[0],
                    'lob_name': row[1],
                    'lob_description': row[2],
                    'application_names': json.loads(row[3]) if row[3] else [],
                    'last_discovery_run': row[4],
                    'discovery_schedule': row[5]
                })
            return lobs
        finally:
            conn.close()
    
    def update_lob_discovery_time(self, lob_id: int):
        """Update last discovery run time for LOB"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE APPD_LOB_CONFIG
                SET LAST_DISCOVERY_RUN = SYSDATE,
                    UPDATED_DATE = SYSDATE
                WHERE LOB_ID = :lob_id
            """, {'lob_id': lob_id})
            conn.commit()
        finally:
            conn.close()
    
    # ========================================
    # Application Operations
    # ========================================
    
    def upsert_application(self, lob_id: int, app_data: Dict) -> int:
        """Insert or update application"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Check if exists
            cursor.execute("""
                SELECT APP_ID FROM APPD_APPLICATIONS
                WHERE LOB_ID = :lob_id AND APPLICATION_NAME = :app_name
            """, {'lob_id': lob_id, 'app_name': app_data['name']})
            
            existing = cursor.fetchone()
            
            if existing:
                # Update
                cursor.execute("""
                    UPDATE APPD_APPLICATIONS
                    SET APPLICATION_ID = :app_id,
                        TOTAL_TIERS = :total_tiers,
                        TOTAL_NODES = :total_nodes,
                        ACTIVE_NODES = :active_nodes,
                        INACTIVE_NODES = :inactive_nodes,
                        LAST_SEEN_DATE = SYSDATE,
                        IS_ACTIVE = 'Y',
                        UPDATED_DATE = SYSDATE
                    WHERE APP_ID = :app_id_pk
                """, {
                    'app_id': app_data.get('id'),
                    'total_tiers': app_data.get('total_tiers', 0),
                    'total_nodes': app_data.get('total_nodes', 0),
                    'active_nodes': app_data.get('active_nodes', 0),
                    'inactive_nodes': app_data.get('inactive_nodes', 0),
                    'app_id_pk': existing[0]
                })
                app_id = existing[0]
            else:
                # Insert
                cursor.execute("""
                    INSERT INTO APPD_APPLICATIONS (
                        APP_ID, LOB_ID, APPLICATION_NAME, APPLICATION_ID,
                        TOTAL_TIERS, TOTAL_NODES, ACTIVE_NODES, INACTIVE_NODES,
                        IS_ACTIVE
                    ) VALUES (
                        APPD_APPLICATIONS_SEQ.NEXTVAL, :lob_id, :app_name, :app_id,
                        :total_tiers, :total_nodes, :active_nodes, :inactive_nodes,
                        'Y'
                    ) RETURNING APP_ID INTO :app_id_out
                """, {
                    'lob_id': lob_id,
                    'app_name': app_data['name'],
                    'app_id': app_data.get('id'),
                    'total_tiers': app_data.get('total_tiers', 0),
                    'total_nodes': app_data.get('total_nodes', 0),
                    'active_nodes': app_data.get('active_nodes', 0),
                    'inactive_nodes': app_data.get('inactive_nodes', 0),
                    'app_id_out': cursor.var(oracledb.NUMBER)
                })
                app_id = cursor.getvalue(0)
            
            conn.commit()
            return int(app_id)
        finally:
            conn.close()
    
    def get_application_id(self, lob_id: int, app_name: str) -> Optional[int]:
        """Get application ID"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT APP_ID FROM APPD_APPLICATIONS
                WHERE LOB_ID = :lob_id AND APPLICATION_NAME = :app_name
            """, {'lob_id': lob_id, 'app_name': app_name})
            
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            conn.close()
    
    # ========================================
    # Tier Operations
    # ========================================
    
    def upsert_tier(self, app_id: int, tier_data: Dict) -> int:
        """Insert or update tier"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Check if exists
            cursor.execute("""
                SELECT TIER_ID FROM APPD_TIERS
                WHERE APP_ID = :app_id AND TIER_NAME = :tier_name
            """, {'app_id': app_id, 'tier_name': tier_data['name']})
            
            existing = cursor.fetchone()
            
            if existing:
                # Update
                cursor.execute("""
                    UPDATE APPD_TIERS
                    SET TIER_ID_APPD = :tier_id,
                        TIER_TYPE = :tier_type,
                        TOTAL_NODES = :total_nodes,
                        ACTIVE_NODES = :active_nodes,
                        IS_ACTIVE = 'Y',
                        LAST_SEEN_DATE = SYSDATE,
                        UPDATED_DATE = SYSDATE
                    WHERE TIER_ID = :tier_id_pk
                """, {
                    'tier_id': tier_data.get('id'),
                    'tier_type': tier_data.get('type'),
                    'total_nodes': tier_data.get('total_nodes', 0),
                    'active_nodes': tier_data.get('active_nodes', 0),
                    'tier_id_pk': existing[0]
                })
                tier_id = existing[0]
            else:
                # Insert
                cursor.execute("""
                    INSERT INTO APPD_TIERS (
                        TIER_ID, APP_ID, TIER_NAME, TIER_ID_APPD, TIER_TYPE,
                        TOTAL_NODES, ACTIVE_NODES, IS_ACTIVE
                    ) VALUES (
                        APPD_TIERS_SEQ.NEXTVAL, :app_id, :tier_name, :tier_id, :tier_type,
                        :total_nodes, :active_nodes, 'Y'
                    ) RETURNING TIER_ID INTO :tier_id_out
                """, {
                    'app_id': app_id,
                    'tier_name': tier_data['name'],
                    'tier_id': tier_data.get('id'),
                    'tier_type': tier_data.get('type'),
                    'total_nodes': tier_data.get('total_nodes', 0),
                    'active_nodes': tier_data.get('active_nodes', 0),
                    'tier_id_out': cursor.var(oracledb.NUMBER)
                })
                tier_id = cursor.getvalue(0)
            
            conn.commit()
            return int(tier_id)
        finally:
            conn.close()
    
    def get_tier_id(self, app_id: int, tier_name: str) -> Optional[int]:
        """Get tier ID"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TIER_ID FROM APPD_TIERS
                WHERE APP_ID = :app_id AND TIER_NAME = :tier_name
            """, {'app_id': app_id, 'tier_name': tier_name})
            
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            conn.close()
    
    # ========================================
    # Node Operations
    # ========================================
    
    def upsert_node(self, tier_id: int, app_id: int, node_data: Dict) -> int:
        """Insert or update node with CPM-based active status"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Determine if node is active based on CPM
            cpm = node_data.get('calls_per_minute', 0)
            threshold = node_data.get('threshold', 10)
            is_active = 'Y' if cpm >= threshold else 'N'
            
            # Check if exists
            cursor.execute("""
                SELECT NODE_ID FROM APPD_NODES
                WHERE TIER_ID = :tier_id AND NODE_NAME = :node_name
            """, {'tier_id': tier_id, 'node_name': node_data['name']})
            
            existing = cursor.fetchone()
            
            if existing:
                # Update
                cursor.execute("""
                    UPDATE APPD_NODES
                    SET NODE_ID_APPD = :node_id,
                        MACHINE_NAME = :machine_name,
                        IP_ADDRESS = :ip_address,
                        CALLS_PER_MINUTE = :cpm,
                        LAST_ACTIVITY_TIME = SYSTIMESTAMP,
                        IS_ACTIVE = :is_active,
                        ACTIVE_THRESHOLD = :threshold,
                        NODE_TYPE = :node_type,
                        AGENT_VERSION = :agent_version,
                        LAST_SEEN_DATE = SYSDATE,
                        UPDATED_DATE = SYSDATE
                    WHERE NODE_ID = :node_id_pk
                """, {
                    'node_id': node_data.get('id'),
                    'machine_name': node_data.get('machine_name'),
                    'ip_address': node_data.get('ip_address'),
                    'cpm': cpm,
                    'is_active': is_active,
                    'threshold': threshold,
                    'node_type': node_data.get('type'),
                    'agent_version': node_data.get('agent_version'),
                    'node_id_pk': existing[0]
                })
                node_id = existing[0]
            else:
                # Insert
                cursor.execute("""
                    INSERT INTO APPD_NODES (
                        NODE_ID, TIER_ID, APP_ID, NODE_NAME, NODE_ID_APPD,
                        MACHINE_NAME, IP_ADDRESS, CALLS_PER_MINUTE, LAST_ACTIVITY_TIME,
                        IS_ACTIVE, ACTIVE_THRESHOLD, NODE_TYPE, AGENT_VERSION
                    ) VALUES (
                        APPD_NODES_SEQ.NEXTVAL, :tier_id, :app_id, :node_name, :node_id,
                        :machine_name, :ip_address, :cpm, SYSTIMESTAMP,
                        :is_active, :threshold, :node_type, :agent_version
                    ) RETURNING NODE_ID INTO :node_id_out
                """, {
                    'tier_id': tier_id,
                    'app_id': app_id,
                    'node_name': node_data['name'],
                    'node_id': node_data.get('id'),
                    'machine_name': node_data.get('machine_name'),
                    'ip_address': node_data.get('ip_address'),
                    'cpm': cpm,
                    'is_active': is_active,
                    'threshold': threshold,
                    'node_type': node_data.get('type'),
                    'agent_version': node_data.get('agent_version'),
                    'node_id_out': cursor.var(oracledb.NUMBER)
                })
                node_id = cursor.getvalue(0)
            
            conn.commit()
            return int(node_id)
        finally:
            conn.close()
    
    def get_active_nodes_for_lob(self, lob_name: str) -> List[Dict]:
        """Get all active nodes for a LOB (Health Check API)"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    l.LOB_NAME,
                    a.APPLICATION_NAME,
                    t.TIER_NAME,
                    n.NODE_NAME,
                    n.NODE_ID,
                    n.CALLS_PER_MINUTE,
                    n.MACHINE_NAME,
                    n.IP_ADDRESS,
                    n.LAST_ACTIVITY_TIME
                FROM APPD_LOB_CONFIG l
                JOIN APPD_APPLICATIONS a ON l.LOB_ID = a.LOB_ID
                JOIN APPD_TIERS t ON a.APP_ID = t.APP_ID
                JOIN APPD_NODES n ON t.TIER_ID = n.TIER_ID
                WHERE l.LOB_NAME = :lob_name
                  AND n.IS_ACTIVE = 'Y'
                  AND a.IS_ACTIVE = 'Y'
                  AND t.IS_ACTIVE = 'Y'
                ORDER BY a.APPLICATION_NAME, t.TIER_NAME, n.NODE_NAME
            """, {'lob_name': lob_name})
            
            nodes = []
            for row in cursor.fetchall():
                nodes.append({
                    'lob_name': row[0],
                    'application_name': row[1],
                    'tier_name': row[2],
                    'node_name': row[3],
                    'node_id': row[4],
                    'calls_per_minute': row[5],
                    'machine_name': row[6],
                    'ip_address': row[7],
                    'last_activity_time': row[8].isoformat() if row[8] else None
                })
            return nodes
        finally:
            conn.close()
    
    # ========================================
    # Monitoring Run Operations
    # ========================================
    
    def create_monitoring_run(self, run_data: Dict) -> str:
        """Create new monitoring run"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO APPD_MONITORING_RUNS (
                    RUN_ID, LOB_ID, LOB_NAME, TRACK, TEST_NAME,
                    START_TIME, STATUS, COLLECTION_INTERVAL_SECONDS,
                    APPLICATIONS
                ) VALUES (
                    :run_id, :lob_id, :lob_name, :track, :test_name,
                    SYSTIMESTAMP, 'RUNNING', :interval,
                    :applications
                )
            """, {
                'run_id': run_data['run_id'],
                'lob_id': run_data['lob_id'],
                'lob_name': run_data['lob_name'],
                'track': run_data['track'],
                'test_name': run_data.get('test_name'),
                'interval': run_data['interval_seconds'],
                'applications': json.dumps(run_data['applications'])
            })
            conn.commit()
            return run_data['run_id']
        finally:
            conn.close()
    
    def update_monitoring_run_status(self, run_id: str, status: str, error: Optional[str] = None):
        """Update monitoring run status"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if status in ['COMPLETED', 'STOPPED', 'FAILED']:
                cursor.execute("""
                    UPDATE APPD_MONITORING_RUNS
                    SET STATUS = :status,
                        END_TIME = SYSTIMESTAMP,
                        ERROR_MESSAGE = :error,
                        UPDATED_DATE = SYSDATE
                    WHERE RUN_ID = :run_id
                """, {'status': status, 'error': error, 'run_id': run_id})
            else:
                cursor.execute("""
                    UPDATE APPD_MONITORING_RUNS
                    SET STATUS = :status,
                        ERROR_MESSAGE = :error,
                        UPDATED_DATE = SYSDATE
                    WHERE RUN_ID = :run_id
                """, {'status': status, 'error': error, 'run_id': run_id})
            conn.commit()
        finally:
            conn.close()
    
    def increment_collection_count(self, run_id: str, success: bool = True):
        """Increment collection counters"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if success:
                cursor.execute("""
                    UPDATE APPD_MONITORING_RUNS
                    SET TOTAL_COLLECTIONS = TOTAL_COLLECTIONS + 1,
                        SUCCESSFUL_COLLECTIONS = SUCCESSFUL_COLLECTIONS + 1,
                        LAST_COLLECTION_TIME = SYSTIMESTAMP,
                        UPDATED_DATE = SYSDATE
                    WHERE RUN_ID = :run_id
                """, {'run_id': run_id})
            else:
                cursor.execute("""
                    UPDATE APPD_MONITORING_RUNS
                    SET TOTAL_COLLECTIONS = TOTAL_COLLECTIONS + 1,
                        FAILED_COLLECTIONS = FAILED_COLLECTIONS + 1,
                        UPDATED_DATE = SYSDATE
                    WHERE RUN_ID = :run_id
                """, {'run_id': run_id})
            conn.commit()
        finally:
            conn.close()
    
    # ========================================
    # Metrics Operations
    # ========================================
    
    def insert_server_metrics(self, run_id: str, node_id: int, metrics: Dict):
        """Insert server metrics"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO APPD_SERVER_METRICS (
                    METRIC_ID, RUN_ID, NODE_ID, COLLECTION_TIME,
                    CPU_BUSY_PERCENT, CPU_IDLE_PERCENT, CPU_STOLEN_PERCENT,
                    MEMORY_TOTAL_MB, MEMORY_USED_MB, MEMORY_FREE_MB, MEMORY_USED_PERCENT,
                    NETWORK_INCOMING_KB, NETWORK_OUTGOING_KB,
                    DISK_READS_PER_SEC, DISK_WRITES_PER_SEC, DISK_USED_PERCENT, DISK_QUEUE_LENGTH,
                    ADDITIONAL_METRICS
                ) VALUES (
                    APPD_SERVER_METRICS_SEQ.NEXTVAL, :run_id, :node_id, SYSTIMESTAMP,
                    :cpu_busy, :cpu_idle, :cpu_stolen,
                    :mem_total, :mem_used, :mem_free, :mem_percent,
                    :net_in, :net_out,
                    :disk_reads, :disk_writes, :disk_used, :disk_queue,
                    :additional
                )
            """, {
                'run_id': run_id,
                'node_id': node_id,
                'cpu_busy': metrics.get('cpu_busy_percent'),
                'cpu_idle': metrics.get('cpu_idle_percent'),
                'cpu_stolen': metrics.get('cpu_stolen_percent'),
                'mem_total': metrics.get('memory_total_mb'),
                'mem_used': metrics.get('memory_used_mb'),
                'mem_free': metrics.get('memory_free_mb'),
                'mem_percent': metrics.get('memory_used_percent'),
                'net_in': metrics.get('network_incoming_kb'),
                'net_out': metrics.get('network_outgoing_kb'),
                'disk_reads': metrics.get('disk_reads_per_sec'),
                'disk_writes': metrics.get('disk_writes_per_sec'),
                'disk_used': metrics.get('disk_used_percent'),
                'disk_queue': metrics.get('disk_queue_length'),
                'additional': json.dumps(metrics.get('additional', {}))
            })
            conn.commit()
        finally:
            conn.close()
    
    def insert_jvm_metrics(self, run_id: str, node_id: int, metrics: Dict):
        """Insert JVM metrics"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO APPD_JVM_METRICS (
                    METRIC_ID, RUN_ID, NODE_ID, COLLECTION_TIME,
                    HEAP_USED_MB, HEAP_COMMITTED_MB, HEAP_MAX_MB, HEAP_USED_PERCENT,
                    NON_HEAP_USED_MB, NON_HEAP_COMMITTED_MB,
                    GC_TIME_MS, GC_MAJOR_COLLECTION_COUNT, GC_MINOR_COLLECTION_COUNT, GC_TIME_SPENT_PERCENT,
                    THREAD_COUNT, THREAD_CURRENT, THREAD_PEAK, THREAD_DAEMON, THREAD_BLOCKED,
                    EXCEPTION_COUNT, ERROR_COUNT,
                    SLOW_CALLS_COUNT, VERY_SLOW_CALLS_COUNT, STALL_CALLS_COUNT,
                    CLASSES_LOADED, CLASSES_UNLOADED,
                    ADDITIONAL_METRICS
                ) VALUES (
                    APPD_JVM_METRICS_SEQ.NEXTVAL, :run_id, :node_id, SYSTIMESTAMP,
                    :heap_used, :heap_committed, :heap_max, :heap_percent,
                    :non_heap_used, :non_heap_committed,
                    :gc_time, :gc_major, :gc_minor, :gc_percent,
                    :thread_count, :thread_current, :thread_peak, :thread_daemon, :thread_blocked,
                    :exception_count, :error_count,
                    :slow_calls, :very_slow_calls, :stall_calls,
                    :classes_loaded, :classes_unloaded,
                    :additional
                )
            """, {
                'run_id': run_id,
                'node_id': node_id,
                'heap_used': metrics.get('heap_used_mb'),
                'heap_committed': metrics.get('heap_committed_mb'),
                'heap_max': metrics.get('heap_max_mb'),
                'heap_percent': metrics.get('heap_used_percent'),
                'non_heap_used': metrics.get('non_heap_used_mb'),
                'non_heap_committed': metrics.get('non_heap_committed_mb'),
                'gc_time': metrics.get('gc_time_ms'),
                'gc_major': metrics.get('gc_major_count'),
                'gc_minor': metrics.get('gc_minor_count'),
                'gc_percent': metrics.get('gc_time_percent'),
                'thread_count': metrics.get('thread_count'),
                'thread_current': metrics.get('thread_current'),
                'thread_peak': metrics.get('thread_peak'),
                'thread_daemon': metrics.get('thread_daemon'),
                'thread_blocked': metrics.get('thread_blocked'),
                'exception_count': metrics.get('exception_count'),
                'error_count': metrics.get('error_count'),
                'slow_calls': metrics.get('slow_calls_count'),
                'very_slow_calls': metrics.get('very_slow_calls_count'),
                'stall_calls': metrics.get('stall_calls_count'),
                'classes_loaded': metrics.get('classes_loaded'),
                'classes_unloaded': metrics.get('classes_unloaded'),
                'additional': json.dumps(metrics.get('additional', {}))
            })
            conn.commit()
        finally:
            conn.close()
    
    def insert_application_metrics(self, run_id: str, node_id: int, tier_id: int, app_id: int, metrics: Dict):
        """Insert application metrics"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO APPD_APPLICATION_METRICS (
                    METRIC_ID, RUN_ID, NODE_ID, TIER_ID, APP_ID, COLLECTION_TIME,
                    CALLS_PER_MINUTE, CALLS_TOTAL,
                    RESPONSE_TIME_AVG_MS, RESPONSE_TIME_MIN_MS, RESPONSE_TIME_MAX_MS,
                    RESPONSE_TIME_P90_MS, RESPONSE_TIME_P95_MS, RESPONSE_TIME_P99_MS,
                    ERRORS_PER_MINUTE, ERROR_RATE_PERCENT, ERRORS_TOTAL,
                    BT_NORMAL_COUNT, BT_SLOW_COUNT, BT_VERY_SLOW_COUNT, BT_STALLED_COUNT, BT_ERROR_COUNT,
                    APDEX_SCORE,
                    ADDITIONAL_METRICS
                ) VALUES (
                    APPD_APP_METRICS_SEQ.NEXTVAL, :run_id, :node_id, :tier_id, :app_id, SYSTIMESTAMP,
                    :cpm, :calls_total,
                    :resp_avg, :resp_min, :resp_max,
                    :resp_p90, :resp_p95, :resp_p99,
                    :err_per_min, :err_rate, :err_total,
                    :bt_normal, :bt_slow, :bt_very_slow, :bt_stalled, :bt_error,
                    :apdex,
                    :additional
                )
            """, {
                'run_id': run_id,
                'node_id': node_id,
                'tier_id': tier_id,
                'app_id': app_id,
                'cpm': metrics.get('calls_per_minute'),
                'calls_total': metrics.get('calls_total'),
                'resp_avg': metrics.get('response_time_avg_ms'),
                'resp_min': metrics.get('response_time_min_ms'),
                'resp_max': metrics.get('response_time_max_ms'),
                'resp_p90': metrics.get('response_time_p90_ms'),
                'resp_p95': metrics.get('response_time_p95_ms'),
                'resp_p99': metrics.get('response_time_p99_ms'),
                'err_per_min': metrics.get('errors_per_minute'),
                'err_rate': metrics.get('error_rate_percent'),
                'err_total': metrics.get('errors_total'),
                'bt_normal': metrics.get('bt_normal_count'),
                'bt_slow': metrics.get('bt_slow_count'),
                'bt_very_slow': metrics.get('bt_very_slow_count'),
                'bt_stalled': metrics.get('bt_stalled_count'),
                'bt_error': metrics.get('bt_error_count'),
                'apdex': metrics.get('apdex_score'),
                'additional': json.dumps(metrics.get('additional', {}))
            })
            conn.commit()
        finally:
            conn.close()
    
    # ========================================
    # Discovery Log Operations
    # ========================================
    
    def create_discovery_log(self, lob_id: int) -> int:
        """Create discovery log entry"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO APPD_DISCOVERY_LOG (
                    LOG_ID, LOB_ID, DISCOVERY_START_TIME, STATUS
                ) VALUES (
                    APPD_DISCOVERY_LOG_SEQ.NEXTVAL, :lob_id, SYSTIMESTAMP, 'RUNNING'
                ) RETURNING LOG_ID INTO :log_id
            """, {
                'lob_id': lob_id,
                'log_id': cursor.var(oracledb.NUMBER)
            })
            log_id = cursor.getvalue(0)
            conn.commit()
            return int(log_id)
        finally:
            conn.close()
    
    def complete_discovery_log(self, log_id: int, stats: Dict, status: str = 'SUCCESS', error: Optional[str] = None):
        """Complete discovery log with statistics"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE APPD_DISCOVERY_LOG
                SET DISCOVERY_END_TIME = SYSTIMESTAMP,
                    STATUS = :status,
                    APPLICATIONS_DISCOVERED = :apps,
                    TIERS_DISCOVERED = :tiers,
                    NODES_DISCOVERED = :nodes,
                    ACTIVE_NODES_COUNT = :active_nodes,
                    ERROR_MESSAGE = :error,
                    EXECUTION_TIME_SECONDS = EXTRACT(DAY FROM (SYSTIMESTAMP - DISCOVERY_START_TIME)) * 86400 +
                                             EXTRACT(HOUR FROM (SYSTIMESTAMP - DISCOVERY_START_TIME)) * 3600 +
                                             EXTRACT(MINUTE FROM (SYSTIMESTAMP - DISCOVERY_START_TIME)) * 60 +
                                             EXTRACT(SECOND FROM (SYSTIMESTAMP - DISCOVERY_START_TIME))
                WHERE LOG_ID = :log_id
            """, {
                'status': status,
                'apps': stats.get('applications', 0),
                'tiers': stats.get('tiers', 0),
                'nodes': stats.get('nodes', 0),
                'active_nodes': stats.get('active_nodes', 0),
                'error': error,
                'log_id': log_id
            })
            conn.commit()
        finally:
            conn.close()