"""
AppDynamics Data Fetcher using REST API - Auto Dashboard Discovery
"""
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from utils.logger import setup_logger
import urllib3
import json
import re

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AppDynamicsDataFetcher:
    """Fetch metrics from AppDynamics using REST API with Dashboard auto-discovery"""
    
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
    
    def get_dashboard_details(self, dashboard_id: int) -> Optional[Dict]:
        """
        Get dashboard details including all widgets and their configurations
        
        Args:
            dashboard_id: Dashboard ID
            
        Returns:
            Dashboard configuration or None
        """
        url = f"{self.controller_url}/controller/restui/dashboards/dashboardIfModified/{dashboard_id}"
        
        try:
            response = self.session.get(url, verify=False, timeout=30)
            response.raise_for_status()
            
            dashboard = response.json()
            self.logger.info(f"✓ Fetched dashboard: {dashboard.get('name', 'Unknown')}")
            return dashboard
            
        except Exception as e:
            self.logger.error(f"✗ Error fetching dashboard {dashboard_id}: {e}")
            return None
    
    def parse_dashboard_to_config(self, dashboard_id: int) -> List[Dict]:
        """
        Parse dashboard and extract widget configurations automatically
        
        Args:
            dashboard_id: Dashboard ID
            
        Returns:
            List of widget configurations ready for metric collection
        """
        dashboard = self.get_dashboard_details(dashboard_id)
        if not dashboard:
            return []
        
        dashboard_name = dashboard.get('name', 'Unknown Dashboard')
        widgets = dashboard.get('widgetTemplates', [])
        
        self.logger.info("=" * 80)
        self.logger.info(f"Parsing Dashboard: {dashboard_name} (ID: {dashboard_id})")
        self.logger.info(f"Total Widgets: {len(widgets)}")
        self.logger.info("=" * 80)
        
        widget_configs = []
        
        for idx, widget in enumerate(widgets, 1):
            widget_config = self._parse_widget(widget, idx, dashboard_name)
            if widget_config:
                widget_configs.append(widget_config)
                self.logger.info(f"  [{idx}] ✓ {widget_config['widget_name']}")
            else:
                self.logger.warning(f"  [{idx}] ⚠ Skipped widget (unsupported type)")
        
        self.logger.info("=" * 80)
        self.logger.info(f"Successfully parsed {len(widget_configs)} widgets")
        self.logger.info("=" * 80)
        
        return widget_configs
    
    def _parse_widget(self, widget: Dict, widget_idx: int, dashboard_name: str) -> Optional[Dict]:
        """
        Parse individual widget and extract metric configuration
        
        Args:
            widget: Widget data from dashboard
            widget_idx: Widget index
            dashboard_name: Dashboard name
            
        Returns:
            Widget configuration or None
        """
        widget_type = widget.get('type', 'UNKNOWN')
        widget_name = widget.get('title', f'Widget_{widget_idx}')
        
        # Get widget data structure
        widget_data = widget.get('dataFetchInfos', [])
        
        if not widget_data:
            return None
        
        # Initialize config
        config = {
            'widget_name': f"{dashboard_name} - {widget_name}",
            'widget_type': widget_type,
            'widget_index': widget_idx,
            'apps_tiers_nodes': []
        }
        
        # Parse data sources
        for data_info in widget_data:
            metric_info = self._extract_metric_info(data_info)
            if metric_info:
                config['apps_tiers_nodes'].append(metric_info)
        
        # Determine metric type based on widget type and metric paths
        config['metric_type'] = self._determine_metric_type(config, widget_type)
        
        return config if config['apps_tiers_nodes'] else None
    
    def _extract_metric_info(self, data_info: Dict) -> Optional[Dict]:
        """
        Extract application, tier, node, and metric information from widget data
        
        Args:
            data_info: Widget data fetch info
            
        Returns:
            Metric information dictionary or None
        """
        try:
            # Get metric path
            metric_path = data_info.get('metricPath', '')
            
            if not metric_path:
                return None
            
            # Parse metric path to extract app, tier, node
            # Example paths:
            # "Application Infrastructure Performance|Tier1|Individual Nodes|Node1|JVM|Memory|Heap|Used %"
            # "Overall Application Performance|Tier1|Calls per Minute"
            
            app_name = data_info.get('applicationName', '')
            
            # Parse from metric path
            parts = metric_path.split('|')
            
            tier_name = None
            node_name = None
            metric_category = None
            
            if 'Application Infrastructure Performance' in metric_path:
                # Node-level metrics
                if len(parts) >= 4:
                    tier_name = parts[1]
                    if 'Individual Nodes' in parts[2]:
                        node_name = parts[3]
                    
                # Determine category
                if 'JVM' in metric_path:
                    metric_category = 'jvm'
                elif 'Hardware Resources' in metric_path:
                    metric_category = 'hardware'
                
            elif 'Overall Application Performance' in metric_path:
                # Tier-level transaction metrics
                if len(parts) >= 2:
                    tier_name = parts[1]
                metric_category = 'transaction'
            
            elif 'Business Transaction Performance' in metric_path:
                # Business transaction metrics
                if len(parts) >= 2:
                    tier_name = parts[1]
                metric_category = 'business_transaction'
            
            return {
                'app_name': app_name,
                'tier_name': tier_name,
                'node_name': node_name,
                'metric_path': metric_path,
                'metric_category': metric_category
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting metric info: {e}")
            return None
    
    def _determine_metric_type(self, config: Dict, widget_type: str) -> str:
        """
        Determine the overall metric type for the widget
        
        Args:
            config: Widget configuration
            widget_type: Widget type from AppDynamics
            
        Returns:
            Metric type: 'jvm', 'transaction', 'combined', 'custom'
        """
        categories = set()
        
        for metric_info in config['apps_tiers_nodes']:
            category = metric_info.get('metric_category')
            if category:
                categories.add(category)
        
        if 'jvm' in categories and 'transaction' in categories:
            return 'combined'
        elif 'jvm' in categories or 'hardware' in categories:
            return 'jvm'
        elif 'transaction' in categories or 'business_transaction' in categories:
            return 'transaction'
        else:
            return 'custom'
    
    def get_dashboard_metrics_by_id(self, dashboard_id: int, duration_mins: int = 5) -> Dict[str, Dict]:
        """
        Automatically fetch all metrics from a dashboard using its ID
        
        Args:
            dashboard_id: Dashboard ID
            duration_mins: Duration in minutes to look back
            
        Returns:
            Dictionary of widget data organized by widget name
        """
        # Parse dashboard to get widget configurations
        widget_configs = self.parse_dashboard_to_config(dashboard_id)
        
        if not widget_configs:
            self.logger.error(f"No widgets found in dashboard {dashboard_id}")
            return {}
        
        # Reorganize configs for metric collection
        organized_configs = self._organize_widget_configs(widget_configs)
        
        # Collect metrics using standard dashboard collection
        return self.get_dashboard_metrics(organized_configs, duration_mins)
    
    def _organize_widget_configs(self, widget_configs: List[Dict]) -> List[Dict]:
        """
        Organize parsed widget configs into format expected by get_dashboard_metrics
        
        Args:
            widget_configs: List of parsed widget configurations
            
        Returns:
            List of organized configurations
        """
        organized = []
        
        for widget in widget_configs:
            widget_name = widget['widget_name']
            metric_type = widget['metric_type']
            
            # Group by application and tier
            app_tier_map = {}
            
            for metric_info in widget['apps_tiers_nodes']:
                app_name = metric_info.get('app_name')
                tier_name = metric_info.get('tier_name')
                node_name = metric_info.get('node_name')
                
                if not app_name or not tier_name:
                    continue
                
                key = (app_name, tier_name)
                
                if key not in app_tier_map:
                    app_tier_map[key] = {
                        'widget_name': widget_name,
                        'app_name': app_name,
                        'tier_name': tier_name,
                        'metric_type': metric_type,
                        'nodes': []
                    }
                
                if node_name and node_name not in app_tier_map[key]['nodes']:
                    app_tier_map[key]['nodes'].append(node_name)
            
            # Add to organized list
            organized.extend(app_tier_map.values())
        
        return organized
    
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
            
            if parsed_data:
                self.logger.debug(f"✓ Fetched metric: {metric_path} ({len(parsed_data)} data points)")
            else:
                self.logger.debug(f"⚠ No data for metric: {metric_path}")
            
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
    
    def get_jvm_metrics_for_node(self, app_name: str, tier_name: str, node_name: str,
                                 duration_mins: int = 5) -> Dict[str, List[Dict]]:
        """
        Get JVM-specific metrics for a single node
        
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
            'jvm_cpu_usage': f"{base_path}|Process CPU Usage %",
            'jvm_heap_used_pct': f"{base_path}|Memory|Heap|Used %",
            'jvm_heap_used_mb': f"{base_path}|Memory|Heap|Used (MB)",
            'jvm_heap_committed_mb': f"{base_path}|Memory|Heap|Committed (MB)",
            'jvm_heap_max_mb': f"{base_path}|Memory|Heap|Max Available (MB)",
            'jvm_gc_time_per_min': f"{base_path}|Garbage Collection|GC Time Spent Per Min (ms)",
            'jvm_gc_major_count': f"{base_path}|Garbage Collection|Major GCs",
            'jvm_gc_minor_count': f"{base_path}|Garbage Collection|Minor GCs",
        }
        
        self.logger.debug(f"→ Fetching JVM metrics: {app_name}/{tier_name}/{node_name}")
        return self.get_multiple_metrics(app_name, metric_paths, duration_mins)
    
    def get_transaction_metrics_for_tier(self, app_name: str, tier_name: str,
                                        duration_mins: int = 5) -> Dict[str, List[Dict]]:
        """
        Get business transaction metrics for a tier
        
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
            'exceptions_per_min': f"{base_path}|Exceptions per Minute",
            'slow_calls': f"{base_path}|Number of Slow Calls",
            'very_slow_calls': f"{base_path}|Number of Very Slow Calls",
            'stall_count': f"{base_path}|Stall Count",
            'http_error_codes_per_min': f"{base_path}|Infrastructure Errors per Minute"
        }
        
        self.logger.debug(f"→ Fetching transaction metrics: {app_name}/{tier_name}")
        return self.get_multiple_metrics(app_name, metric_paths, duration_mins)
    
    def get_dashboard_metrics(self, dashboard_config: List[Dict], 
                             duration_mins: int = 5) -> Dict[str, Dict]:
        """
        Collect metrics from dashboard configuration with multiple widgets
        
        Args:
            dashboard_config: List of widget configurations
            duration_mins: Duration in minutes
            
        Returns:
            Dictionary organized by widget and metrics
        """
        all_dashboard_data = {}
        
        self.logger.info("=" * 80)
        self.logger.info(f"Collecting Dashboard Metrics - {len(dashboard_config)} widgets")
        self.logger.info("=" * 80)
        
        for widget_idx, widget in enumerate(dashboard_config, 1):
            widget_name = widget.get('widget_name', f'Widget_{widget_idx}')
            app_name = widget.get('app_name')
            tier_name = widget.get('tier_name')
            metric_type = widget.get('metric_type', 'jvm')
            nodes = widget.get('nodes', [])
            
            self.logger.info(f"\n[{widget_idx}/{len(dashboard_config)}] Processing: {widget_name}")
            self.logger.info(f"  App: {app_name}, Tier: {tier_name}, Type: {metric_type}")
            
            widget_data = {
                'widget_name': widget_name,
                'app_name': app_name,
                'tier_name': tier_name,
                'metric_type': metric_type,
                'metrics': {}
            }
            
            try:
                if metric_type == 'jvm':
                    # Collect JVM metrics for specified nodes
                    if not nodes:
                        # Auto-discover nodes if not specified
                        discovered_nodes = self.get_nodes_for_tier(app_name, tier_name)
                        if discovered_nodes:
                            nodes = [node.get('name') for node in discovered_nodes]
                            self.logger.info(f"  Auto-discovered {len(nodes)} nodes")
                    
                    for node_name in nodes:
                        node_metrics = self.get_jvm_metrics_for_node(
                            app_name, tier_name, node_name, duration_mins
                        )
                        widget_data['metrics'][node_name] = node_metrics
                        
                        # Count data points
                        total_points = sum(len(values) for values in node_metrics.values())
                        self.logger.info(f"    ✓ {node_name}: {total_points} data points")
                
                elif metric_type == 'transaction':
                    # Collect transaction metrics for tier
                    tier_metrics = self.get_transaction_metrics_for_tier(
                        app_name, tier_name, duration_mins
                    )
                    widget_data['metrics']['tier_metrics'] = tier_metrics
                    
                    total_points = sum(len(values) for values in tier_metrics.values())
                    self.logger.info(f"    ✓ Transaction metrics: {total_points} data points")
                
                elif metric_type == 'combined':
                    # Collect both JVM and transaction metrics
                    # JVM metrics for nodes
                    if not nodes:
                        discovered_nodes = self.get_nodes_for_tier(app_name, tier_name)
                        if discovered_nodes:
                            nodes = [node.get('name') for node in discovered_nodes]
                    
                    jvm_data = {}
                    for node_name in nodes:
                        node_metrics = self.get_jvm_metrics_for_node(
                            app_name, tier_name, node_name, duration_mins
                        )
                        jvm_data[node_name] = node_metrics
                    
                    # Transaction metrics for tier
                    transaction_data = self.get_transaction_metrics_for_tier(
                        app_name, tier_name, duration_mins
                    )
                    
                    widget_data['metrics'] = {
                        'jvm': jvm_data,
                        'transaction': transaction_data
                    }
                    
                    jvm_points = sum(
                        sum(len(v) for v in node_metrics.values()) 
                        for node_metrics in jvm_data.values()
                    )
                    trans_points = sum(len(values) for values in transaction_data.values())
                    
                    self.logger.info(f"    ✓ JVM: {jvm_points} points, Transaction: {trans_points} points")
                
                all_dashboard_data[widget_name] = widget_data
                
            except Exception as e:
                self.logger.error(f"  ✗ Error processing widget {widget_name}: {e}")
                all_dashboard_data[widget_name] = {
                    'widget_name': widget_name,
                    'error': str(e)
                }
        
        self.logger.info("\n" + "=" * 80)
        self.logger.info(f"Dashboard Collection Complete - {len(all_dashboard_data)} widgets processed")
        self.logger.info("=" * 80)
        
        return all_dashboard_data