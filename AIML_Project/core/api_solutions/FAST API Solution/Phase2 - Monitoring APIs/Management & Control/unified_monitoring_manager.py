"""
Unified Monitoring Manager
Central manager for all monitoring systems (AppDynamics, Kibana, Splunk, MongoDB)
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from config_monitoring import Settings
from monitoring_appdynamics import AppDynamicsConfig, AppDynamicsMonitor
from monitoring_kibana import KibanaConfig, KibanaMonitor
from monitoring_splunk import SplunkConfig, SplunkMonitor
from monitoring_mongodb import MongoDBConfig, MongoDBAnalyzer

logger = logging.getLogger(__name__)


class MonitoringSystem(str, Enum):
    """Supported monitoring systems"""
    APPDYNAMICS = "appdynamics"
    KIBANA = "kibana"
    SPLUNK = "splunk"
    MONGODB = "mongodb"
    ALL = "all"


class MonitoringStatus(str, Enum):
    """Monitoring status states"""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    NOT_CONFIGURED = "not_configured"


class UnifiedMonitoringManager:
    """Unified manager for all monitoring systems"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.monitors: Dict[str, Any] = {}
        self.status: Dict[str, MonitoringStatus] = {}
        
        # Initialize monitors
        self._initialize_monitors()
        
    def _initialize_monitors(self):
        """Initialize all enabled monitoring systems"""
        logger.info("Initializing monitoring systems...")
        
        # AppDynamics
        if self.settings.APPDYNAMICS_ENABLED:
            try:
                config = AppDynamicsConfig(self.settings)
                self.monitors[MonitoringSystem.APPDYNAMICS] = AppDynamicsMonitor(config)
                self.status[MonitoringSystem.APPDYNAMICS] = MonitoringStatus.STOPPED
                logger.info("AppDynamics monitor initialized")
            except Exception as e:
                logger.error(f"Failed to initialize AppDynamics: {e}")
                self.status[MonitoringSystem.APPDYNAMICS] = MonitoringStatus.ERROR
        else:
            self.status[MonitoringSystem.APPDYNAMICS] = MonitoringStatus.NOT_CONFIGURED
        
        # Kibana
        if self.settings.KIBANA_ENABLED:
            try:
                config = KibanaConfig(self.settings)
                self.monitors[MonitoringSystem.KIBANA] = KibanaMonitor(config)
                self.status[MonitoringSystem.KIBANA] = MonitoringStatus.STOPPED
                logger.info("Kibana monitor initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Kibana: {e}")
                self.status[MonitoringSystem.KIBANA] = MonitoringStatus.ERROR
        else:
            self.status[MonitoringSystem.KIBANA] = MonitoringStatus.NOT_CONFIGURED
        
        # Splunk
        if self.settings.SPLUNK_ENABLED:
            try:
                config = SplunkConfig(self.settings)
                self.monitors[MonitoringSystem.SPLUNK] = SplunkMonitor(config)
                self.status[MonitoringSystem.SPLUNK] = MonitoringStatus.STOPPED
                logger.info("Splunk monitor initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Splunk: {e}")
                self.status[MonitoringSystem.SPLUNK] = MonitoringStatus.ERROR
        else:
            self.status[MonitoringSystem.SPLUNK] = MonitoringStatus.NOT_CONFIGURED
        
        # MongoDB
        if self.settings.MONGODB_ENABLED:
            try:
                config = MongoDBConfig(self.settings)
                self.monitors[MonitoringSystem.MONGODB] = MongoDBAnalyzer(config)
                self.status[MonitoringSystem.MONGODB] = MonitoringStatus.STOPPED
                logger.info("MongoDB analyzer initialized")
            except Exception as e:
                logger.error(f"Failed to initialize MongoDB: {e}")
                self.status[MonitoringSystem.MONGODB] = MonitoringStatus.ERROR
        else:
            self.status[MonitoringSystem.MONGODB] = MonitoringStatus.NOT_CONFIGURED
        
        logger.info(f"Monitoring systems initialized: {list(self.monitors.keys())}")
    
    def start_monitoring(
        self,
        system: MonitoringSystem,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Start monitoring for a specific system
        
        Args:
            system: Monitoring system to start
            **kwargs: System-specific parameters
            
        Returns:
            Start result
        """
        try:
            if system == MonitoringSystem.ALL:
                return self.start_all_monitoring(**kwargs)
            
            if system not in self.monitors:
                return {
                    "status": "error",
                    "system": system,
                    "message": f"Monitoring system '{system}' not configured or not available",
                    "current_status": self.status.get(system, MonitoringStatus.NOT_CONFIGURED).value
                }
            
            logger.info(f"Starting {system} monitoring...")
            
            monitor = self.monitors[system]
            
            # Call appropriate start method based on system
            if system == MonitoringSystem.APPDYNAMICS:
                result = monitor.start_monitoring(**kwargs)
            elif system == MonitoringSystem.KIBANA:
                result = monitor.start_monitoring(**kwargs)
            elif system == MonitoringSystem.SPLUNK:
                result = monitor.start_monitoring(**kwargs)
            elif system == MonitoringSystem.MONGODB:
                result = monitor.start_analysis(**kwargs)
            else:
                raise ValueError(f"Unknown monitoring system: {system}")
            
            self.status[system] = MonitoringStatus.RUNNING
            
            return {
                "status": "success",
                "system": system,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to start {system} monitoring: {e}")
            self.status[system] = MonitoringStatus.ERROR
            return {
                "status": "error",
                "system": system,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def stop_monitoring(
        self,
        system: MonitoringSystem
    ) -> Dict[str, Any]:
        """
        Stop monitoring for a specific system
        
        Args:
            system: Monitoring system to stop
            
        Returns:
            Stop result
        """
        try:
            if system == MonitoringSystem.ALL:
                return self.stop_all_monitoring()
            
            if system not in self.monitors:
                return {
                    "status": "error",
                    "system": system,
                    "message": f"Monitoring system '{system}' not configured or not available"
                }
            
            logger.info(f"Stopping {system} monitoring...")
            
            monitor = self.monitors[system]
            
            # Call appropriate stop method
            if system == MonitoringSystem.MONGODB:
                result = monitor.stop_analysis()
            else:
                result = monitor.stop_monitoring()
            
            self.status[system] = MonitoringStatus.STOPPED
            
            return {
                "status": "success",
                "system": system,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to stop {system} monitoring: {e}")
            self.status[system] = MonitoringStatus.ERROR
            return {
                "status": "error",
                "system": system,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def start_all_monitoring(self, **kwargs) -> Dict[str, Any]:
        """Start all configured monitoring systems"""
        results = {}
        
        for system in self.monitors.keys():
            try:
                results[system] = self.start_monitoring(system, **kwargs)
            except Exception as e:
                logger.error(f"Failed to start {system}: {e}")
                results[system] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return {
            "status": "success",
            "message": "Started all configured monitoring systems",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    def stop_all_monitoring(self) -> Dict[str, Any]:
        """Stop all running monitoring systems"""
        results = {}
        
        for system in self.monitors.keys():
            try:
                if self.status.get(system) == MonitoringStatus.RUNNING:
                    results[system] = self.stop_monitoring(system)
                else:
                    results[system] = {
                        "status": "skipped",
                        "message": f"{system} was not running"
                    }
            except Exception as e:
                logger.error(f"Failed to stop {system}: {e}")
                results[system] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return {
            "status": "success",
            "message": "Stopped all monitoring systems",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_status(
        self,
        system: Optional[MonitoringSystem] = None
    ) -> Dict[str, Any]:
        """
        Get monitoring status
        
        Args:
            system: Specific system or None for all
            
        Returns:
            Status information
        """
        if system and system != MonitoringSystem.ALL:
            if system not in self.monitors:
                return {
                    "system": system,
                    "status": self.status.get(system, MonitoringStatus.NOT_CONFIGURED).value,
                    "message": "Not configured or not available"
                }
            
            monitor = self.monitors[system]
            monitor_status = monitor.get_status()
            
            return {
                "system": system,
                "status": self.status.get(system, MonitoringStatus.STOPPED).value,
                "details": monitor_status,
                "timestamp": datetime.now().isoformat()
            }
        
        # Get status for all systems
        all_status = {}
        for sys, monitor in self.monitors.items():
            try:
                all_status[sys] = {
                    "status": self.status.get(sys, MonitoringStatus.STOPPED).value,
                    "details": monitor.get_status()
                }
            except Exception as e:
                all_status[sys] = {
                    "status": MonitoringStatus.ERROR.value,
                    "error": str(e)
                }
        
        # Add not configured systems
        for sys_enum in MonitoringSystem:
            if sys_enum != MonitoringSystem.ALL and sys_enum.value not in all_status:
                all_status[sys_enum.value] = {
                    "status": MonitoringStatus.NOT_CONFIGURED.value
                }
        
        return {
            "overall_status": self._get_overall_status(),
            "systems": all_status,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data for all monitoring systems
        
        Returns:
            Dashboard data
        """
        dashboard = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": self._get_overall_status(),
            "systems_count": {
                "total": len(MonitoringSystem) - 1,  # Exclude ALL
                "configured": len(self.monitors),
                "running": sum(1 for status in self.status.values() if status == MonitoringStatus.RUNNING),
                "stopped": sum(1 for status in self.status.values() if status == MonitoringStatus.STOPPED),
                "error": sum(1 for status in self.status.values() if status == MonitoringStatus.ERROR),
                "not_configured": sum(1 for status in self.status.values() if status == MonitoringStatus.NOT_CONFIGURED)
            },
            "systems": {}
        }
        
        # Get data from each system
        for system, monitor in self.monitors.items():
            try:
                system_data = {
                    "status": self.status.get(system, MonitoringStatus.STOPPED).value,
                    "enabled": True,
                    "details": monitor.get_status()
                }
                
                # Add system-specific metrics
                if system == MonitoringSystem.APPDYNAMICS and self.status.get(system) == MonitoringStatus.RUNNING:
                    try:
                        system_data["health"] = monitor._get_application_health(
                            monitor.config.application_name
                        )
                    except:
                        pass
                
                dashboard["systems"][system] = system_data
                
            except Exception as e:
                logger.warning(f"Failed to get dashboard data for {system}: {e}")
                dashboard["systems"][system] = {
                    "status": MonitoringStatus.ERROR.value,
                    "enabled": True,
                    "error": str(e)
                }
        
        # Add not configured systems
        for sys_enum in MonitoringSystem:
            if sys_enum != MonitoringSystem.ALL and sys_enum.value not in dashboard["systems"]:
                dashboard["systems"][sys_enum.value] = {
                    "status": MonitoringStatus.NOT_CONFIGURED.value,
                    "enabled": False
                }
        
        return dashboard
    
    def _get_overall_status(self) -> str:
        """Calculate overall status"""
        if any(status == MonitoringStatus.ERROR for status in self.status.values()):
            return "degraded"
        elif any(status == MonitoringStatus.RUNNING for status in self.status.values()):
            return "active"
        elif all(status == MonitoringStatus.NOT_CONFIGURED for status in self.status.values()):
            return "not_configured"
        else:
            return "inactive"
    
    def cleanup(self):
        """Cleanup all monitoring connections"""
        logger.info("Cleaning up monitoring connections...")
        
        for system, monitor in self.monitors.items():
            try:
                if hasattr(monitor, 'close'):
                    monitor.close()
                logger.info(f"Closed {system} monitor")
            except Exception as e:
                logger.error(f"Failed to close {system} monitor: {e}")