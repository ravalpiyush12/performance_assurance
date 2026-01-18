"""
Configuration classes for monitoring system
"""
from dataclasses import dataclass
from typing import Optional, List, Dict

@dataclass
class MonitoringConfig:
    """Main monitoring configuration"""
    collection_interval: int = 300  # 5 minutes in seconds
    test_duration: int = 3600  # Duration in seconds
    enable_kibana: bool = True
    enable_appdynamics: bool = True
    
    def __post_init__(self):
        """Validate configuration"""
        if self.collection_interval < 60:
            raise ValueError("Collection interval must be at least 60 seconds")
        if self.test_duration < self.collection_interval:
            raise ValueError("Test duration must be longer than collection interval")

@dataclass
class AppDynamicsConfig:
    """AppDynamics connection configuration"""
    controller_url: str
    account_name: str
    username: str
    password: str
    applications: List[Dict] = None
    
    def __post_init__(self):
        """Validate AppDynamics configuration"""
        if not self.controller_url:
            raise ValueError("AppDynamics controller URL is required")
        if not self.account_name:
            raise ValueError("AppDynamics account name is required")
        if not self.username:
            raise ValueError("AppDynamics username is required")
        if not self.password:
            raise ValueError("AppDynamics password is required")

@dataclass
class KibanaConfig:
    """Kibana connection configuration"""
    kibana_url: str
    username: str
    password: str
    dashboards: List[Dict] = None
    index_pattern: str = "logs-*"
    
    # Field mappings
    api_field: str = "api_name.keyword"
    status_field: str = "status"
    response_time_field: str = "response_time"
    timestamp_field: str = "@timestamp"
    
    def __post_init__(self):
        """Validate Kibana configuration"""
        if not self.kibana_url:
            raise ValueError("Kibana URL is required")
        if not self.username:
            raise ValueError("Kibana username is required")
        if not self.password:
            raise ValueError("Kibana password is required")

@dataclass
class DatabaseConfig:
    """Oracle database configuration"""
    username: str
    password: str
    dsn: str
    
    def __post_init__(self):
        """Validate database configuration"""
        if not self.username:
            raise ValueError("Database username is required")
        if not self.password:
            raise ValueError("Database password is required")
        if not self.dsn:
            raise ValueError("Database DSN is required")
        
        # Validate DSN format (host:port/service)
        if ':' not in self.dsn or '/' not in self.dsn:
            raise ValueError("DSN must be in format: host:port/service_name")

@dataclass
class TestRunConfig:
    """Test run configuration"""
    test_run_id: str
    test_name: Optional[str] = None
    duration_minutes: int = 60
    
    def __post_init__(self):
        """Validate test run configuration"""
        if not self.test_run_id:
            raise ValueError("Test run ID is required")
        if self.duration_minutes < 1:
            raise ValueError("Duration must be at least 1 minute")

@dataclass
class EmailConfig:
    """Email notification configuration"""
    enabled: bool = False
    recipients: List[str] = None
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    
    def __post_init__(self):
        """Validate email configuration"""
        if self.enabled:
            if not self.recipients:
                raise ValueError("Email recipients required when email is enabled")
            if not self.smtp_server:
                raise ValueError("SMTP server required when email is enabled")