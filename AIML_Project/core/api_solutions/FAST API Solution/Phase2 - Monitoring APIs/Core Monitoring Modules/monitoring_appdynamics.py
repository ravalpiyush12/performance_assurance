"""
AppDynamics Monitoring Handler
Handles start/stop of AppDynamics monitoring and data fetching
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import requests
from requests.auth import HTTPBasicAuth
import json
from config import Settings

logger = logging.getLogger(__name__)


class AppDynamicsConfig:
    """AppDynamics configuration"""
    
    def __init__(self, settings: Settings):
        self.controller_url = settings.APPDYNAMICS_CONTROLLER_URL
        self.account_name = settings.APPDYNAMICS_ACCOUNT_NAME
        self.username = settings.APPDYNAMICS_USERNAME
        self.password = settings.APPDYNAMICS_PASSWORD
        self.application_name = settings.APPDYNAMICS_APPLICATION_NAME
        self.timeout = settings.APPDYNAMICS_TIMEOUT
        
        # Build authentication
        self.auth_username = f"{self.username}@{self.account_name}"
        self.auth = HTTPBasicAuth(self.auth_username, self.password)
        
        # API base URL
        self.api_base = f"{self.controller_url}/controller/rest"


class AppDynamicsMonitor:
    """AppDynamics monitoring operations"""
    
    def __init__(self, config: AppDynamicsConfig):
        self.config = config
        self.session = requests.Session()
        self.session.auth = self.config.auth
        self.monitoring_active = False
        self.last_fetch_time = None
        
    def start_monitoring(
        self,
        application_name: Optional[str] = None,
        tier_name: Optional[str] = None,
        node_name: Optional[str] = None,
        duration_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Start AppDynamics monitoring
        
        Args:
            application_name: Application to monitor
            tier_name: Specific tier (optional)
            node_name: Specific node (optional)
            duration_minutes: Monitoring duration
            
        Returns:
            Status and configuration
        """
        try:
            app_name = application_name or self.config.application_name
            
            logger.info(f"Starting AppDynamics monitoring for {app_name}")
            
            # Verify application exists
            app_info = self._get_application_info(app_name)
            
            if not app_info:
                raise Exception(f"Application '{app_name}' not found in AppDynamics")
            
            # Get initial metrics to verify connectivity
            health_status = self._get_application_health(app_name)
            
            self.monitoring_active = True
            self.last_fetch_time = datetime.now()
            
            result = {
                "status": "started",
                "application": app_name,
                "application_id": app_info.get("id"),
                "tier": tier_name,
                "node": node_name,
                "duration_minutes": duration_minutes,
                "start_time": self.last_fetch_time.isoformat(),
                "end_time": (self.last_fetch_time + timedelta(minutes=duration_minutes)).isoformat(),
                "health_status": health_status,
                "monitoring_active": self.monitoring_active
            }
            
            logger.info(f"AppDynamics monitoring started successfully for {app_name}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to start AppDynamics monitoring: {e}")
            raise Exception(f"AppDynamics monitoring start failed: {e}")
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """
        Stop AppDynamics monitoring
        
        Returns:
            Final status and summary
        """
        try:
            logger.info("Stopping AppDynamics monitoring")
            
            if not self.monitoring_active:
                return {
                    "status": "not_active",
                    "message": "Monitoring was not active"
                }
            
            duration = None
            if self.last_fetch_time:
                duration = (datetime.now() - self.last_fetch_time).total_seconds() / 60
            
            self.monitoring_active = False
            
            result = {
                "status": "stopped",
                "stop_time": datetime.now().isoformat(),
                "duration_minutes": round(duration, 2) if duration else None,
                "monitoring_active": self.monitoring_active
            }
            
            logger.info("AppDynamics monitoring stopped successfully")
            return result
            
        except Exception as e:
            logger.error(f"Failed to stop AppDynamics monitoring: {e}")
            raise Exception(f"AppDynamics monitoring stop failed: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            "monitoring_active": self.monitoring_active,
            "last_fetch_time": self.last_fetch_time.isoformat() if self.last_fetch_time else None,
            "controller_url": self.config.controller_url,
            "application": self.config.application_name
        }
    
    def fetch_metrics(
        self,
        application_name: Optional[str] = None,
        metric_path: str = "Overall Application Performance|*",
        time_range_minutes: int = 15
    ) -> Dict[str, Any]:
        """
        Fetch metrics from AppDynamics
        
        Args:
            application_name: Application name
            metric_path: Metric path (wildcards supported)
            time_range_minutes: Time range for metrics
            
        Returns:
            Metrics data
        """
        try:
            app_name = application_name or self.config.application_name
            
            # Build metric data URL
            url = f"{self.config.api_base}/applications/{app_name}/metric-data"
            
            # Calculate time range
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=time_range_minutes)
            
            params = {
                "metric-path": metric_path,
                "time-range-type": "BEFORE_NOW",
                "duration-in-mins": time_range_minutes,
                "output": "JSON"
            }
            
            logger.info(f"Fetching AppDynamics metrics: {metric_path}")
            
            response = self.session.get(
                url,
                params=params,
                timeout=self.config.timeout
            )
            
            response.raise_for_status()
            
            metrics_data = response.json()
            
            return {
                "status": "success",
                "application": app_name,
                "metric_path": metric_path,
                "time_range_minutes": time_range_minutes,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "metrics_count": len(metrics_data) if isinstance(metrics_data, list) else 1,
                "metrics": metrics_data,
                "fetched_at": datetime.now().isoformat()
            }
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch AppDynamics metrics: {e}")
            raise Exception(f"AppDynamics metrics fetch failed: {e}")
    
    def get_business_transactions(
        self,
        application_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get business transactions for application
        
        Args:
            application_name: Application name
            
        Returns:
            List of business transactions
        """
        try:
            app_name = application_name or self.config.application_name
            
            url = f"{self.config.api_base}/applications/{app_name}/business-transactions"
            
            params = {"output": "JSON"}
            
            response = self.session.get(
                url,
                params=params,
                timeout=self.config.timeout
            )
            
            response.raise_for_status()
            transactions = response.json()
            
            return {
                "status": "success",
                "application": app_name,
                "transaction_count": len(transactions),
                "transactions": transactions,
                "fetched_at": datetime.now().isoformat()
            }
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch business transactions: {e}")
            raise Exception(f"Business transactions fetch failed: {e}")
    
    def _get_application_info(self, app_name: str) -> Optional[Dict]:
        """Get application information"""
        try:
            url = f"{self.config.api_base}/applications/{app_name}"
            params = {"output": "JSON"}
            
            response = self.session.get(url, params=params, timeout=self.config.timeout)
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            
            apps = response.json()
            if isinstance(apps, list) and len(apps) > 0:
                return apps[0]
            
            return apps if isinstance(apps, dict) else None
            
        except Exception as e:
            logger.error(f"Failed to get application info: {e}")
            return None
    
    def _get_application_health(self, app_name: str) -> Dict[str, Any]:
        """Get application health status"""
        try:
            url = f"{self.config.api_base}/applications/{app_name}/metric-data"
            
            params = {
                "metric-path": "Overall Application Performance|Average Response Time (ms)",
                "time-range-type": "BEFORE_NOW",
                "duration-in-mins": 5,
                "output": "JSON"
            }
            
            response = self.session.get(url, params=params, timeout=self.config.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "status": "healthy" if response.status_code == 200 else "unknown",
                "response_time_available": len(data) > 0 if isinstance(data, list) else False
            }
            
        except Exception as e:
            logger.warning(f"Failed to get health status: {e}")
            return {"status": "unknown", "error": str(e)}
    
    def close(self):
        """Close session"""
        if self.session:
            self.session.close()