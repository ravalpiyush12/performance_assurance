"""
AppDynamics Data Fetcher using REST API - Auto Dashboard Discovery
Fixed for Custom Dashboard Export and PieWidget support
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
        Get dashboard details using CustomDashboardImportExportServlet
        
        Args:
            dashboard_id: Dashboard ID
            
        Returns:
            Dashboard configuration or None
        """
        # Use the correct URL for custom dashboard export
        url = f"{self.controller_url}/controller/CustomDashboardImportExportServlet"
        
        params = {
            'dashboardId': dashboard_id
        }
        
        try:
            response = self.session.get(url, params=params, verify=False, timeout=30)
            response.raise_for_status()
            
            dashboard = response.json()
            dashboard_name = dashboard.get('name', 'Unknown Dashboard')
            
            self.logger.info(f"✓ Fetched dashboard: {dashboard_name} (ID: {dashboard_id})")
            self.logger.info(f"  Dashboard Type: {dashboard.get('dashboardFormatVersion', 'Unknown')}")
            
            return dashboard
            
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"✗ HTTP error fetching dashboard {dashboard_id}: {e}")
            self.logger.error(f"  Response: {e.response.text if hasattr(e, 'response') else 'N/A'}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"✗ JSON decode error: {e}")
            return None
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
        
        # Different dashboard formats use different structures
        widgets = []
        
        # Try different possible widget locations in the JSON structure
        if 'widgetTemplates' in dashboard:
            widgets = dashboard.get('widgetTemplates', [])
        elif 'widgets' in dashboard:
            widgets = dashboard.get('widgets', [])
        elif 'rows' in dashboard:
            # Some dashboards organize widgets in rows
            for row in dashboard.get('rows', []):
                widgets.extend(row.get('widgets', []))
        
        self.logger.info("=" * 80)
        self.logger.info(f"Parsing Dashboard: {dashboard_name} (ID: {dashboard_id})")
        self.logger.info(f"Total Widgets Found: {len(widgets)}")
        self.logger.info("=" * 80)
        
        widget_configs = []
        
        for idx, widget in enumerate(widgets, 1):
            widget_config = self._parse_widget(widget, idx, dashboard_name)
            if widget_config:
                widget_configs.append(widget_config)
                self.logger.info(f"  [{idx}] ✓ {widget_config['widget_name']} (Type: {widget_config.get('widget_type', 'Unknown')})")
            else:
                widget_type = widget.get('type', widget.get('widgetType', 'UNKNOWN'))
                self.logger.warning(f"  [{idx}] ⚠ Skipped widget (Type: {widget_type})")
        
        self.logger.info("=" * 80)
        self.logger.info(f"Successfully parsed {len(widget_configs)} widgets")
        self.logger.info("=" * 80)
        
        return widget_configs
    
    def _parse_widget(self, widget: Dict, widget_idx: int, dashboard_name: str) -> Optional[Dict]:
        """
        Parse individual widget and extract metric configuration
        Supports: PieWidget, MetricLabelWidget, TimeSeriesWidget, etc.
        
        Args:
            widget: Widget data from dashboard
            widget_idx: Widget index
            dashboard_name: Dashboard name
            
        Returns:
            Widget configuration or None
        """
        # Get widget type from different possible fields
        widget_type = widget.get('type') or widget.get('widgetType') or 'UNKNOWN'
        widget_name = widget.get('title') or widget.get('name') or f'Widget_{widget_idx}'
        
        self.logger.debug(f"\nParsing Widget {widget_idx}:")
        self.logger.debug(f"  Name: {widget_name}")
        self.logger.debug(f"  Type: {widget_type}")
        
        # Initialize config
        config = {
            'widget_name': f"{dashboard_name} - {widget_name}",
            'widget_type': widget_type,
            'widget_index': widget_idx,
            'apps_tiers_nodes': []
        }
        
        # Different parsing based on widget type
        if widget_type == 'PieWidget':
            metric_info = self._parse_pie_widget(widget)
            if metric_info:
                config['apps_tiers_nodes'].extend(metric_info)
        
        elif widget_type == 'MetricLabelWidget':
            metric_info = self._parse_metric_label_widget(widget)
            if metric_info:
                config['apps_tiers_nodes'].extend(metric_info)
        
        elif widget_type == 'TimeSeriesWidget':
            metric_info = self._parse_timeseries_widget(widget)
            if metric_info:
                config['apps_tiers_nodes'].extend(metric_info)
        
        elif widget_type == 'HealthListWidget':
            metric_info = self._parse_health_list_widget(widget)
            if metric_info:
                config['apps_tiers_nodes'].extend(metric_info)
        
        else:
            # Generic parsing for unknown widget types
            metric_info = self._parse_generic_widget(widget)
            if metric_info:
                config['apps_tiers_nodes'].extend(metric_info)
        
        # Determine metric type based on collected information
        if config['apps_tiers_nodes']:
            config['metric_type'] = self._determine_metric_type(config, widget_type)
            return config
        
        return None
    
    def _parse_pie_widget(self, widget: Dict) -> List[Dict]:
        """
        Parse PieWidget to extract metric configurations
        
        Args:
            widget: PieWidget data
            
        Returns:
            List of metric information dictionaries
        """
        metric_infos = []
        
        # PieWidget structure usually has dataSeriesTemplates or series
        data_series = widget.get('dataSeriesTemplates', []) or widget.get('series', [])
        
        for series in data_series:
            # Extract metric expression or metric path
            metric_expression = series.get('metricExpression', '')
            metric_path = series.get('metricPath', '')
            
            if not metric_expression and not metric_path:
                continue
            
            # Get application name
            app_name = series.get('applicationName', '') or series.get('appName', '')
            
            # Parse the metric expression/path
            metric_info = self._parse_metric_expression(
                metric_expression or metric_path,
                app_name
            )
            
            if metric_info:
                metric_infos.append(metric_info)
        
        return metric_infos
    
    def _parse_metric_label_widget(self, widget: Dict) -> List[Dict]:
        """Parse MetricLabelWidget"""
        metric_infos = []
        
        data_series = widget.get('dataSeriesTemplates', [])
        
        for series in data_series:
            metric_path = series.get('metricPath', '')
            app_name = series.get('applicationName', '')
            
            if metric_path and app_name:
                metric_info = self._parse_metric_expression(metric_path, app_name)
                if metric_info:
                    metric_infos.append(metric_info)
        
        return metric_infos
    
    def _parse_timeseries_widget(self, widget: Dict) -> List[Dict]:
        """Parse TimeSeriesWidget"""
        metric_infos = []
        
        data_series = widget.get('dataSeriesTemplates', [])
        
        for series in data_series:
            metric_path = series.get('metricPath', '')
            app_name = series.get('applicationName', '')
            
            if metric_path and app_name:
                metric_info = self._parse_metric_expression(metric_path, app_name)
                if metric_info:
                    metric_infos.append(metric_info)
        
        return metric_infos
    
    def _parse_health_list_widget(self, widget: Dict) -> List[Dict]:
        """Parse HealthListWidget"""
        metric_infos = []
        
        # Health list widgets may reference entities directly
        entity_refs = widget.get('entityReferences', [])
        
        for entity_ref in entity_refs:
            entity_type = entity_ref.get('entityType', '')
            app_name = entity_ref.get('applicationName', '')
            tier_name = entity_ref.get('tierName', '')
            node_name = entity_ref.get('nodeName', '')
            
            if app_name:
                metric_info = {
                    'app_name': app_name,
                    'tier_name': tier_name,
                    'node_name': node_name,
                    'metric_path': '',
                    'metric_category': 'health'
                }
                metric_infos.append(metric_info)
        
        return metric_infos
    
    def _parse_generic_widget(self, widget: Dict) -> List[Dict]:
        """Generic parser for unknown widget types"""
        metric_infos = []
        
        # Try to find dataSeriesTemplates, dataFetchInfos, or similar structures
        possible_data_fields = [
            'dataSeriesTemplates',
            'dataFetchInfos',
            'series',
            'metrics',
            'dataSources'
        ]
        
        for field in possible_data_fields:
            if field in widget:
                data_items = widget[field]
                if isinstance(data_items, list):
                    for item in data_items:
                        metric_path = item.get('metricPath', '') or item.get('metricExpression', '')
                        app_name = item.get('applicationName', '') or item.get('appName', '')
                        
                        if metric_path and app_name:
                            metric_info = self._parse_metric_expression(metric_path, app_name)
                            if metric_info:
                                metric_infos.append(metric_info)
        
        return metric_infos
    
    def _parse_metric_expression(self, metric_expression: str, app_name: str) -> Optional[Dict]:
        """
        Parse metric expression/path to extract tier, node, and category information
        
        Args:
            metric_expression: Metric path or expression
            app_name: Application name
            
        Returns:
            Dictionary with parsed metric information or None
        """
        if not metric_expression or not app_name:
            return None
        
        # Clean up metric expression
        metric_path = metric_expression.strip()
        
        # Parse metric path components
        parts = metric_path.split('|')
        
        tier_name = None
        node_name = None
        metric_category = None
        
        try:
            # Pattern 1: Application Infrastructure Performance|Tier|Individual Nodes|Node|...
            if 'Application Infrastructure Performance' in metric_path:
                if len(parts) >= 2:
                    tier_name = parts[1].strip()
                
                if 'Individual Nodes' in metric_path and len(parts) >= 4:
                    node_name = parts[3].strip()
                
                # Determine category from metric path
                if 'JVM' in metric_path:
                    if 'Memory' in metric_path:
                        metric_category = 'jvm_memory'
                    elif 'Garbage Collection' in metric_path or 'GC' in metric_path:
                        metric_category = 'jvm_gc'
                    elif 'CPU' in metric_path:
                        metric_category = 'jvm_cpu'
                    else:
                        metric_category = 'jvm'
                
                elif 'Hardware Resources' in metric_path:
                    if 'CPU' in metric_path:
                        metric_category = 'hardware_cpu'
                    elif 'Memory' in metric_path:
                        metric_category = 'hardware_memory'
                    else:
                        metric_category = 'hardware'
            
            # Pattern 2: Overall Application Performance|Tier|...
            elif 'Overall Application Performance' in metric_path:
                if len(parts) >= 2:
                    tier_name = parts[1].strip()
                
                # Determine transaction metric type
                if 'Calls per Minute' in metric_path:
                    metric_category = 'transaction_throughput'
                elif 'Response Time' in metric_path:
                    metric_category = 'transaction_response'
                elif 'Errors' in metric_path:
                    metric_category = 'transaction_errors'
                elif 'Exceptions' in metric_path:
                    metric_category = 'transaction_exceptions'
                elif 'Stall' in metric_path:
                    metric_category = 'transaction_stall'
                else:
                    metric_category = 'transaction'
            
            # Pattern 3: Business Transaction Performance|Tier|BT Name|...
            elif 'Business Transaction Performance' in metric_path:
                if len(parts) >= 2:
                    tier_name = parts[1].strip()
                metric_category = 'business_transaction'
            
            # Pattern 4: End User Experience|...
            elif 'End User Experience' in metric_path:
                metric_category = 'end_user'
            
            # Default category
            if not metric_category:
                metric_category = 'custom'
            
            return {
                'app_name': app_name,
                'tier_name': tier_name,
                'node_name': node_name,
                'metric_path': metric_path,
                'metric_category': metric_category,
                'metric_expression': metric_expression
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing metric expression '{metric_expression}': {e}")
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
        has_nodes = False
        
        for metric_info in config['apps_tiers_nodes']:
            category = metric_info.get('metric_category', '')
            
            if category:
                # Simplify categories for grouping
                if 'jvm' in category or 'hardware' in category:
                    categories.add('jvm')
                elif 'transaction' in category:
                    categories.add('transaction')
                else:
                    categories.add('custom')
            
            if metric_info.get('node_name'):
                has_nodes = True
        
        # Determine overall type
        if 'jvm' in categories and 'transaction' in categories:
            return 'combined'
        elif 'jvm' in categories:
            return 'jvm'
        elif 'transaction' in categories:
            return 'transaction'
        else:
            return 'custom'
    
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
                self.logger.debug(f"✓ Fetched metric: {metric_path[-50:]} ({len(parsed_data)} data points)")
            
            return parsed_data
            
        except requests.exceptions.HTTPError as e:
            self.logger.warning(f"⚠ HTTP error fetching metric: {e}")
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
                
                if not app_name:
                    continue
                
                # Use app_name as key if no tier
                key = (app_name, tier_name if tier_name else 'ALL_TIERS')
                
                if key not in app_tier_map:
                    app_tier_map[key] = {
                        'widget_name': widget_name,
                        'app_name': app_name,
                        'tier_name': tier_name if tier_name else None,
                        'metric_type': metric_type,
                        'nodes': [],
                        'metric_paths': []
                    }
                
                # Add node if specified
                if node_name and node_name not in app_tier_map[key]['nodes']:
                    app_tier_map[key]['nodes'].append(node_name)
                
                # Store metric path for custom collection
                metric_path = metric_info.get('metric_path', '')
                if metric_path and metric_path not in app_tier_map[key]['metric_paths']:
                    app_tier_map[key]['metric_paths'].append(metric_path)
            
            # Add to organized list
            organized.extend(app_tier_map.values())
        
        return organized
    
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
            metric_paths = widget.get('metric_paths', [])
            
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
                    if not nodes and tier_name:
                        # Auto-discover nodes if not specified and tier exists
                        discovered_nodes = self.get_nodes_for_tier(app_name, tier_name)
                        if discovered_nodes:
                            nodes = [node.get('name') for node in discovered_nodes]
                            self.logger.info(f"  Auto-discovered {len(nodes)} nodes")
                    
                    if nodes and tier_name:
                        for node_name in nodes:
                            node_metrics = self.get_jvm_metrics_for_node(
                                app_name, tier_name, node_name, duration_mins
                            )
                            widget_data['metrics'][node_name] = node_metrics
                            
                            # Count data points
                            total_points = sum(len(values) for values in node_metrics.values())
                            self.logger.info(f"    ✓ {node_name}: {total_points} data points")
                    elif metric_paths:
                        # Use direct metric paths
                        custom_metrics = {}
                        for idx, metric_path in enumerate(metric_paths):
                            data = self.get_metric_data(app_name, metric_path, duration_mins)
                            if data:
                                custom_metrics[f'metric_{idx}'] = data
                        widget_data['metrics']['custom_metrics'] = custom_metrics
                        total_points = sum(len(v) for v in custom_metrics.values())
                        self.logger.info(f"    ✓ Custom metrics: {total_points} data points")
                
                elif metric_type == 'transaction':
                    # Collect transaction metrics for tier
                    if tier_name:
                        tier_metrics = self.get_transaction_metrics_for_tier(
                            app_name, tier_name, duration_mins
                        )
                        widget_data['metrics']['tier_metrics'] = tier_metrics
                        
                        total_points = sum(len(values) for values in tier_metrics.values())
                        self.logger.info(f"    ✓ Transaction metrics: {total_points} data points")
                    elif metric_paths:
                        # Use direct metric paths
                        custom_metrics = {}
                        for idx, metric_path in enumerate(metric_paths):
                            data = self.get_metric_data(app_name, metric_path, duration_mins)
                            if data:
                                custom_metrics[f'metric_{idx}'] = data
                        widget_data['metrics']['custom_metrics'] = custom_metrics
                        total_points = sum(len(v) for v in custom_metrics.values())
                        self.logger.info(f"    ✓ Custom metrics: {total_points} data points")
                
                elif metric_type == 'combined':
                    # Collect both JVM and transaction metrics
                    if tier_name:
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
                
                elif metric_type == 'custom':
                    # Use direct metric paths from widget
                    if metric_paths:
                        custom_metrics = {}
                        for idx, metric_path in enumerate(metric_paths):
                            data = self.get_metric_data(app_name, metric_path, duration_mins)
                            if data:
                                custom_metrics[f'metric_{idx}'] = data
                        
                        widget_data['metrics']['custom_metrics'] = custom_metrics
                        total_points = sum(len(v) for v in custom_metrics.values())
                        self.logger.info(f"    ✓ Custom metrics: {total_points} data points")
                
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