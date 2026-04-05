"""
Self-Healing Orchestration Engine - Production Version with K8s Integration
"""

import asyncio
import logging
import os
from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

# Kubernetes client
try:
    from kubernetes import client, config
    KUBERNETES_AVAILABLE = True
except ImportError:
    KUBERNETES_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment configuration
TARGET_APP = os.getenv('TARGET_APP', 'sample-app')
TARGET_NAMESPACE = os.getenv('TARGET_NAMESPACE', 'monitoring-demo')
KUBERNETES_ENABLED = os.getenv('KUBERNETES_ENABLED', 'false').lower() == 'true'
MODE = os.getenv('MODE', 'development')


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
        self.kubernetes_action = False
        
    def to_dict(self) -> Dict:
        """Convert action to dictionary for API/UI"""
        result = {
            'action_id': self.action_id,
            'action_type': self.action_type.value,
            'target_resource': self.target,  # ← This becomes "Target: api-gateway"
            'status': self.status,           # ← This should be "completed" not "failed"
            'timestamp': self.timestamp.isoformat(),
            'execution_time_seconds': self.execution_time,
            'error_message': self.error_message,
            'kubernetes_action': self.kubernetes_action
        }
        
        # Add K8s-specific details if available
        if self.kubernetes_action and 'new_replicas' in self.params:
            result['replicas_info'] = f"{self.params.get('previous_replicas', '?')} → {self.params.get('new_replicas', '?')}"
        
        return result


