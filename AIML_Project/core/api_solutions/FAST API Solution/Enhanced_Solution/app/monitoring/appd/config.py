"""
AppDynamics Monitoring Configuration
Centralized configuration for AppD REST API and monitoring
"""
from pydantic import BaseSettings
from typing import Optional


class AppDynamicsConfig(BaseSettings):
    """AppDynamics Controller Configuration"""
    
    # Controller Connection
    APPD_CONTROLLER_HOST: str = "controller.appdynamics.com"
    APPD_CONTROLLER_PORT: int = 443
    APPD_ACCOUNT_NAME: str = "customer1"
    APPD_USERNAME: str = "admin@customer1"
    APPD_PASSWORD: str = ""
    APPD_USE_SSL: bool = True
    
    # API Configuration
    APPD_API_TIMEOUT: int = 30  # seconds
    APPD_MAX_RETRIES: int = 3
    
    # Discovery Configuration
    APPD_ACTIVE_NODE_CPM_THRESHOLD: int = 10  # Minimum CPM to be considered active
    APPD_DISCOVERY_SCHEDULE: str = "DAILY"  # DAILY, WEEKLY, etc.
    APPD_DISCOVERY_LOOKBACK_MINUTES: int = 30  # How far back to check for CPM
    
    # Monitoring Configuration
    APPD_COLLECTION_INTERVAL_SECONDS: int = 1800  # 30 minutes default
    APPD_MAX_CONCURRENT_MONITORS: int = 10
    APPD_METRICS_BATCH_SIZE: int = 100
    
    # Thread Pool Configuration
    APPD_THREAD_POOL_SIZE_PER_TIER: int = 5  # Threads per tier for parallel collection
    APPD_THREAD_TIMEOUT_SECONDS: int = 300  # 5 minutes timeout per thread
    
    # Metric Collection Flags
    APPD_COLLECT_SERVER_METRICS: bool = True
    APPD_COLLECT_JVM_METRICS: bool = True
    APPD_COLLECT_APP_METRICS: bool = True
    
    # Database Configuration (uses main Oracle connection)
    # These will be passed from main settings
    
    class Config:
        env_file = ".env.local"
        case_sensitive = True
    
    @property
    def controller_url(self) -> str:
        """Build complete controller URL"""
        protocol = "https" if self.APPD_USE_SSL else "http"
        return f"{protocol}://{self.APPD_CONTROLLER_HOST}:{self.APPD_CONTROLLER_PORT}"
    
    @property
    def rest_api_base_url(self) -> str:
        """REST API base URL"""
        return f"{self.controller_url}/controller/rest"
    
    @property
    def metrics_api_base_url(self) -> str:
        """Metrics API base URL"""
        return f"{self.controller_url}/controller/rest/applications"
    
    def get_auth(self) -> tuple:
        """Get authentication tuple for requests"""
        return (f"{self.APPD_USERNAME}@{self.APPD_ACCOUNT_NAME}", self.APPD_PASSWORD)


# Global config instance
appd_config = AppDynamicsConfig()