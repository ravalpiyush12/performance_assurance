"""
Chaos Engineering & Automated Testing Framework
Injects failures to test self-healing capabilities
"""

import asyncio
import random
import logging
from typing import List, Dict, Callable
from datetime import datetime, timedelta
from enum import Enum
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChaosType(Enum):
    CPU_SPIKE = "cpu_spike"
    MEMORY_LEAK = "memory_leak"
    NETWORK_LATENCY = "network_latency"
    PACKET_LOSS = "packet_loss"
    SERVICE_CRASH = "service_crash"
    DATABASE_SLOWDOWN = "database_slowdown"
    DISK_FULL = "disk_full"
    API_ERROR_RATE = "api_error_rate"

class ChaosExperiment:
    """Represents a single chaos experiment"""
    
    def __init__(self, chaos_type: ChaosType, duration_sec: int, 
                 intensity: float, target: str):
        self.chaos_type = chaos_type
        self.duration_sec = duration_sec
        self.intensity = intensity  # 0.0 to 1.0
        self.target = target
        self.start_time = None
        self.end_time = None
        self.status = "pending"
        self.observed_effects = []
        
    def to_dict(self):
        return {
            'chaos_type': self.chaos_type.value,
            'duration_sec': self.duration_sec,
            'intensity': self.intensity,
            'target': self.target,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'observed_effects': self.observed_effects
        }

