"""
Configuration Management for Performance Monitoring
"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class KibanaConfig:
    """Kibana configuration"""
    url: str
    username: str
    password: str
    visualizations: list
    use_selenium: bool = False
    
    @classmethod
    def from_env(cls):
        return cls(
            url=os.getenv('KIBANA_URL', 'http://localhost:5601'),
            username=os.getenv('KIBANA_USERNAME', ''),
            password=os.getenv('KIBANA_PASSWORD', ''),
            visualizations=os.getenv('KIBANA_VIZ_IDS', '').split(','),
            use_selenium=os.getenv('KIBANA_USE_SELENIUM', 'false').lower() == 'true'
        )

@dataclass
class AppDynamicsConfig:
    """AppDynamics configuration"""
    controller_url: str
    account_name: str
    username: str
    password: str
    application_name: str
    tier_name: str
    node_name: str
    
    @classmethod
    def from_env(cls):
        return cls(
            controller_url=os.getenv('APPD_CONTROLLER_URL', ''),
            account_name=os.getenv('APPD_ACCOUNT_NAME', ''),
            username=os.getenv('APPD_USERNAME', ''),
            password=os.getenv('APPD_PASSWORD', ''),
            application_name=os.getenv('APPD_APP_NAME', ''),
            tier_name=os.getenv('APPD_TIER_NAME', ''),
            node_name=os.getenv('APPD_NODE_NAME', '')
        )

@dataclass
class DatabaseConfig:
    """Database configuration"""
    db_type: str
    host: str
    port: int
    username: str
    password: str
    database: str
    
    @classmethod
    def from_env(cls):
        return cls(
            db_type=os.getenv('DB_TYPE', 'mysql'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '3306')),
            username=os.getenv('DB_USERNAME', ''),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'performance_monitoring')
        )

@dataclass
class MonitoringConfig:
    """Overall monitoring configuration"""
    collection_interval: int = 300  # 5 minutes in seconds
    test_duration: int = 3600  # 1 hour in seconds
    enable_kibana: bool = True
    enable_appdynamics: bool = True
    
    @classmethod
    def from_env(cls):
        return cls(
            collection_interval=int(os.getenv('COLLECTION_INTERVAL', '300')),
            test_duration=int(os.getenv('TEST_DURATION', '3600')),
            enable_kibana=os.getenv('ENABLE_KIBANA', 'true').lower() == 'true',
            enable_appdynamics=os.getenv('ENABLE_APPDYNAMICS', 'true').lower() == 'true'
        )