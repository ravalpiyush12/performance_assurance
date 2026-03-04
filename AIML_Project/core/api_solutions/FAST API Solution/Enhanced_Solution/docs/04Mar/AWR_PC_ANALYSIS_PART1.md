# 🎯 Complete Implementation Guide - AWR Analysis & Performance Center Integration

## 📋 Table of Contents
1. Database Schema (Unified RUN_ID System)
2. AWR Analysis Implementation
3. Performance Center Integration
4. API Endpoints
5. UI Components

---

## 🗄️ PART 1: Database Schema

### Unified RUN_ID Format
```
Master RUN_ID: RUNID_{PC_RUN_ID}_{DATE}_{SEQ}
Example: RUNID_35678_04Mar2026_001

Solution-specific IDs:
- AppD_Run_04Mar2026_001_35678
- AWR_Run_04Mar2026_001_35678
- PC_Run_04Mar2026_001_35678
- Mongo_Run_04Mar2026_001_35678
```

---

### Table 1: RUN_MASTER (Central Registry)

```sql
-- Drop existing if recreating
-- DROP TABLE RUN_MASTER CASCADE CONSTRAINTS;

CREATE TABLE RUN_MASTER (
    RUN_ID VARCHAR2(100) PRIMARY KEY,
    PC_RUN_ID VARCHAR2(50) NOT NULL,
    LOB_NAME VARCHAR2(100) NOT NULL,
    TRACK VARCHAR2(50),
    TEST_NAME VARCHAR2(200),
    TEST_START_TIME TIMESTAMP,
    TEST_END_TIME TIMESTAMP,
    TEST_DURATION_MINUTES NUMBER,
    TEST_STATUS VARCHAR2(20) DEFAULT 'INITIATED',
    CREATED_BY VARCHAR2(100),
    CREATED_DATE DATE DEFAULT SYSDATE,
    UPDATED_DATE DATE DEFAULT SYSDATE,
    CONSTRAINT CHK_RUN_STATUS CHECK (TEST_STATUS IN ('INITIATED', 'RUNNING', 'COMPLETED', 'FAILED', 'ANALYZING'))
);

CREATE INDEX IDX_RUN_MASTER_LOB ON RUN_MASTER(LOB_NAME);
CREATE INDEX IDX_RUN_MASTER_PC ON RUN_MASTER(PC_RUN_ID);
CREATE INDEX IDX_RUN_MASTER_STATUS ON RUN_MASTER(TEST_STATUS);
CREATE INDEX IDX_RUN_MASTER_DATE ON RUN_MASTER(CREATED_DATE);

COMMENT ON TABLE RUN_MASTER IS 'Central registry for all test runs across monitoring solutions';
COMMENT ON COLUMN RUN_MASTER.PC_RUN_ID IS 'Performance Center run ID from LoadRunner';
```

---

### Table 2: AWR_ANALYSIS_RESULTS

```sql
CREATE TABLE AWR_ANALYSIS_RESULTS (
    ANALYSIS_ID NUMBER PRIMARY KEY,
    RUN_ID VARCHAR2(100) NOT NULL,
    AWR_RUN_ID VARCHAR2(150) NOT NULL UNIQUE,
    DATABASE_NAME VARCHAR2(100),
    INSTANCE_NAME VARCHAR2(50),
    HOST_NAME VARCHAR2(100),
    SNAPSHOT_BEGIN NUMBER,
    SNAPSHOT_END NUMBER,
    SNAPSHOT_BEGIN_TIME TIMESTAMP,
    SNAPSHOT_END_TIME TIMESTAMP,
    ELAPSED_TIME_MINUTES NUMBER,
    DB_TIME_MINUTES NUMBER,
    DB_CPU_MINUTES NUMBER,
    TOTAL_CONCERNS NUMBER DEFAULT 0,
    CRITICAL_CONCERNS NUMBER DEFAULT 0,
    WARNING_CONCERNS NUMBER DEFAULT 0,
    INFO_CONCERNS NUMBER DEFAULT 0,
    ANALYSIS_STATUS VARCHAR2(20) DEFAULT 'PROCESSING',
    REPORT_FILE_NAME VARCHAR2(200),
    REPORT_SIZE_KB NUMBER,
    REPORT_UPLOAD_TIME TIMESTAMP DEFAULT SYSTIMESTAMP,
    ANALYSIS_COMPLETED_TIME TIMESTAMP,
    CREATED_DATE DATE DEFAULT SYSDATE,
    CONSTRAINT FK_AWR_RUN FOREIGN KEY (RUN_ID) REFERENCES RUN_MASTER(RUN_ID) ON DELETE CASCADE,
    CONSTRAINT CHK_AWR_STATUS CHECK (ANALYSIS_STATUS IN ('PROCESSING', 'COMPLETED', 'FAILED'))
);

CREATE SEQUENCE AWR_ANALYSIS_SEQ START WITH 1 INCREMENT BY 1;
CREATE INDEX IDX_AWR_RUN_ID ON AWR_ANALYSIS_RESULTS(RUN_ID);
CREATE INDEX IDX_AWR_DB ON AWR_ANALYSIS_RESULTS(DATABASE_NAME);
CREATE INDEX IDX_AWR_STATUS ON AWR_ANALYSIS_RESULTS(ANALYSIS_STATUS);

COMMENT ON TABLE AWR_ANALYSIS_RESULTS IS 'AWR report analysis summary and metadata';
```

