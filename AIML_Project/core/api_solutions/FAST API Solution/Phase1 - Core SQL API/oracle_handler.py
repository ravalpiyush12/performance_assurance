"""
Oracle Database Handler Module
Manages connection pool and SQL execution
"""
import cx_Oracle
import logging
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
from datetime import datetime
import re
from config import Settings
from cyberark_provider import CredentialManager, OracleCredentials

logger = logging.getLogger(__name__)


class OracleConnectionPool:
    """Oracle connection pool manager"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.pool: Optional[cx_Oracle.SessionPool] = None
        self.credentials: Optional[OracleCredentials] = None
        
    def initialize(self):
        """Initialize connection pool with credentials"""
        try:
            # Get credentials
            cred_manager = CredentialManager(self.settings)
            self.credentials = cred_manager.get_oracle_credentials()
            cred_manager.close()
            
            logger.info(f"Initializing Oracle connection pool to {self.credentials.host}")
            
            # Create connection pool
            self.pool = cx_Oracle.SessionPool(
                user=self.credentials.username,
                password=self.credentials.password,
                dsn=self.credentials.get_dsn(),
                min=self.settings.ORACLE_POOL_MIN,
                max=self.settings.ORACLE_POOL_MAX,
                increment=self.settings.ORACLE_POOL_INCREMENT,
                threaded=True,
                encoding="UTF-8"
            )
            
            logger.info(f"Connection pool initialized successfully (min={self.settings.ORACLE_POOL_MIN}, max={self.settings.ORACLE_POOL_MAX})")
            
            # Test connection
            self._test_connection()
            
        except cx_Oracle.Error as e:
            logger.error(f"Oracle connection pool initialization failed: {e}")
            raise Exception(f"Failed to initialize Oracle connection pool: {e}")
        except Exception as e:
            logger.error(f"Error initializing connection pool: {e}")
            raise
    
    def _test_connection(self):
        """Test connection pool with a simple query"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM DUAL")
                result = cursor.fetchone()
                cursor.close()
                logger.info("Connection pool test successful")
        except Exception as e:
            logger.error(f"Connection pool test failed: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """
        Get connection from pool (context manager)
        
        Usage:
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                ...
        """
        if not self.pool:
            raise Exception("Connection pool not initialized")
        
        connection = None
        try:
            connection = self.pool.acquire()
            yield connection
        except cx_Oracle.Error as e:
            logger.error(f"Database connection error: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                self.pool.release(connection)
    
    def close(self):
        """Close connection pool"""
        if self.pool:
            try:
                self.pool.close()
                logger.info("Connection pool closed")
            except Exception as e:
                logger.error(f"Error closing connection pool: {e}")
            finally:
                self.pool = None
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        if not self.pool:
            return {"status": "not_initialized"}
        
        return {
            "status": "active",
            "open_connections": self.pool.opened,
            "busy_connections": self.pool.busy,
            "max_connections": self.pool.max,
            "min_connections": self.pool.min
        }


class SQLExecutor:
    """SQL execution handler with validation and audit"""
    
    def __init__(self, pool: OracleConnectionPool, settings: Settings):
        self.pool = pool
        self.settings = settings
    
    def validate_sql(self, sql_content: str) -> Tuple[bool, Optional[str], str]:
        """
        Validate SQL content
        
        Returns:
            Tuple of (is_valid, error_message, operation_type)
        """
        # Remove comments and extra whitespace
        sql_cleaned = re.sub(r'--.*$', '', sql_content, flags=re.MULTILINE)
        sql_cleaned = re.sub(r'/\*.*?\*/', '', sql_cleaned, flags=re.DOTALL)
        sql_cleaned = sql_cleaned.strip()
        
        if not sql_cleaned:
            return False, "Empty SQL content", "UNKNOWN"
        
        # Detect SQL operation type
        operation = self._detect_operation(sql_cleaned)
        
        if operation not in self.settings.ALLOWED_SQL_OPERATIONS:
            return False, f"Operation '{operation}' not allowed. Allowed: {self.settings.ALLOWED_SQL_OPERATIONS}", operation
        
        # Check for dangerous patterns
        dangerous_patterns = [
            r'\bDROP\s+TABLE\b',
            r'\bDROP\s+DATABASE\b',
            r'\bTRUNCATE\s+TABLE\b',
            r'\bALTER\s+TABLE\b',
            r'\bCREATE\s+TABLE\b',
            r'\bGRANT\b',
            r'\bREVOKE\b',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, sql_cleaned, re.IGNORECASE):
                return False, f"Potentially dangerous SQL pattern detected: {pattern}", operation
        
        return True, None, operation
    
    def _detect_operation(self, sql: str) -> str:
        """Detect SQL operation type"""
        sql_upper = sql.upper().strip()
        
        if sql_upper.startswith('SELECT'):
            return 'SELECT'
        elif sql_upper.startswith('INSERT'):
            return 'INSERT'
        elif sql_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif sql_upper.startswith('DELETE'):
            return 'DELETE'
        elif sql_upper.startswith('MERGE'):
            return 'MERGE'
        else:
            return 'UNKNOWN'
    
    def execute_sql(
        self,
        sql_content: str,
        operation_type: str,
        request_id: str,
        username: str
    ) -> Dict[str, Any]:
        """
        Execute SQL and return results
        
        Args:
            sql_content: SQL statements to execute
            operation_type: Type of SQL operation
            request_id: Unique request identifier
            username: User executing the SQL
            
        Returns:
            Dictionary with execution results
        """
        start_time = datetime.now()
        
        try:
            with self.pool.get_connection() as connection:
                cursor = connection.cursor()
                
                # Execute SQL
                logger.info(f"[{request_id}] Executing {operation_type} query for user {username}")
                
                result_data = {
                    "request_id": request_id,
                    "operation_type": operation_type,
                    "status": "success",
                    "rows_affected": 0,
                    "data": [],
                    "columns": [],
                    "execution_time_seconds": 0,
                    "timestamp": datetime.now().isoformat()
                }
                
                try:
                    cursor.execute(sql_content)
                    
                    # Handle SELECT queries
                    if operation_type == 'SELECT':
                        # Get column names
                        result_data["columns"] = [desc[0] for desc in cursor.description]
                        
                        # Fetch results
                        rows = cursor.fetchall()
                        result_data["rows_affected"] = len(rows)
                        
                        # Convert to list of dictionaries
                        result_data["data"] = [
                            dict(zip(result_data["columns"], row))
                            for row in rows
                        ]
                        
                        logger.info(f"[{request_id}] Query returned {len(rows)} rows")
                    
                    # Handle DML queries (INSERT, UPDATE, DELETE, MERGE)
                    else:
                        result_data["rows_affected"] = cursor.rowcount
                        connection.commit()
                        logger.info(f"[{request_id}] DML operation affected {cursor.rowcount} rows")
                    
                except cx_Oracle.Error as e:
                    connection.rollback()
                    error_obj, = e.args
                    logger.error(f"[{request_id}] SQL execution error: {error_obj.message}")
                    raise Exception(f"SQL execution error: {error_obj.message}")
                
                finally:
                    cursor.close()
                
                # Calculate execution time
                execution_time = (datetime.now() - start_time).total_seconds()
                result_data["execution_time_seconds"] = round(execution_time, 3)
                
                return result_data
                
        except Exception as e:
            logger.error(f"[{request_id}] Execution failed: {e}")
            return {
                "request_id": request_id,
                "operation_type": operation_type,
                "status": "error",
                "error": str(e),
                "execution_time_seconds": round((datetime.now() - start_time).total_seconds(), 3),
                "timestamp": datetime.now().isoformat()
            }
    
    def execute_multiple_statements(
        self,
        sql_statements: List[str],
        request_id: str,
        username: str
    ) -> Dict[str, Any]:
        """
        Execute multiple SQL statements in sequence
        
        Args:
            sql_statements: List of SQL statements
            request_id: Unique request identifier
            username: User executing the SQL
            
        Returns:
            Dictionary with aggregated results
        """
        results = []
        total_rows = 0
        
        for idx, sql in enumerate(sql_statements, 1):
            # Validate each statement
            is_valid, error_msg, operation = self.validate_sql(sql)
            
            if not is_valid:
                results.append({
                    "statement_number": idx,
                    "status": "validation_failed",
                    "error": error_msg,
                    "sql_preview": sql[:100]
                })
                continue
            
            # Execute statement
            result = self.execute_sql(
                sql,
                operation,
                f"{request_id}-{idx}",
                username
            )
            
            results.append({
                "statement_number": idx,
                **result
            })
            
            if result["status"] == "success":
                total_rows += result.get("rows_affected", 0)
        
        return {
            "request_id": request_id,
            "total_statements": len(sql_statements),
            "successful_statements": sum(1 for r in results if r.get("status") == "success"),
            "total_rows_affected": total_rows,
            "statements": results,
            "timestamp": datetime.now().isoformat()
        }