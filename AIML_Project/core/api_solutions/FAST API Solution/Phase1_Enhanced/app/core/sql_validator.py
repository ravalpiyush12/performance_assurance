"""
SQL Validator - Enforces DQL/DML restrictions per database
Complete implementation from architecture
"""
import re
from typing import List, Tuple
from enum import Enum


class SQLOperationType(str, Enum):
    """SQL operation types"""
    DQL = "DQL"  # Data Query Language (SELECT)
    DML = "DML"  # Data Manipulation Language (INSERT, UPDATE, DELETE)
    DDL = "DDL"  # Data Definition Language (CREATE, ALTER, DROP, TRUNCATE)
    DCL = "DCL"  # Data Control Language (GRANT, REVOKE)


class SQLValidator:
    """Validates SQL statements based on allowed operations"""
    
    # DQL keywords
    DQL_KEYWORDS = ["SELECT", "WITH"]
    
    # DML keywords
    DML_KEYWORDS = ["INSERT", "UPDATE", "DELETE", "MERGE"]
    
    # DDL keywords (always blocked)
    DDL_KEYWORDS = [
        "CREATE", "ALTER", "DROP", "TRUNCATE", "RENAME",
        "COMMENT", "FLASHBACK", "PURGE"
    ]
    
    # DCL keywords (always blocked)
    DCL_KEYWORDS = ["GRANT", "REVOKE"]
    
    # Dangerous patterns (always blocked)
    DANGEROUS_PATTERNS = [
        r";\s*DROP\s+",
        r";\s*DELETE\s+FROM\s+",
        r";\s*TRUNCATE\s+",
        r"--\s*DROP",
        r"/\*.*DROP.*\*/",
    ]
    
    @staticmethod
    def detect_operation_type(sql: str) -> SQLOperationType:
        """Detect the type of SQL operation"""
        sql_upper = sql.strip().upper()
        
        # Remove comments
        sql_upper = re.sub(r'--.*$', '', sql_upper, flags=re.MULTILINE)
        sql_upper = re.sub(r'/\*.*?\*/', '', sql_upper, flags=re.DOTALL)
        
        # Get first keyword
        first_keyword = sql_upper.split()[0] if sql_upper.split() else ""
        
        if first_keyword in SQLValidator.DQL_KEYWORDS:
            return SQLOperationType.DQL
        elif first_keyword in SQLValidator.DML_KEYWORDS:
            return SQLOperationType.DML
        elif first_keyword in SQLValidator.DDL_KEYWORDS:
            return SQLOperationType.DDL
        elif first_keyword in SQLValidator.DCL_KEYWORDS:
            return SQLOperationType.DCL
        else:
            # Default to DML for unknown (safer to block)
            return SQLOperationType.DML
    
    @staticmethod
    def validate_sql(sql: str, allowed_operations: List[str]) -> Tuple[bool, str]:
        """
        Validate SQL against allowed operations
        
        Returns:
            (is_valid, error_message)
        """
        if not sql or not sql.strip():
            return False, "Empty SQL statement"
        
        # Check for dangerous patterns first
        for pattern in SQLValidator.DANGEROUS_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                return False, f"SQL contains dangerous pattern: {pattern}"
        
        # Detect operation type
        op_type = SQLValidator.detect_operation_type(sql)
        
        # Check if operation is DDL or DCL (always blocked)
        if op_type in [SQLOperationType.DDL, SQLOperationType.DCL]:
            return False, f"{op_type.value} operations are not allowed"
        
        # Check if operation is allowed for this database
        if op_type.value not in allowed_operations:
            return False, f"{op_type.value} operations not allowed for this database. Allowed: {', '.join(allowed_operations)}"
        
        return True, ""
    
    @staticmethod
    def validate_multiple_sql(sql_statements: List[str], allowed_operations: List[str]) -> Tuple[bool, str, List[str]]:
        """
        Validate multiple SQL statements
        
        Returns:
            (all_valid, error_message, failed_statements)
        """
        failed = []
        
        for i, sql in enumerate(sql_statements, 1):
            is_valid, error_msg = SQLValidator.validate_sql(sql, allowed_operations)
            if not is_valid:
                failed.append(f"Statement {i}: {error_msg}")
        
        if failed:
            return False, "\n".join(failed), failed
        
        return True, "", []