---

### Table 3: AWR_CONCERNS

```sql
CREATE TABLE AWR_CONCERNS (
    CONCERN_ID NUMBER PRIMARY KEY,
    ANALYSIS_ID NUMBER NOT NULL,
    RUN_ID VARCHAR2(100) NOT NULL,
    AWR_RUN_ID VARCHAR2(150) NOT NULL,
    CONCERN_CATEGORY VARCHAR2(50),
    CONCERN_TYPE VARCHAR2(50),
    SEVERITY VARCHAR2(20),
    CONCERN_TITLE VARCHAR2(500),
    CONCERN_DESCRIPTION CLOB,
    METRIC_NAME VARCHAR2(100),
    METRIC_VALUE NUMBER,
    THRESHOLD_VALUE NUMBER,
    RECOMMENDATION CLOB,
    SQL_ID VARCHAR2(20),
    CREATED_DATE DATE DEFAULT SYSDATE,
    CONSTRAINT FK_AWR_CONCERN_ANALYSIS FOREIGN KEY (ANALYSIS_ID) REFERENCES AWR_ANALYSIS_RESULTS(ANALYSIS_ID) ON DELETE CASCADE,
    CONSTRAINT FK_AWR_CONCERN_RUN FOREIGN KEY (RUN_ID) REFERENCES RUN_MASTER(RUN_ID) ON DELETE CASCADE,
    CONSTRAINT CHK_AWR_SEVERITY CHECK (SEVERITY IN ('CRITICAL', 'WARNING', 'INFO'))
);

CREATE SEQUENCE AWR_CONCERN_SEQ START WITH 1 INCREMENT BY 1;
CREATE INDEX IDX_AWR_CONCERN_ANALYSIS ON AWR_CONCERNS(ANALYSIS_ID);
CREATE INDEX IDX_AWR_CONCERN_RUN ON AWR_CONCERNS(RUN_ID);
CREATE INDEX IDX_AWR_CONCERN_SEVERITY ON AWR_CONCERNS(SEVERITY);
CREATE INDEX IDX_AWR_CONCERN_CATEGORY ON AWR_CONCERNS(CONCERN_CATEGORY);

COMMENT ON TABLE AWR_CONCERNS IS 'Detailed performance concerns identified from AWR analysis';
```

---

### Table 4: AWR_TOP_SQL

```sql
CREATE TABLE AWR_TOP_SQL (
    TOP_SQL_ID NUMBER PRIMARY KEY,
    ANALYSIS_ID NUMBER NOT NULL,
    RUN_ID VARCHAR2(100) NOT NULL,
    SQL_ID VARCHAR2(20),
    SQL_TEXT CLOB,
    EXECUTIONS NUMBER,
    ELAPSED_TIME_SECONDS NUMBER,
    CPU_TIME_SECONDS NUMBER,
    BUFFER_GETS NUMBER,
    DISK_READS NUMBER,
    ROWS_PROCESSED NUMBER,
    ELAPSED_PER_EXEC_MS NUMBER,
    CPU_PER_EXEC_MS NUMBER,
    RANK_BY_ELAPSED NUMBER,
    RANK_BY_CPU NUMBER,
    RANK_BY_READS NUMBER,
    CREATED_DATE DATE DEFAULT SYSDATE,
    CONSTRAINT FK_AWR_SQL_ANALYSIS FOREIGN KEY (ANALYSIS_ID) REFERENCES AWR_ANALYSIS_RESULTS(ANALYSIS_ID) ON DELETE CASCADE,
    CONSTRAINT FK_AWR_SQL_RUN FOREIGN KEY (RUN_ID) REFERENCES RUN_MASTER(RUN_ID) ON DELETE CASCADE
);

CREATE SEQUENCE AWR_TOP_SQL_SEQ START WITH 1 INCREMENT BY 1;
CREATE INDEX IDX_AWR_SQL_ANALYSIS ON AWR_TOP_SQL(ANALYSIS_ID);
CREATE INDEX IDX_AWR_SQL_ID ON AWR_TOP_SQL(SQL_ID);

COMMENT ON TABLE AWR_TOP_SQL IS 'Top SQL statements extracted from AWR reports';
```

