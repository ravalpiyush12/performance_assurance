# 🎯 Complete Implementation Guide - Part 3: Database, API & Performance Center

## 📝 PART 6: AWR Database Operations

### File: `monitoring/awr/database.py`

```python
"""
AWR Analysis Database Operations
"""
import cx_Oracle
from typing import List, Dict, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class AWRDatabase:
    """Handle AWR analysis database operations"""
    
    def __init__(self, connection_pool):
        self.pool = connection_pool
    
    def save_analysis_result(
        self,
        run_id: str,
        awr_run_id: str,
        header: Dict,
        parsed_data: Dict,
        concerns: List[Dict],
        top_sql: List[Dict],
        wait_events: List[Dict]
    ) -> int:
        """Save complete AWR analysis to database"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            # Calculate summary stats
            critical_count = sum(1 for c in concerns if c['severity'] == 'CRITICAL')
            warning_count = sum(1 for c in concerns if c['severity'] == 'WARNING')
            info_count = sum(1 for c in concerns if c['severity'] == 'INFO')
            
            # Insert analysis result
            cursor.execute("""
                INSERT INTO AWR_ANALYSIS_RESULTS (
                    ANALYSIS_ID, RUN_ID, AWR_RUN_ID, DATABASE_NAME, INSTANCE_NAME,
                    HOST_NAME, SNAPSHOT_BEGIN, SNAPSHOT_END,
                    SNAPSHOT_BEGIN_TIME, SNAPSHOT_END_TIME,
                    ELAPSED_TIME_MINUTES, DB_TIME_MINUTES, DB_CPU_MINUTES,
                    TOTAL_CONCERNS, CRITICAL_CONCERNS, WARNING_CONCERNS, INFO_CONCERNS,
                    ANALYSIS_STATUS, REPORT_FILE_NAME, ANALYSIS_COMPLETED_TIME
                ) VALUES (
                    AWR_ANALYSIS_SEQ.NEXTVAL, :run_id, :awr_run_id, :db_name, :instance,
                    :host, :snap_begin, :snap_end,
                    :snap_begin_time, :snap_end_time,
                    :elapsed, :db_time, :db_cpu,
                    :total, :critical, :warning, :info,
                    'COMPLETED', :filename, SYSTIMESTAMP
                ) RETURNING ANALYSIS_ID INTO :analysis_id
            """, {
                'run_id': run_id,
                'awr_run_id': awr_run_id,
                'db_name': header.get('db_name', 'UNKNOWN'),
                'instance': header.get('instance_name', 'UNKNOWN'),
                'host': header.get('host_name', 'UNKNOWN'),
                'snap_begin': header.get('snapshot_begin', 0),
                'snap_end': header.get('snapshot_end', 0),
                'snap_begin_time': None,  # Parse from report if available
                'snap_end_time': None,
                'elapsed': header.get('elapsed_time_minutes', 0),
                'db_time': header.get('db_time_minutes', 0),
                'db_cpu': parsed_data.get('time_model_stats', {}).get('DB CPU', 0) / 60,
                'total': len(concerns),
                'critical': critical_count,
                'warning': warning_count,
                'info': info_count,
                'filename': 'uploaded_report.html',
                'analysis_id': cursor.var(cx_Oracle.NUMBER)
            })
            
            analysis_id = int(cursor.getvalue()[0])
            
            # Save concerns
            for concern in concerns:
                self._save_concern(cursor, analysis_id, run_id, awr_run_id, concern)
            
            # Save top SQL
            for sql in top_sql[:10]:
                self._save_top_sql(cursor, analysis_id, run_id, sql)
            
            # Save wait events
            for event in wait_events[:10]:
                self._save_wait_event(cursor, analysis_id, run_id, event)
            
            conn.commit()
            logger.info(f"Saved AWR analysis {analysis_id} for run {run_id}")
            
            return analysis_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving AWR analysis: {e}", exc_info=True)
            raise
        finally:
            cursor.close()
            conn.close()
    
    def _save_concern(self, cursor, analysis_id: int, run_id: str, 
                     awr_run_id: str, concern: Dict):
        """Save individual concern"""
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
    
    def _save_top_sql(self, cursor, analysis_id: int, run_id: str, sql: Dict):
        """Save top SQL entry"""
        cursor.execute("""
            INSERT INTO AWR_TOP_SQL (
                TOP_SQL_ID, ANALYSIS_ID, RUN_ID, SQL_ID,
                EXECUTIONS, ELAPSED_TIME_SECONDS, CPU_TIME_SECONDS,
                BUFFER_GETS, DISK_READS, ROWS_PROCESSED,
                ELAPSED_PER_EXEC_MS, CPU_PER_EXEC_MS,
                RANK_BY_ELAPSED, RANK_BY_CPU
            ) VALUES (
                AWR_TOP_SQL_SEQ.NEXTVAL, :analysis_id, :run_id, :sql_id,
                :executions, :elapsed, :cpu,
                :gets, :reads, :rows,
                :elapsed_per_exec, :cpu_per_exec,
                :rank_elapsed, :rank_cpu
            )
        """, {
            'analysis_id': analysis_id,
            'run_id': run_id,
            'sql_id': sql.get('sql_id', 'UNKNOWN'),
            'executions': sql.get('executions', 0),
            'elapsed': sql.get('elapsed_time_sec', 0),
            'cpu': sql.get('cpu_time_sec', 0),
            'gets': sql.get('buffer_gets', 0),
            'reads': 0,  # Not always in report
            'rows': 0,
            'elapsed_per_exec': sql.get('elapsed_per_exec', 0),
            'cpu_per_exec': sql.get('cpu_per_exec', 0),
            'rank_elapsed': sql.get('rank', 0),
            'rank_cpu': 0
        })
    
    def _save_wait_event(self, cursor, analysis_id: int, run_id: str, event: Dict):
        """Save wait event"""
        cursor.execute("""
            INSERT INTO AWR_WAIT_EVENTS (
                WAIT_EVENT_ID, ANALYSIS_ID, RUN_ID,
                EVENT_NAME, EVENT_CLASS, WAITS,
                TOTAL_WAIT_TIME_SECONDS, AVG_WAIT_TIME_MS,
                PERCENT_DB_TIME, RANK_POSITION
            ) VALUES (
                AWR_WAIT_EVENT_SEQ.NEXTVAL, :analysis_id, :run_id,
                :event_name, :event_class, :waits,
                :total_wait, :avg_wait,
                :percent_db, :rank
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
    
    def get_analysis_by_run_id(self, run_id: str) -> Optional[Dict]:
        """Get AWR analysis for a run"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    ANALYSIS_ID, AWR_RUN_ID, DATABASE_NAME, INSTANCE_NAME,
                    SNAPSHOT_BEGIN, SNAPSHOT_END, ELAPSED_TIME_MINUTES,
                    DB_TIME_MINUTES, TOTAL_CONCERNS, CRITICAL_CONCERNS,
                    WARNING_CONCERNS, ANALYSIS_STATUS
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
                'db_time_minutes': row[7],
                'total_concerns': row[8],
                'critical_concerns': row[9],
                'warning_concerns': row[10],
                'analysis_status': row[11]
            }
            
        finally:
            cursor.close()
            conn.close()
    
    def get_concerns_by_analysis_id(self, analysis_id: int) -> List[Dict]:
        """Get all concerns for an analysis"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    CONCERN_CATEGORY, CONCERN_TYPE, SEVERITY,
                    CONCERN_TITLE, CONCERN_DESCRIPTION,
                    METRIC_NAME, METRIC_VALUE, THRESHOLD_VALUE,
                    RECOMMENDATION, SQL_ID
                FROM AWR_CONCERNS
                WHERE ANALYSIS_ID = :analysis_id
                ORDER BY 
                    CASE SEVERITY 
                        WHEN 'CRITICAL' THEN 1
                        WHEN 'WARNING' THEN 2
                        ELSE 3
                    END,
                    CONCERN_ID
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
                    'threshold_value': float(row[7]) if row[7] else None,
                    'recommendation': row[8].read() if hasattr(row[8], 'read') else row[8],
                    'sql_id': row[9]
                })
            
            return concerns
            
        finally:
            cursor.close()
            conn.close()
```

