# 🏗️ Unified Architecture - Common Routing & Database Structure

## 📋 Overview

Create a unified architecture where:
- **Single `routes.py`** - All monitoring solutions (AWR, PC, AppD, MongoDB, Splunk)
- **Single `database.py`** - Common database operations for all solutions
- **Modular design** - Each solution has its own parser/analyzer modules
- **UI Integration** - AWR Tab and PC Tab with forms and results display

---

## 🗂️ Unified Directory Structure

```
monitoring/
├── __init__.py
├── routes.py              # ← UNIFIED: All monitoring routes
├── database.py            # ← UNIFIED: All database operations
├── models.py              # ← UNIFIED: All Pydantic models
│
├── appd/                  # AppDynamics (existing)
│   ├── __init__.py
│   ├── config.py
│   ├── client.py
│   ├── discovery.py
│   └── orchestrator.py
│
├── awr/                   # AWR Analysis
│   ├── __init__.py
│   ├── parser.py          # AWR HTML parser
│   └── analyzer.py        # AWR concern analyzer
│
├── pc/                    # Performance Center
│   ├── __init__.py
│   ├── client.py          # PC REST API client
│   └── parser.py          # Summary.html parser
│
├── mongodb/               # MongoDB (future)
│   ├── __init__.py
│   └── client.py
│
└── splunk/               # Splunk (future)
    ├── __init__.py
    └── client.py
```

---

## 📝 PART 1: Unified Pydantic Models

### File: `monitoring/models.py`

```python
"""
Unified Pydantic Models for All Monitoring Solutions
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# ==========================================
# Common Enums
# ==========================================

class ConcernSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"

class ConcernCategory(str, Enum):
    TOP_SQL = "TOP_SQL"
    WAIT_EVENTS = "WAIT_EVENTS"
    SYSTEM_STATS = "SYSTEM_STATS"
    IO_STATS = "IO_STATS"
    INSTANCE_EFFICIENCY = "INSTANCE_EFFICIENCY"
    TRANSACTION = "TRANSACTION"
    RESPONSE_TIME = "RESPONSE_TIME"

# ==========================================
# AWR Models
# ==========================================

class AWRUploadRequest(BaseModel):
    """Request model for AWR report upload"""
    run_id: str = Field(..., description="Master run ID from RUN_MASTER")
    pc_run_id: str = Field(..., description="Performance Center run ID")
    database_name: str
    lob_name: str
    track: Optional[str] = None
    test_name: Optional[str] = None

class AWRConcern(BaseModel):
    """AWR Performance concern"""
    category: ConcernCategory
    concern_type: str
    severity: ConcernSeverity
    title: str
    description: str
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    threshold_value: Optional[float] = None
    recommendation: str
    sql_id: Optional[str] = None

class AWRAnalysisResponse(BaseModel):
    """Response for AWR analysis"""
    success: bool
    awr_run_id: str
    run_id: str
    analysis_id: int
    database_name: str
    instance_name: str
    snapshot_begin: int
    snapshot_end: int
    elapsed_time_minutes: float
    db_time_minutes: float
    total_concerns: int
    critical_concerns: int
    warning_concerns: int
    concerns: List[AWRConcern]
    message: str

# ==========================================
# Performance Center Models
# ==========================================

class PCConnectionRequest(BaseModel):
    """Request to connect to Performance Center"""
    run_id: str
    pc_run_id: str
    pc_url: str
    pc_port: int = 8080
    pc_domain: str
    pc_project: str
    username: str
    password: str
    test_set_name: Optional[str] = None
    test_instance_id: Optional[str] = None
    lob_name: str
    track: Optional[str] = None

class LRTransaction(BaseModel):
    """LoadRunner transaction statistics"""
    transaction_name: str
    minimum_time: float
    average_time: float
    maximum_time: float
    std_deviation: float
    percentile_90: float
    percentile_95: Optional[float] = None
    percentile_99: Optional[float] = None
    pass_count: int
    fail_count: int
    stop_count: int
    total_count: int
    pass_percentage: float
    throughput_tps: Optional[float] = None

class PCFetchResponse(BaseModel):
    """Response from PC fetch operation"""
    success: bool
    run_id: str
    pc_run_id: str
    test_status: str
    collation_status: str
    transactions: List[LRTransaction]
    total_transactions: int
    passed_transactions: int
    failed_transactions: int
    message: str

# ==========================================
# MongoDB Models
# ==========================================

class MongoDBStatsResponse(BaseModel):
    """MongoDB statistics for LOB"""
    lob_name: str
    collections: int
    documents: int
    size_bytes: int
    avg_document_size: float
    indexes: int

# ==========================================
# Splunk Models
# ==========================================

class SplunkStatusResponse(BaseModel):
    """Splunk indexing status"""
    lob_name: str
    status: str
    last_indexed: datetime
    events_today: int
    indexes: int
```