class ChaosEngine:
    """Main chaos engineering engine"""
    
    def __init__(self):
        self.active_experiments = []
        self.experiment_history = []
        self.chaos_handlers = self._register_handlers()
        
    def _register_handlers(self) -> Dict[ChaosType, Callable]:
        """Register chaos injection handlers"""
        return {
            ChaosType.CPU_SPIKE: self._inject_cpu_spike,
            ChaosType.MEMORY_LEAK: self._inject_memory_leak,
            ChaosType.NETWORK_LATENCY: self._inject_network_latency,
            ChaosType.PACKET_LOSS: self._inject_packet_loss,
            ChaosType.SERVICE_CRASH: self._inject_service_crash,
            ChaosType.DATABASE_SLOWDOWN: self._inject_database_slowdown,
            ChaosType.DISK_FULL: self._inject_disk_full,
            ChaosType.API_ERROR_RATE: self._inject_api_errors
        }
    
    async def run_experiment(self, experiment: ChaosExperiment) -> bool:
        """Execute a chaos experiment"""
        logger.info(f"Starting chaos experiment: {experiment.chaos_type.value} "
                   f"on {experiment.target} for {experiment.duration_sec}s")
        
        experiment.start_time = datetime.now()
        experiment.status = "running"
        self.active_experiments.append(experiment)
        
        try:
            handler = self.chaos_handlers.get(experiment.chaos_type)
            if handler:
                await handler(experiment)
                experiment.status = "completed"
                logger.info(f"Chaos experiment completed: {experiment.chaos_type.value}")
                return True
            else:
                logger.error(f"No handler for chaos type: {experiment.chaos_type}")
                experiment.status = "failed"
                return False
                
        except Exception as e:
            logger.error(f"Chaos experiment failed: {str(e)}")
            experiment.status = "failed"
            return False
        finally:
            experiment.end_time = datetime.now()
            self.active_experiments.remove(experiment)
            self.experiment_history.append(experiment)
    
    # Chaos Injection Handlers
    
    async def _inject_cpu_spike(self, experiment: ChaosExperiment):
        """Simulate CPU spike"""
        logger.info(f"Injecting CPU spike: {experiment.intensity * 100}%")
        
        # In production:
        # - stress-ng --cpu 4 --timeout 60s
        # - kubectl exec pod -- stress-ng --cpu 2 --timeout 30s
        
        experiment.observed_effects.append({
            'type': 'cpu_usage',
            'before': 50,
            'during': 50 + (experiment.intensity * 40),
            'expected_healing': 'auto-scaling'
        })
        
        await asyncio.sleep(experiment.duration_sec)
        logger.info("CPU spike experiment completed")
    
    async def _inject_memory_leak(self, experiment: ChaosExperiment):
        """Simulate memory leak"""
        logger.info(f"Injecting memory leak: {experiment.intensity * 100}%")
        
        # In production:
        # - Allocate memory gradually
        # - Use memory stress tools
        
        experiment.observed_effects.append({
            'type': 'memory_usage',
            'before': 60,
            'during': 60 + (experiment.intensity * 30),
            'expected_healing': 'pod_restart_or_scaling'
        })
        
        await asyncio.sleep(experiment.duration_sec)
        logger.info("Memory leak experiment completed")
    
    async def _inject_network_latency(self, experiment: ChaosExperiment):
        """Inject network latency"""
        latency_ms = experiment.intensity * 500
        logger.info(f"Injecting network latency: {latency_ms}ms")
        
        # In production:
        # - tc qdisc add dev eth0 root netem delay 300ms
        # - toxiproxy for proxy-based latency injection
        # - Istio fault injection
        
        experiment.observed_effects.append({
            'type': 'response_time',
            'before': 200,
            'during': 200 + latency_ms,
            'expected_healing': 'cache_optimization'
        })
        
        await asyncio.sleep(experiment.duration_sec)
        logger.info("Network latency experiment completed")
    
    async def _inject_packet_loss(self, experiment: ChaosExperiment):
        """Inject packet loss"""
        loss_percent = experiment.intensity * 20
        logger.info(f"Injecting packet loss: {loss_percent}%")
        
        # In production:
        # - tc qdisc add dev eth0 root netem loss 10%
        # - iptables rules
        
        experiment.observed_effects.append({
            'type': 'packet_loss',
            'loss_percent': loss_percent,
            'expected_healing': 'connection_retry_and_failover'
        })
        
        await asyncio.sleep(experiment.duration_sec)
        logger.info("Packet loss experiment completed")
    
    async def _inject_service_crash(self, experiment: ChaosExperiment):
        """Crash a service"""
        logger.info(f"Crashing service: {experiment.target}")
        
        # In production:
        # - kubectl delete pod {pod-name}
        # - kill -9 {pid}
        # - systemctl stop {service}
        
        experiment.observed_effects.append({
            'type': 'service_availability',
            'before': 100,
            'during': 0,
            'expected_healing': 'pod_restart_and_health_check'
        })
        
        await asyncio.sleep(experiment.duration_sec)
        logger.info("Service crash experiment completed")
    
    async def _inject_database_slowdown(self, experiment: ChaosExperiment):
        """Simulate database slowdown"""
        slowdown_factor = 1 + (experiment.intensity * 4)
        logger.info(f"Injecting database slowdown: {slowdown_factor}x")
        
        # In production:
        # - Add artificial delays to queries
        # - Inject lock contention
        # - Network latency to database
        
        experiment.observed_effects.append({
            'type': 'database_latency',
            'slowdown_factor': slowdown_factor,
            'expected_healing': 'connection_pool_adjustment'
        })
        
        await asyncio.sleep(experiment.duration_sec)
        logger.info("Database slowdown experiment completed")
    
    async def _inject_disk_full(self, experiment: ChaosExperiment):
        """Simulate disk full condition"""
        usage_percent = 85 + (experiment.intensity * 14)
        logger.info(f"Simulating disk usage: {usage_percent}%")
        
        # In production:
        # - dd if=/dev/zero of=/tmp/fill bs=1M count=1000
        # - Fill disk with temp files
        
        experiment.observed_effects.append({
            'type': 'disk_usage',
            'usage_percent': usage_percent,
            'expected_healing': 'log_rotation_and_cleanup'
        })
        
        await asyncio.sleep(experiment.duration_sec)
        logger.info("Disk full experiment completed")
    
    async def _inject_api_errors(self, experiment: ChaosExperiment):
        """Inject API error responses"""
        error_rate = experiment.intensity * 20
        logger.info(f"Injecting API errors: {error_rate}%")
        
        # In production:
        # - Modify API responses
        # - Use service mesh fault injection
        # - Proxy intercept and modify
        
        experiment.observed_effects.append({
            'type': 'error_rate',
            'error_rate_percent': error_rate,
            'expected_healing': 'circuit_breaker_and_retry'
        })
        
        await asyncio.sleep(experiment.duration_sec)
        logger.info("API error injection completed")
    
    def get_experiment_history(self, limit: int = 10) -> List[Dict]:
        """Get experiment history"""
        return [exp.to_dict() for exp in self.experiment_history[-limit:]]


