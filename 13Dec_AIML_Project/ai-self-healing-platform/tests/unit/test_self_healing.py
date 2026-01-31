"""
Unit Tests for Self-Healing Orchestrator
Tests automated remediation functionality
Run with: pytest tests/unit/test_self_healing.py -v
"""

import pytest
import asyncio
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from orchestrator.self_healing import (
    SelfHealingOrchestrator,
    RemediationAction,
    ActionType,
    CloudProvider
)


class TestRemediationAction:
    """Test RemediationAction class"""
    
    def test_creation(self):
        """Test action creation"""
        action = RemediationAction(
            action_type=ActionType.SCALE_UP,
            target="test-cluster",
            params={'instances': 2}
        )
        
        assert action.action_type == ActionType.SCALE_UP
        assert action.target == "test-cluster"
        assert action.params == {'instances': 2}
        assert action.status == "pending"
    
    def test_to_dict(self):
        """Test action serialization"""
        action = RemediationAction(
            action_type=ActionType.RESTART_SERVICE,
            target="api-service"
        )
        
        action_dict = action.to_dict()
        
        assert 'action_type' in action_dict
        assert 'target' in action_dict
        assert 'status' in action_dict
        assert action_dict['action_type'] == 'restart_service'


class TestSelfHealingOrchestrator:
    """Test SelfHealingOrchestrator"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance"""
        return SelfHealingOrchestrator(cloud_provider=CloudProvider.LOCAL)
    
    @pytest.fixture
    def cpu_anomaly(self):
        """CPU usage anomaly"""
        return {
            'anomaly_type': 'CPU_USAGE',
            'severity': 'warning',
            'metrics': {
                'cpu_usage': 85,
                'memory_usage': 70,
                'response_time': 300
            }
        }
    
    @pytest.fixture
    def memory_anomaly(self):
        """Memory usage anomaly"""
        return {
            'anomaly_type': 'MEMORY_USAGE',
            'severity': 'warning',
            'metrics': {
                'cpu_usage': 60,
                'memory_usage': 90,
                'response_time': 300
            }
        }
    
    def test_initialization(self, orchestrator):
        """Test orchestrator initialization"""
        assert orchestrator.cloud_provider == CloudProvider.LOCAL
        assert len(orchestrator.action_history) == 0
        assert len(orchestrator.active_actions) == 0
    
    def test_decide_action_cpu(self, orchestrator, cpu_anomaly):
        """Test action decision for CPU anomaly"""
        action = orchestrator.decide_action(cpu_anomaly)
        
        assert action is not None
        assert action.action_type == ActionType.SCALE_UP
        assert action.target == "application-cluster"
        assert 'cpu_threshold' in action.params
    
    def test_decide_action_memory(self, orchestrator, memory_anomaly):
        """Test action decision for memory anomaly"""
        action = orchestrator.decide_action(memory_anomaly)
        
        assert action is not None
        assert action.action_type == ActionType.SCALE_UP
        assert 'memory_threshold' in action.params
    
    def test_decide_action_response_time(self, orchestrator):
        """Test action decision for high response time"""
        anomaly = {
            'anomaly_type': 'RESPONSE_TIME',
            'severity': 'warning',
            'metrics': {
                'cpu_usage': 50,
                'memory_usage': 60,
                'response_time': 900
            }
        }
        
        action = orchestrator.decide_action(anomaly)
        
        assert action is not None
        assert action.action_type == ActionType.ENABLE_CACHE
    
    def test_decide_action_error_rate(self, orchestrator):
        """Test action decision for high error rate"""
        anomaly = {
            'anomaly_type': 'ERROR_RATE',
            'severity': 'critical',
            'metrics': {
                'error_rate': 8.0
            }
        }
        
        action = orchestrator.decide_action(anomaly)
        
        assert action is not None
        assert action.action_type in [ActionType.CIRCUIT_BREAKER, ActionType.TRAFFIC_SHIFT]
    
    def test_cooldown_mechanism(self, orchestrator, cpu_anomaly):
        """Test cooldown prevents action spam"""
        # First decision should return action
        action1 = orchestrator.decide_action(cpu_anomaly)
        assert action1 is not None
        
        # Second decision (immediate) should return None (cooldown)
        action2 = orchestrator.decide_action(cpu_anomaly)
        assert action2 is None
    
    @pytest.mark.asyncio
    async def test_execute_action(self, orchestrator, cpu_anomaly):
        """Test action execution"""
        action = orchestrator.decide_action(cpu_anomaly)
        
        success = await orchestrator.execute_action(action)
        
        assert success
        assert action.status == "completed"
        assert action.execution_time is not None
        assert len(orchestrator.action_history) == 1
    
    @pytest.mark.asyncio
    async def test_execute_scale_up(self, orchestrator):
        """Test scale up execution"""
        action = RemediationAction(
            action_type=ActionType.SCALE_UP,
            target="test-cluster",
            params={'instances': 2}
        )
        
        success = await orchestrator.execute_action(action)
        
        assert success
        assert action.status == "completed"
    
    @pytest.mark.asyncio
    async def test_execute_restart_service(self, orchestrator):
        """Test service restart execution"""
        action = RemediationAction(
            action_type=ActionType.RESTART_SERVICE,
            target="api-service",
            params={'graceful': True}
        )
        
        success = await orchestrator.execute_action(action)
        
        assert success
        assert action.status == "completed"
    
    def test_action_history(self, orchestrator, cpu_anomaly):
        """Test action history tracking"""
        action = orchestrator.decide_action(cpu_anomaly)
        
        # Execute action
        asyncio.run(orchestrator.execute_action(action))
        
        # Check history
        history = orchestrator.get_action_history(limit=10)
        
        assert len(history) == 1
        assert history[0]['action_type'] == 'scale_up'
        assert history[0]['status'] == 'completed'
    
    def test_get_statistics(self, orchestrator, cpu_anomaly):
        """Test orchestrator statistics"""
        # Execute some actions
        for i in range(3):
            action = RemediationAction(
                action_type=ActionType.SCALE_UP,
                target=f"cluster-{i}"
            )
            asyncio.run(orchestrator.execute_action(action))
        
        stats = orchestrator.get_statistics()
        
        assert stats['total_actions'] == 3
        assert stats['completed'] == 3
        assert stats['failed'] == 0
        assert stats['success_rate'] == 100.0
    
    def test_cloud_provider_selection(self):
        """Test different cloud providers"""
        providers = [
            CloudProvider.AWS,
            CloudProvider.AZURE,
            CloudProvider.KUBERNETES,
            CloudProvider.LOCAL
        ]
        
        for provider in providers:
            orch = SelfHealingOrchestrator(cloud_provider=provider)
            assert orch.cloud_provider == provider


