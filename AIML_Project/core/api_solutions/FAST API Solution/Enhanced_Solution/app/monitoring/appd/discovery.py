"""
AppDynamics Discovery Service - Code 1
Discovers applications, tiers, nodes and loads to database
Classifies nodes as active/inactive based on CPM threshold
"""
from typing import List, Dict, Optional
import time


class AppDynamicsDiscoveryService:
    """Discovery service for AppDynamics applications"""
    
    def __init__(self, client, database, config):
        """
        Initialize discovery service
        
        Args:
            client: AppDynamicsClient instance
            database: AppDynamicsDatabase instance
            config: AppDynamicsConfig instance
        """
        self.client = client
        self.db = database
        self.config = config
    
    def run_discovery_for_lob(self, lob_name: str) -> Dict:
        """
        Run discovery for a specific LOB
        
        Args:
            lob_name: LOB name to discover
            
        Returns:
            Discovery statistics
        """
        print(f"[Discovery] Starting for LOB: {lob_name}", flush=True)
        
        # Get LOB configuration
        lob_config = self.db.get_lob_config(lob_name)
        if not lob_config:
            raise ValueError(f"LOB not found: {lob_name}")
        
        lob_id = lob_config['lob_id']
        app_names = lob_config['application_names']
        
        if not app_names:
            raise ValueError(f"No applications configured for LOB: {lob_name}")
        
        # Create discovery log
        log_id = self.db.create_discovery_log(lob_id)
        
        stats = {
            'applications': 0,
            'tiers': 0,
            'nodes': 0,
            'active_nodes': 0
        }
        
        try:
            # Discover each application
            for app_name in app_names:
                print(f"[Discovery] Processing application: {app_name}", flush=True)
                app_stats = self._discover_application(lob_id, app_name)
                
                stats['applications'] += 1
                stats['tiers'] += app_stats['tiers']
                stats['nodes'] += app_stats['nodes']
                stats['active_nodes'] += app_stats['active_nodes']
            
            # Update LOB discovery time
            self.db.update_lob_discovery_time(lob_id)
            
            # Complete discovery log
            self.db.complete_discovery_log(log_id, stats, 'SUCCESS')
            
            print(f"[Discovery] Completed for LOB: {lob_name}", flush=True)
            print(f"[Discovery] Stats: {stats}", flush=True)
            
            return {
                'lob_name': lob_name,
                'log_id': log_id,
                'status': 'SUCCESS',
                'statistics': stats
            }
            
        except Exception as e:
            print(f"[Discovery] Failed for LOB {lob_name}: {e}", flush=True)
            self.db.complete_discovery_log(log_id, stats, 'FAILED', str(e))
            raise
    
    def _discover_application(self, lob_id: int, app_name: str) -> Dict:
        """Discover single application"""
        app_stats = {'tiers': 0, 'nodes': 0, 'active_nodes': 0}
        
        # Get application details from AppD
        app_details = self.client.get_application_by_name(app_name)
        if not app_details:
            print(f"[Discovery] Application not found in AppD: {app_name}", flush=True)
            return app_stats
        
        # Get tiers
        tiers = self.client.get_tiers(app_name)
        app_stats['tiers'] = len(tiers)
        
        # Count nodes
        total_nodes = 0
        active_nodes = 0
        
        for tier in tiers:
            tier_name = tier.get('name')
            nodes = self.client.get_nodes(app_name, tier_name)
            total_nodes += len(nodes)
            
            # Check CPM for each node to classify active/inactive
            for node in nodes:
                node_name = node.get('name')
                cpm = self.client.get_calls_per_minute(
                    app_name,
                    tier_name,
                    node_name,
                    self.config.APPD_DISCOVERY_LOOKBACK_MINUTES
                )
                
                if cpm >= self.config.APPD_ACTIVE_NODE_CPM_THRESHOLD:
                    active_nodes += 1
        
        app_stats['nodes'] = total_nodes
        app_stats['active_nodes'] = active_nodes
        
        # Save application to database
        app_data = {
            'name': app_name,
            'id': app_details.get('id'),
            'total_tiers': len(tiers),
            'total_nodes': total_nodes,
            'active_nodes': active_nodes,
            'inactive_nodes': total_nodes - active_nodes
        }
        
        app_id = self.db.upsert_application(lob_id, app_data)
        
        # Save tiers and nodes
        for tier in tiers:
            self._discover_tier(app_id, app_name, tier)
        
        return app_stats
    
    def _discover_tier(self, app_id: int, app_name: str, tier_data: Dict):
        """Discover single tier and its nodes"""
        tier_name = tier_data.get('name')
        
        # Get nodes for this tier
        nodes = self.client.get_nodes(app_name, tier_name)
        
        # Count active nodes
        active_count = 0
        for node in nodes:
            node_name = node.get('name')
            cpm = self.client.get_calls_per_minute(
                app_name,
                tier_name,
                node_name,
                self.config.APPD_DISCOVERY_LOOKBACK_MINUTES
            )
            
            if cpm >= self.config.APPD_ACTIVE_NODE_CPM_THRESHOLD:
                active_count += 1
        
        # Save tier to database
        tier_save_data = {
            'name': tier_name,
            'id': tier_data.get('id'),
            'type': tier_data.get('type'),
            'total_nodes': len(nodes),
            'active_nodes': active_count
        }
        
        tier_id = self.db.upsert_tier(app_id, tier_save_data)
        
        # Save nodes
        for node in nodes:
            self._discover_node(tier_id, app_id, app_name, tier_name, node)
    
    def _discover_node(self, tier_id: int, app_id: int, app_name: str, tier_name: str, node_data: Dict):
        """Discover single node and classify as active/inactive"""
        node_name = node_data.get('name')
        
        # Get CPM for this node
        cpm = self.client.get_calls_per_minute(
            app_name,
            tier_name,
            node_name,
            self.config.APPD_DISCOVERY_LOOKBACK_MINUTES
        )
        
        # Get node details
        node_details = self.client.get_node_details(app_name, node_name) or {}
        
        # Save node to database (will be classified based on CPM)
        node_save_data = {
            'name': node_name,
            'id': node_data.get('id'),
            'machine_name': node_details.get('machineName'),
            'ip_address': node_details.get('ipAddresses', [None])[0] if node_details.get('ipAddresses') else None,
            'calls_per_minute': cpm,
            'threshold': self.config.APPD_ACTIVE_NODE_CPM_THRESHOLD,
            'type': node_data.get('type') or node_details.get('nodeType'),
            'agent_version': node_details.get('agentVersion')
        }
        
        self.db.upsert_node(tier_id, app_id, node_save_data)
        
        status = "ACTIVE" if cpm >= self.config.APPD_ACTIVE_NODE_CPM_THRESHOLD else "INACTIVE"
        print(f"[Discovery]   Node: {node_name} - CPM: {cpm:.2f} - Status: {status}", flush=True)
    
    def run_discovery_for_all_lobs(self) -> List[Dict]:
        """Run discovery for all active LOBs"""
        lobs = self.db.get_all_active_lobs()
        results = []
        
        for lob in lobs:
            try:
                result = self.run_discovery_for_lob(lob['lob_name'])
                results.append(result)
            except Exception as e:
                results.append({
                    'lob_name': lob['lob_name'],
                    'status': 'FAILED',
                    'error': str(e)
                })
        
        return results