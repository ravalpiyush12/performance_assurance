"""
Configuration Management Module
Handles environment-specific settings and credentials
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application Settings with Environment Support"""
    
    # Application Settings
    APP_NAME: str = "Oracle SQL API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "local"  # local, dev, prod
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # API Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # API Keys for Authentication (comma-separated for multiple keys)
    VALID_API_KEYS: str = "default-api-key-change-me"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 3600  # seconds
    
    # Oracle Database - Local Configuration
    ORACLE_HOST: Optional[str] = None
    ORACLE_PORT: int = 1521
    ORACLE_SERVICE_NAME: Optional[str] = None
    ORACLE_USERNAME: Optional[str] = None
    ORACLE_PASSWORD: Optional[str] = None
    
    # Oracle Connection Pool Settings
    ORACLE_POOL_MIN: int = 2
    ORACLE_POOL_MAX: int = 10
    ORACLE_POOL_INCREMENT: int = 1
    
    # CyberArk Settings (Production)
    CYBERARK_ENABLED: bool = False
    CYBERARK_URL: Optional[str] = None
    CYBERARK_APP_ID: Optional[str] = None
    CYBERARK_SAFE: Optional[str] = None
    CYBERARK_OBJECT: Optional[str] = None
    CYBERARK_CERT_PATH: Optional[str] = None
    CYBERARK_CERT_KEY_PATH: Optional[str] = None
    
    # SQL Execution Settings
    MAX_SQL_FILE_SIZE_MB: int = 10
    SQL_EXECUTION_TIMEOUT: int = 300  # seconds
    ALLOWED_SQL_OPERATIONS: List[str] = ["SELECT", "INSERT", "UPDATE", "DELETE", "MERGE"]
    
    # Audit Settings
    ENABLE_AUDIT_LOG: bool = True
    AUDIT_LOG_PATH: str = "/app/logs/audit"
    
    # AWS Settings (for ECS)
    AWS_REGION: Optional[str] = "us-east-1"
    
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


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()


# Environment-specific configuration templates
ENV_TEMPLATES = {
    "local": {
        "ENVIRONMENT": "local",
        "DEBUG": "true",
        "CYBERARK_ENABLED": "false",
        "ORACLE_HOST": "localhost",
        "ORACLE_PORT": "1521",
        "ORACLE_SERVICE_NAME": "ORCL",
        "ORACLE_USERNAME": "your_username",
        "ORACLE_PASSWORD": "your_password",
    },
    "dev": {
        "ENVIRONMENT": "dev",
        "DEBUG": "true",
        "CYBERARK_ENABLED": "true",
        "LOG_LEVEL": "DEBUG",
    },
    "prod": {
        "ENVIRONMENT": "prod",
        "DEBUG": "false",
        "CYBERARK_ENABLED": "true",
        "LOG_LEVEL": "INFO",
        "RATE_LIMIT_REQUESTS": "50",
    }
}