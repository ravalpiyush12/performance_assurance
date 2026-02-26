"""
AppDynamics Monitoring Orchestrator - Code 3
Coordinates metric collection with multi-threading per tier
"""
import threading
import time
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


class MonitoringOrchestrator:
    """Orchestrates monitoring collection with multi-threading"""
    
    def __init__(self, client, database, collectors, config):
        """
        Initialize orchestrator
        
        Args:
            client: AppDynamicsClient
            database: AppDynamicsDatabase
            collectors: MetricsCollectorManager
            config: AppDynamicsConfig
        """
        self.client = client
        self.db = database
        self.collectors = collectors
        self.config = config
        self.monitoring_sessions = {}
        self.session_lock = threading.Lock()
    
    def start_monitoring(self, run_id: str, lob_name: str, applications: List[str]) -> bool:
        """
        Start monitoring session
        
        Args:
            run_id: Unique run ID
            lob_name: LOB name
            applications: List of application names to monitor
            
        Returns:
            True if started successfully
        """
        print(f"[Orchestrator] Starting monitoring for Run ID: {run_id}", flush=True)
        
        # Get LOB config
        lob_config = self.db.get_lob_config(lob_name)
        if not lob_config:
            raise ValueError(f"LOB not found: {lob_name}")
        
        lob_id = lob_config['lob_id']
        
        # Create monitoring run in database
        run_data = {
            'run_id': run_id,
            'lob_id': lob_id,
            'lob_name': lob_name,
            'track': '',  # Can be passed as parameter
            'test_name': '',
            'interval_seconds': self.config.APPD_COLLECTION_INTERVAL_SECONDS,
            'applications': applications
        }
        
        self.db.create_monitoring_run(run_data)
        
        # Create session tracking
        with self.session_lock:
            self.monitoring_sessions[run_id] = {
                'status': 'RUNNING',
                'lob_name': lob_name,
                'applications': applications,
                'start_time': datetime.now(),
                'iterations': 0
            }
        
        return True
    
    def collect_metrics_once(self, run_id: str) -> Dict:
        """
        Collect metrics once for all active nodes in the run
        
        Args:
            run_id: Run ID
            
        Returns:
            Collection statistics
        """
        with self.session_lock:
            if run_id not in self.monitoring_sessions:
                raise ValueError(f"Monitoring session not found: {run_id}")
            
            session = self.monitoring_sessions[run_id]
            if session['status'] != 'RUNNING':
                raise ValueError(f"Session not running: {run_id}")
        
        lob_name = session['lob_name']
        applications = session['applications']
        
        print(f"[Orchestrator] Collecting metrics for Run ID: {run_id}", flush=True)
        
        stats = {
            'total_nodes': 0,
            'successful_nodes': 0,
            'failed_nodes': 0,
            'tiers_processed': 0
        }
        
        try:
            # Get all active nodes for this LOB
            all_nodes = self.db.get_active_nodes_for_lob(lob_name)
            
            # Filter by applications if specified
            if applications:
                all_nodes = [n for n in all_nodes if n['application_name'] in applications]
            
            stats['total_nodes'] = len(all_nodes)
            
            if not all_nodes:
                print(f"[Orchestrator] No active nodes found for {lob_name}", flush=True)
                return stats
            
            # Group nodes by tier for parallel processing
            nodes_by_tier = self._group_nodes_by_tier(all_nodes)
            stats['tiers_processed'] = len(nodes_by_tier)
            
            # Process each tier in parallel
            tier_results = []
            with ThreadPoolExecutor(max_workers=len(nodes_by_tier)) as executor:
                future_to_tier = {
                    executor.submit(self._collect_tier_metrics, run_id, tier_name, nodes): tier_name
                    for tier_name, nodes in nodes_by_tier.items()
                }
                
                for future in as_completed(future_to_tier):
                    tier_name = future_to_tier[future]
                    try:
                        result = future.result()
                        tier_results.append(result)
                        stats['successful_nodes'] += result['successful']
                        stats['failed_nodes'] += result['failed']
                    except Exception as e:
                        print(f"[Orchestrator] Tier {tier_name} failed: {e}", flush=True)
                        stats['failed_nodes'] += len(nodes_by_tier[tier_name])
            
            # Update database
            self.db.increment_collection_count(run_id, success=True)
            
            # Update session
            with self.session_lock:
                if run_id in self.monitoring_sessions:
                    self.monitoring_sessions[run_id]['iterations'] += 1
                    self.monitoring_sessions[run_id]['last_collection'] = datetime.now()
            
            print(f"[Orchestrator] Collection complete: {stats['successful_nodes']}/{stats['total_nodes']} nodes successful", flush=True)
            return stats
            
        except Exception as e:
            print(f"[Orchestrator] Collection failed: {e}", flush=True)
            self.db.increment_collection_count(run_id, success=False)
            raise
    
    def _group_nodes_by_tier(self, nodes: List[Dict]) -> Dict[str, List[Dict]]:
        """Group nodes by tier for parallel processing"""
        nodes_by_tier = {}
        for node in nodes:
            tier_key = f"{node['application_name']}_{node['tier_name']}"
            if tier_key not in nodes_by_tier:
                nodes_by_tier[tier_key] = []
            nodes_by_tier[tier_key].append(node)
        return nodes_by_tier
    
    def _collect_tier_metrics(self, run_id: str, tier_name: str, nodes: List[Dict]) -> Dict:
        """
        Collect metrics for all nodes in a tier using thread pool
        
        Args:
            run_id: Run ID
            tier_name: Tier name
            nodes: List of nodes in this tier
            
        Returns:
            Collection statistics for tier
        """
        print(f"[Orchestrator] Processing tier: {tier_name} ({len(nodes)} nodes)", flush=True)
        
        results = {
            'tier_name': tier_name,
            'successful': 0,
            'failed': 0
        }
        
        # Process nodes in parallel within tier
        max_workers = min(self.config.APPD_THREAD_POOL_SIZE_PER_TIER, len(nodes))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_node = {
                executor.submit(self._collect_node_metrics, run_id, node): node['node_name']
                for node in nodes
            }
            
            for future in as_completed(future_to_node):
                node_name = future_to_node[future]
                try:
                    success = future.result(timeout=self.config.APPD_THREAD_TIMEOUT_SECONDS)
                    if success:
                        results['successful'] += 1
                    else:
                        results['failed'] += 1
                except Exception as e:
                    print(f"[Orchestrator]   Node {node_name} failed: {e}", flush=True)
                    results['failed'] += 1
        
        print(f"[Orchestrator] Tier {tier_name} complete: {results['successful']}/{len(nodes)} successful", flush=True)
        return results
    
    def _collect_node_metrics(self, run_id: str, node: Dict) -> bool:
        """
        Collect all metrics for a single node
        
        Args:
            run_id: Run ID
            node: Node dictionary with metadata
            
        Returns:
            True if successful
        """
        try:
            # Get IDs from database
            lob_config = self.db.get_lob_config(node['lob_name'])
            lob_id = lob_config['lob_id']
            
            app_id = self.db.get_application_id(lob_id, node['application_name'])
            tier_id = self.db.get_tier_id(app_id, node['tier_name'])
            node_id = node['node_id']
            
            # Collect all metrics
            results = self.collectors.collect_all_metrics(
                run_id=run_id,
                node_id=node_id,
                tier_id=tier_id,
                app_id=app_id,
                app_name=node['application_name'],
                tier_name=node['tier_name'],
                node_name=node['node_name']
            )
            
            # Consider successful if at least one metric type succeeded
            success = any([results['server'], results['jvm'], results['application']])
            return success
            
        except Exception as e:
            print(f"[Orchestrator]   Error collecting metrics for {node['node_name']}: {e}", flush=True)
            return False
    
    def stop_monitoring(self, run_id: str) -> bool:
        """
        Stop monitoring session
        
        Args:
            run_id: Run ID
            
        Returns:
            True if stopped successfully
        """
        with self.session_lock:
            if run_id not in self.monitoring_sessions:
                raise ValueError(f"Monitoring session not found: {run_id}")
            
            self.monitoring_sessions[run_id]['status'] = 'STOPPED'
        
        self.db.update_monitoring_run_status(run_id, 'STOPPED')
        print(f"[Orchestrator] Monitoring stopped for Run ID: {run_id}", flush=True)
        return True
    
    def get_session_status(self, run_id: str) -> Dict:
        """Get monitoring session status"""
        with self.session_lock:
            if run_id not in self.monitoring_sessions:
                return {'status': 'NOT_FOUND'}
            return self.monitoring_sessions[run_id].copy()
    
    def get_all_sessions(self) -> List[Dict]:
        """Get all monitoring sessions"""
        with self.session_lock:
            return [
                {
                    'run_id': run_id,
                    **session
                }
                for run_id, session in self.monitoring_sessions.items()
            ]