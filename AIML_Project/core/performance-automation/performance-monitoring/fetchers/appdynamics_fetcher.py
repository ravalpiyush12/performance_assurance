"""
AppDynamics Data Fetcher using REST API
"""
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from utils.logger import setup_logger
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AppDynamicsDataFetcher:
    """Fetch metrics from AppDynamics using REST API"""
    
    def __init__(self, controller_url: str, account_name: str, username: str, password: str):
        self.controller_url = controller_url.rstrip('/')
        self.account_name = account_name
        self.username = username
        self.password = password
        self.auth = (f"{username}@{account_name}", password)
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update(self.headers)
        self.logger = setup_logger('AppDynamicsFetcher')
    
    def test_connection(self) -> bool:
        """Test connection to AppDynamics controller"""
        try:
            url = f"{self.controller_url}/controller/rest/applications"
            response = self.session.get(url, verify=False, timeout=10)
            
            if response.status_code == 200:
                self.logger.info("✓ AppDynamics connection successful")
                return True
            else:
                self.logger.error(f"✗ AppDynamics connection failed: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"✗ AppDynamics connection error: {e}")
            return False
    
    def get_applications(self) -> Optional[List[Dict]]:
        """Get list of all applications"""
        url = f"{self.controller_url}/controller/rest/applications"
        
        try:
            response = self.session.get(url, params={'output': 'JSON'}, verify=False, timeout=30)
            response.raise_for_status()
            
            apps = response.json()
            self.logger.info(f"✓ Fetched {len(apps)} applications")
            return apps
            
        except Exception as e:
            self.logger.error(f"✗ Error fetching applications: {e}")
            return None
    
    def get_metric_data(self, app_name: str, metric_path: str, 
                       duration_mins: int = 5, rollup: bool = False) -> Optional[List[Dict]]:
        """
        Fetch metric data from AppDynamics
        
        Args:
            app_name: Application name
            metric_path: Full metric path
            duration_mins: Duration in minutes to look back
            rollup: Whether to rollup data
            
        Returns:
            List of metric data points or None
        """
        url = f"{self.controller_url}/controller/rest/applications/{app_name}/metric-data"
        
        params = {
            'metric-path': metric_path,
            'time-range-type': 'BEFORE_NOW',
            'duration-in-mins': duration_mins,
            'rollup': str(rollup).lower(),
            'output': 'JSON'
        }
        
        try:
            response = self.session.get(url, params=params, verify=False, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            parsed_data = self._parse_metric_data(data)
            
            self.logger.info(f"✓ Fetched metric: {metric_path} ({len(parsed_data)} data points)")
            return parsed_data
            
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"✗ HTTP error fetching metric {metric_path}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"✗ Error fetching metric {metric_path}: {e}")
            return None
    
    def _parse_metric_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Parse AppDynamics metric response"""
        parsed = []
        
        for metric in raw_data:
            metric_name = metric.get('metricName', '')
            metric_path = metric.get('metricPath', '')
            metric_values = metric.get('metricValues', [])
            
            for value in metric_values:
                parsed.append({
                    'metric_name': metric_name,
                    'metric_path': metric_path,
                    'timestamp': value.get('startTimeInMillis'),
                    'value': value.get('value'),
                    'count': value.get('count'),
                    'sum': value.get('sum'),
                    'min': value.get('min'),
                    'max': value.get('max')
                })
        
        return parsed
    
    def get_multiple_metrics(self, app_name: str, metric_paths: Dict[str, str], 
                           duration_mins: int = 5) -> Dict[str, List[Dict]]:
        """
        Fetch multiple metrics in batch
        
        Args:
            app_name: Application name
            metric_paths: Dictionary of {metric_name: metric_path}
            duration_mins: Duration in minutes
            
        Returns:
            Dictionary of {metric_name: data_points}
        """
        results = {}
        
        for metric_name, metric_path in metric_paths.items():
            data = self.get_metric_data(app_name, metric_path, duration_mins)
            if data:
                results[metric_name] = data
            else:
                results[metric_name] = []
        
        return results
    
    def get_server_metrics(self, app_name: str, tier_name: str, node_name: str,
                          duration_mins: int = 5) -> Dict[str, List[Dict]]:
        """
        Get comprehensive server metrics
        
        Args:
            app_name: Application name
            tier_name: Tier name
            node_name: Node name
            duration_mins: Duration in minutes
            
        Returns:
            Dictionary of server metrics
        """
        base_path = f"Application Infrastructure Performance|{tier_name}|Individual Nodes|{node_name}"
        
        metric_paths = {
            'cpu_usage': f"{base_path}|Hardware Resources|CPU|%Busy",
            'cpu_stolen': f"{base_path}|Hardware Resources|CPU|%Stolen",
            'memory_used_pct': f"{base_path}|Hardware Resources|Memory|Used %",
            'memory_used_mb': f"{base_path}|Hardware Resources|Memory|Used (MB)",
            'memory_free_mb': f"{base_path}|Hardware Resources|Memory|Free (MB)",
            'disk_reads': f"{base_path}|Hardware Resources|Disks|Reads/sec",
            'disk_writes': f"{base_path}|Hardware Resources|Disks|Writes/sec",
            'network_incoming': f"{base_path}|Hardware Resources|Network|Incoming KB/sec",
            'network_outgoing': f"{base_path}|Hardware Resources|Network|Outgoing KB/sec"
        }
        
        self.logger.info(f"Fetching server metrics for: {app_name}/{tier_name}/{node_name}")
        return self.get_multiple_metrics(app_name, metric_paths, duration_mins)
    
    def get_jvm_metrics(self, app_name: str, tier_name: str, node_name: str,
                       duration_mins: int = 5) -> Dict[str, List[Dict]]:
        """
        Get JVM-specific metrics
        
        Args:
            app_name: Application name
            tier_name: Tier name
            node_name: Node name
            duration_mins: Duration in minutes
            
        Returns:
            Dictionary of JVM metrics
        """
        base_path = f"Application Infrastructure Performance|{tier_name}|Individual Nodes|{node_name}|JVM"
        
        metric_paths = {
            'heap_used_pct': f"{base_path}|Memory|Heap|Used %",
            'heap_used_mb': f"{base_path}|Memory|Heap|Used (MB)",
            'heap_committed_mb': f"{base_path}|Memory|Heap|Committed (MB)",
            'heap_max_mb': f"{base_path}|Memory|Heap|Max Available (MB)",
            'gc_time_per_min': f"{base_path}|Garbage Collection|GC Time Spent Per Min (ms)",
            'gc_major_count': f"{base_path}|Garbage Collection|Major GCs",
            'gc_minor_count': f"{base_path}|Garbage Collection|Minor GCs",
            'thread_count': f"{base_path}|Process|Thread Count"
        }
        
        self.logger.info(f"Fetching JVM metrics for: {app_name}/{tier_name}/{node_name}")
        return self.get_multiple_metrics(app_name, metric_paths, duration_mins)
    
    def get_transaction_metrics(self, app_name: str, tier_name: str,
                               duration_mins: int = 5) -> Dict[str, List[Dict]]:
        """
        Get business transaction metrics
        
        Args:
            app_name: Application name
            tier_name: Tier name
            duration_mins: Duration in minutes
            
        Returns:
            Dictionary of transaction metrics
        """
        base_path = f"Overall Application Performance|{tier_name}"
        
        metric_paths = {
            'calls_per_min': f"{base_path}|Calls per Minute",
            'avg_response_time': f"{base_path}|Average Response Time (ms)",
            'errors_per_min': f"{base_path}|Errors per Minute",
            'slow_calls': f"{base_path}|Number of Slow Calls",
            'very_slow_calls': f"{base_path}|Number of Very Slow Calls",
            'stall_count': f"{base_path}|Stall Count"
        }
        
        self.logger.info(f"Fetching transaction metrics for: {app_name}/{tier_name}")
        return self.get_multiple_metrics(app_name, metric_paths, duration_mins)
    
    def get_all_metrics(self, app_name: str, tier_name: str, node_name: str,
                       duration_mins: int = 5) -> Dict[str, Dict]:
        """
        Get all available metrics (server, JVM, transactions)
        
        Returns:
            Dictionary with keys: 'server', 'jvm', 'transactions'
        """
        all_metrics = {
            'server': self.get_server_metrics(app_name, tier_name, node_name, duration_mins),
            'jvm': self.get_jvm_metrics(app_name, tier_name, node_name, duration_mins),
            'transactions': self.get_transaction_metrics(app_name, tier_name, duration_mins)
        }
        
        return all_metrics