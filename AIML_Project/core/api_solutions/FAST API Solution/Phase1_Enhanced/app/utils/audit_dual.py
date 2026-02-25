"""
Enhanced Audit Logger - Dual Logging System
Supports both JSONL file logging and Oracle Database (CQE_NFT) table logging
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import cx_Oracle


class AuditLogger:
    """
    Dual audit logger that writes to:
    1. JSONL files (one JSON object per line)
    2. Oracle database table in CQE_NFT
    """
    
    def __init__(self, settings, cqe_nft_pool=None):
        """
        Initialize audit logger
        
        Args:
            settings: Application settings
            cqe_nft_pool: Optional CQE_NFT connection pool for database audit
        """
        self.settings = settings
        self.enabled = settings.ENABLE_AUDIT_LOG
        self.log_path = settings.AUDIT_LOG_PATH
        self.cqe_nft_pool = cqe_nft_pool
        
        # Configure audit destinations
        self.file_audit_enabled = True
        self.db_audit_enabled = cqe_nft_pool is not None
        
        if self.enabled and self.file_audit_enabled:
            # Create audit log directory for JSONL files
            Path(self.log_path).mkdir(parents=True, exist_ok=True)
        
        if self.db_audit_enabled:
            # Initialize database audit table
            self._initialize_audit_table()
    
    def _initialize_audit_table(self):
        """
        Create audit table in CQE_NFT if it doesn't exist
        
        Table: AUDIT_LOG
        Columns:
        - AUDIT_ID (NUMBER, Primary Key)
        - EVENT_TIMESTAMP (TIMESTAMP)
        - EVENT_TYPE (VARCHAR2)
        - DATABASE_NAME (VARCHAR2)
        - USERNAME (VARCHAR2)
        - SQL_STATEMENT (CLOB)
        - ROWS_AFFECTED (NUMBER)
        - EXECUTION_TIME_MS (NUMBER)
        - STATUS (VARCHAR2)
        - ERROR_MESSAGE (VARCHAR2)
        - API_KEY_HASH (VARCHAR2)
        - CLIENT_IP (VARCHAR2)
        - ENVIRONMENT (VARCHAR2)
        - ADDITIONAL_DATA (CLOB)
        """
        try:
            with self.cqe_nft_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create sequence for audit ID
                create_sequence_sql = """
                BEGIN
                    EXECUTE IMMEDIATE 'CREATE SEQUENCE AUDIT_LOG_SEQ START WITH 1 INCREMENT BY 1';
                EXCEPTION
                    WHEN OTHERS THEN
                        IF SQLCODE != -955 THEN  -- -955: name is already used
                            RAISE;
                        END IF;
                END;
                """
                cursor.execute(create_sequence_sql)
                
                # Create audit table
                create_table_sql = """
                BEGIN
                    EXECUTE IMMEDIATE '
                    CREATE TABLE AUDIT_LOG (
                        AUDIT_ID NUMBER PRIMARY KEY,
                        EVENT_TIMESTAMP TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        EVENT_TYPE VARCHAR2(100) NOT NULL,
                        DATABASE_NAME VARCHAR2(100),
                        USERNAME VARCHAR2(100),
                        SQL_STATEMENT CLOB,
                        ROWS_AFFECTED NUMBER,
                        EXECUTION_TIME_MS NUMBER,
                        STATUS VARCHAR2(50),
                        ERROR_MESSAGE VARCHAR2(4000),
                        API_KEY_HASH VARCHAR2(100),
                        CLIENT_IP VARCHAR2(50),
                        ENVIRONMENT VARCHAR2(50),
                        ADDITIONAL_DATA CLOB,
                        CREATED_DATE DATE DEFAULT SYSDATE
                    )';
                EXCEPTION
                    WHEN OTHERS THEN
                        IF SQLCODE != -955 THEN  -- -955: name is already used
                            RAISE;
                        END IF;
                END;
                """
                cursor.execute(create_table_sql)
                
                # Create index on event_timestamp for performance
                create_index_sql = """
                BEGIN
                    EXECUTE IMMEDIATE 'CREATE INDEX IDX_AUDIT_LOG_TIMESTAMP ON AUDIT_LOG(EVENT_TIMESTAMP)';
                EXCEPTION
                    WHEN OTHERS THEN
                        IF SQLCODE != -955 THEN
                            RAISE;
                        END IF;
                END;
                """
                cursor.execute(create_index_sql)
                
                # Create index on database_name
                create_index2_sql = """
                BEGIN
                    EXECUTE IMMEDIATE 'CREATE INDEX IDX_AUDIT_LOG_DATABASE ON AUDIT_LOG(DATABASE_NAME)';
                EXCEPTION
                    WHEN OTHERS THEN
                        IF SQLCODE != -955 THEN
                            RAISE;
                        END IF;
                END;
                """
                cursor.execute(create_index2_sql)
                
                conn.commit()
                cursor.close()
                
                print("✓ Audit table initialized in CQE_NFT", flush=True)
                
        except Exception as e:
            print(f"⚠ Failed to initialize audit table: {e}", flush=True)
            # Don't raise - audit table creation failure shouldn't stop app
    
    def log_event(
        self,
        event_type: str,
        database: Optional[str] = None,
        username: Optional[str] = None,
        sql: Optional[str] = None,
        rows_affected: Optional[int] = None,
        execution_time_ms: Optional[float] = None,
        status: str = "success",
        error: Optional[str] = None,
        api_key: Optional[str] = None,
        client_ip: Optional[str] = None,
        **kwargs
    ):
        """
        Log an audit event to both JSONL file and Oracle database
        
        Args:
            event_type: Type of event (sql_executed, sql_failed, etc.)
            database: Database name where operation was performed
            username: Database username used
            sql: SQL statement executed (truncated to 200 chars for file, full for DB)
            rows_affected: Number of rows affected
            execution_time_ms: Execution time in milliseconds
            status: Event status (success, failed, error)
            error: Error message if failed
            api_key: API key used (last 8 chars only for security)
            client_ip: Client IP address
            **kwargs: Additional event data
        """
        if not self.enabled:
            return
        
        timestamp = datetime.now()
        
        # Build event record
        event = {
            "timestamp": timestamp.isoformat(),
            "event_type": event_type,
            "environment": self.settings.ENVIRONMENT,
            "database": database,
            "username": username,
            "sql": sql[:200] if sql else None,  # Truncate for JSONL
            "rows_affected": rows_affected,
            "execution_time_ms": execution_time_ms,
            "status": status,
            "error": error,
            "api_key_hash": api_key,
            "client_ip": client_ip,
            **kwargs
        }
        
        # Log to JSONL file
        if self.file_audit_enabled:
            self._log_to_file(event)
        
        # Log to Oracle database
        if self.db_audit_enabled:
            self._log_to_database(
                timestamp=timestamp,
                event_type=event_type,
                database=database,
                username=username,
                sql=sql,  # Full SQL for database
                rows_affected=rows_affected,
                execution_time_ms=execution_time_ms,
                status=status,
                error=error,
                api_key_hash=api_key,
                client_ip=client_ip,
                additional_data=kwargs
            )
    
    def _log_to_file(self, event: Dict[str, Any]):
        """
        Log event to JSONL file
        
        Args:
            event: Event data dictionary
        """
        try:
            # Generate filename with current date
            log_file = os.path.join(
                self.log_path,
                f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"
            )
            
            # Write to JSONL file (one JSON object per line)
            with open(log_file, 'a') as f:
                f.write(json.dumps(event) + '\n')
                
        except Exception as e:
            print(f"Failed to write file audit log: {e}", flush=True)
    
    def _log_to_database(
        self,
        timestamp: datetime,
        event_type: str,
        database: Optional[str],
        username: Optional[str],
        sql: Optional[str],
        rows_affected: Optional[int],
        execution_time_ms: Optional[float],
        status: str,
        error: Optional[str],
        api_key_hash: Optional[str],
        client_ip: Optional[str],
        additional_data: Dict[str, Any]
    ):
        """
        Log event to Oracle CQE_NFT database table
        
        Args:
            All audit event parameters
        """
        try:
            with self.cqe_nft_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # Convert additional_data to JSON string
                additional_json = json.dumps(additional_data) if additional_data else None
                
                # Insert audit record
                insert_sql = """
                INSERT INTO AUDIT_LOG (
                    AUDIT_ID,
                    EVENT_TIMESTAMP,
                    EVENT_TYPE,
                    DATABASE_NAME,
                    USERNAME,
                    SQL_STATEMENT,
                    ROWS_AFFECTED,
                    EXECUTION_TIME_MS,
                    STATUS,
                    ERROR_MESSAGE,
                    API_KEY_HASH,
                    CLIENT_IP,
                    ENVIRONMENT,
                    ADDITIONAL_DATA
                ) VALUES (
                    AUDIT_LOG_SEQ.NEXTVAL,
                    :event_timestamp,
                    :event_type,
                    :database_name,
                    :username,
                    :sql_statement,
                    :rows_affected,
                    :execution_time_ms,
                    :status,
                    :error_message,
                    :api_key_hash,
                    :client_ip,
                    :environment,
                    :additional_data
                )
                """
                
                cursor.execute(insert_sql, {
                    'event_timestamp': timestamp,
                    'event_type': event_type,
                    'database_name': database,
                    'username': username,
                    'sql_statement': sql,
                    'rows_affected': rows_affected,
                    'execution_time_ms': execution_time_ms,
                    'status': status,
                    'error_message': error[:4000] if error else None,  # Truncate to VARCHAR2 limit
                    'api_key_hash': api_key_hash,
                    'client_ip': client_ip,
                    'environment': self.settings.ENVIRONMENT,
                    'additional_data': additional_json
                })
                
                conn.commit()
                cursor.close()
                
        except Exception as e:
            print(f"Failed to write database audit log: {e}", flush=True)
            # Don't raise - audit failure shouldn't stop the main operation
    
    def query_audit_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        database: Optional[str] = None,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """
        Query audit logs from Oracle database
        
        Args:
            start_date: Filter logs from this date
            end_date: Filter logs until this date
            database: Filter by database name
            event_type: Filter by event type
            status: Filter by status (success/failed)
            limit: Maximum number of records to return
            
        Returns:
            List of audit log records
        """
        if not self.db_audit_enabled:
            return []
        
        try:
            with self.cqe_nft_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic query
                where_clauses = []
                params = {}
                
                if start_date:
                    where_clauses.append("EVENT_TIMESTAMP >= :start_date")
                    params['start_date'] = start_date
                
                if end_date:
                    where_clauses.append("EVENT_TIMESTAMP <= :end_date")
                    params['end_date'] = end_date
                
                if database:
                    where_clauses.append("DATABASE_NAME = :database")
                    params['database'] = database
                
                if event_type:
                    where_clauses.append("EVENT_TYPE = :event_type")
                    params['event_type'] = event_type
                
                if status:
                    where_clauses.append("STATUS = :status")
                    params['status'] = status
                
                where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
                
                query_sql = f"""
                SELECT 
                    AUDIT_ID,
                    EVENT_TIMESTAMP,
                    EVENT_TYPE,
                    DATABASE_NAME,
                    USERNAME,
                    SQL_STATEMENT,
                    ROWS_AFFECTED,
                    EXECUTION_TIME_MS,
                    STATUS,
                    ERROR_MESSAGE,
                    API_KEY_HASH,
                    CLIENT_IP,
                    ENVIRONMENT,
                    ADDITIONAL_DATA,
                    CREATED_DATE
                FROM AUDIT_LOG
                WHERE {where_clause}
                ORDER BY EVENT_TIMESTAMP DESC
                FETCH FIRST :limit ROWS ONLY
                """
                
                params['limit'] = limit
                
                cursor.execute(query_sql, params)
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    record = {}
                    for i, col in enumerate(columns):
                        value = row[i]
                        # Convert datetime to string
                        if isinstance(value, datetime):
                            value = value.isoformat()
                        # Parse JSON additional_data
                        if col == 'ADDITIONAL_DATA' and value:
                            try:
                                value = json.loads(value)
                            except:
                                pass
                        record[col.lower()] = value
                    results.append(record)
                
                cursor.close()
                return results
                
        except Exception as e:
            print(f"Failed to query audit logs: {e}", flush=True)
            return []
    
    def get_audit_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get audit log statistics
        
        Args:
            start_date: Start date for statistics
            end_date: End date for statistics
            
        Returns:
            Dictionary with statistics
        """
        if not self.db_audit_enabled:
            return {}
        
        try:
            with self.cqe_nft_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                where_clauses = []
                params = {}
                
                if start_date:
                    where_clauses.append("EVENT_TIMESTAMP >= :start_date")
                    params['start_date'] = start_date
                
                if end_date:
                    where_clauses.append("EVENT_TIMESTAMP <= :end_date")
                    params['end_date'] = end_date
                
                where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
                
                stats_sql = f"""
                SELECT 
                    COUNT(*) as total_events,
                    SUM(CASE WHEN STATUS = 'success' THEN 1 ELSE 0 END) as successful_events,
                    SUM(CASE WHEN STATUS = 'failed' THEN 1 ELSE 0 END) as failed_events,
                    AVG(EXECUTION_TIME_MS) as avg_execution_time,
                    MAX(EXECUTION_TIME_MS) as max_execution_time,
                    SUM(ROWS_AFFECTED) as total_rows_affected
                FROM AUDIT_LOG
                WHERE {where_clause}
                """
                
                cursor.execute(stats_sql, params)
                row = cursor.fetchone()
                
                # Get event type breakdown
                event_type_sql = f"""
                SELECT EVENT_TYPE, COUNT(*) as count
                FROM AUDIT_LOG
                WHERE {where_clause}
                GROUP BY EVENT_TYPE
                ORDER BY count DESC
                """
                
                cursor.execute(event_type_sql, params)
                event_types = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Get database breakdown
                database_sql = f"""
                SELECT DATABASE_NAME, COUNT(*) as count
                FROM AUDIT_LOG
                WHERE {where_clause} AND DATABASE_NAME IS NOT NULL
                GROUP BY DATABASE_NAME
                ORDER BY count DESC
                """
                
                cursor.execute(database_sql, params)
                databases = {row[0]: row[1] for row in cursor.fetchall()}
                
                cursor.close()
                
                return {
                    "total_events": row[0] or 0,
                    "successful_events": row[1] or 0,
                    "failed_events": row[2] or 0,
                    "avg_execution_time_ms": float(row[3]) if row[3] else 0,
                    "max_execution_time_ms": float(row[4]) if row[4] else 0,
                    "total_rows_affected": row[5] or 0,
                    "event_types": event_types,
                    "databases": databases
                }
                
        except Exception as e:
            print(f"Failed to get audit statistics: {e}", flush=True)
            return {}
    
    def cleanup_old_logs(self, days_to_keep: int = 90):
        """
        Clean up old audit logs from database
        
        Args:
            days_to_keep: Number of days to retain (default 90)
        """
        if not self.db_audit_enabled:
            return
        
        try:
            with self.cqe_nft_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                delete_sql = """
                DELETE FROM AUDIT_LOG
                WHERE EVENT_TIMESTAMP < SYSDATE - :days_to_keep
                """
                
                cursor.execute(delete_sql, {'days_to_keep': days_to_keep})
                rows_deleted = cursor.rowcount
                
                conn.commit()
                cursor.close()
                
                print(f"✓ Cleaned up {rows_deleted} old audit records", flush=True)
                
        except Exception as e:
            print(f"Failed to cleanup old audit logs: {e}", flush=True)