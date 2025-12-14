"""
Self-Healing Orchestration Engine
Automatically remediates issues detected by anomaly detection
Save as: src/orchestrator/self_healing.py
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
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    RESTART_SERVICE = "restart_service"
    ENABLE_CACHE = "enable_cache"
    CIRCUIT_BREAKER = "circuit_breaker"
    TRAFFIC_SHIFT = "traffic_shift"
    ROLLBACK = "rollback"
    CLEAR_CACHE = "clear_cache"

class RemediationAction:
    def __init__(self, action_type: ActionType, target: str, params: dict = None):
        self.action_type = action_type
        self.target = target
        self.params = params or {}
        self.status = "pending"
        self.timestamp = datetime.now()
        self.execution_time = None
        
    def to_dict(self):
        return {
            'action_type': self.action_type.value,
            'target': self.target,
            'params': self.params,
            'status': self.status,
            'timestamp': self.timestamp.isoformat(),
            'execution_time': self.execution_time
        }

class SelfHealingOrchestrator:
    def __init__(self):
        self.action_history = []
        self.active_actions = {}
        self.cooldown_periods = {}
        self.action_handlers = self._register_handlers()
        
    def _register_handlers(self):
        """Register remediation action handlers"""
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
        """
        anomaly_type = anomaly.get('anomaly_type', 'UNKNOWN')
        severity = anomaly.get('severity', 'warning')
        metrics = anomaly.get('metrics', {})
        
        if self._is_in_cooldown(anomaly_type):
            logger.info(f"Action for {anomaly_type} in cooldown, skipping")
            return None
        
        action = None
        
        if anomaly_type == 'CPU_USAGE':
            if metrics.get('cpu_usage', 0) > 80:
                action = RemediationAction(
                    ActionType.SCALE_UP,
                    target="application-cluster",
                    params={'instances': 2, 'reason': 'high_cpu'}
                )
        
        elif anomaly_type == 'MEMORY_USAGE':
            if metrics.get('memory_usage', 0) > 85:
                action = RemediationAction(
                    ActionType.SCALE_UP,
                    target="application-cluster",
                    params={'instances': 2, 'reason': 'high_memory'}
                )
        
        elif anomaly_type == 'RESPONSE_TIME':
            if metrics.get('response_time', 0) > 800:
                action = RemediationAction(
                    ActionType.ENABLE_CACHE,
                    target="api-gateway",
                    params={'ttl': 300, 'aggressive': True}
                )
        
        elif anomaly_type == 'ERROR_RATE':
            error_rate = metrics.get('error_rate', 0)
            if error_rate > 5:
                if severity == 'critical':
                    action = RemediationAction(
                        ActionType.CIRCUIT_BREAKER,
                        target="failing-service",
                        params={'threshold': 50, 'timeout': 30}
                    )
                else:
                    action = RemediationAction(
                        ActionType.TRAFFIC_SHIFT,
                        target="healthy-instances",
                        params={'percentage': 80}
                    )
        
        elif anomaly_type == 'REQUESTS_PER_SEC':
            if metrics.get('requests_per_sec', 0) < 20:
                action = RemediationAction(
                    ActionType.RESTART_SERVICE,
                    target="web-service",
                    params={'graceful': True}
                )
        
        if action:
            self._set_cooldown(anomaly_type, duration=60)
            
        return action
    
    async def execute_action(self, action: RemediationAction) -> bool:
        """Execute a remediation action"""
        logger.info(f"Executing action: {action.action_type.value} on {action.target}")
        
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
                    logger.info(f"Action completed successfully in {action.execution_time}s")
                else:
                    action.status = "failed"
                    logger.error(f"Action failed: {action.action_type.value}")
                    
                self.action_history.append(action)
                return success
            else:
                logger.error(f"No handler for action type: {action.action_type}")
                action.status = "failed"
                return False
                
        except Exception as e:
            logger.error(f"Error executing action: {str(e)}")
            action.status = "failed"
            return False
        finally:
            if action.target in self.active_actions:
                del self.active_actions[action.target]
    
    async def _handle_scale_up(self, action: RemediationAction) -> bool:
        """Scale up instances"""
        logger.info(f"Scaling up {action.params.get('instances', 1)} instances for {action.target}")
        await asyncio.sleep(2)
        logger.info(f"Successfully scaled {action.target}")
        return True
    
    async def _handle_scale_down(self, action: RemediationAction) -> bool:
        """Scale down instances"""
        logger.info(f"Scaling down instances for {action.target}")
        await asyncio.sleep(2)
        return True
    
    async def _handle_restart_service(self, action: RemediationAction) -> bool:
        """Restart a service"""
        logger.info(f"Restarting service: {action.target}")
        graceful = action.params.get('graceful', True)
        
        if graceful:
            logger.info("Draining connections...")
            await asyncio.sleep(1)
        
        await asyncio.sleep(2)
        logger.info(f"Service {action.target} restarted successfully")
        return True
    
    async def _handle_enable_cache(self, action: RemediationAction) -> bool:
        """Enable or optimize caching"""
        logger.info(f"Enabling aggressive caching for {action.target}")
        ttl = action.params.get('ttl', 300)
        await asyncio.sleep(1)
        logger.info(f"Cache enabled with TTL={ttl}s")
        return True
    
    async def _handle_circuit_breaker(self, action: RemediationAction) -> bool:
        """Open circuit breaker for failing service"""
        logger.info(f"Opening circuit breaker for {action.target}")
        threshold = action.params.get('threshold', 50)
        timeout = action.params.get('timeout', 30)
        await asyncio.sleep(1)
        logger.info(f"Circuit breaker opened (threshold={threshold}%, timeout={timeout}s)")
        return True
    
    async def _handle_traffic_shift(self, action: RemediationAction) -> bool:
        """Shift traffic to healthy instances"""
        logger.info(f"Shifting traffic to {action.target}")
        percentage = action.params.get('percentage', 100)
        await asyncio.sleep(1.5)
        logger.info(f"Traffic shifted: {percentage}% to healthy instances")
        return True
    
    async def _handle_rollback(self, action: RemediationAction) -> bool:
        """Rollback to previous version"""
        logger.info(f"Rolling back {action.target}")
        await asyncio.sleep(3)
        logger.info(f"Rollback completed for {action.target}")
        return True
    
    async def _handle_clear_cache(self, action: RemediationAction) -> bool:
        """Clear cache to resolve stale data issues"""
        logger.info(f"Clearing cache for {action.target}")
        await asyncio.sleep(0.5)
        logger.info("Cache cleared successfully")
        return True
    
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


if __name__ == '__main__':
    async def main():
        orchestrator = SelfHealingOrchestrator()
        
        anomaly = {
            'anomaly_type': 'CPU_USAGE',
            'severity': 'warning',
            'metrics': {
                'cpu_usage': 85,
                'memory_usage': 70,
                'response_time': 300
            }
        }
        
        action = orchestrator.decide_action(anomaly)
        if action:
            logger.info(f"Action decided: {action.to_dict()}")
            success = await orchestrator.execute_action(action)
            logger.info(f"Action success: {success}")
        
        history = orchestrator.get_action_history()
        logger.info(f"Action history: {json.dumps(history, indent=2)}")
    
    asyncio.run(main())
    