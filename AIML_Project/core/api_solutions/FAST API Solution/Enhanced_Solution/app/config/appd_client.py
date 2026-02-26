"""
AppDynamics REST API Client
Handles all communication with AppDynamics Controller
"""
import requests
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json


class AppDynamicsClient:
    """Client for AppDynamics REST API"""
    
    def __init__(self, config):
        """
        Initialize AppD client
        
        Args:
            config: AppDynamicsConfig instance
        """
        self.config = config
        self.base_url = config.rest_api_base_url
        self.auth = config.get_auth()
        self.session = requests.Session()
        self.session.auth = self.auth
    
    def _make_request(self, method: str, url: str, **kwargs) -> Optional[Dict]:
        """
        Make HTTP request with retry logic
        
        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            Response data or None
        """
        kwargs.setdefault('timeout', self.config.APPD_API_TIMEOUT)
        kwargs.setdefault('verify', self.config.APPD_USE_SSL)
        
        for attempt in range(self.config.APPD_MAX_RETRIES):
            try:
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                
                # Handle JSON and XML responses
                content_type = response.headers.get('Content-Type', '')
                if 'json' in content_type:
                    return response.json()
                else:
                    return response.text
                    
            except requests.exceptions.RequestException as e:
                print(f"Request failed (attempt {attempt + 1}/{self.config.APPD_MAX_RETRIES}): {e}")
                if attempt < self.config.APPD_MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
        
        return None
    
    # ========================================
    # Application APIs
    # ========================================
    
    def get_applications(self) -> List[Dict]:
        """
        Get all applications
        
        Returns:
            List of application dictionaries
        """
        url = f"{self.base_url}/applications"
        params = {'output': 'JSON'}
        
        result = self._make_request('GET', url, params=params)
        return result if isinstance(result, list) else []
    
    def get_application_by_name(self, app_name: str) -> Optional[Dict]:
        """
        Get application details by name
        
        Args:
            app_name: Application name
            
        Returns:
            Application details or None
        """
        apps = self.get_applications()
        for app in apps:
            if app.get('name') == app_name:
                return app
        return None
    
    # ========================================
    # Tier APIs
    # ========================================
    
    def get_tiers(self, app_name: str) -> List[Dict]:
        """
        Get all tiers for an application
        
        Args:
            app_name: Application name
            
        Returns:
            List of tier dictionaries
        """
        url = f"{self.base_url}/applications/{app_name}/tiers"
        params = {'output': 'JSON'}
        
        result = self._make_request('GET', url, params=params)
        return result if isinstance(result, list) else []
    
    # ========================================
    # Node APIs
    # ========================================
    
    def get_nodes(self, app_name: str, tier_name: Optional[str] = None) -> List[Dict]:
        """
        Get all nodes for an application or tier
        
        Args:
            app_name: Application name
            tier_name: Optional tier name to filter
            
        Returns:
            List of node dictionaries
        """
        if tier_name:
            url = f"{self.base_url}/applications/{app_name}/tiers/{tier_name}/nodes"
        else:
            url = f"{self.base_url}/applications/{app_name}/nodes"
        
        params = {'output': 'JSON'}
        result = self._make_request('GET', url, params=params)
        return result if isinstance(result, list) else []
    
    def get_node_details(self, app_name: str, node_name: str) -> Optional[Dict]:
        """
        Get detailed information about a node
        
        Args:
            app_name: Application name
            node_name: Node name
            
        Returns:
            Node details or None
        """
        url = f"{self.base_url}/applications/{app_name}/nodes/{node_name}"
        params = {'output': 'JSON'}
        
        return self._make_request('GET', url, params=params)
    
    # ========================================
    # Metrics APIs
    # ========================================
    
    def get_metric_data(
        self,
        app_name: str,
        metric_path: str,
        duration_minutes: int = 30,
        rollup: bool = False
    ) -> List[Dict]:
        """
        Get metric data for specified metric path
        
        Args:
            app_name: Application name
            metric_path: Full metric path (e.g., "Overall Application Performance|Calls per Minute")
            duration_minutes: How many minutes of data to fetch
            rollup: Whether to rollup data
            
        Returns:
            List of metric data points
        """
        url = f"{self.config.metrics_api_base_url}/{app_name}/metric-data"
        
        params = {
            'metric-path': metric_path,
            'time-range-type': 'BEFORE_NOW',
            'duration-in-mins': duration_minutes,
            'rollup': 'true' if rollup else 'false',
            'output': 'JSON'
        }
        
        result = self._make_request('GET', url, params=params)
        return result if isinstance(result, list) else []
    
    def get_calls_per_minute(
        self,
        app_name: str,
        tier_name: Optional[str] = None,
        node_name: Optional[str] = None,
        duration_minutes: int = 30
    ) -> float:
        """
        Get calls per minute for app/tier/node
        
        Args:
            app_name: Application name
            tier_name: Optional tier name
            node_name: Optional node name
            duration_minutes: Data duration
            
        Returns:
            Average calls per minute
        """
        # Build metric path
        if node_name:
            metric_path = f"Application Infrastructure Performance|{tier_name}|Individual Nodes|{node_name}|Calls per Minute"
        elif tier_name:
            metric_path = f"Application Infrastructure Performance|{tier_name}|Calls per Minute"
        else:
            metric_path = "Overall Application Performance|Calls per Minute"
        
        data = self.get_metric_data(app_name, metric_path, duration_minutes)
        
        if data and len(data) > 0:
            # Calculate average from metric values
            values = []
            for metric in data:
                for value_dict in metric.get('metricValues', []):
                    values.append(value_dict.get('value', 0))
            
            return sum(values) / len(values) if values else 0.0
        
        return 0.0
    
    # ========================================
    # Server Metrics (Hardware)
    # ========================================
    
    def get_server_metrics(
        self,
        app_name: str,
        tier_name: str,
        node_name: str,
        duration_minutes: int = 5
    ) -> Dict[str, Any]:
        """
        Get server/hardware metrics for a node
        
        Args:
            app_name: Application name
            tier_name: Tier name
            node_name: Node name
            duration_minutes: Data duration
            
        Returns:
            Dictionary with CPU, Memory, Network, Disk metrics
        """
        base_path = f"Application Infrastructure Performance|{tier_name}|Individual Nodes|{node_name}|Hardware Resources"
        
        metrics = {}
        
        # CPU Metrics
        cpu_metrics = {
            'CPU|%Busy': 'cpu_busy_percent',
            'CPU|%Idle': 'cpu_idle_percent',
            'CPU|%Stolen': 'cpu_stolen_percent'
        }
        
        for metric_path, key in cpu_metrics.items():
            data = self.get_metric_data(app_name, f"{base_path}|{metric_path}", duration_minutes)
            metrics[key] = self._extract_latest_value(data)
        
        # Memory Metrics
        memory_metrics = {
            'Memory|Total (MB)': 'memory_total_mb',
            'Memory|Used (MB)': 'memory_used_mb',
            'Memory|Free (MB)': 'memory_free_mb',
            'Memory|Used %': 'memory_used_percent'
        }
        
        for metric_path, key in memory_metrics.items():
            data = self.get_metric_data(app_name, f"{base_path}|{metric_path}", duration_minutes)
            metrics[key] = self._extract_latest_value(data)
        
        # Network Metrics
        network_metrics = {
            'Network|Incoming KB': 'network_incoming_kb',
            'Network|Outgoing KB': 'network_outgoing_kb'
        }
        
        for metric_path, key in network_metrics.items():
            data = self.get_metric_data(app_name, f"{base_path}|{metric_path}", duration_minutes)
            metrics[key] = self._extract_latest_value(data)
        
        # Disk Metrics
        disk_metrics = {
            'Disks|Reads/sec': 'disk_reads_per_sec',
            'Disks|Writes/sec': 'disk_writes_per_sec',
            'Disks|Used %': 'disk_used_percent',
            'Disks|Queue Length': 'disk_queue_length'
        }
        
        for metric_path, key in disk_metrics.items():
            data = self.get_metric_data(app_name, f"{base_path}|{metric_path}", duration_minutes)
            metrics[key] = self._extract_latest_value(data)
        
        return metrics
    
    # ========================================
    # JVM Metrics
    # ========================================
    
    def get_jvm_metrics(
        self,
        app_name: str,
        tier_name: str,
        node_name: str,
        duration_minutes: int = 5
    ) -> Dict[str, Any]:
        """
        Get JVM metrics for a node
        
        Args:
            app_name: Application name
            tier_name: Tier name
            node_name: Node name
            duration_minutes: Data duration
            
        Returns:
            Dictionary with Heap, GC, Thread, Exception metrics
        """
        base_path = f"Application Infrastructure Performance|{tier_name}|Individual Nodes|{node_name}|JVM"
        
        metrics = {}
        
        # Heap Metrics
        heap_metrics = {
            'Memory|Heap|Used (MB)': 'heap_used_mb',
            'Memory|Heap|Committed (MB)': 'heap_committed_mb',
            'Memory|Heap|Max Available (MB)': 'heap_max_mb',
            'Memory|Heap|Used %': 'heap_used_percent',
            'Memory|Non-Heap|Used (MB)': 'non_heap_used_mb',
            'Memory|Non-Heap|Committed (MB)': 'non_heap_committed_mb'
        }
        
        for metric_path, key in heap_metrics.items():
            data = self.get_metric_data(app_name, f"{base_path}|{metric_path}", duration_minutes)
            metrics[key] = self._extract_latest_value(data)
        
        # GC Metrics
        gc_metrics = {
            'Garbage Collection|GC Time Spent (ms/min)': 'gc_time_ms',
            'Garbage Collection|Major GC Collection Count': 'gc_major_count',
            'Garbage Collection|Minor GC Collection Count': 'gc_minor_count',
            'Garbage Collection|GC Time Spent Per Min (%)': 'gc_time_percent'
        }
        
        for metric_path, key in gc_metrics.items():
            data = self.get_metric_data(app_name, f"{base_path}|{metric_path}", duration_minutes)
            metrics[key] = self._extract_latest_value(data)
        
        # Thread Metrics
        thread_metrics = {
            'Threads|Total Threads': 'thread_count',
            'Threads|Current Thread Count': 'thread_current',
            'Threads|Peak Thread Count': 'thread_peak',
            'Threads|Daemon Thread Count': 'thread_daemon',
            'Threads|Blocked Threads': 'thread_blocked'
        }
        
        for metric_path, key in thread_metrics.items():
            data = self.get_metric_data(app_name, f"{base_path}|{metric_path}", duration_minutes)
            metrics[key] = self._extract_latest_value(data)
        
        # Class Metrics
        class_metrics = {
            'Classes|Total Classes Loaded': 'classes_loaded',
            'Classes|Total Classes Unloaded': 'classes_unloaded'
        }
        
        for metric_path, key in class_metrics.items():
            data = self.get_metric_data(app_name, f"{base_path}|{metric_path}", duration_minutes)
            metrics[key] = self._extract_latest_value(data)
        
        return metrics
    
    # ========================================
    # Application Performance Metrics
    # ========================================
    
    def get_application_metrics(
        self,
        app_name: str,
        tier_name: str,
        node_name: str,
        duration_minutes: int = 5
    ) -> Dict[str, Any]:
        """
        Get application performance metrics for a node
        
        Args:
            app_name: Application name
            tier_name: Tier name  
            node_name: Node name
            duration_minutes: Data duration
            
        Returns:
            Dictionary with CPM, Response Time, Error metrics
        """
        base_path = f"Application Infrastructure Performance|{tier_name}|Individual Nodes|{node_name}"
        
        metrics = {}
        
        # Call Metrics
        call_metrics = {
            'Calls per Minute': 'calls_per_minute',
            'Number of Calls': 'calls_total'
        }
        
        for metric_path, key in call_metrics.items():
            data = self.get_metric_data(app_name, f"{base_path}|{metric_path}", duration_minutes)
            metrics[key] = self._extract_latest_value(data)
        
        # Response Time Metrics
        response_metrics = {
            'Average Response Time (ms)': 'response_time_avg_ms',
            'Minimum Response Time (ms)': 'response_time_min_ms',
            'Maximum Response Time (ms)': 'response_time_max_ms'
        }
        
        for metric_path, key in response_metrics.items():
            data = self.get_metric_data(app_name, f"{base_path}|{metric_path}", duration_minutes)
            metrics[key] = self._extract_latest_value(data)
        
        # Error Metrics
        error_metrics = {
            'Errors per Minute': 'errors_per_minute',
            'Number of Errors': 'errors_total',
            'Error Rate (%)': 'error_rate_percent'
        }
        
        for metric_path, key in error_metrics.items():
            data = self.get_metric_data(app_name, f"{base_path}|{metric_path}", duration_minutes)
            metrics[key] = self._extract_latest_value(data)
        
        # Business Transaction Metrics
        bt_metrics = {
            'Number of Normal Calls': 'bt_normal_count',
            'Number of Slow Calls': 'bt_slow_count',
            'Number of Very Slow Calls': 'bt_very_slow_count',
            'Number of Stalled Calls': 'bt_stalled_count'
        }
        
        for metric_path, key in bt_metrics.items():
            data = self.get_metric_data(app_name, f"{base_path}|{metric_path}", duration_minutes)
            metrics[key] = self._extract_latest_value(data)
        
        # Exception Metrics  
        exception_metrics = {
            'Exceptions per Minute': 'exception_count',
            'Number of Slow Transactions': 'slow_calls_count',
            'Number of Very Slow Transactions': 'very_slow_calls_count',
            'Number of Stalled Transactions': 'stall_calls_count'
        }
        
        for metric_path, key in exception_metrics.items():
            data = self.get_metric_data(app_name, f"{base_path}|{metric_path}", duration_minutes)
            metrics[key] = self._extract_latest_value(data)
        
        return metrics
    
    # ========================================
    # Helper Methods
    # ========================================
    
    def _extract_latest_value(self, metric_data: List[Dict]) -> Optional[float]:
        """
        Extract the latest value from metric data
        
        Args:
            metric_data: Metric data from API
            
        Returns:
            Latest metric value or None
        """
        if not metric_data or not isinstance(metric_data, list):
            return None
        
        for metric in metric_data:
            values = metric.get('metricValues', [])
            if values:
                # Get the last value (most recent)
                return values[-1].get('value')
        
        return None
    
    def close(self):
        """Close the session"""
        self.session.close()