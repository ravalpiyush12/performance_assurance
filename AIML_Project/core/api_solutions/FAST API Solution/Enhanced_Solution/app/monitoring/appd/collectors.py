"""
AppDynamics Metrics Collectors
Collects Server, JVM, and Application metrics
"""
from typing import Dict, Optional


class ServerMetricsCollector:
    """Collects server/hardware metrics: CPU, Memory, Network, Disk"""
    
    def __init__(self, client, config):
        self.client = client
        self.config = config
    
    def collect(self, app_name: str, tier_name: str, node_name: str) -> Dict:
        """
        Collect server metrics for a node
        
        Returns:
            Dictionary with CPU, Memory, Network, Disk metrics
        """
        try:
            metrics = self.client.get_server_metrics(
                app_name,
                tier_name,
                node_name,
                duration_minutes=5
            )
            
            print(f"[ServerCollector] {node_name}: CPU={metrics.get('cpu_busy_percent')}%, Mem={metrics.get('memory_used_percent')}%", flush=True)
            return metrics
            
        except Exception as e:
            print(f"[ServerCollector] Error collecting for {node_name}: {e}", flush=True)
            return {}


class JVMMetricsCollector:
    """Collects JVM metrics: Heap, GC, Threads, Exceptions"""
    
    def __init__(self, client, config):
        self.client = client
        self.config = config
    
    def collect(self, app_name: str, tier_name: str, node_name: str) -> Dict:
        """
        Collect JVM metrics for a node
        
        Returns:
            Dictionary with Heap, GC, Thread, Exception metrics
        """
        try:
            metrics = self.client.get_jvm_metrics(
                app_name,
                tier_name,
                node_name,
                duration_minutes=5
            )
            
            print(f"[JVMCollector] {node_name}: Heap={metrics.get('heap_used_percent')}%, GC={metrics.get('gc_time_ms')}ms", flush=True)
            return metrics
            
        except Exception as e:
            print(f"[JVMCollector] Error collecting for {node_name}: {e}", flush=True)
            return {}


class ApplicationMetricsCollector:
    """Collects application metrics: CPM, Response Time, Errors"""
    
    def __init__(self, client, config):
        self.client = client
        self.config = config
    
    def collect(self, app_name: str, tier_name: str, node_name: str) -> Dict:
        """
        Collect application metrics for a node
        
        Returns:
            Dictionary with CPM, Response Time, Error metrics
        """
        try:
            metrics = self.client.get_application_metrics(
                app_name,
                tier_name,
                node_name,
                duration_minutes=5
            )
            
            print(f"[AppCollector] {node_name}: CPM={metrics.get('calls_per_minute')}, RT={metrics.get('response_time_avg_ms')}ms", flush=True)
            return metrics
            
        except Exception as e:
            print(f"[AppCollector] Error collecting for {node_name}: {e}", flush=True)
            return {}


class MetricsCollectorManager:
    """Manages all collectors and orchestrates collection"""
    
    def __init__(self, client, database, config):
        self.server_collector = ServerMetricsCollector(client, config)
        self.jvm_collector = JVMMetricsCollector(client, config)
        self.app_collector = ApplicationMetricsCollector(client, config)
        self.db = database
        self.config = config
    
    def collect_all_metrics(
        self,
        run_id: str,
        node_id: int,
        tier_id: int,
        app_id: int,
        app_name: str,
        tier_name: str,
        node_name: str
    ) -> Dict:
        """
        Collect all metrics for a node and save to database
        
        Returns:
            Collection results summary
        """
        results = {
            'node_name': node_name,
            'server': False,
            'jvm': False,
            'application': False
        }
        
        # Collect Server Metrics
        if self.config.APPD_COLLECT_SERVER_METRICS:
            try:
                server_metrics = self.server_collector.collect(app_name, tier_name, node_name)
                if server_metrics:
                    self.db.insert_server_metrics(run_id, node_id, server_metrics)
                    results['server'] = True
            except Exception as e:
                print(f"[MetricsCollector] Server metrics failed for {node_name}: {e}", flush=True)
        
        # Collect JVM Metrics
        if self.config.APPD_COLLECT_JVM_METRICS:
            try:
                jvm_metrics = self.jvm_collector.collect(app_name, tier_name, node_name)
                if jvm_metrics:
                    self.db.insert_jvm_metrics(run_id, node_id, jvm_metrics)
                    results['jvm'] = True
            except Exception as e:
                print(f"[MetricsCollector] JVM metrics failed for {node_name}: {e}", flush=True)
        
        # Collect Application Metrics
        if self.config.APPD_COLLECT_APP_METRICS:
            try:
                app_metrics = self.app_collector.collect(app_name, tier_name, node_name)
                if app_metrics:
                    self.db.insert_application_metrics(run_id, node_id, tier_id, app_id, app_metrics)
                    results['application'] = True
            except Exception as e:
                print(f"[MetricsCollector] Application metrics failed for {node_name}: {e}", flush=True)
        
        return results