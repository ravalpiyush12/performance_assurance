"""
Audit Logger - JSONL Format
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class AuditLogger:
    """Audit logger that writes to JSONL files"""
    
    def __init__(self, settings):
        """
        Initialize audit logger
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.enabled = settings.ENABLE_AUDIT_LOG
        self.log_path = settings.AUDIT_LOG_PATH
        
        if self.enabled:
            # Create audit log directory
            Path(self.log_path).mkdir(parents=True, exist_ok=True)
    
    def log_event(self, event_type: str, **kwargs):
        """
        Log an audit event
        
        Args:
            event_type: Type of event (sql_executed, sql_failed, etc.)
            **kwargs: Additional event data
        """
        if not self.enabled:
            return
        
        # Build event record
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "environment": self.settings.ENVIRONMENT,
            **kwargs
        }
        
        # Write to JSONL file (one JSON object per line)
        log_file = os.path.join(
            self.log_path,
            f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"
        )
        
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            print(f"Failed to write audit log: {e}", flush=True)