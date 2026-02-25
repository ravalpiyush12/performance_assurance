"""
SQL Executor with DQL/DML Validation - Updated for python-oracledb
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import oracledb
from app.core.sql_validator import SQLValidator


class SQLExecutor:
    """Executes SQL queries with validation and error handling"""
    
    def __init__(self, connection_pool, db_config):
        """
        Initialize SQL executor
        
        Args:
            connection_pool: OracleConnectionPool instance
            db_config: DatabaseConfig object
        """
        self.pool = connection_pool
        self.db_config = db_config
        self.validator = SQLValidator()
    
    def execute_query(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        fetch_size: int = 1000
    ) -> Dict[str, Any]:
        """
        Execute SQL query with validation
        
        Args:
            sql: SQL statement to execute
            params: Optional bind parameters
            fetch_size: Number of rows to fetch (arraysize)
            
        Returns:
            Dict with execution results
        """
        # Validate SQL
        is_valid, error_msg = self.validator.validate_sql(
            sql,
            self.db_config.allowed_operations
        )
        
        if not is_valid:
            raise ValueError(error_msg)
        
        # Execute query
        connection = self.pool.get_connection()
        
        try:
            cursor = connection.cursor()
            
            try:
                # Set fetch size (arraysize)
                cursor.arraysize = fetch_size
                
                # Execute with or without parameters
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                
                # Determine operation type
                op_type = self.validator.detect_operation_type(sql)
                
                if op_type.value == "DQL":
                    # Fetch results for SELECT
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    rows = cursor.fetchall()
                    
                    # Convert to list of dicts
                    data = []
                    for row in rows:
                        row_dict = {}
                        for i, col in enumerate(columns):
                            value = row[i]
                            
                            # Convert Oracle data types to JSON-serializable types
                            if isinstance(value, datetime):
                                value = value.isoformat()
                            elif isinstance(value, oracledb.LOB):
                                # Handle LOB objects (CLOB, BLOB)
                                value = value.read() if value else None
                            elif value is None:
                                value = None
                            else:
                                # Try to convert to string if needed
                                try:
                                    value = str(value) if not isinstance(value, (int, float, bool, str)) else value
                                except:
                                    value = None
                            
                            row_dict[col] = value
                        data.append(row_dict)
                    
                    return {
                        "success": True,
                        "rows_affected": len(data),
                        "data": data,
                        "columns": columns
                    }
                else:
                    # DML operation
                    rows_affected = cursor.rowcount
                    connection.commit()
                    
                    return {
                        "success": True,
                        "rows_affected": rows_affected,
                        "data": None,
                        "columns": None
                    }
                    
            except oracledb.DatabaseError as e:
                connection.rollback()
                error_obj = e.args[0] if e.args else str(e)
                raise Exception(f"Database error: {error_obj}")
            finally:
                cursor.close()
                
        finally:
            # Release connection back to pool
            connection.close()
    
    def execute_many(
        self,
        sql: str,
        params_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute SQL with multiple parameter sets (batch execution)
        
        Args:
            sql: SQL statement to execute
            params_list: List of parameter dictionaries
            
        Returns:
            Dict with execution results
        """
        # Validate SQL
        is_valid, error_msg = self.validator.validate_sql(
            sql,
            self.db_config.allowed_operations
        )
        
        if not is_valid:
            raise ValueError(error_msg)
        
        connection = self.pool.get_connection()
        
        try:
            cursor = connection.cursor()
            
            try:
                # Convert list of dicts to list of tuples for executemany
                # Assuming all dicts have same keys in same order
                if params_list:
                    keys = list(params_list[0].keys())
                    params_tuples = [tuple(p[k] for k in keys) for p in params_list]
                    
                    # Use executemany for batch operations
                    cursor.executemany(sql, params_tuples)
                else:
                    cursor.executemany(sql, [])
                
                rows_affected = cursor.rowcount
                connection.commit()
                
                return {
                    "success": True,
                    "rows_affected": rows_affected,
                    "batches_executed": len(params_list)
                }
                
            except oracledb.DatabaseError as e:
                connection.rollback()
                error_obj = e.args[0] if e.args else str(e)
                raise Exception(f"Database error: {error_obj}")
            finally:
                cursor.close()
                
        finally:
            connection.close()