---

## 📝 PART 7: AWR API Routes

### File: `monitoring/awr/routes.py`

```python
"""
AWR Analysis API Endpoints
"""
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Optional
import logging

from .models import AWRUploadRequest, AWRAnalysisResponse
from .parser import AWRParser
from .analyzer import AWRAnalyzer
from .database import AWRDatabase
from common.run_id_generator import RunIDGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/awr", tags=["AWR Analysis"])

# Database instance (injected)
awr_db: Optional[AWRDatabase] = None

def init_awr_routes(db_pool):
    """Initialize AWR routes with database connection"""
    global awr_db
    awr_db = AWRDatabase(db_pool)


@router.post("/upload", response_model=AWRAnalysisResponse)
async def upload_awr_report(
    file: UploadFile = File(..., description="AWR HTML report file"),
    run_id: str = Form(..., description="Master run ID"),
    pc_run_id: str = Form(..., description="Performance Center run ID"),
    database_name: str = Form(...),
    lob_name: str = Form(...),
    track: Optional[str] = Form(None),
    test_name: Optional[str] = Form(None)
):
    """
    Upload and analyze AWR HTML report
    
    - Parses AWR report
    - Identifies performance concerns
    - Stores results in database
    - Returns analysis summary
    """
    if not awr_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        logger.info(f"Receiving AWR report upload for run {run_id}")
        
        # Read file content
        content = await file.read()
        html_content = content.decode('utf-8', errors='ignore')
        
        # Generate AWR-specific run ID
        awr_run_id = RunIDGenerator.generate_solution_run_id("AWR", pc_run_id, 1)
        
        logger.info(f"Generated AWR Run ID: {awr_run_id}")
        
        # Parse AWR report
        logger.info("Parsing AWR report...")
        parser = AWRParser(html_content)
        parsed_data = parser.parse()
        
        header = parsed_data['header']
        logger.info(f"Parsed report for DB: {header.get('db_name')}, Instance: {header.get('instance_name')}")
        
        # Analyze report
        logger.info("Analyzing AWR data...")
        analyzer = AWRAnalyzer(parsed_data)
        concerns = analyzer.analyze()
        
        logger.info(f"Analysis complete. Found {len(concerns)} concerns")
        
        # Save to database
        logger.info("Saving analysis to database...")
        analysis_id = awr_db.save_analysis_result(
            run_id=run_id,
            awr_run_id=awr_run_id,
            header=header,
            parsed_data=parsed_data,
            concerns=[c.dict() for c in concerns],
            top_sql=parsed_data.get('top_sql', []),
            wait_events=parsed_data.get('wait_events', [])
        )
        
        logger.info(f"Analysis saved with ID: {analysis_id}")
        
        # Prepare response
        summary = analyzer.get_summary()
        
        return AWRAnalysisResponse(
            success=True,
            awr_run_id=awr_run_id,
            run_id=run_id,
            analysis_id=analysis_id,
            database_name=header.get('db_name', database_name),
            instance_name=header.get('instance_name', 'UNKNOWN'),
            snapshot_begin=header.get('snapshot_begin', 0),
            snapshot_end=header.get('snapshot_end', 0),
            elapsed_time_minutes=header.get('elapsed_time_minutes', 0),
            db_time_minutes=header.get('db_time_minutes', 0),
            db_cpu_minutes=parsed_data.get('time_model_stats', {}).get('DB CPU', 0) / 60,
            total_concerns=summary['total_concerns'],
            critical_concerns=summary['critical_concerns'],
            warning_concerns=summary['warning_concerns'],
            info_concerns=summary['info_concerns'],
            concerns=concerns,
            top_sql=[],  # Can add if needed
            top_wait_events=[],
            message=f"AWR analysis completed successfully. Found {summary['critical_concerns']} critical and {summary['warning_concerns']} warning concerns."
        )
        
    except Exception as e:
        logger.error(f"Error processing AWR report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error analyzing AWR report: {str(e)}")


@router.get("/analysis/{run_id}")
async def get_awr_analysis(run_id: str):
    """Get AWR analysis for a specific run"""
    if not awr_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        analysis = awr_db.get_analysis_by_run_id(run_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail=f"No AWR analysis found for run {run_id}")
        
        # Get concerns
        concerns = awr_db.get_concerns_by_analysis_id(analysis['analysis_id'])
        
        return {
            "success": True,
            "analysis": analysis,
            "concerns": concerns
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving AWR analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/{lob_name}")
async def get_awr_health_status(lob_name: str):
    """Get AWR analysis health status for landing page"""
    if not awr_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    # Placeholder - implement based on your needs
    return {
        "lob_name": lob_name,
        "status": "configured",
        "recent_analyses": 0,
        "message": "AWR analysis configured"
    }
```

**Continue to Part 4 with Performance Center integration...**