---

### Table 5: AWR_WAIT_EVENTS

```sql
CREATE TABLE AWR_WAIT_EVENTS (
    WAIT_EVENT_ID NUMBER PRIMARY KEY,
    ANALYSIS_ID NUMBER NOT NULL,
    RUN_ID VARCHAR2(100) NOT NULL,
    EVENT_NAME VARCHAR2(100),
    EVENT_CLASS VARCHAR2(50),
    WAITS NUMBER,
    TOTAL_WAIT_TIME_SECONDS NUMBER,
    AVG_WAIT_TIME_MS NUMBER,
    PERCENT_DB_TIME NUMBER,
    RANK_POSITION NUMBER,
    CREATED_DATE DATE DEFAULT SYSDATE,
    CONSTRAINT FK_AWR_WAIT_ANALYSIS FOREIGN KEY (ANALYSIS_ID) REFERENCES AWR_ANALYSIS_RESULTS(ANALYSIS_ID) ON DELETE CASCADE,
    CONSTRAINT FK_AWR_WAIT_RUN FOREIGN KEY (RUN_ID) REFERENCES RUN_MASTER(RUN_ID) ON DELETE CASCADE
);

CREATE SEQUENCE AWR_WAIT_EVENT_SEQ START WITH 1 INCREMENT BY 1;
CREATE INDEX IDX_AWR_WAIT_ANALYSIS ON AWR_WAIT_EVENTS(ANALYSIS_ID);
CREATE INDEX IDX_AWR_WAIT_EVENT ON AWR_WAIT_EVENTS(EVENT_NAME);

COMMENT ON TABLE AWR_WAIT_EVENTS IS 'Top wait events extracted from AWR reports';
```

---

### Table 6: PC_TEST_RUNS (Performance Center)

```sql
CREATE TABLE PC_TEST_RUNS (
    PC_TEST_ID NUMBER PRIMARY KEY,
    RUN_ID VARCHAR2(100) NOT NULL,
    PC_RUN_ID VARCHAR2(50) NOT NULL,
    PC_URL VARCHAR2(500),
    PC_DOMAIN VARCHAR2(100),
    PC_PROJECT VARCHAR2(100),
    TEST_SET_NAME VARCHAR2(200),
    TEST_INSTANCE_ID VARCHAR2(50),
    TEST_STATUS VARCHAR2(50),
    START_TIME TIMESTAMP,
    END_TIME TIMESTAMP,
    DURATION_SECONDS NUMBER,
    COLLATION_STATUS VARCHAR2(50),
    REPORT_FILE_PATH VARCHAR2(500),
    REPORT_FETCHED CHAR(1) DEFAULT 'N',
    CREATED_DATE DATE DEFAULT SYSDATE,
    UPDATED_DATE DATE DEFAULT SYSDATE,
    CONSTRAINT FK_PC_RUN FOREIGN KEY (RUN_ID) REFERENCES RUN_MASTER(RUN_ID) ON DELETE CASCADE,
    CONSTRAINT CHK_PC_REPORT_FETCHED CHECK (REPORT_FETCHED IN ('Y', 'N'))
);

CREATE SEQUENCE PC_TEST_SEQ START WITH 1 INCREMENT BY 1;
CREATE INDEX IDX_PC_RUN_ID ON PC_TEST_RUNS(RUN_ID);
CREATE INDEX IDX_PC_RUN_ID_UNIQUE ON PC_TEST_RUNS(PC_RUN_ID);
CREATE INDEX IDX_PC_STATUS ON PC_TEST_RUNS(TEST_STATUS);

COMMENT ON TABLE PC_TEST_RUNS IS 'Performance Center test run details';
```