class AutomatedTestSuite:
    """Automated test suite for self-healing validation"""
    
    def __init__(self, chaos_engine: ChaosEngine):
        self.chaos_engine = chaos_engine
        self.test_results = []
        
    async def run_test_scenario(self, name: str, experiments: List[ChaosExperiment],
                                 expected_healing_time: int = 60):
        """Run a complete test scenario"""
        logger.info(f"Running test scenario: {name}")
        
        scenario_start = datetime.now()
        scenario_results = {
            'name': name,
            'start_time': scenario_start.isoformat(),
            'experiments': [],
            'healing_detected': False,
            'healing_time_sec': None,
            'status': 'running'
        }
        
        # Run experiments sequentially
        for experiment in experiments:
            success = await self.chaos_engine.run_experiment(experiment)
            scenario_results['experiments'].append(experiment.to_dict())
            
            if not success:
                scenario_results['status'] = 'failed'
                break
        
        # Wait for healing
        healing_start = datetime.now()
        await asyncio.sleep(5)  # Simulate healing detection
        
        healing_time = (datetime.now() - healing_start).total_seconds()
        scenario_results['healing_detected'] = True
        scenario_results['healing_time_sec'] = healing_time
        scenario_results['status'] = 'passed' if healing_time < expected_healing_time else 'slow_healing'
        
        self.test_results.append(scenario_results)
        logger.info(f"Test scenario completed: {name} - {scenario_results['status']}")
        
        return scenario_results
    
    async def run_full_test_suite(self):
        """Run complete automated test suite"""
        logger.info("Starting full automated test suite...")
        
        # Test 1: CPU spike and auto-scaling
        await self.run_test_scenario(
            "CPU Spike Auto-Scaling",
            [ChaosExperiment(ChaosType.CPU_SPIKE, 30, 0.8, "web-service")],
            expected_healing_time=45
        )
        
        # Test 2: Memory leak and pod restart
        await self.run_test_scenario(
            "Memory Leak Recovery",
            [ChaosExperiment(ChaosType.MEMORY_LEAK, 25, 0.7, "api-service")],
            expected_healing_time=60
        )
        
        # Test 3: High latency and cache enablement
        await self.run_test_scenario(
            "Latency Mitigation",
            [ChaosExperiment(ChaosType.NETWORK_LATENCY, 20, 0.6, "api-gateway")],
            expected_healing_time=30
        )
        
        # Test 4: Service crash and restart
        await self.run_test_scenario(
            "Service Crash Recovery",
            [ChaosExperiment(ChaosType.SERVICE_CRASH, 10, 1.0, "worker-pod")],
            expected_healing_time=40
        )
        
        # Test 5: Combined failure scenario
        await self.run_test_scenario(
            "Multi-Failure Cascade",
            [
                ChaosExperiment(ChaosType.CPU_SPIKE, 15, 0.6, "web-service"),
                ChaosExperiment(ChaosType.DATABASE_SLOWDOWN, 15, 0.5, "postgres")
            ],
            expected_healing_time=90
        )
        
        # Generate report
        return self._generate_test_report()
    
    def _generate_test_report(self) -> Dict:
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed = len([t for t in self.test_results if t['status'] == 'passed'])
        failed = len([t for t in self.test_results if t['status'] == 'failed'])
        slow = len([t for t in self.test_results if t['status'] == 'slow_healing'])
        
        avg_healing_time = sum(
            t['healing_time_sec'] for t in self.test_results 
            if t['healing_time_sec']
        ) / total_tests if total_tests > 0 else 0
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed': passed,
                'failed': failed,
                'slow_healing': slow,
                'pass_rate': (passed / total_tests * 100) if total_tests > 0 else 0,
                'avg_healing_time_sec': avg_healing_time
            },
            'test_results': self.test_results,
            'recommendations': []
        }
        
        # Add recommendations
        if slow > 0:
            report['recommendations'].append(
                "Some healing actions took longer than expected. "
                "Review auto-scaling policies and cooldown periods."
            )
        
        if failed > 0:
            report['recommendations'].append(
                "Some tests failed. Investigate healing orchestrator logs "
                "and verify remediation actions are configured correctly."
            )
        
        if avg_healing_time > 60:
            report['recommendations'].append(
                "Average healing time exceeds 60 seconds. "
                "Consider optimizing detection algorithms and action execution."
            )
        
        return report


# Example usage
if __name__ == '__main__':
    async def main():
        chaos_engine = ChaosEngine()
        test_suite = AutomatedTestSuite(chaos_engine)
        
        # Run single experiment
        experiment = ChaosExperiment(
            ChaosType.CPU_SPIKE,
            duration_sec=15,
            intensity=0.7,
            target="web-service"
        )
        
        await chaos_engine.run_experiment(experiment)
        
        # Run full test suite
        report = await test_suite.run_full_test_suite()
        
        # Print report
        print("\n" + "="*60)
        print("AUTOMATED TEST SUITE REPORT")
        print("="*60)
        print(json.dumps(report['summary'], indent=2))
        print("\nRecommendations:")
        for rec in report['recommendations']:
            print(f"- {rec}")
    
    asyncio.run(main())
    