---

## 📝 PART 2: Unified Database Operations

### File: `monitoring/database.py`

```python
"""
Unified Database Operations for All Monitoring Solutions
"""
import cx_Oracle
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class MonitoringDatabase:
    """Unified database operations for all monitoring solutions"""
    
    def __init__(self, connection_pool):
        self.pool = connection_pool
    
    # ==========================================
    # RUN_MASTER Operations
    # ==========================================
    
    def create_master_run(
        self,
        run_id: str,
        pc_run_id: str,
        lob_name: str,
        track: Optional[str] = None,
        test_name: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> bool:
        """Create entry in RUN_MASTER"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO RUN_MASTER (
                    RUN_ID, PC_RUN_ID, LOB_NAME, TRACK, TEST_NAME,
                    TEST_STATUS, CREATED_BY
                ) VALUES (
                    :run_id, :pc_run_id, :lob_name, :track, :test_name,
                    'INITIATED', :created_by
                )
            """, {
                'run_id': run_id,
                'pc_run_id': pc_run_id,
                'lob_name': lob_name,
                'track': track,
                'test_name': test_name,
                'created_by': created_by
            })
            
            conn.commit()
            logger.info(f"Created RUN_MASTER entry: {run_id}")
            return True
            
        except cx_Oracle.IntegrityError:
            # Run already exists
            conn.rollback()
            logger.info(f"RUN_MASTER entry already exists: {run_id}")
            return False
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating RUN_MASTER: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def update_run_status(
        self,
        run_id: str,
        status: str,
        end_time: Optional[datetime] = None
    ):
        """Update run status"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            if end_time:
                cursor.execute("""
                    UPDATE RUN_MASTER
                    SET TEST_STATUS = :status,
                        TEST_END_TIME = :end_time,
                        UPDATED_DATE = SYSDATE
                    WHERE RUN_ID = :run_id
                """, {
                    'status': status,
                    'end_time': end_time,
                    'run_id': run_id
                })
            else:
                cursor.execute("""
                    UPDATE RUN_MASTER
                    SET TEST_STATUS = :status,
                        UPDATED_DATE = SYSDATE
                    WHERE RUN_ID = :run_id
                """, {
                    'status': status,
                    'run_id': run_id
                })
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating run status: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    # ==========================================
    # AWR Operations
    # ==========================================
    
    def save_awr_analysis(
        self,
        run_id: str,
        awr_run_id: str,
        header: Dict,
        parsed_data: Dict,
        concerns: List[Dict],
        top_sql: List[Dict],
        wait_events: List[Dict]
    ) -> int:
        """Save AWR analysis results"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            # Calculate summary
            critical = sum(1 for c in concerns if c['severity'] == 'CRITICAL')
            warning = sum(1 for c in concerns if c['severity'] == 'WARNING')
            info = sum(1 for c in concerns if c['severity'] == 'INFO')
            
            # Insert analysis
            cursor.execute("""
                INSERT INTO AWR_ANALYSIS_RESULTS (
                    ANALYSIS_ID, RUN_ID, AWR_RUN_ID, DATABASE_NAME, INSTANCE_NAME,
                    HOST_NAME, SNAPSHOT_BEGIN, SNAPSHOT_END,
                    ELAPSED_TIME_MINUTES, DB_TIME_MINUTES, DB_CPU_MINUTES,
                    TOTAL_CONCERNS, CRITICAL_CONCERNS, WARNING_CONCERNS, INFO_CONCERNS,
                    ANALYSIS_STATUS, ANALYSIS_COMPLETED_TIME
                ) VALUES (
                    AWR_ANALYSIS_SEQ.NEXTVAL, :run_id, :awr_run_id, :db_name, :instance,
                    :host, :snap_begin, :snap_end,
                    :elapsed, :db_time, :db_cpu,
                    :total, :critical, :warning, :info,
                    'COMPLETED', SYSTIMESTAMP
                ) RETURNING ANALYSIS_ID INTO :analysis_id
            """, {
                'run_id': run_id,
                'awr_run_id': awr_run_id,
                'db_name': header.get('db_name', 'UNKNOWN'),
                'instance': header.get('instance_name', 'UNKNOWN'),
                'host': header.get('host_name', 'UNKNOWN'),
                'snap_begin': header.get('snapshot_begin', 0),
                'snap_end': header.get('snapshot_end', 0),
                'elapsed': header.get('elapsed_time_minutes', 0),
                'db_time': header.get('db_time_minutes', 0),
                'db_cpu': parsed_data.get('time_model_stats', {}).get('DB CPU', 0) / 60,
                'total': len(concerns),
                'critical': critical,
                'warning': warning,
                'info': info,
                'analysis_id': cursor.var(cx_Oracle.NUMBER)
            })
            
            analysis_id = int(cursor.getvalue()[0])
            
            # Save concerns
            for concern in concerns:
                self._save_awr_concern(cursor, analysis_id, run_id, awr_run_id, concern)
            
            # Save top SQL
            for sql in top_sql[:10]:
                self._save_awr_top_sql(cursor, analysis_id, run_id, sql)
            
            # Save wait events
            for event in wait_events[:10]:
                self._save_awr_wait_event(cursor, analysis_id, run_id, event)
            
            conn.commit()
            logger.info(f"Saved AWR analysis {analysis_id}")
            
            return analysis_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving AWR analysis: {e}", exc_info=True)
            raise
        finally:
            cursor.close()
            conn.close()
    
    def _save_awr_concern(self, cursor, analysis_id, run_id, awr_run_id, concern):
        """Save AWR concern"""
        cursor.execute("""
            INSERT INTO AWR_CONCERNS (
                CONCERN_ID, ANALYSIS_ID, RUN_ID, AWR_RUN_ID,
                CONCERN_CATEGORY, CONCERN_TYPE, SEVERITY,
                CONCERN_TITLE, CONCERN_DESCRIPTION,
                METRIC_NAME, METRIC_VALUE, THRESHOLD_VALUE,
                RECOMMENDATION, SQL_ID
            ) VALUES (
                AWR_CONCERN_SEQ.NEXTVAL, :analysis_id, :run_id, :awr_run_id,
                :category, :type, :severity,
                :title, :description,
                :metric_name, :metric_value, :threshold,
                :recommendation, :sql_id
            )
        """, {
            'analysis_id': analysis_id,
            'run_id': run_id,
            'awr_run_id': awr_run_id,
            'category': concern['category'],
            'type': concern['concern_type'],
            'severity': concern['severity'],
            'title': concern['title'],
            'description': concern['description'],
            'metric_name': concern.get('metric_name'),
            'metric_value': concern.get('metric_value'),
            'threshold': concern.get('threshold_value'),
            'recommendation': concern['recommendation'],
            'sql_id': concern.get('sql_id')
        })
    
    def _save_awr_top_sql(self, cursor, analysis_id, run_id, sql):
        """Save AWR top SQL"""
        cursor.execute("""
            INSERT INTO AWR_TOP_SQL (
                TOP_SQL_ID, ANALYSIS_ID, RUN_ID, SQL_ID,
                EXECUTIONS, ELAPSED_TIME_SECONDS, CPU_TIME_SECONDS,
                BUFFER_GETS, ELAPSED_PER_EXEC_MS, RANK_BY_ELAPSED
            ) VALUES (
                AWR_TOP_SQL_SEQ.NEXTVAL, :analysis_id, :run_id, :sql_id,
                :executions, :elapsed, :cpu,
                :gets, :elapsed_per_exec, :rank
            )
        """, {
            'analysis_id': analysis_id,
            'run_id': run_id,
            'sql_id': sql.get('sql_id', 'UNKNOWN'),
            'executions': sql.get('executions', 0),
            'elapsed': sql.get('elapsed_time_sec', 0),
            'cpu': sql.get('cpu_time_sec', 0),
            'gets': sql.get('buffer_gets', 0),
            'elapsed_per_exec': sql.get('elapsed_per_exec', 0),
            'rank': sql.get('rank', 0)
        })
    
    def _save_awr_wait_event(self, cursor, analysis_id, run_id, event):
        """Save AWR wait event"""
        cursor.execute("""
            INSERT INTO AWR_WAIT_EVENTS (
                WAIT_EVENT_ID, ANALYSIS_ID, RUN_ID,
                EVENT_NAME, EVENT_CLASS, WAITS,
                TOTAL_WAIT_TIME_SECONDS, AVG_WAIT_TIME_MS,
                PERCENT_DB_TIME, RANK_POSITION
            ) VALUES (
                AWR_WAIT_EVENT_SEQ.NEXTVAL, :analysis_id, :run_id,
                :event_name, :event_class, :waits,
                :total_wait, :avg_wait, :percent_db, :rank
            )
        """, {
            'analysis_id': analysis_id,
            'run_id': run_id,
            'event_name': event.get('event_name', 'UNKNOWN'),
            'event_class': event.get('event_class', 'Unknown'),
            'waits': event.get('waits', 0),
            'total_wait': event.get('total_wait_time_sec', 0),
            'avg_wait': event.get('avg_wait_ms', 0),
            'percent_db': event.get('percent_db_time', 0),
            'rank': event.get('rank', 0)
        })
    
    def get_awr_analysis_by_run(self, run_id: str) -> Optional[Dict]:
        """Get AWR analysis for run"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    ANALYSIS_ID, AWR_RUN_ID, DATABASE_NAME, INSTANCE_NAME,
                    SNAPSHOT_BEGIN, SNAPSHOT_END, ELAPSED_TIME_MINUTES,
                    TOTAL_CONCERNS, CRITICAL_CONCERNS, WARNING_CONCERNS
                FROM AWR_ANALYSIS_RESULTS
                WHERE RUN_ID = :run_id
                ORDER BY CREATED_DATE DESC
                FETCH FIRST 1 ROW ONLY
            """, {'run_id': run_id})
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                'analysis_id': row[0],
                'awr_run_id': row[1],
                'database_name': row[2],
                'instance_name': row[3],
                'snapshot_begin': row[4],
                'snapshot_end': row[5],
                'elapsed_time_minutes': row[6],
                'total_concerns': row[7],
                'critical_concerns': row[8],
                'warning_concerns': row[9]
            }
            
        finally:
            cursor.close()
            conn.close()
    
    def get_awr_concerns(self, analysis_id: int) -> List[Dict]:
        """Get concerns for analysis"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    CONCERN_CATEGORY, CONCERN_TYPE, SEVERITY,
                    CONCERN_TITLE, CONCERN_DESCRIPTION,
                    METRIC_NAME, METRIC_VALUE, RECOMMENDATION
                FROM AWR_CONCERNS
                WHERE ANALYSIS_ID = :analysis_id
                ORDER BY 
                    CASE SEVERITY 
                        WHEN 'CRITICAL' THEN 1
                        WHEN 'WARNING' THEN 2
                        ELSE 3
                    END
            """, {'analysis_id': analysis_id})
            
            concerns = []
            for row in cursor.fetchall():
                concerns.append({
                    'category': row[0],
                    'concern_type': row[1],
                    'severity': row[2],
                    'title': row[3],
                    'description': row[4].read() if hasattr(row[4], 'read') else row[4],
                    'metric_name': row[5],
                    'metric_value': float(row[6]) if row[6] else None,
                    'recommendation': row[7].read() if hasattr(row[7], 'read') else row[7]
                })
            
            return concerns
            
        finally:
            cursor.close()
            conn.close()
    
    # ==========================================
    # Performance Center Operations
    # ==========================================
    
    def save_pc_test_run(
        self,
        run_id: str,
        pc_run_id: str,
        pc_url: str,
        pc_domain: str,
        pc_project: str,
        test_status: str,
        collation_status: str
    ) -> int:
        """Save PC test run details"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO PC_TEST_RUNS (
                    PC_TEST_ID, RUN_ID, PC_RUN_ID, PC_URL,
                    PC_DOMAIN, PC_PROJECT, TEST_STATUS, COLLATION_STATUS
                ) VALUES (
                    PC_TEST_SEQ.NEXTVAL, :run_id, :pc_run_id, :pc_url,
                    :domain, :project, :test_status, :collation_status
                ) RETURNING PC_TEST_ID INTO :test_id
            """, {
                'run_id': run_id,
                'pc_run_id': pc_run_id,
                'pc_url': pc_url,
                'domain': pc_domain,
                'project': pc_project,
                'test_status': test_status,
                'collation_status': collation_status,
                'test_id': cursor.var(cx_Oracle.NUMBER)
            })
            
            test_id = int(cursor.getvalue()[0])
            conn.commit()
            
            return test_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving PC test run: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def save_lr_transactions(
        self,
        run_id: str,
        pc_run_id: str,
        transactions: List[Dict]
    ):
        """Save LoadRunner transaction results"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            for trans in transactions:
                cursor.execute("""
                    INSERT INTO LR_TRANSACTION_RESULTS (
                        TRANSACTION_ID, RUN_ID, PC_RUN_ID, TRANSACTION_NAME,
                        MINIMUM_TIME, AVERAGE_TIME, MAXIMUM_TIME,
                        STD_DEVIATION, PERCENTILE_90, PERCENTILE_95, PERCENTILE_99,
                        PASS_COUNT, FAIL_COUNT, STOP_COUNT, TOTAL_COUNT,
                        PASS_PERCENTAGE, THROUGHPUT_TPS
                    ) VALUES (
                        LR_TRANSACTION_SEQ.NEXTVAL, :run_id, :pc_run_id, :name,
                        :min, :avg, :max,
                        :std, :p90, :p95, :p99,
                        :pass, :fail, :stop, :total,
                        :pass_pct, :tps
                    )
                """, {
                    'run_id': run_id,
                    'pc_run_id': pc_run_id,
                    'name': trans['transaction_name'],
                    'min': trans['minimum_time'],
                    'avg': trans['average_time'],
                    'max': trans['maximum_time'],
                    'std': trans['std_deviation'],
                    'p90': trans['percentile_90'],
                    'p95': trans.get('percentile_95'),
                    'p99': trans.get('percentile_99'),
                    'pass': trans['pass_count'],
                    'fail': trans['fail_count'],
                    'stop': trans['stop_count'],
                    'total': trans['total_count'],
                    'pass_pct': trans['pass_percentage'],
                    'tps': trans.get('throughput_tps')
                })
            
            conn.commit()
            logger.info(f"Saved {len(transactions)} LR transactions")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving LR transactions: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def get_lr_transactions(self, run_id: str) -> List[Dict]:
        """Get LoadRunner transactions for run"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    TRANSACTION_NAME, MINIMUM_TIME, AVERAGE_TIME, MAXIMUM_TIME,
                    PERCENTILE_90, PERCENTILE_95, PERCENTILE_99,
                    PASS_COUNT, FAIL_COUNT, TOTAL_COUNT, PASS_PERCENTAGE
                FROM LR_TRANSACTION_RESULTS
                WHERE RUN_ID = :run_id
                ORDER BY AVERAGE_TIME DESC
            """, {'run_id': run_id})
            
            transactions = []
            for row in cursor.fetchall():
                transactions.append({
                    'transaction_name': row[0],
                    'minimum_time': float(row[1]),
                    'average_time': float(row[2]),
                    'maximum_time': float(row[3]),
                    'percentile_90': float(row[4]),
                    'percentile_95': float(row[5]) if row[5] else None,
                    'percentile_99': float(row[6]) if row[6] else None,
                    'pass_count': int(row[7]),
                    'fail_count': int(row[8]),
                    'total_count': int(row[9]),
                    'pass_percentage': float(row[10])
                })
            
            return transactions
            
        finally:
            cursor.close()
            conn.close()
```

**Continue to Part 2 with Unified Routing...**