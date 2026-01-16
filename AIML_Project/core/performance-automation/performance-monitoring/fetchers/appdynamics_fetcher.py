"""
AppDynamics Data Fetcher - Simplified for Server, JVM, and Transaction Metrics
"""
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from utils.logger import setup_logger
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AppDynamicsDataFetcher:
    """Fetch Server, JVM, and Transaction metrics from AppDynamics"""
    
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
    
    def get_tiers_for_application(self, app_name: str) -> Optional[List[Dict]]:
        """Get all tiers for an application"""
        url = f"{self.controller_url}/controller/rest/applications/{app_name}/tiers"
        
        try:
            response = self.session.get(url, params={'output': 'JSON'}, verify=False, timeout=30)
            response.raise_for_status()
            
            tiers = response.json()
            self.logger.info(f"✓ Fetched {len(tiers)} tiers for {app_name}")
            return tiers
            
        except Exception as e:
            self.logger.error(f"✗ Error fetching tiers for {app_name}: {e}")
            return None
    
    def get_nodes_for_tier(self, app_name: str, tier_name: str) -> Optional[List[Dict]]:
        """Get all nodes for a tier"""
        url = f"{self.controller_url}/controller/rest/applications/{app_name}/tiers/{tier_name}/nodes"
        
        try:
            response = self.session.get(url, params={'output': 'JSON'}, verify=False, timeout=30)
            response.raise_for_status()
            
            nodes = response.json()
            self.logger.info(f"✓ Fetched {len(nodes)} nodes for {app_name}/{tier_name}")
            return nodes
            
        except Exception as e:
            self.logger.error(f"✗ Error fetching nodes for {app_name}/{tier_name}: {e}")
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
            
            return parsed_data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                self.logger.warning(f"⚠ Metric not found: {metric_path}")
            else:
                self.logger.error(f"✗ HTTP error fetching metric: {e}")
            return None
        except Exception as e:
            self.logger.error(f"✗ Error fetching metric: {e}")
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
    
    def get_server_metrics(self, app_name: str, tier_name: str, node_name: str,
                          duration_mins: int = 5) -> Dict[str, List[Dict]]:
        """
        Get server/hardware metrics for a node
        
        Args:
            app_name: Application name
            tier_name: Tier name
            node_name: Node name
            duration_mins: Duration in minutes
            
        Returns:
            Dictionary of server metrics
        """
        base_path = f"Application Infrastructure Performance|{tier_name}|Individual Nodes|{node_name}|Hardware Resources"
        
        metric_paths = {
            'cpu_busy': f"{base_path}|CPU|%Busy",
            'cpu_idle': f"{base_path}|CPU|%Idle",
            'cpu_stolen': f"{base_path}|CPU|%Stolen",
            'memory_used_pct': f"{base_path}|Memory|Used %",
            'memory_used_mb': f"{base_path}|Memory|Used (MB)",
            'memory_free_mb': f"{base_path}|Memory|Free (MB)",
            'memory_total_mb': f"{base_path}|Memory|Total (MB)",
            'disk_reads_per_sec': f"{base_path}|Disks|Reads/sec",
            'disk_writes_per_sec': f"{base_path}|Disks|Writes/sec",
            'disk_kb_read_per_sec': f"{base_path}|Disks|KB read/sec",
            'disk_kb_written_per_sec': f"{base_path}|Disks|KB written/sec",
            'network_incoming_kb': f"{base_path}|Network|Incoming KB/sec",
            'network_outgoing_kb': f"{base_path}|Network|Outgoing KB/sec"
        }
        
        self.logger.debug(f"→ Fetching server metrics: {app_name}/{tier_name}/{node_name}")
        return self._fetch_multiple_metrics(app_name, metric_paths, duration_mins)
    
    def get_jvm_metrics(self, app_name: str, tier_name: str, node_name: str,
                       duration_mins: int = 5) -> Dict[str, List[Dict]]:
        """
        Get JVM metrics for a node
        
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
            # Memory metrics
            'heap_used_pct': f"{base_path}|Memory|Heap|Used %",
            'heap_used_mb': f"{base_path}|Memory|Heap|Used (MB)",
            'heap_committed_mb': f"{base_path}|Memory|Heap|Committed (MB)",
            'heap_max_mb': f"{base_path}|Memory|Heap|Max Available (MB)",
            'heap_current_usage_mb': f"{base_path}|Memory|Heap|Current Usage (MB)",
            'non_heap_used_mb': f"{base_path}|Memory|Non-Heap|Used (MB)",
            'non_heap_committed_mb': f"{base_path}|Memory|Non-Heap|Committed (MB)",
            
            # Garbage Collection metrics
            'gc_time_spent_per_min': f"{base_path}|Garbage Collection|GC Time Spent Per Min (ms)",
            'gc_major_collection_time': f"{base_path}|Garbage Collection|Major Collection Time (ms)",
            'gc_minor_collection_time': f"{base_path}|Garbage Collection|Minor Collection Time (ms)",
            'gc_number_of_major_collections': f"{base_path}|Garbage Collection|Number of Major Collections Per Min",
            'gc_number_of_minor_collections': f"{base_path}|Garbage Collection|Number of Minor Collections Per Min",
            
            # CPU metrics
            'process_cpu_usage_pct': f"{base_path}|Process CPU Usage %",
            'process_cpu_burned_per_min': f"{base_path}|Process CPU Burned (ms/min)",
            
            # Thread metrics
            'thread_count': f"{base_path}|Process|Thread Count",
            'thread_blocked_count': f"{base_path}|Process|Threads Blocked",
            'thread_deadlocked_count': f"{base_path}|Process|Threads Deadlocked"
        }
        
        self.logger.debug(f"→ Fetching JVM metrics: {app_name}/{tier_name}/{node_name}")
        return self._fetch_multiple_metrics(app_name, metric_paths, duration_mins)
    
    def get_application_metrics(self, app_name: str, tier_name: str,
                               duration_mins: int = 5) -> Dict[str, List[Dict]]:
        """
        Get application/transaction metrics for a tier
        
        Args:
            app_name: Application name
            tier_name: Tier name
            duration_mins: Duration in minutes
            
        Returns:
            Dictionary of application metrics
        """
        base_path = f"Overall Application Performance|{tier_name}"
        
        metric_paths = {
            # Call/Transaction metrics
            'calls_per_min': f"{base_path}|Calls per Minute",
            'avg_response_time_ms': f"{base_path}|Average Response Time (ms)",
            'normal_avg_response_time_ms': f"{base_path}|Normal Average Response Time (ms)",
            
            # Error metrics
            'errors_per_min': f"{base_path}|Errors per Minute",
            'exceptions_per_min': f"{base_path}|Exceptions per Minute",
            'error_percentage': f"{base_path}|Error Percentage",
            
            # Performance metrics
            'slow_calls_count': f"{base_path}|Number of Slow Calls",
            'very_slow_calls_count': f"{base_path}|Number of Very Slow Calls",
            'stall_count': f"{base_path}|Stall Count",
            
            # Infrastructure errors
            'infrastructure_errors_per_min': f"{base_path}|Infrastructure Errors per Minute",
            'http_error_codes_per_min': f"{base_path}|HTTP Error Codes per Minute"
        }
        
        self.logger.debug(f"→ Fetching application metrics: {app_name}/{tier_name}")
        return self._fetch_multiple_metrics(app_name, metric_paths, duration_mins)
    
    def _fetch_multiple_metrics(self, app_name: str, metric_paths: Dict[str, str], 
                               duration_mins: int) -> Dict[str, List[Dict]]:
        """Helper method to fetch multiple metrics"""
        results = {}
        
        for metric_name, metric_path in metric_paths.items():
            data = self.get_metric_data(app_name, metric_path, duration_mins)
            if data:
                results[metric_name] = data
            else:
                results[metric_name] = []
        
        return results
    
    def collect_all_metrics(self, app_configs: List[Dict], duration_mins: int = 5) -> Dict:
        """
        Collect all metrics (Server, JVM, Application) for multiple apps/tiers/nodes
        
        Args:
            app_configs: List of app configurations
                Example:
                [
                    {
                        'app_name': 'Application1',
                        'tiers': [
                            {
                                'tier_name': 'Tier1',
                                'nodes': ['Node1', 'Node2']  # or None for auto-discovery
                            }
                        ]
                    }
                ]
            duration_mins: Duration in minutes
            
        Returns:
            Dictionary with all collected metrics organized by app/tier/node
        """
        all_metrics = {}
        
        self.logger.info("=" * 80)
        self.logger.info(f"Starting Metrics Collection - {len(app_configs)} Applications")
        self.logger.info("=" * 80)
        
        for app_idx, app_config in enumerate(app_configs, 1):
            app_name = app_config.get('app_name')
            tiers = app_config.get('tiers', [])
            
            self.logger.info(f"\n[App {app_idx}/{len(app_configs)}] Processing: {app_name}")
            
            if app_name not in all_metrics:
                all_metrics[app_name] = {}
            
            for tier_idx, tier_config in enumerate(tiers, 1):
                tier_name = tier_config.get('tier_name')
                nodes = tier_config.get('nodes')
                
                self.logger.info(f"  [Tier {tier_idx}/{len(tiers)}] {tier_name}")
                
                # Auto-discover nodes if not specified
                if nodes is None or (isinstance(nodes, list) and len(nodes) == 0):
                    self.logger.info(f"    Auto-discovering nodes for {tier_name}...")
                    discovered_nodes = self.get_nodes_for_tier(app_name, tier_name)
                    if discovered_nodes:
                        nodes = [node.get('name') for node in discovered_nodes]
                        self.logger.info(f"    Found {len(nodes)} nodes: {', '.join(nodes)}")
                    else:
                        self.logger.warning(f"    No nodes found for {tier_name}")
                        nodes = []
                
                if tier_name not in all_metrics[app_name]:
                    all_metrics[app_name][tier_name] = {
                        'application_metrics': {},
                        'nodes': {}
                    }
                
                # Collect application-level metrics (tier level)
                try:
                    self.logger.info(f"    → Collecting application metrics...")
                    app_metrics = self.get_application_metrics(app_name, tier_name, duration_mins)
                    
                    # Count data points
                    total_app_points = sum(len(values) for values in app_metrics.values())
                    all_metrics[app_name][tier_name]['application_metrics'] = app_metrics
                    self.logger.info(f"      ✓ Application metrics: {total_app_points} data points")
                    
                except Exception as e:
                    self.logger.error(f"      ✗ Error collecting application metrics: {e}")
                
                # Collect node-level metrics (Server + JVM)
                for node_idx, node_name in enumerate(nodes, 1):
                    self.logger.info(f"    [Node {node_idx}/{len(nodes)}] {node_name}")
                    
                    if node_name not in all_metrics[app_name][tier_name]['nodes']:
                        all_metrics[app_name][tier_name]['nodes'][node_name] = {
                            'server_metrics': {},
                            'jvm_metrics': {}
                        }
                    
                    # Collect Server metrics
                    try:
                        self.logger.info(f"      → Collecting server metrics...")
                        server_metrics = self.get_server_metrics(
                            app_name, tier_name, node_name, duration_mins
                        )
                        
                        total_server_points = sum(len(values) for values in server_metrics.values())
                        all_metrics[app_name][tier_name]['nodes'][node_name]['server_metrics'] = server_metrics
                        self.logger.info(f"        ✓ Server metrics: {total_server_points} data points")
                        
                    except Exception as e:
                        self.logger.error(f"        ✗ Error collecting server metrics: {e}")
                    
                    # Collect JVM metrics
                    try:
                        self.logger.info(f"      → Collecting JVM metrics...")
                        jvm_metrics = self.get_jvm_metrics(
                            app_name, tier_name, node_name, duration_mins
                        )
                        
                        total_jvm_points = sum(len(values) for values in jvm_metrics.values())
                        all_metrics[app_name][tier_name]['nodes'][node_name]['jvm_metrics'] = jvm_metrics
                        self.logger.info(f"        ✓ JVM metrics: {total_jvm_points} data points")
                        
                    except Exception as e:
                        self.logger.error(f"        ✗ Error collecting JVM metrics: {e}")
        
        # Calculate totals
        total_data_points = self._count_total_data_points(all_metrics)
        
        self.logger.info("\n" + "=" * 80)
        self.logger.info(f"Metrics Collection Complete")
        self.logger.info(f"Total Data Points Collected: {total_data_points}")
        self.logger.info("=" * 80)
        
        return all_metrics
    
    def _count_total_data_points(self, metrics_data: Dict) -> int:
        """Count total data points in collected metrics"""
        total = 0
        
        for app_name, app_data in metrics_data.items():
            for tier_name, tier_data in app_data.items():
                # Count application metrics
                app_metrics = tier_data.get('application_metrics', {})
                total += sum(len(values) for values in app_metrics.values())
                
                # Count node metrics
                nodes = tier_data.get('nodes', {})
                for node_name, node_data in nodes.items():
                    server_metrics = node_data.get('server_metrics', {})
                    jvm_metrics = node_data.get('jvm_metrics', {})
                    
                    total += sum(len(values) for values in server_metrics.values())
                    total += sum(len(values) for values in jvm_metrics.values())
        
        return total