---

### Table 7: LR_TRANSACTION_RESULTS (LoadRunner Transactions)

```sql
CREATE TABLE LR_TRANSACTION_RESULTS (
    TRANSACTION_ID NUMBER PRIMARY KEY,
    RUN_ID VARCHAR2(100) NOT NULL,
    PC_RUN_ID VARCHAR2(50) NOT NULL,
    TRANSACTION_NAME VARCHAR2(200),
    MINIMUM_TIME NUMBER,
    AVERAGE_TIME NUMBER,
    MAXIMUM_TIME NUMBER,
    STD_DEVIATION NUMBER,
    PERCENTILE_90 NUMBER,
    PERCENTILE_95 NUMBER,
    PERCENTILE_99 NUMBER,
    PASS_COUNT NUMBER,
    FAIL_COUNT NUMBER,
    STOP_COUNT NUMBER,
    TOTAL_COUNT NUMBER,
    PASS_PERCENTAGE NUMBER,
    THROUGHPUT_TPS NUMBER,
    CREATED_DATE DATE DEFAULT SYSDATE,
    CONSTRAINT FK_LR_TRANS_RUN FOREIGN KEY (RUN_ID) REFERENCES RUN_MASTER(RUN_ID) ON DELETE CASCADE
);

CREATE SEQUENCE LR_TRANSACTION_SEQ START WITH 1 INCREMENT BY 1;
CREATE INDEX IDX_LR_TRANS_RUN ON LR_TRANSACTION_RESULTS(RUN_ID);
CREATE INDEX IDX_LR_TRANS_PC ON LR_TRANSACTION_RESULTS(PC_RUN_ID);
CREATE INDEX IDX_LR_TRANS_NAME ON LR_TRANSACTION_RESULTS(TRANSACTION_NAME);

COMMENT ON TABLE LR_TRANSACTION_RESULTS IS 'LoadRunner transaction statistics from summary.html';
```

---

### Table 8: Update APPD_MONITORING_RUNS (Add RUN_ID)

```sql
-- Add RUN_ID column to existing AppD monitoring runs table
ALTER TABLE APPD_MONITORING_RUNS ADD RUN_ID VARCHAR2(100);
ALTER TABLE APPD_MONITORING_RUNS ADD PC_RUN_ID VARCHAR2(50);

-- Add foreign key constraint
ALTER TABLE APPD_MONITORING_RUNS 
ADD CONSTRAINT FK_APPD_RUN_MASTER 
FOREIGN KEY (RUN_ID) REFERENCES RUN_MASTER(RUN_ID) ON DELETE CASCADE;

CREATE INDEX IDX_APPD_RUN_ID ON APPD_MONITORING_RUNS(RUN_ID);

COMMENT ON COLUMN APPD_MONITORING_RUNS.RUN_ID IS 'Links to central RUN_MASTER table';
COMMENT ON COLUMN APPD_MONITORING_RUNS.PC_RUN_ID IS 'Performance Center run ID';
```

---

## 🔧 PART 2: Python Helper Functions

### File: `common/run_id_generator.py`

