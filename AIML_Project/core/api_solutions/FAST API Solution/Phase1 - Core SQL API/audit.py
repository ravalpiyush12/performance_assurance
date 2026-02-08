"""
Audit Logging Module
Tracks all SQL operations for security and compliance
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from config import Settings

logger = logging.getLogger(__name__)


class AuditLogger:
    """Audit logging for SQL operations"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.enabled = settings.ENABLE_AUDIT_LOG
        
        if self.enabled:
            self.audit_dir = Path(settings.AUDIT_LOG_PATH)
            self.audit_dir.mkdir(parents=True, exist_ok=True)
            self.audit_file = self.audit_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"
    
    def log_request(
        self,
        request_id: str,
        username: str,
        api_key: str,
        operation_type: str,
        sql_preview: str,
        client_ip: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Log SQL request
        
        Args:
            request_id: Unique request ID
            username: User making the request
            api_key: API key used (masked)
            operation_type: SQL operation type
            sql_preview: First 500 chars of SQL
            client_ip: Client IP address
            metadata: Additional metadata
        """
        if not self.enabled:
            return
        
        try:
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": "sql_request",
                "request_id": request_id,
                "username": username,
                "api_key_masked": self._mask_api_key(api_key),
                "operation_type": operation_type,
                "sql_preview": sql_preview[:500],
                "client_ip": client_ip,
                "metadata": metadata or {}
            }
            
            self._write_audit_log(audit_entry)
            
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    def log_response(
        self,
        request_id: str,
        status: str,
        rows_affected: int,
        execution_time: float,
        error: Optional[str] = None
    ):
        """
        Log SQL response
        
        Args:
            request_id: Unique request ID
            status: success or error
            rows_affected: Number of rows affected
            execution_time: Execution time in seconds
            error: Error message if failed
        """
        if not self.enabled:
            return
        
        try:
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": "sql_response",
                "request_id": request_id,
                "status": status,
                "rows_affected": rows_affected,
                "execution_time_seconds": execution_time,
                "error": error
            }
            
            self._write_audit_log(audit_entry)
            
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    def log_authentication(
        self,
        username: str,
        api_key: str,
        success: bool,
        client_ip: Optional[str] = None,
        reason: Optional[str] = None
    ):
        """
        Log authentication attempt
        
        Args:
            username: Username attempting authentication
            api_key: API key used
            success: Whether authentication succeeded
            client_ip: Client IP address
            reason: Failure reason if unsuccessful
        """
        if not self.enabled:
            return
        
        try:
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": "authentication",
                "username": username,
                "api_key_masked": self._mask_api_key(api_key),
                "success": success,
                "client_ip": client_ip,
                "reason": reason
            }
            
            self._write_audit_log(audit_entry)
            
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    def _mask_api_key(self, api_key: str) -> str:
        """Mask API key for logging"""
        if len(api_key) <= 8:
            return "****"
        return f"{api_key[:4]}...{api_key[-4:]}"
    
    def _write_audit_log(self, entry: Dict[str, Any]):
        """Write audit entry to file"""
        try:
            with open(self.audit_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            logger.error(f"Error writing to audit file: {e}")
    
    def get_audit_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get audit summary for a specific date
        
        Args:
            date: Date in YYYYMMDD format (default: today)
            
        Returns:
            Summary statistics
        """
        if not self.enabled:
            return {"error": "Audit logging not enabled"}
        
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        audit_file = self.audit_dir / f"audit_{date}.jsonl"
        
        if not audit_file.exists():
            return {"error": f"No audit log found for {date}"}
        
        try:
            total_requests = 0
            successful_requests = 0
            failed_requests = 0
            operations = {}
            users = set()
            
            with open(audit_file, 'r') as f:
                for line in f:
                    entry = json.loads(line)
                    
                    if entry["event_type"] == "sql_request":
                        total_requests += 1
                        operation = entry.get("operation_type", "UNKNOWN")
                        operations[operation] = operations.get(operation, 0) + 1
                        users.add(entry.get("username", "unknown"))
                    
                    elif entry["event_type"] == "sql_response":
                        if entry.get("status") == "success":
                            successful_requests += 1
                        else:
                            failed_requests += 1
            
            return {
                "date": date,
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "operations": operations,
                "unique_users": len(users),
                "audit_file": str(audit_file)
            }
            
        except Exception as e:
            logger.error(f"Error reading audit log: {e}")
            return {"error": str(e)}