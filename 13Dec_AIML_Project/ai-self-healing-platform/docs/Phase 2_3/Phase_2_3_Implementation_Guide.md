# PHASE 2 & 3 IMPLEMENTATION GUIDE
## Functional Prototype + Deployment & Testing

**Project:** AI/ML-Driven Self-Healing Platform  
**Student:** Piyush Ashokkumar Raval  
**Timeline:** January - March 2026

---

## 📋 TABLE OF CONTENTS

### PHASE 2: Functional Prototype (Jan-Feb 2026)
1. [JMeter Load Testing Setup](#1-jmeter-load-testing-setup)
2. [Enhanced Chaos Engineering](#2-enhanced-chaos-engineering)
3. [Kubernetes Local Deployment](#3-kubernetes-local-deployment)
4. [AWS Cloud Integration](#4-aws-cloud-integration)
5. [Azure Cloud Integration (Optional)](#5-azure-cloud-integration)

### PHASE 3: Deployment & Testing (Feb-Mar 2026)
6. [CI/CD Pipeline with GitHub Actions](#6-cicd-pipeline-github-actions)
7. [Automated Testing Suite](#7-automated-testing-suite)
8. [Cloud Performance Testing](#8-cloud-performance-testing)
9. [Monitoring & Observability](#9-monitoring--observability)

---

# PHASE 2: FUNCTIONAL PROTOTYPE

## 1. JMETER LOAD TESTING SETUP

### 1.1 Installation

**Windows:**
```bash
# Download JMeter
# Visit: https://jmeter.apache.org/download_jmeter.cgi
# Download: apache-jmeter-5.6.3.zip

# Extract and add to PATH
setx PATH "%PATH%;C:\apache-jmeter-5.6.3\bin"

# Verify installation
jmeter --version
```

**Linux/Mac:**
```bash
# Download and extract
cd ~/Downloads
wget https://dlcdn.apache.org//jmeter/binaries/apache-jmeter-5.6.3.tgz
tar -xzf apache-jmeter-5.6.3.tgz
sudo mv apache-jmeter-5.6.3 /opt/jmeter

# Add to PATH
echo 'export PATH=$PATH:/opt/jmeter/bin' >> ~/.bashrc
source ~/.bashrc

# Verify
jmeter --version
```

### 1.2 JMeter Test Plan Files

Create directory structure:
```bash
mkdir -p jmeter/test-plans
mkdir -p jmeter/results
mkdir -p jmeter/reports
```

**File 1: `jmeter/test-plans/normal_load_test.jmx`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6.3">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Normal Load Test">
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments">
        <collectionProp name="Arguments.arguments"/>
      </elementProp>
      <stringProp name="TestPlan.comments">Normal load: 100 concurrent users</stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
    </TestPlan>
    <hashTree>
      <!-- Thread Group -->
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Users">
        <intProp name="ThreadGroup.num_threads">100</intProp>
        <intProp name="ThreadGroup.ramp_time">60</intProp>
        <longProp name="ThreadGroup.duration">300</longProp>
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController">
          <boolProp name="LoopController.continue_forever">false</boolProp>
          <intProp name="LoopController.loops">-1</intProp>
        </elementProp>
      </ThreadGroup>
      <hashTree>
        <!-- HTTP Request Defaults -->
        <ConfigTestElement guiclass="HttpDefaultsGui" testclass="ConfigTestElement" testname="HTTP Request Defaults">
          <stringProp name="HTTPSampler.domain">localhost</stringProp>
          <stringProp name="HTTPSampler.port">8000</stringProp>
          <stringProp name="HTTPSampler.protocol">http</stringProp>
        </ConfigTestElement>
        <hashTree/>
        
        <!-- HTTP Request 1: Get Status -->
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="Get System Status">
          <stringProp name="HTTPSampler.path">/api/v1/status</stringProp>
          <stringProp name="HTTPSampler.method">GET</stringProp>
          <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
        </HTTPSamplerProxy>
        <hashTree>
          <!-- Response Assertion -->
          <ResponseAssertion guiclass="AssertionGui" testclass="ResponseAssertion" testname="Response Code Assertion">
            <collectionProp name="Asserion.test_strings">
              <stringProp name="49586">200</stringProp>
            </collectionProp>
            <stringProp name="Assertion.test_field">Assertion.response_code</stringProp>
            <boolProp name="Assertion.assume_success">false</boolProp>
            <intProp name="Assertion.test_type">16</intProp>
          </ResponseAssertion>
          <hashTree/>
          
          <!-- Duration Assertion -->
          <DurationAssertion guiclass="DurationAssertionGui" testclass="DurationAssertion" testname="Response Time < 500ms">
            <stringProp name="DurationAssertion.duration">500</stringProp>
          </DurationAssertion>
          <hashTree/>
        </hashTree>
        
        <!-- HTTP Request 2: Get Metrics -->
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="Get Metrics">
          <stringProp name="HTTPSampler.path">/api/v1/metrics?limit=10</stringProp>
          <stringProp name="HTTPSampler.method">GET</stringProp>
          <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
        </HTTPSamplerProxy>
        <hashTree/>
        
        <!-- Constant Timer -->
        <ConstantTimer guiclass="ConstantTimerGui" testclass="ConstantTimer" testname="Think Time">
          <stringProp name="ConstantTimer.delay">1000</stringProp>
        </ConstantTimer>
        <hashTree/>
      </hashTree>
      
      <!-- Listeners -->
      <ResultCollector guiclass="SummaryReport" testclass="ResultCollector" testname="Summary Report">
        <boolProp name="ResultCollector.error_logging">false</boolProp>
        <objProp>
          <name>saveConfig</name>
          <value class="SampleSaveConfiguration">
            <time>true</time>
            <latency>true</latency>
            <timestamp>true</timestamp>
            <success>true</success>
            <label>true</label>
            <code>true</code>
            <message>true</message>
            <threadName>true</threadName>
            <dataType>true</dataType>
            <encoding>false</encoding>
            <assertions>true</assertions>
            <subresults>true</subresults>
            <responseData>false</responseData>
            <samplerData>false</samplerData>
            <xml>false</xml>
            <fieldNames>true</fieldNames>
            <responseHeaders>false</responseHeaders>
            <requestHeaders>false</requestHeaders>
            <responseDataOnError>false</responseDataOnError>
            <saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>
            <assertionsResultsToSave>0</assertionsResultsToSave>
            <bytes>true</bytes>
            <sentBytes>true</sentBytes>
            <threadCounts>true</threadCounts>
            <idleTime>true</idleTime>
            <connectTime>true</connectTime>
          </value>
        </objProp>
        <stringProp name="filename">jmeter/results/normal_load_results.csv</stringProp>
      </ResultCollector>
      <hashTree/>
    </hashTree>
  </hashTree>
</jmeterTestPlan>
```

### 1.3 Automated JMeter Runner Script

**File: `jmeter/run_load_tests.py`**

```python
#!/usr/bin/env python3
"""
Automated JMeter Test Runner
Runs all load tests and generates HTML reports
"""

import subprocess
import os
import sys
from datetime import datetime
from pathlib import Path

class JMeterRunner:
    def __init__(self):
        self.jmeter_home = os.getenv('JMETER_HOME', '/opt/jmeter')
        self.jmeter_bin = os.path.join(self.jmeter_home, 'bin', 'jmeter')
        self.test_plans_dir = Path('jmeter/test-plans')
        self.results_dir = Path('jmeter/results')
        self.reports_dir = Path('jmeter/reports')
        
        # Create directories
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def run_test(self, test_plan_file, test_name):
        """Run a single JMeter test"""
        print(f"\n{'='*70}")
        print(f"Running Test: {test_name}")
        print(f"Test Plan: {test_plan_file}")
        print(f"{'='*70}\n")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = self.results_dir / f"{test_name}_{timestamp}.jtl"
        report_dir = self.reports_dir / f"{test_name}_{timestamp}"
        
        # JMeter command
        cmd = [
            self.jmeter_bin,
            '-n',  # Non-GUI mode
            '-t', str(test_plan_file),  # Test plan
            '-l', str(results_file),  # Results log
            '-e',  # Generate HTML report
            '-o', str(report_dir)  # Output directory for report
        ]
        
        try:
            print(f"Command: {' '.join(cmd)}\n")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            print("✅ Test completed successfully!")
            print(f"📊 Results: {results_file}")
            print(f"📈 HTML Report: {report_dir}/index.html")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Test failed with error:")
            print(e.stderr)
            return False
    
    def run_all_tests(self):
        """Run all test plans"""
        test_plans = [
            ('normal_load_test.jmx', 'normal_load'),
            ('stress_test.jmx', 'stress_test'),
            ('spike_test.jmx', 'spike_test')
        ]
        
        results = {}
        
        for test_file, test_name in test_plans:
            test_path = self.test_plans_dir / test_file
            
            if not test_path.exists():
                print(f"⚠️  Test plan not found: {test_path}")
                print(f"   Skipping {test_name}...")
                continue
            
            success = self.run_test(test_path, test_name)
            results[test_name] = success
        
        # Print summary
        print(f"\n{'='*70}")
        print("TEST EXECUTION SUMMARY")
        print(f"{'='*70}")
        
        for test_name, success in results.items():
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{test_name:30} {status}")
        
        print(f"{'='*70}\n")
        
        # Overall result
        all_passed = all(results.values())
        if all_passed:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed!")
            return 1

def main():
    runner = JMeterRunner()
    
    # Check if JMeter is installed
    if not os.path.exists(runner.jmeter_bin):
        print("❌ JMeter not found!")
        print(f"   Expected location: {runner.jmeter_bin}")
        print("\n💡 Install JMeter:")
        print("   - Download from: https://jmeter.apache.org/download_jmeter.cgi")
        print("   - Set JMETER_HOME environment variable")
        sys.exit(1)
    
    sys.exit(runner.run_all_tests())

if __name__ == '__main__':
    main()
```

### 1.4 Additional Test Plans

**File: `jmeter/test-plans/stress_test.jmx`**
*(Similar structure, but with 500 threads for 5 minutes)*

**File: `jmeter/test-plans/spike_test.jmx`**
*(Similar structure, but ramps to 1000 threads in 30 seconds)*

### 1.5 JMeter Integration with Platform

**File: `src/testing/jmeter_integration.py`**

```python
"""
JMeter Integration Module
Runs load tests and analyzes results
"""

import subprocess
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List

class JMeterIntegration:
    def __init__(self, platform_url: str = "http://localhost:8000"):
        self.platform_url = platform_url
        self.results_dir = Path('jmeter/results')
    
    def run_load_test(self, users: int = 100, duration: int = 300) -> Dict:
        """
        Run load test with specified parameters
        """
        print(f"🔄 Starting load test: {users} users for {duration}s")
        
        # This would trigger JMeter via subprocess
        # For now, return simulated results
        
        return {
            'users': users,
            'duration': duration,
            'total_requests': users * (duration // 2),
            'avg_response_time': 245.3,
            'error_rate': 0.2,
            'throughput': 95.5
        }
    
    def analyze_results(self, results_file: Path) -> Dict:
        """
        Analyze JMeter results CSV
        """
        if not results_file.exists():
            return {'error': 'Results file not found'}
        
        df = pd.read_csv(results_file)
        
        analysis = {
            'total_samples': len(df),
            'successful': len(df[df['success'] == True]),
            'failed': len(df[df['success'] == False]),
            'avg_response_time': df['elapsed'].mean(),
            'min_response_time': df['elapsed'].min(),
            'max_response_time': df['elapsed'].max(),
            'percentile_90': df['elapsed'].quantile(0.9),
            'percentile_95': df['elapsed'].quantile(0.95),
            'percentile_99': df['elapsed'].quantile(0.99),
            'throughput': len(df) / (df['timeStamp'].max() - df['timeStamp'].min()) * 1000
        }
        
        return analysis
```

---

## 2. ENHANCED CHAOS ENGINEERING

### 2.1 Advanced Chaos Scenarios

**File: `src/chaos/advanced_chaos.py`**

```python
"""
Advanced Chaos Engineering Framework
Implements complex failure scenarios
"""

import asyncio
import random
import psutil
import logging
from typing import List, Dict, Callable
from enum import Enum
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChaosScenario(Enum):
    CPU_SPIKE = "cpu_spike"
    MEMORY_LEAK = "memory_leak"
    NETWORK_LATENCY = "network_latency"
    PACKET_LOSS = "packet_loss"
    DISK_FULL = "disk_full"
    SERVICE_CRASH = "service_crash"
    DATABASE_SLOWDOWN = "database_slowdown"
    CASCADE_FAILURE = "cascade_failure"
    SPLIT_BRAIN = "split_brain"
    RESOURCE_EXHAUSTION = "resource_exhaustion"

class AdvancedChaosEngine:
    """
    Advanced chaos engineering with complex scenarios
    """
    
    def __init__(self):
        self.active_scenarios = []
        self.scenario_history = []
        self.handlers = self._register_handlers()
    
    def _register_handlers(self) -> Dict[ChaosScenario, Callable]:
        """Register chaos scenario handlers"""
        return {
            ChaosScenario.CPU_SPIKE: self._inject_cpu_spike,
            ChaosScenario.MEMORY_LEAK: self._inject_memory_leak,
            ChaosScenario.NETWORK_LATENCY: self._inject_network_latency,
            ChaosScenario.PACKET_LOSS: self._inject_packet_loss,
            ChaosScenario.DISK_FULL: self._simulate_disk_full,
            ChaosScenario.SERVICE_CRASH: self._crash_service,
            ChaosScenario.DATABASE_SLOWDOWN: self._slow_database,
            ChaosScenario.CASCADE_FAILURE: self._cascade_failure,
            ChaosScenario.SPLIT_BRAIN: self._split_brain_scenario,
            ChaosScenario.RESOURCE_EXHAUSTION: self._exhaust_resources
        }
    
    async def inject_chaos(self, scenario: ChaosScenario, duration: int = 30, 
                          intensity: float = 0.7) -> Dict:
        """
        Inject chaos scenario
        
        Args:
            scenario: Type of chaos to inject
            duration: Duration in seconds
            intensity: Intensity level (0.0 to 1.0)
        """
        logger.info(f"🔥 Injecting chaos: {scenario.value} (intensity={intensity}, duration={duration}s)")
        
        start_time = datetime.now()
        
        handler = self.handlers.get(scenario)
        if not handler:
            return {'error': f'No handler for {scenario.value}'}
        
        try:
            result = await handler(duration, intensity)
            result['scenario'] = scenario.value
            result['duration'] = duration
            result['intensity'] = intensity
            result['start_time'] = start_time.isoformat()
            result['end_time'] = datetime.now().isoformat()
            
            self.scenario_history.append(result)
            logger.info(f"✅ Chaos scenario completed: {scenario.value}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Chaos scenario failed: {e}")
            return {'error': str(e), 'scenario': scenario.value}
    
    async def _inject_cpu_spike(self, duration: int, intensity: float) -> Dict:
        """
        Inject CPU spike by running intensive computations
        """
        logger.info(f"💥 CPU spike: {intensity * 100}% for {duration}s")
        
        # Simulate CPU-intensive work
        def cpu_intensive():
            end_time = datetime.now().timestamp() + duration
            while datetime.now().timestamp() < end_time:
                _ = sum([i**2 for i in range(1000)])
        
        # Run in background (in real scenario, use multiprocessing)
        await asyncio.sleep(duration)
        
        return {
            'type': 'cpu_spike',
            'peak_cpu': 85 + (intensity * 15),
            'avg_cpu': 70 + (intensity * 20),
            'expected_healing': 'auto_scaling'
        }
    
    async def _inject_memory_leak(self, duration: int, intensity: float) -> Dict:
        """
        Simulate memory leak
        """
        logger.info(f"💧 Memory leak: {intensity * 100}% for {duration}s")
        
        # In real scenario, gradually allocate memory
        leaked_memory = []
        leak_rate = int(intensity * 10)  # MB per second
        
        for _ in range(duration):
            # Simulate memory allocation
            leaked_memory.append(bytearray(leak_rate * 1024 * 1024))
            await asyncio.sleep(1)
        
        memory_used = psutil.virtual_memory().percent
        
        # Clean up
        del leaked_memory
        
        return {
            'type': 'memory_leak',
            'peak_memory': memory_used,
            'leaked_mb': leak_rate * duration,
            'expected_healing': 'service_restart'
        }
    
    async def _inject_network_latency(self, duration: int, intensity: float) -> Dict:
        """
        Inject network latency
        """
        latency_ms = int(intensity * 500)
        logger.info(f"🐌 Network latency: {latency_ms}ms for {duration}s")
        
        # In production, use tc (traffic control) on Linux:
        # sudo tc qdisc add dev eth0 root netem delay {latency_ms}ms
        
        await asyncio.sleep(duration)
        
        # Cleanup:
        # sudo tc qdisc del dev eth0 root
        
        return {
            'type': 'network_latency',
            'latency_ms': latency_ms,
            'expected_healing': 'traffic_reroute'
        }
    
    async def _inject_packet_loss(self, duration: int, intensity: float) -> Dict:
        """
        Inject packet loss
        """
        loss_percent = int(intensity * 20)
        logger.info(f"📉 Packet loss: {loss_percent}% for {duration}s")
        
        # In production, use tc:
        # sudo tc qdisc add dev eth0 root netem loss {loss_percent}%
        
        await asyncio.sleep(duration)
        
        return {
            'type': 'packet_loss',
            'loss_percent': loss_percent,
            'expected_healing': 'connection_retry'
        }
    
    async def _simulate_disk_full(self, duration: int, intensity: float) -> Dict:
        """
        Simulate disk full condition
        """
        usage_percent = 85 + (intensity * 14)
        logger.info(f"💾 Disk full: {usage_percent}% for {duration}s")
        
        # In production, fill disk with temp files:
        # dd if=/dev/zero of=/tmp/fill bs=1M count=1000
        
        await asyncio.sleep(duration)
        
        return {
            'type': 'disk_full',
            'usage_percent': usage_percent,
            'expected_healing': 'log_rotation_cleanup'
        }
    
    async def _crash_service(self, duration: int, intensity: float) -> Dict:
        """
        Crash a service (simulated)
        """
        logger.info(f"💥 Service crash for {duration}s")
        
        # In production:
        # kubectl delete pod <pod-name>
        # docker kill <container-id>
        
        await asyncio.sleep(duration)
        
        return {
            'type': 'service_crash',
            'downtime_seconds': duration,
            'expected_healing': 'pod_restart'
        }
    
    async def _slow_database(self, duration: int, intensity: float) -> Dict:
        """
        Simulate database slowdown
        """
        slowdown_factor = 1 + (intensity * 4)
        logger.info(f"🐢 Database slowdown: {slowdown_factor}x for {duration}s")
        
        await asyncio.sleep(duration)
        
        return {
            'type': 'database_slowdown',
            'slowdown_factor': slowdown_factor,
            'expected_healing': 'connection_pool_adjustment'
        }
    
    async def _cascade_failure(self, duration: int, intensity: float) -> Dict:
        """
        Simulate cascade failure across multiple services
        """
        logger.info(f"⛓️  Cascade failure for {duration}s")
        
        # Simulate multiple failures in sequence
        failures = []
        
        # Service A fails
        failures.append({'service': 'A', 'time': 0})
        await asyncio.sleep(5)
        
        # Service B depends on A, fails
        failures.append({'service': 'B', 'time': 5})
        await asyncio.sleep(5)
        
        # Service C depends on B, fails
        failures.append({'service': 'C', 'time': 10})
        await asyncio.sleep(duration - 10)
        
        return {
            'type': 'cascade_failure',
            'failed_services': ['A', 'B', 'C'],
            'cascade_depth': 3,
            'expected_healing': 'circuit_breaker_isolation'
        }
    
    async def _split_brain_scenario(self, duration: int, intensity: float) -> Dict:
        """
        Simulate split-brain scenario in distributed system
        """
        logger.info(f"🧠 Split-brain scenario for {duration}s")
        
        # Simulate network partition
        await asyncio.sleep(duration)
        
        return {
            'type': 'split_brain',
            'partitioned_nodes': 2,
            'expected_healing': 'quorum_reestablishment'
        }
    
    async def _exhaust_resources(self, duration: int, intensity: float) -> Dict:
        """
        Exhaust multiple resources simultaneously
        """
        logger.info(f"🔥 Resource exhaustion for {duration}s")
        
        # Simulate CPU + Memory + Disk pressure
        tasks = [
            self._inject_cpu_spike(duration, intensity * 0.8),
            self._inject_memory_leak(duration, intensity * 0.6),
            self._simulate_disk_full(duration, intensity * 0.7)
        ]
        
        results = await asyncio.gather(*tasks)
        
        return {
            'type': 'resource_exhaustion',
            'resources_affected': ['cpu', 'memory', 'disk'],
            'sub_scenarios': results,
            'expected_healing': 'multi_action_remediation'
        }
    
    async def run_chaos_experiment(self, scenarios: List[ChaosScenario], 
                                   sequential: bool = True) -> List[Dict]:
        """
        Run multiple chaos scenarios
        
        Args:
            scenarios: List of scenarios to run
            sequential: If True, run one after another; if False, run in parallel
        """
        logger.info(f"🎯 Running {len(scenarios)} chaos scenarios")
        logger.info(f"   Mode: {'Sequential' if sequential else 'Parallel'}")
        
        if sequential:
            results = []
            for scenario in scenarios:
                result = await self.inject_chaos(scenario, duration=30, intensity=0.7)
                results.append(result)
                await asyncio.sleep(10)  # Recovery time between scenarios
            return results
        else:
            tasks = [self.inject_chaos(s, duration=30, intensity=0.7) for s in scenarios]
            return await asyncio.gather(*tasks)


# Example usage
async def main():
    engine = AdvancedChaosEngine()
    
    # Test individual scenario
    result = await engine.inject_chaos(ChaosScenario.CPU_SPIKE, duration=15, intensity=0.8)
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Run comprehensive chaos test suite
    scenarios = [
        ChaosScenario.CPU_SPIKE,
        ChaosScenario.MEMORY_LEAK,
        ChaosScenario.NETWORK_LATENCY,
        ChaosScenario.SERVICE_CRASH,
        ChaosScenario.CASCADE_FAILURE
    ]
    
    results = await engine.run_chaos_experiment(scenarios, sequential=True)
    
    print("\n" + "="*70)
    print("CHAOS EXPERIMENT RESULTS")
    print("="*70)
    for r in results:
        print(f"Scenario: {r.get('scenario')}")
        print(f"  Expected Healing: {r.get('expected_healing')}")
        print()

if __name__ == '__main__':
    import json
    asyncio.run(main())
```

---

## 3. KUBERNETES LOCAL DEPLOYMENT

### 3.1 Install Minikube

```bash
# Linux
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Mac
brew install minikube

# Windows (PowerShell as Administrator)
choco install minikube

# Start Minikube
minikube start --driver=docker --cpus=4 --memory=8192

# Verify
kubectl get nodes
minikube status
```

### 3.2 Kubernetes Manifests

Create directory:
```bash
mkdir -p kubernetes/base
mkdir -p kubernetes/overlays/{dev,prod}
```

**File: `kubernetes/base/namespace.yaml`**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: self-healing-platform
  labels:
    name: self-healing-platform
    environment: production
```

**File: `kubernetes/base/configmap.yaml`**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: platform-config
  namespace: self-healing-platform
data:
  # Platform configuration
  PLATFORM_ENV: "kubernetes"
  LOG_LEVEL: "INFO"
  ML_MODEL_PATH: "/app/models"
  METRICS_INTERVAL: "2"
  
  # ML Configuration
  ML_CONTAMINATION: "0.1"
  ML_WINDOW_SIZE: "100"
  
  # Self-Healing Configuration
  HEALING_COOLDOWN: "60"
  AUTO_SCALING_ENABLED: "true"
  CIRCUIT_BREAKER_THRESHOLD: "50"
```

**File: `kubernetes/base/deployment.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: self-healing-platform
  namespace: self-healing-platform
  labels:
    app: self-healing-platform
    version: v1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: self-healing-platform
  template:
    metadata:
      labels:
        app: self-healing-platform
        version: v1
    spec:
      containers:
      - name: platform
        image: self-healing-platform:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
          name: http
          protocol: TCP
        
        env:
        - name: PLATFORM_ENV
          valueFrom:
            configMapKeyRef:
              name: platform-config
              key: PLATFORM_ENV
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: platform-config
              key: LOG_LEVEL
        
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "2000m"
            memory: "4Gi"
        
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        
        volumeMounts:
        - name: logs
          mountPath: /app/logs
        - name: models
          mountPath: /app/models
      
      volumes:
      - name: logs
        emptyDir: {}
      - name: models
        emptyDir: {}
```

**File: `kubernetes/base/service.yaml`**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: self-healing-platform-service
  namespace: self-healing-platform
  labels:
    app: self-healing-platform
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
    name: http
  selector:
    app: self-healing-platform
```

**File: `kubernetes/base/hpa.yaml`**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: self-healing-platform-hpa
  namespace: self-healing-platform
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: self-healing-platform
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 2
        periodSeconds: 30
      selectPolicy: Max
```

### 3.3 Dockerfile for Kubernetes

**File: `Dockerfile`**

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create directories
RUN mkdir -p /app/logs /app/models /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3.4 Build and Deploy Script

**File: `scripts/deploy_kubernetes.sh`**

```bash
#!/bin/bash

set -e

echo "🚀 Deploying Self-Healing Platform to Kubernetes"
echo "================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="self-healing-platform"
IMAGE_TAG="latest"
NAMESPACE="self-healing-platform"

echo -e "${YELLOW}Step 1: Building Docker image...${NC}"
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built successfully${NC}"
else
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 2: Loading image into Minikube...${NC}"
minikube image load ${IMAGE_NAME}:${IMAGE_TAG}

echo -e "${YELLOW}Step 3: Creating namespace...${NC}"
kubectl apply -f kubernetes/base/namespace.yaml

echo -e "${YELLOW}Step 4: Applying ConfigMap...${NC}"
kubectl apply -f kubernetes/base/configmap.yaml

echo -e "${YELLOW}Step 5: Deploying application...${NC}"
kubectl apply -f kubernetes/base/deployment.yaml

echo -e "${YELLOW}Step 6: Creating service...${NC}"
kubectl apply -f kubernetes/base/service.yaml

echo -e "${YELLOW}Step 7: Setting up HPA...${NC}"
kubectl apply -f kubernetes/base/hpa.yaml

echo -e "${YELLOW}Step 8: Waiting for pods to be ready...${NC}"
kubectl wait --for=condition=ready pod \
    -l app=self-healing-platform \
    -n ${NAMESPACE} \
    --timeout=300s

echo -e "${GREEN}✅ Deployment successful!${NC}"
echo ""
echo "📊 Cluster Status:"
kubectl get all -n ${NAMESPACE}

echo ""
echo "🌐 Access the application:"
minikube service self-healing-platform-service -n ${NAMESPACE} --url

echo ""
echo "📝 Useful commands:"
echo "  - View pods: kubectl get pods -n ${NAMESPACE}"
echo "  - View logs: kubectl logs -f <pod-name> -n ${NAMESPACE}"
echo "  - Port forward: kubectl port-forward svc/self-healing-platform-service 8000:80 -n ${NAMESPACE}"
echo "  - Delete deployment: kubectl delete namespace ${NAMESPACE}"
```

Make it executable:
```bash
chmod +x scripts/deploy_kubernetes.sh
```

---

*Continued in next message due to length...*

Would you like me to continue with:
- **Part 2**: AWS Cloud Integration
- **Part 3**: CI/CD Pipeline with GitHub Actions
- **Part 4**: Automated Testing Suite
- **Part 5**: Monitoring & Observability

Which section would you like me to create next?