class TestActionHandlers:
    """Test specific action handlers"""
    
    @pytest.fixture
    def orchestrator(self):
        return SelfHealingOrchestrator(cloud_provider=CloudProvider.LOCAL)
    
    @pytest.mark.asyncio
    async def test_handle_scale_up(self, orchestrator):
        """Test scale up handler"""
        action = RemediationAction(
            action_type=ActionType.SCALE_UP,
            target="app-cluster",
            params={'instances': 3}
        )
        
        success = await orchestrator._handle_scale_up(action)
        assert success
    
    @pytest.mark.asyncio
    async def test_handle_enable_cache(self, orchestrator):
        """Test cache enablement handler"""
        action = RemediationAction(
            action_type=ActionType.ENABLE_CACHE,
            target="api-gateway",
            params={'ttl': 600, 'aggressive': True}
        )
        
        success = await orchestrator._handle_enable_cache(action)
        assert success
    
    @pytest.mark.asyncio
    async def test_handle_circuit_breaker(self, orchestrator):
        """Test circuit breaker handler"""
        action = RemediationAction(
            action_type=ActionType.CIRCUIT_BREAKER,
            target="failing-service",
            params={'threshold': 50, 'timeout': 30}
        )
        
        success = await orchestrator._handle_circuit_breaker(action)
        assert success
    
    @pytest.mark.asyncio
    async def test_handle_traffic_shift(self, orchestrator):
        """Test traffic shifting handler"""
        action = RemediationAction(
            action_type=ActionType.TRAFFIC_SHIFT,
            target="healthy-instances",
            params={'percentage': 80}
        )
        
        success = await orchestrator._handle_traffic_shift(action)
        assert success


class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_full_healing_workflow(self):
        """Test complete healing workflow"""
        orchestrator = SelfHealingOrchestrator()
        
        # Create anomaly
        anomaly = {
            'anomaly_type': 'CPU_USAGE',
            'severity': 'warning',
            'metrics': {'cpu_usage': 90}
        }
        
        # Decide action
        action = orchestrator.decide_action(anomaly)
        assert action is not None
        
        # Execute action
        success = await orchestrator.execute_action(action)
        assert success
        
        # Verify history
        history = orchestrator.get_action_history()
        assert len(history) == 1
        assert history[0]['status'] == 'completed'
    
    @pytest.mark.asyncio
    async def test_multiple_anomalies(self):
        """Test handling multiple different anomalies"""
        orchestrator = SelfHealingOrchestrator()
        
        anomalies = [
            {'anomaly_type': 'CPU_USAGE', 'severity': 'warning', 
             'metrics': {'cpu_usage': 85}},
            {'anomaly_type': 'RESPONSE_TIME', 'severity': 'warning',
             'metrics': {'response_time': 900}},
            {'anomaly_type': 'ERROR_RATE', 'severity': 'critical',
             'metrics': {'error_rate': 10}}
        ]
        
        # Process each anomaly
        for anomaly in anomalies:
            # Need to clear cooldown for testing
            orchestrator.cooldown_periods.clear()
            
            action = orchestrator.decide_action(anomaly)
            if action:
                success = await orchestrator.execute_action(action)
                assert success
        
        # Verify all were handled
        stats = orchestrator.get_statistics()
        assert stats['total_actions'] >= 2  # At least 2 should execute


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])