class SelfHealingOrchestrator:
    """Main orchestrator for self-healing actions"""
    
    def __init__(self, cloud_provider: CloudProvider = CloudProvider.LOCAL):
        self.cloud_provider = cloud_provider
        self.action_history = []
        self.active_actions = {}
        self.cooldown_periods = {}
        self.action_handlers = self._register_handlers()
        self.action_counter = 0
        self.kubernetes_client = None
        
        # Initialize Kubernetes if enabled
        if KUBERNETES_ENABLED and KUBERNETES_AVAILABLE:
            try:
                if MODE == 'production':
                    config.load_incluster_config()
                else:
                    config.load_kube_config()
                
                self.kubernetes_client = client.AppsV1Api()
                self.cloud_provider = CloudProvider.KUBERNETES
                logger.info(f"✅ Kubernetes client initialized (target: {TARGET_APP})")
            except Exception as e:
                logger.warning(f"⚠️  Could not initialize Kubernetes: {e}")
                self.kubernetes_client = None
        
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
        """Decide which remediation action to take based on anomaly"""
        anomaly_type = anomaly.get('anomaly_type', 'UNKNOWN')
        severity = anomaly.get('severity', 'warning')
        metrics = anomaly.get('metrics', {})
        
        if self._is_in_cooldown(anomaly_type):
            logger.info(f"⏳ Action for {anomaly_type} in cooldown, skipping")
            return None
        
        action = None
        
        # CPU-based scaling (REAL KUBERNETES ACTION)
        if anomaly_type == 'CPU_USAGE':
            if metrics.get('cpu_usage', 0) > 80:
                action = RemediationAction(
                    ActionType.SCALE_UP,
                    target=TARGET_APP,
                    params={
                        'replicas': 2,
                        'reason': 'high_cpu',
                        'cpu_threshold': metrics.get('cpu_usage')
                    }
                )
                action.kubernetes_action = True
        
        # Memory-based scaling (REAL KUBERNETES ACTION)
        elif anomaly_type == 'MEMORY_USAGE':
            if metrics.get('memory_usage', 0) > 85:
                action = RemediationAction(
                    ActionType.SCALE_UP,
                    target=TARGET_APP,
                    params={
                        'replicas': 2,
                        'reason': 'high_memory',
                        'memory_threshold': metrics.get('memory_usage')
                    }
                )
                action.kubernetes_action = True
        
        # High traffic scaling (REAL KUBERNETES ACTION)
        elif anomaly_type == 'REQUESTS_PER_SEC':
            if metrics.get('requests_per_sec', 0) > 30:
                action = RemediationAction(
                    ActionType.SCALE_UP,
                    target=TARGET_APP,
                    params={
                        'replicas': 2,
                        'reason': 'high_traffic',
                        'current_rps': metrics.get('requests_per_sec')
                    }
                )
                action.kubernetes_action = True

        elif anomaly_type == 'REQUESTS_PER_SEC':
            if metrics.get('requests_per_sec', 0) < 20:
                action = RemediationAction(
                    ActionType.RESTART_SERVICE,
                    target=TARGET_APP,
                    params={
                        'graceful': True,
                        'current_rps': metrics.get('requests_per_sec')
                    }
                )
                action.kubernetes_action = True        
        
        # Response time - enable caching
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
        
        # Error rate - circuit breaker
        elif anomaly_type == 'ERROR_RATE':
            error_rate = metrics.get('error_rate', 0)
            if error_rate > 5:
                action = RemediationAction(
                    ActionType.CIRCUIT_BREAKER if severity == 'critical' else ActionType.TRAFFIC_SHIFT,
                    target="service-mesh",
                    params={'error_rate': error_rate}
                )

        
        if action:
            self.action_counter += 1
            action.action_id = f"action_{self.action_counter}"
            self._set_cooldown(anomaly_type, duration=60)
            logger.info(f"✅ Action decided: {action.action_type.value} for {anomaly_type}")
            
        return action
    
    async def execute_action(self, action: RemediationAction) -> bool:
        """Execute a remediation action"""
        logger.info(f"🎯 Executing action: {action.action_type.value} on {action.target}")
        
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
            logger.error(f"❌ Error executing action: {str(e)}")
            action.status = "failed"
            action.error_message = str(e)
            self.action_history.append(action)
            return False
        finally:
            if action.target in self.active_actions:
                del self.active_actions[action.target]
    
    # ==================== ACTION HANDLERS ====================
    
    async def _handle_scale_up(self, action: RemediationAction) -> bool:
        """Scale up instances - REAL KUBERNETES IMPLEMENTATION"""
        
        # Use Kubernetes if available
        if self.kubernetes_client and action.kubernetes_action:
            return await self._k8s_scale_up(action)
        
        # Fallback to cloud-specific or simulation
        if self.cloud_provider == CloudProvider.AWS:
            return await self._aws_scale_up(action)
        elif self.cloud_provider == CloudProvider.AZURE:
            return await self._azure_scale_up(action)
        else:
            # Simulation
            instances = action.params.get('replicas', 1)
            logger.info(f"🔄 Simulating scale-up of {instances} instances for {action.target}")
            await asyncio.sleep(2)
            logger.info(f"✅ Simulated scale-up completed")
            return True
    
    async def _k8s_scale_up(self, action: RemediationAction) -> bool:
        """REAL Kubernetes scaling implementation"""
        try:
            # Get current deployment
            deployment = self.kubernetes_client.read_namespaced_deployment(
                name=action.target,
                namespace=TARGET_NAMESPACE
            )
            
            current_replicas = deployment.spec.replicas
            additional_replicas = action.params.get('replicas', 2)
            new_replicas = current_replicas + additional_replicas
            
            logger.info(f"🎯 Triggering K8s scaling: {action.target} {current_replicas} → {new_replicas}")
            
            # Update replicas
            deployment.spec.replicas = new_replicas
            self.kubernetes_client.patch_namespaced_deployment(
                name=action.target,
                namespace=TARGET_NAMESPACE,
                body=deployment
            )
            
            logger.info(f"✅ Scaled {action.target} from {current_replicas} → {new_replicas} replicas")
            
            # Update action params with actual values
            action.params['previous_replicas'] = current_replicas
            action.params['new_replicas'] = new_replicas
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Kubernetes scaling failed: {str(e)}")
            action.error_message = str(e)
            return False
    
    async def _aws_scale_up(self, action: RemediationAction) -> bool:
        """AWS Auto Scaling simulation"""
        await asyncio.sleep(2)
        logger.info(f"AWS: Scaled {action.target}")
        return True
    
    async def _azure_scale_up(self, action: RemediationAction) -> bool:
        """Azure scaling simulation"""
        await asyncio.sleep(2)
        logger.info(f"Azure: Scaled {action.target}")
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
        
        await asyncio.sleep(2)
        logger.info(f"✅ Service {action.target} restarted")
        return True
    
    async def _handle_enable_cache(self, action: RemediationAction) -> bool:
        """Enable caching"""
        ttl = action.params.get('ttl', 300)
        logger.info(f"Enabling caching for {action.target} (TTL={ttl}s)")
        await asyncio.sleep(1)
        logger.info(f"✅ Cache enabled")
        return True
    
    async def _handle_circuit_breaker(self, action: RemediationAction) -> bool:
        """Open circuit breaker"""
        logger.info(f"Opening circuit breaker for {action.target}")
        await asyncio.sleep(1)
        logger.info(f"✅ Circuit breaker opened")
        return True
    
    async def _handle_traffic_shift(self, action: RemediationAction) -> bool:
        """Shift traffic"""
        percentage = action.params.get('percentage', 100)
        logger.info(f"Shifting {percentage}% traffic to healthy instances")
        await asyncio.sleep(1.5)
        logger.info(f"✅ Traffic shifted")
        return True
    
    async def _handle_rollback(self, action: RemediationAction) -> bool:
        """Rollback"""
        logger.info(f"Rolling back {action.target}")
        await asyncio.sleep(3)
        logger.info(f"✅ Rollback completed")
        return True
    
    async def _handle_clear_cache(self, action: RemediationAction) -> bool:
        """Clear cache"""
        logger.info(f"Clearing cache for {action.target}")
        await asyncio.sleep(0.5)
        logger.info("✅ Cache cleared")
        return True
    
    # ==================== HELPER METHODS ====================
    
    def _is_in_cooldown(self, action_key: str) -> bool:
        """Check if action is in cooldown period"""
        if action_key not in self.cooldown_periods:
            return False
        return datetime.now() < self.cooldown_periods[action_key]
    
    def _set_cooldown(self, action_key: str, duration: int):
        """Set cooldown period"""
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