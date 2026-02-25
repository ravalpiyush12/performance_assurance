"""
SQL Executor with DQL/DML Validation
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from core.sql_validator import SQLValidator


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
            fetch_size: Number of rows to fetch
            
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
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # Set fetch size
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
                            # Convert datetime/date to string
                            if isinstance(value, (datetime, )):
                                value = value.isoformat()
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
                    conn.commit()
                    
                    return {
                        "success": True,
                        "rows_affected": rows_affected,
                        "data": None,
                        "columns": None
                    }
                    
            except Exception as e:
                conn.rollback()
                raise
            finally:
                cursor.close()