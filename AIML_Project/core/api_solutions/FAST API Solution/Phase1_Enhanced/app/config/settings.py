"""
Multi-Database Configuration Settings - Pydantic v1
Complete settings module from architecture
"""
from pydantic import BaseSettings, Field, validator
from typing import Dict, List, Optional
from functools import lru_cache
import os
import json


class DatabaseConfig(BaseSettings):
    """Individual database configuration"""
    name: str
    host: str
    port: int = 1521
    service_name: str
    username: Optional[str] = None
    password: Optional[str] = None
    use_cyberark: bool = False
    allowed_operations: List[str]  # ["DQL"] or ["DML"] or ["DQL", "DML"]
    secret_key: str
    api_keys: str  # Comma-separated
    
    # Connection pool settings
    pool_min: int = 2
    pool_max: int = 10
    pool_increment: int = 1
    
    # CyberArk settings (if use_cyberark=True)
    cyberark_safe: Optional[str] = None
    cyberark_object: Optional[str] = None
    
    def get_api_keys_list(self) -> List[str]:
        """Parse API keys into list"""
        return [k.strip() for k in self.api_keys.split(",") if k.strip()]
    
    def get_dsn(self) -> str:
        """Build Oracle DSN string"""
        return f"{self.host}:{self.port}/{self.service_name}"
    
    class Config:
        env_file = None
        case_sensitive = True


class Settings(BaseSettings):
    """Application Settings with Multi-Database Support"""
    
    # Application Settings
    APP_NAME: str = "Oracle SQL API - Multi-Database"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = "local"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Global CyberArk Settings
    CYBERARK_ENABLED: bool = False
    CYBERARK_URL: Optional[str] = None
    CYBERARK_APP_ID: Optional[str] = None
    CYBERARK_CERT_PATH: Optional[str] = None
    CYBERARK_CERT_KEY_PATH: Optional[str] = None
    
    # SQL Execution Settings
    MAX_SQL_FILE_SIZE_MB: int = 10
    SQL_EXECUTION_TIMEOUT: int = 300
    
    # Audit Settings
    ENABLE_AUDIT_LOG: bool = True
    AUDIT_LOG_PATH: str = "/app/logs/audit"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 3600
    
    class Config:
        env_file = None
        case_sensitive = True
    
    def get_databases(self) -> Dict[str, DatabaseConfig]:
        """
        Get all database configurations from environment variables
        """
        from config.database_config import get_databases_config
        
        databases_dict = get_databases_config()
        databases = {}
        
        for db_name, db_config in databases_dict.items():
            databases[db_name] = DatabaseConfig(
                name=db_name,
                **db_config
            )
        
        return databases
    
    def get_database(self, db_name: str) -> Optional[DatabaseConfig]:
        """Get specific database configuration"""
        databases = self.get_databases()
        return databases.get(db_name.upper())


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    import sys
    
    print("Loading multi-database settings...", flush=True)
    settings = Settings()
    
    databases = settings.get_databases()
    print(f"✓ Settings loaded: {settings.ENVIRONMENT} v{settings.APP_VERSION}", flush=True)
    print(f"✓ Databases configured: {len(databases)}", flush=True)
    
    for db_name, db_config in databases.items():
        print(f"  - {db_name}: {db_config.host}:{db_config.port}/{db_config.service_name}", flush=True)
        print(f"    Operations: {', '.join(db_config.allowed_operations)}", flush=True)
        print(f"    Auth: {'CyberArk' if db_config.use_cyberark else 'Direct'}", flush=True)
        print(f"    API Keys: {len(db_config.get_api_keys_list())} configured", flush=True)
    
    sys.stdout.flush()
    return settings