```python
"""
Unified RUN_ID Generation System
Generates consistent run IDs across all monitoring solutions
"""
from datetime import datetime
from typing import Optional

class RunIDGenerator:
    """Generate unified run IDs for monitoring solutions"""
    
    @staticmethod
    def generate_master_run_id(pc_run_id: str, sequence: int = 1) -> str:
        """
        Generate master run ID
        Format: RUNID_{PC_RUN_ID}_{DATE}_{SEQ}
        Example: RUNID_35678_04Mar2026_001
        """
        now = datetime.now()
        day = now.strftime('%d')
        month = now.strftime('%b')
        year = now.strftime('%Y')
        seq_str = str(sequence).zfill(3)
        
        return f"RUNID_{pc_run_id}_{day}{month}{year}_{seq_str}"
    
    @staticmethod
    def generate_solution_run_id(
        solution_prefix: str,
        pc_run_id: str,
        sequence: int = 1
    ) -> str:
        """
        Generate solution-specific run ID
        Format: {PREFIX}_Run_{DATE}_{SEQ}_{PC_RUN_ID}
        
        Examples:
        - AppD_Run_04Mar2026_001_35678
        - AWR_Run_04Mar2026_001_35678
        - PC_Run_04Mar2026_001_35678
        """
        now = datetime.now()
        day = now.strftime('%d')
        month = now.strftime('%b')
        year = now.strftime('%Y')
        seq_str = str(sequence).zfill(3)
        
        return f"{solution_prefix}_Run_{day}{month}{year}_{seq_str}_{pc_run_id}"
    
    @staticmethod
    def parse_pc_run_id_from_solution_id(solution_run_id: str) -> Optional[str]:
        """
        Extract PC Run ID from solution-specific run ID
        Example: AppD_Run_04Mar2026_001_35678 -> 35678
        """
        parts = solution_run_id.split('_')
        if len(parts) >= 5:
            return parts[-1]
        return None
    
    @staticmethod
    def get_next_sequence(pc_run_id: str, db_connection) -> int:
        """
        Get next sequence number for today's runs with same PC_RUN_ID
        """
        from datetime import date
        
        cursor = db_connection.cursor()
        try:
            today = date.today()
            
            sql = """
                SELECT COUNT(*) 
                FROM RUN_MASTER 
                WHERE PC_RUN_ID = :pc_run_id 
                  AND TRUNC(CREATED_DATE) = :today
            """
            
            cursor.execute(sql, {'pc_run_id': pc_run_id, 'today': today})
            count = cursor.fetchone()[0]
            
            return count + 1
            
        finally:
            cursor.close()


# Usage Examples:
if __name__ == "__main__":
    generator = RunIDGenerator()
    
    pc_run_id = "35678"
    sequence = 1
    
    # Generate master run ID
    master_id = generator.generate_master_run_id(pc_run_id, sequence)
    print(f"Master RUN_ID: {master_id}")
    # Output: RUNID_35678_04Mar2026_001
    
    # Generate solution-specific IDs
    appd_id = generator.generate_solution_run_id("AppD", pc_run_id, sequence)
    print(f"AppD RUN_ID: {appd_id}")
    # Output: AppD_Run_04Mar2026_001_35678
    
    awr_id = generator.generate_solution_run_id("AWR", pc_run_id, sequence)
    print(f"AWR RUN_ID: {awr_id}")
    # Output: AWR_Run_04Mar2026_001_35678
    
    # Parse PC Run ID
    extracted = generator.parse_pc_run_id_from_solution_id(appd_id)
    print(f"Extracted PC_RUN_ID: {extracted}")
    # Output: 35678
```

---

## 📝 PART 3: AWR Analysis - Pydantic Models

### File: `monitoring/awr/models.py`

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

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

class AWRUploadRequest(BaseModel):
    """Request model for AWR report upload"""
    run_id: str = Field(..., description="Master run ID from RUN_MASTER")
    pc_run_id: str = Field(..., description="Performance Center run ID")
    database_name: str
    lob_name: str
    track: Optional[str] = None
    test_name: Optional[str] = None

class AWRConcern(BaseModel):
    """Individual performance concern"""
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

class TopSQL(BaseModel):
    """Top SQL statement details"""
    sql_id: str
    sql_text: Optional[str] = ""
    executions: int
    elapsed_time_seconds: float
    cpu_time_seconds: float
    buffer_gets: int
    disk_reads: int
    rows_processed: int
    elapsed_per_exec_ms: float
    rank_by_elapsed: int

class WaitEvent(BaseModel):
    """Wait event details"""
    event_name: str
    event_class: Optional[str] = "Unknown"
    waits: int
    total_wait_time_seconds: float
    avg_wait_time_ms: float
    percent_db_time: float
    rank_position: int

class AWRAnalysisResponse(BaseModel):
    """Response model for AWR analysis"""
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
    db_cpu_minutes: float
    total_concerns: int
    critical_concerns: int
    warning_concerns: int
    info_concerns: int
    concerns: List[AWRConcern]
    top_sql: List[TopSQL]
    top_wait_events: List[WaitEvent]
    message: str

class AWRAnalysisSummary(BaseModel):
    """Summary model for UI display"""
    awr_run_id: str
    database_name: str
    snapshot_range: str
    elapsed_time: str
    total_concerns: int
    critical_concerns: int
    warning_concerns: int
    top_concerns: List[AWRConcern]
    analysis_date: datetime
```

---

*Continue to Part 2 with AWR Parser, Analyzer, Database operations, and API endpoints...*