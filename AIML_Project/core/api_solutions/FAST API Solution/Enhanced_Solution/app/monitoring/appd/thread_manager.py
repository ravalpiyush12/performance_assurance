"""
Thread Manager for AppDynamics Monitoring
Manages multi-threaded metric collection per tier
"""
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from typing import List, Dict, Callable, Any
import time


class ThreadPoolManager:
    """
    Manages thread pools for parallel metric collection
    Creates separate thread pool for each tier
    """
    
    def __init__(self, threads_per_tier: int = 5, timeout_seconds: int = 300):
        """
        Initialize thread pool manager
        
        Args:
            threads_per_tier: Number of threads per tier (default: 5)
            timeout_seconds: Timeout for each thread (default: 300)
        """
        self.threads_per_tier = threads_per_tier
        self.timeout_seconds = timeout_seconds
        self.active_pools = {}
        self.lock = threading.Lock()
    
    def execute_tier_collection(
        self,
        tier_name: str,
        nodes: List[Dict],
        collection_func: Callable,
        **kwargs
    ) -> Dict:
        """
        Execute metric collection for all nodes in a tier using thread pool
        
        Args:
            tier_name: Name of the tier
            nodes: List of node dictionaries
            collection_func: Function to call for each node
            **kwargs: Additional arguments to pass to collection_func
            
        Returns:
            Dictionary with results and statistics
        """
        if not nodes:
            return {
                'tier_name': tier_name,
                'total_nodes': 0,
                'successful': 0,
                'failed': 0,
                'results': []
            }
        
        results = {
            'tier_name': tier_name,
            'total_nodes': len(nodes),
            'successful': 0,
            'failed': 0,
            'results': [],
            'errors': []
        }
        
        # Determine optimal thread count
        max_workers = min(self.threads_per_tier, len(nodes))
        
        print(f"[ThreadManager] Processing tier: {tier_name} with {max_workers} threads for {len(nodes)} nodes", flush=True)
        
        # Execute in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_node = {
                executor.submit(
                    self._safe_execute,
                    collection_func,
                    node,
                    **kwargs
                ): node
                for node in nodes
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_node):
                node = future_to_node[future]
                node_name = node.get('node_name', 'Unknown')
                
                try:
                    result = future.result(timeout=self.timeout_seconds)
                    
                    if result['success']:
                        results['successful'] += 1
                        results['results'].append({
                            'node_name': node_name,
                            'success': True,
                            'data': result.get('data')
                        })
                    else:
                        results['failed'] += 1
                        results['errors'].append({
                            'node_name': node_name,
                            'error': result.get('error', 'Unknown error')
                        })
                        
                except TimeoutError:
                    results['failed'] += 1
                    results['errors'].append({
                        'node_name': node_name,
                        'error': f'Timeout after {self.timeout_seconds} seconds'
                    })
                    print(f"[ThreadManager]   Node {node_name} timed out", flush=True)
                    
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({
                        'node_name': node_name,
                        'error': str(e)
                    })
                    print(f"[ThreadManager]   Node {node_name} failed: {e}", flush=True)
        
        print(f"[ThreadManager] Tier {tier_name} complete: {results['successful']}/{results['total_nodes']} successful", flush=True)
        return results
    
    def _safe_execute(self, func: Callable, node: Dict, **kwargs) -> Dict:
        """
        Safely execute collection function with error handling
        
        Args:
            func: Function to execute
            node: Node dictionary
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with success status and data/error
        """
        try:
            data = func(node, **kwargs)
            return {
                'success': True,
                'data': data
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def execute_parallel_tiers(
        self,
        tiers_data: Dict[str, List[Dict]],
        collection_func: Callable,
        **kwargs
    ) -> Dict:
        """
        Execute metric collection for multiple tiers in parallel
        
        Args:
            tiers_data: Dictionary mapping tier names to node lists
            collection_func: Function to call for each node
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with aggregated results
        """
        if not tiers_data:
            return {
                'total_tiers': 0,
                'total_nodes': 0,
                'successful_nodes': 0,
                'failed_nodes': 0,
                'tier_results': []
            }
        
        aggregated = {
            'total_tiers': len(tiers_data),
            'total_nodes': sum(len(nodes) for nodes in tiers_data.values()),
            'successful_nodes': 0,
            'failed_nodes': 0,
            'tier_results': []
        }
        
        print(f"[ThreadManager] Processing {len(tiers_data)} tiers in parallel", flush=True)
        
        # Execute each tier in parallel
        with ThreadPoolExecutor(max_workers=len(tiers_data)) as executor:
            future_to_tier = {
                executor.submit(
                    self.execute_tier_collection,
                    tier_name,
                    nodes,
                    collection_func,
                    **kwargs
                ): tier_name
                for tier_name, nodes in tiers_data.items()
            }
            
            for future in as_completed(future_to_tier):
                tier_name = future_to_tier[future]
                try:
                    result = future.result()
                    aggregated['tier_results'].append(result)
                    aggregated['successful_nodes'] += result['successful']
                    aggregated['failed_nodes'] += result['failed']
                except Exception as e:
                    print(f"[ThreadManager] Tier {tier_name} failed completely: {e}", flush=True)
                    aggregated['failed_nodes'] += len(tiers_data[tier_name])
                    aggregated['tier_results'].append({
                        'tier_name': tier_name,
                        'total_nodes': len(tiers_data[tier_name]),
                        'successful': 0,
                        'failed': len(tiers_data[tier_name]),
                        'errors': [{'error': str(e)}]
                    })
        
        print(f"[ThreadManager] All tiers complete: {aggregated['successful_nodes']}/{aggregated['total_nodes']} nodes successful", flush=True)
        return aggregated


class NodeCollectionWorker:
    """
    Worker class for collecting metrics from a single node
    Used by ThreadPoolManager
    """
    
    def __init__(self, client, database, collectors):
        """
        Initialize worker
        
        Args:
            client: AppDynamics client
            database: Database instance
            collectors: Metrics collectors
        """
        self.client = client
        self.db = database
        self.collectors = collectors
    
    def collect_node_metrics(
        self,
        node: Dict,
        run_id: str,
        collect_server: bool = True,
        collect_jvm: bool = True,
        collect_app: bool = True
    ) -> Dict:
        """
        Collect all metrics for a single node
        
        Args:
            node: Node dictionary with metadata
            run_id: Run ID
            collect_server: Whether to collect server metrics
            collect_jvm: Whether to collect JVM metrics
            collect_app: Whether to collect application metrics
            
        Returns:
            Dictionary with collection results
        """
        node_name = node.get('node_name')
        app_name = node.get('application_name')
        tier_name = node.get('tier_name')
        
        results = {
            'node_name': node_name,
            'server': False,
            'jvm': False,
            'application': False,
            'errors': []
        }
        
        try:
            # Get IDs
            lob_config = self.db.get_lob_config(node['lob_name'])
            lob_id = lob_config['lob_id']
            app_id = self.db.get_application_id(lob_id, app_name)
            tier_id = self.db.get_tier_id(app_id, tier_name)
            node_id = node['node_id']
            
            # Collect Server Metrics
            if collect_server:
                try:
                    server_metrics = self.client.get_server_metrics(
                        app_name, tier_name, node_name, duration_minutes=5
                    )
                    if server_metrics:
                        self.db.insert_server_metrics(run_id, node_id, server_metrics)
                        results['server'] = True
                except Exception as e:
                    results['errors'].append(f"Server metrics: {str(e)}")
            
            # Collect JVM Metrics
            if collect_jvm:
                try:
                    jvm_metrics = self.client.get_jvm_metrics(
                        app_name, tier_name, node_name, duration_minutes=5
                    )
                    if jvm_metrics:
                        self.db.insert_jvm_metrics(run_id, node_id, jvm_metrics)
                        results['jvm'] = True
                except Exception as e:
                    results['errors'].append(f"JVM metrics: {str(e)}")
            
            # Collect Application Metrics
            if collect_app:
                try:
                    app_metrics = self.client.get_application_metrics(
                        app_name, tier_name, node_name, duration_minutes=5
                    )
                    if app_metrics:
                        self.db.insert_application_metrics(
                            run_id, node_id, tier_id, app_id, app_metrics
                        )
                        results['application'] = True
                except Exception as e:
                    results['errors'].append(f"App metrics: {str(e)}")
            
            return results
            
        except Exception as e:
            results['errors'].append(f"Collection failed: {str(e)}")
            return results


# Example Usage
"""
# Initialize thread manager
thread_manager = ThreadPoolManager(threads_per_tier=5, timeout_seconds=300)

# Group nodes by tier
nodes_by_tier = {
    'RetailWeb_WebTier': [node1, node2, node3],
    'RetailWeb_APITier': [node4, node5],
    'RetailAPI_ServiceTier': [node6, node7, node8, node9]
}

# Create worker
worker = NodeCollectionWorker(client, database, collectors)

# Execute collection for all tiers in parallel
results = thread_manager.execute_parallel_tiers(
    tiers_data=nodes_by_tier,
    collection_func=worker.collect_node_metrics,
    run_id='RUN_001',
    collect_server=True,
    collect_jvm=True,
    collect_app=True
)

# Results contain:
# - total_tiers: 3
# - total_nodes: 9
# - successful_nodes: 8
# - failed_nodes: 1
# - tier_results: [detailed results per tier]
"""