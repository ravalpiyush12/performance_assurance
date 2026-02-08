"""
Updated Configuration Management Module with Monitoring Settings
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache


class Settings(BaseSettings):
    """Application Settings with Monitoring Support"""
    
    # Application Settings
    APP_NAME: str = "Oracle SQL API with Monitoring"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = "local"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # API Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    VALID_API_KEYS: str = "default-api-key-change-me"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 3600
    
    # Oracle Database Settings
    ORACLE_HOST: Optional[str] = None
    ORACLE_PORT: int = 1521
    ORACLE_SERVICE_NAME: Optional[str] = None
    ORACLE_USERNAME: Optional[str] = None
    ORACLE_PASSWORD: Optional[str] = None
    ORACLE_POOL_MIN: int = 2
    ORACLE_POOL_MAX: int = 10
    ORACLE_POOL_INCREMENT: int = 1
    
    # CyberArk Settings
    CYBERARK_ENABLED: bool = False
    CYBERARK_URL: Optional[str] = None
    CYBERARK_APP_ID: Optional[str] = None
    CYBERARK_SAFE: Optional[str] = None
    CYBERARK_OBJECT: Optional[str] = None
    CYBERARK_CERT_PATH: Optional[str] = None
    CYBERARK_CERT_KEY_PATH: Optional[str] = None
    
    # SQL Execution Settings
    MAX_SQL_FILE_SIZE_MB: int = 10
    SQL_EXECUTION_TIMEOUT: int = 300
    ALLOWED_SQL_OPERATIONS: List[str] = ["SELECT", "INSERT", "UPDATE", "DELETE", "MERGE"]
    
    # Audit Settings
    ENABLE_AUDIT_LOG: bool = True
    AUDIT_LOG_PATH: str = "/app/logs/audit"
    
    # AWS Settings
    AWS_REGION: Optional[str] = "us-east-1"
    
    # ========================================
    # MONITORING SETTINGS
    # ========================================
    
    # AppDynamics Settings
    APPDYNAMICS_ENABLED: bool = False
    APPDYNAMICS_CONTROLLER_URL: Optional[str] = None
    APPDYNAMICS_ACCOUNT_NAME: Optional[str] = None
    APPDYNAMICS_USERNAME: Optional[str] = None
    APPDYNAMICS_PASSWORD: Optional[str] = None
    APPDYNAMICS_APPLICATION_NAME: Optional[str] = None
    APPDYNAMICS_TIMEOUT: int = 30
    
    # Kibana/Elasticsearch Settings
    KIBANA_ENABLED: bool = False
    KIBANA_URL: Optional[str] = None
    ELASTICSEARCH_URL: Optional[str] = None
    KIBANA_USERNAME: Optional[str] = None
    KIBANA_PASSWORD: Optional[str] = None
    KIBANA_INDEX_PATTERN: str = "logstash-*"
    KIBANA_TIMEOUT: int = 30
    
    # Splunk Settings
    SPLUNK_ENABLED: bool = False
    SPLUNK_URL: Optional[str] = None
    SPLUNK_USERNAME: Optional[str] = None
    SPLUNK_PASSWORD: Optional[str] = None
    SPLUNK_INDEX: str = "main"
    SPLUNK_TIMEOUT: int = 30
    
    # MongoDB Settings
    MONGODB_ENABLED: bool = False
    MONGODB_CONNECTION_STRING: Optional[str] = None
    MONGODB_DATABASE: str = "admin"
    MONGODB_TIMEOUT: int = 10
    MONGODB_MAX_POOL_SIZE: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def get_api_keys(self) -> List[str]:
        """Parse and return list of valid API keys"""
        return [key.strip() for key in self.VALID_API_KEYS.split(",")]
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT.lower() == "prod"
    
    def get_oracle_dsn(self) -> str:
        """Build Oracle DSN string"""
        if not all([self.ORACLE_HOST, self.ORACLE_SERVICE_NAME]):
            raise ValueError("Oracle connection details not configured")
        return f"{self.ORACLE_HOST}:{self.ORACLE_PORT}/{self.ORACLE_SERVICE_NAME}"
    
    def get_enabled_monitors(self) -> List[str]:
        """Get list of enabled monitoring systems"""
        enabled = []
        if self.APPDYNAMICS_ENABLED:
            enabled.append("appdynamics")
        if self.KIBANA_ENABLED:
            enabled.append("kibana")
        if self.SPLUNK_ENABLED:
            enabled.append("splunk")
        if self.MONGODB_ENABLED:
            enabled.append("mongodb")
        return enabled


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()