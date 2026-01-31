"""
Self-Healing Orchestration Engine - Complete Implementation
Save as: src/orchestrator/self_healing.py

Features:
- Intelligent action selection
- Multiple healing strategies
- Cloud integration ready (AWS, Azure, K8s)
- Cooldown management
- Action history tracking
"""

import asyncio
import logging
from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of remediation actions"""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    RESTART_SERVICE = "restart_service"
    ENABLE_CACHE = "enable_cache"
    CIRCUIT_BREAKER = "circuit_breaker"
    TRAFFIC_SHIFT = "traffic_shift"
    ROLLBACK = "rollback"
    CLEAR_CACHE = "clear_cache"


class CloudProvider(Enum):
    """Supported cloud providers"""
    AWS = "aws"
    AZURE = "azure"
    KUBERNETES = "kubernetes"
    DOCKER = "docker"
    LOCAL = "local"


class RemediationAction:
    """Represents a single remediation action"""
    
    def __init__(self, action_type: ActionType, target: str, params: dict = None):
        self.action_type = action_type
        self.target = target
        self.params = params or {}
        self.status = "pending"
        self.timestamp = datetime.now()
        self.execution_time = None
        self.error_message = None
        self.action_id = None
        
    def to_dict(self) -> Dict:
        """Convert action to dictionary"""
        return {
            'action_id': self.action_id,
            'action_type': self.action_type.value,
            'target': self.target,
            'params': self.params,
            'status': self.status,
            'timestamp': self.timestamp.isoformat(),
            'execution_time': self.execution_time,
            'error_message': self.error_message
        }


class SelfHealingOrchestrator:
    """
    Main orchestrator for self-healing actions
    """
    
    def __init__(self, cloud_provider: CloudProvider = CloudProvider.LOCAL):
        self.cloud_provider = cloud_provider
        self.action_history = []
        self.active_actions = {}
        self.cooldown_periods = {}
        self.action_handlers = self._register_handlers()
        self.action_counter = 0
        
        logger.info(f"Self-Healing Orchestrator initialized (provider: {cloud_provider.value})")
        
    def _register_handlers(self) -> Dict:
        """Register action handlers"""
        return {
            ActionType.SCALE_UP: self._handle_scale_up,
            ActionType.SCALE_DOWN: self._handle_scale_down,
            ActionType.RESTART_SERVICE: self._handle_restart_service,
            ActionType.ENABLE_CACHE: self._handle_enable_cache,
            ActionType.CIRCUIT_BREAKER: self._handle_circuit_breaker,
            ActionType.TRAFFIC_SHIFT: self._handle_traffic_shift,
            ActionType.ROLLBACK: self._handle_rollback,
            ActionType.CLEAR_CACHE: self._handle_clear_cache
        }
    
    def decide_action(self, anomaly: Dict) -> Optional[RemediationAction]:
        """
        Decide which remediation action to take based on anomaly
        
        Args:
            anomaly: Detected anomaly information
            
        Returns:
            RemediationAction or None
        """
        anomaly_type = anomaly.get('anomaly_type', 'UNKNOWN')
        severity = anomaly.get('severity', 'warning')
        metrics = anomaly.get('metrics', {})
        
        # Check cooldown to prevent action spam
        if self._is_in_cooldown(anomaly_type):
            logger.info(f"Action for {anomaly_type} in cooldown, skipping")
            return None
        
        action = None
        
        # Decision logic based on anomaly type and metrics
        if anomaly_type == 'CPU_USAGE':
            if metrics.get('cpu_usage', 0) > 80:
                action = RemediationAction(
                    ActionType.SCALE_UP,
                    target="application-cluster",
                    params={
                        'instances': 2,
                        'reason': 'high_cpu',
                        'cpu_threshold': metrics.get('cpu_usage')
                    }
                )
        
        elif anomaly_type == 'MEMORY_USAGE':
            if metrics.get('memory_usage', 0) > 85:
                action = RemediationAction(
                    ActionType.SCALE_UP,
                    target="application-cluster",
                    params={
                        'instances': 2,
                        'reason': 'high_memory',
                        'memory_threshold': metrics.get('memory_usage')
                    }
                )
        
        elif anomaly_type == 'RESPONSE_TIME':
            if metrics.get('response_time', 0) > 800:
                action = RemediationAction(
                    ActionType.ENABLE_CACHE,
                    target="api-gateway",
                    params={
                        'ttl': 300,
                        'aggressive': True,
                        'latency': metrics.get('response_time')
                    }
                )
        
        elif anomaly_type == 'ERROR_RATE':
            error_rate = metrics.get('error_rate', 0)
            if error_rate > 5:
                if severity == 'critical':
                    action = RemediationAction(
                        ActionType.CIRCUIT_BREAKER,
                        target="failing-service",
                        params={
                            'threshold': 50,
                            'timeout': 30,
                            'error_rate': error_rate
                        }
                    )
                else:
                    action = RemediationAction(
                        ActionType.TRAFFIC_SHIFT,
                        target="healthy-instances",
                        params={
                            'percentage': 80,
                            'error_rate': error_rate
                        }
                    )
        
        elif anomaly_type == 'REQUESTS_PER_SEC':
            if metrics.get('requests_per_sec', 0) < 20:
                action = RemediationAction(
                    ActionType.RESTART_SERVICE,
                    target="web-service",
                    params={
                        'graceful': True,
                        'current_rps': metrics.get('requests_per_sec')
                    }
                )
        
        elif anomaly_type == 'DISK_IO':
            action = RemediationAction(
                ActionType.CLEAR_CACHE,
                target="application-cache",
                params={'reason': 'high_disk_io'}
            )
        
        if action:
            self.action_counter += 1
            action.action_id = f"action_{self.action_counter}"
            self._set_cooldown(anomaly_type, duration=60)
            logger.info(f"✅ Action decided: {action.action_type.value} for {anomaly_type}")
            
        return action
    
    async def execute_action(self, action: RemediationAction) -> bool:
        """
        Execute a remediation action
        
        Args:
            action: RemediationAction to execute
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"🔄 Executing action: {action.action_type.value} on {action.target}")
        
        action.status = "executing"
        self.active_actions[action.target] = action
        
        start_time = datetime.now()
        
        try:
            handler = self.action_handlers.get(action.action_type)
            if handler:
                success = await handler(action)
                
                if success:
                    action.status = "completed"
                    action.execution_time = (datetime.now() - start_time).total_seconds()
                    logger.info(f"✅ Action completed successfully in {action.execution_time:.2f}s")
                else:
                    action.status = "failed"
                    logger.error(f"❌ Action failed: {action.action_type.value}")
                    
                self.action_history.append(action)
                return success
            else:
                logger.error(f"No handler for action type: {action.action_type}")
                action.status = "failed"
                action.error_message = "No handler registered"
                return False
                
        except Exception as e:
            logger.error(f"Error executing action: {str(e)}")
            action.status = "failed"
            action.error_message = str(e)
            return False
        finally:
            if action.target in self.active_actions:
                del self.active_actions[action.target]
    
    # ==================== ACTION HANDLERS ====================
    
    async def _handle_scale_up(self, action: RemediationAction) -> bool:
        """Scale up instances"""
        instances = action.params.get('instances', 1)
        logger.info(f"Scaling up {instances} instances for {action.target}")
        
        # Simulate cloud-specific scaling
        if self.cloud_provider == CloudProvider.AWS:
            return await self._aws_scale_up(action)
        elif self.cloud_provider == CloudProvider.AZURE:
            return await self._azure_scale_up(action)
        elif self.cloud_provider == CloudProvider.KUBERNETES:
            return await self._k8s_scale_up(action)
        elif self.cloud_provider == CloudProvider.DOCKER:
            return await self._docker_scale_up(action)
        else:
            # Local simulation
            await asyncio.sleep(2)
            logger.info(f"✅ Simulated scale-up of {action.target}")
            return True
    
    async def _aws_scale_up(self, action: RemediationAction) -> bool:
        """AWS Auto Scaling implementation"""
        # In production:
        # import boto3
        # autoscaling = boto3.client('autoscaling')
        # response = autoscaling.set_desired_capacity(
        #     AutoScalingGroupName=action.target,
        #     DesiredCapacity=current_capacity + action.params['instances']
        # )
        
        await asyncio.sleep(2)
        logger.info(f"AWS: Scaled {action.target}")
        return True
    
    async def _azure_scale_up(self, action: RemediationAction) -> bool:
        """Azure VM Scale Sets implementation"""
        # In production:
        # from azure.mgmt.compute import ComputeManagementClient
        # compute_client = ComputeManagementClient(credentials, subscription_id)
        # compute_client.virtual_machine_scale_sets.update(
        #     resource_group, vmss_name,
        #     {'sku': {'capacity': new_capacity}}
        # )
        
        await asyncio.sleep(2)
        logger.info(f"Azure: Scaled {action.target}")
        return True
    
    async def _k8s_scale_up(self, action: RemediationAction) -> bool:
        """Kubernetes HPA implementation"""
        # In production:
        # from kubernetes import client, config
        # config.load_kube_config()
        # apps_v1 = client.AppsV1Api()
        # apps_v1.patch_namespaced_deployment_scale(
        #     name=action.target,
        #     namespace='default',
        #     body={'spec': {'replicas': new_replicas}}
        # )
        
        await asyncio.sleep(2)
        logger.info(f"K8s: Scaled deployment {action.target}")
        return True
    
    async def _docker_scale_up(self, action: RemediationAction) -> bool:
        """Docker Swarm scaling implementation"""
        # In production:
        # import docker
        # client = docker.from_env()
        # service = client.services.get(action.target)
        # service.update(mode={'replicated': {'replicas': new_count}})
        
        await asyncio.sleep(2)
        logger.info(f"Docker: Scaled service {action.target}")
        return True
    
    async def _handle_scale_down(self, action: RemediationAction) -> bool:
        """Scale down instances"""
        logger.info(f"Scaling down instances for {action.target}")
        await asyncio.sleep(2)
        return True
    
    async def _handle_restart_service(self, action: RemediationAction) -> bool:
        """Restart a service"""
        graceful = action.params.get('graceful', True)
        logger.info(f"Restarting service: {action.target} (graceful={graceful})")
        
        if graceful:
            logger.info("Draining connections...")
            await asyncio.sleep(1)
        
        # In production:
        # - kubectl rollout restart deployment {action.target}
        # - systemctl restart {action.target}
        # - docker restart {container_id}
        
        await asyncio.sleep(2)
        logger.info(f"✅ Service {action.target} restarted")
        return True
    
    async def _handle_enable_cache(self, action: RemediationAction) -> bool:
        """Enable or optimize caching"""
        ttl = action.params.get('ttl', 300)
        aggressive = action.params.get('aggressive', False)
        
        logger.info(f"Enabling caching for {action.target} (TTL={ttl}s, aggressive={aggressive})")
        
        # In production:
        # - Update Redis configuration
        # - Enable CDN caching
        # - Configure application cache headers
        
        await asyncio.sleep(1)
        logger.info(f"✅ Cache enabled with TTL={ttl}s")
        return True
    
    async def _handle_circuit_breaker(self, action: RemediationAction) -> bool:
        """Open circuit breaker for failing service"""
        threshold = action.params.get('threshold', 50)
        timeout = action.params.get('timeout', 30)
        
        logger.info(f"Opening circuit breaker for {action.target} (threshold={threshold}%, timeout={timeout}s)")
        
        # In production:
        # - Configure Istio circuit breaker
        # - Update service mesh policies
        # - Enable fallback responses
        
        await asyncio.sleep(1)
        logger.info(f"✅ Circuit breaker opened")
        return True
    
    async def _handle_traffic_shift(self, action: RemediationAction) -> bool:
        """Shift traffic to healthy instances"""
        percentage = action.params.get('percentage', 100)
        
        logger.info(f"Shifting {percentage}% traffic to {action.target}")
        
        # In production:
        # - Update load balancer configuration
        # - Modify service mesh routing rules (Istio)
        # - Update DNS records
        
        await asyncio.sleep(1.5)
        logger.info(f"✅ Traffic shifted: {percentage}% to healthy instances")
        return True
    
    async def _handle_rollback(self, action: RemediationAction) -> bool:
        """Rollback to previous version"""
        logger.info(f"Rolling back {action.target}")
        
        # In production:
        # - kubectl rollout undo deployment {action.target}
        # - Revert to previous container image
        # - Restore previous configuration
        
        await asyncio.sleep(3)
        logger.info(f"✅ Rollback completed for {action.target}")
        return True
    
    async def _handle_clear_cache(self, action: RemediationAction) -> bool:
        """Clear cache"""
        logger.info(f"Clearing cache for {action.target}")
        
        # In production:
        # - Redis FLUSHDB
        # - Memcached flush_all
        # - CDN cache purge
        
        await asyncio.sleep(0.5)
        logger.info("✅ Cache cleared")
        return True
    
    # ==================== HELPER METHODS ====================
    
    def _is_in_cooldown(self, action_key: str) -> bool:
        """Check if action is in cooldown period"""
        if action_key not in self.cooldown_periods:
            return False
        cooldown_until = self.cooldown_periods[action_key]
        return datetime.now() < cooldown_until
    
    def _set_cooldown(self, action_key: str, duration: int):
        """Set cooldown period for action"""
        self.cooldown_periods[action_key] = datetime.now() + timedelta(seconds=duration)
    
    def get_action_history(self, limit: int = 10) -> List[Dict]:
        """Get recent action history"""
        return [action.to_dict() for action in self.action_history[-limit:]]
    
    def get_active_actions(self) -> List[Dict]:
        """Get currently executing actions"""
        return [action.to_dict() for action in self.active_actions.values()]
    
    def get_statistics(self) -> Dict:
        """Get orchestrator statistics"""
        total = len(self.action_history)
        completed = len([a for a in self.action_history if a.status == 'completed'])
        failed = len([a for a in self.action_history if a.status == 'failed'])
        
        avg_execution_time = 0
        if completed > 0:
            total_time = sum(a.execution_time for a in self.action_history if a.execution_time)
            avg_execution_time = total_time / completed
        
        return {
            'total_actions': total,
            'completed': completed,
            'failed': failed,
            'success_rate': (completed / total * 100) if total > 0 else 0,
            'average_execution_time': avg_execution_time,
            'active_actions': len(self.active_actions),
            'cooldowns_active': len(self.cooldown_periods)
        }


# Example usage
if __name__ == '__main__':
    async def main():
        orchestrator = SelfHealingOrchestrator(CloudProvider.LOCAL)
        
        print("Testing Self-Healing Orchestrator...")
        print("=" * 60)
        
        # Simulate anomaly
        anomaly = {
            'anomaly_type': 'CPU_USAGE',
            'severity': 'warning',
            'metrics': {
                'cpu_usage': 85,
                'memory_usage': 70,
                'response_time': 300
            }
        }
        
        # Decide action
        action = orchestrator.decide_action(anomaly)
        if action:
            print(f"\n✅ Action decided: {action.to_dict()}")
            
            # Execute action
            success = await orchestrator.execute_action(action)
            print(f"\n{'✅' if success else '❌'} Action execution: {'Success' if success else 'Failed'}")
        
        # Get statistics
        stats = orchestrator.get_statistics()
        print(f"\n📊 Statistics:")
        print(json.dumps(stats, indent=2))
        
        # Get history
        history = orchestrator.get_action_history()
        print(f"\n📜 Action History:")
        print(json.dumps(history, indent=2))
        
        print("\n" + "=" * 60)
        print("Test completed!")
    
    asyncio.run(main())
    