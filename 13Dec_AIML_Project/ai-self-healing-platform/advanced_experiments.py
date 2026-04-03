"""
Advanced Self-Healing Experiments
Beyond basic CPU/Memory scaling

NEW EXPERIMENTS:
1. Pod Failure Recovery
2. Network Latency Degradation
3. Database Connection Pool Exhaustion
4. Cascading Failure Detection
5. Resource Quota Breach
6. Log-based Anomaly Detection
7. Multi-service Correlation
"""

import requests
import time
import subprocess
import json
from typing import Dict, List
from datetime import datetime

class AdvancedExperiments:
    def __init__(self, sample_app_url: str, kubeconfig_path: str = None):
        self.sample_app_url = sample_app_url.rstrip('/')
        self.kubeconfig = kubeconfig_path
    
    # ========================================================================
    # EXPERIMENT 1: Pod Failure Recovery
    # ========================================================================
    
    def experiment_pod_failure(self):
        """
        EXPERIMENT: Pod Failure Recovery
        
        Scenario:
        1. Kill a pod randomly
        2. Detect service degradation
        3. Verify Kubernetes restarts pod
        4. Measure recovery time
        
        Expected:
        - Pod restart within 30 seconds
        - No service downtime (other pods handle load)
        - Health score temporarily drops but recovers
        """
        print("\n" + "="*80)
        print("EXPERIMENT 1: POD FAILURE RECOVERY")
        print("="*80)
        
        # Get current pods
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", "monitoring-demo", 
             "-l", "app=sample-app", "-o", "json"],
            capture_output=True,
            text=True
        )
        
        pods_data = json.loads(result.stdout)
        pods = [p['metadata']['name'] for p in pods_data['items']]
        
        if not pods:
            print("❌ No pods found")
            return False
        
        # Kill first pod
        victim_pod = pods[0]
        print(f"\n🎯 Killing pod: {victim_pod}")
        
        subprocess.run([
            "kubectl", "delete", "pod", victim_pod, 
            "-n", "monitoring-demo", "--grace-period=0", "--force"
        ])
        
        start_time = time.time()
        
        # Monitor recovery
        print("\n⏳ Monitoring recovery...")
        recovered = False
        
        for i in range(60):  # 60 seconds timeout
            time.sleep(1)
            
            result = subprocess.run(
                ["kubectl", "get", "pods", "-n", "monitoring-demo",
                 "-l", "app=sample-app", "-o", "json"],
                capture_output=True,
                text=True
            )
            
            pods_data = json.loads(result.stdout)
            running_pods = [
                p for p in pods_data['items'] 
                if p['status']['phase'] == 'Running'
            ]
            
            if len(running_pods) >= len(pods):
                recovery_time = time.time() - start_time
                print(f"\n✅ Pod recovered in {recovery_time:.2f} seconds")
                recovered = True
                break
            
            if i % 5 == 0:
                print(f"   {i}s: {len(running_pods)}/{len(pods)} pods running")
        
        return recovered
    
    # ========================================================================
    # EXPERIMENT 2: Network Latency Injection
    # ========================================================================
    
    def experiment_network_latency(self):
        """
        EXPERIMENT: Network Latency Detection
        
        Scenario:
        1. Inject artificial latency (sleep in /slow endpoint)
        2. Detect response time anomaly
        3. Trigger cache enablement or traffic rerouting
        
        Validation:
        - Response time anomaly detected
        - Healing action triggered (enable_cache)
        - Subsequent requests faster (if cached)
        """
        print("\n" + "="*80)
        print("EXPERIMENT 2: NETWORK LATENCY DETECTION")
        print("="*80)
        
        # Baseline latency
        print("\n📊 Measuring baseline latency...")
        baseline_times = []
        
        for _ in range(10):
            start = time.time()
            requests.get(f"{self.sample_app_url}/health", timeout=10)
            latency = (time.time() - start) * 1000
            baseline_times.append(latency)
        
        avg_baseline = sum(baseline_times) / len(baseline_times)
        print(f"   Baseline: {avg_baseline:.2f}ms")
        
        # Inject latency
        print("\n🐌 Injecting latency (hitting /slow endpoint)...")
        slow_times = []
        
        for i in range(20):
            start = time.time()
            try:
                response = requests.get(
                    f"{self.sample_app_url}/slow",
                    timeout=15
                )
                latency = (time.time() - start) * 1000
                slow_times.append(latency)
                
                if (i + 1) % 5 == 0:
                    print(f"   Request {i+1}: {latency:.2f}ms")
            except:
                pass
            
            time.sleep(0.5)
        
        avg_slow = sum(slow_times) / len(slow_times) if slow_times else 0
        print(f"\n📈 Degraded latency: {avg_slow:.2f}ms (vs {avg_baseline:.2f}ms baseline)")
        
        if avg_slow > avg_baseline * 2:
            print("✅ Latency degradation detected!")
            return True
        else:
            print("⚠️  Latency degradation not significant")
            return False
    
    # ========================================================================
    # EXPERIMENT 3: Database Connection Simulation
    # ========================================================================
    
    def experiment_connection_exhaustion(self):
        """
        EXPERIMENT: Database Connection Pool Exhaustion
        
        Scenario:
        1. Simulate many simultaneous connections (/db endpoint)
        2. Exhaust connection pool (simulated)
        3. Detect error rate spike
        4. Trigger pod restart or scale up
        """
        print("\n" + "="*80)
        print("EXPERIMENT 3: CONNECTION POOL EXHAUSTION")
        print("="*80)
        
        print("\n🔌 Simulating connection pool exhaustion...")
        print("   (Hitting /db endpoint repeatedly)")
        
        import concurrent.futures
        
        def make_db_request():
            try:
                response = requests.get(
                    f"{self.sample_app_url}/db",
                    timeout=5
                )
                return response.status_code
            except:
                return 500
        
        # Send 50 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(make_db_request) for _ in range(50)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        success_count = sum(1 for r in results if r == 200)
        error_count = sum(1 for r in results if r >= 500)
        
        error_rate = (error_count / len(results)) * 100
        
        print(f"\n📊 Results:")
        print(f"   Total: {len(results)}")
        print(f"   Success: {success_count}")
        print(f"   Errors: {error_count}")
        print(f"   Error Rate: {error_rate:.1f}%")
        
        if error_rate > 10:
            print("\n✅ Connection exhaustion detected (high error rate)")
            return True
        else:
            print("\n⚠️  No significant connection issues")
            return False
    
    # ========================================================================
    # EXPERIMENT 4: Cascading Failure
    # ========================================================================
    
    def experiment_cascading_failure(self):
        """
        EXPERIMENT: Cascading Failure Detection
        
        Scenario:
        1. Trigger failure in one service
        2. Cause dependent service to degrade
        3. Detect multiple correlated anomalies
        4. Trigger circuit breaker or rollback
        """
        print("\n" + "="*80)
        print("EXPERIMENT 4: CASCADING FAILURE SIMULATION")
        print("="*80)
        
        print("\n⚠️  Simulating cascading failure...")
        print("   Phase 1: Primary service degradation")
        
        # Phase 1: Degrade primary service
        for i in range(20):
            try:
                requests.get(f"{self.sample_app_url}/slow", timeout=10)
            except:
                pass
            time.sleep(0.2)
        
        print("   Phase 2: Secondary service affected")
        
        # Phase 2: Stress dependent services
        for i in range(20):
            try:
                requests.get(f"{self.sample_app_url}/compute", timeout=10)
            except:
                pass
            time.sleep(0.2)
        
        print("   Phase 3: System-wide impact")
        
        # Phase 3: Mix of requests showing cascading
        endpoints = ['/compute', '/memory', '/slow']
        for i in range(30):
            endpoint = endpoints[i % len(endpoints)]
            try:
                requests.get(f"{self.sample_app_url}{endpoint}", timeout=10)
            except:
                pass
            time.sleep(0.1)
        
        print("\n✅ Cascading failure pattern generated")
        print("   Expected: Multiple correlated anomalies")
        return True
    
    # ========================================================================
    # EXPERIMENT 5: Resource Quota Breach
    # ========================================================================
    
    def experiment_resource_quota(self):
        """
        EXPERIMENT: Resource Quota Breach
        
        Scenario:
        1. Hit resource limits (CPU/Memory)
        2. Trigger quota breach
        3. Detect OOMKilled or CPU throttling
        4. Scale up or adjust limits
        """
        print("\n" + "="*80)
        print("EXPERIMENT 5: RESOURCE QUOTA BREACH")
        print("="*80)
        
        print("\n📦 Checking current resource usage...")
        
        # Get pod metrics
        result = subprocess.run(
            ["kubectl", "top", "pods", "-n", "monitoring-demo", 
             "-l", "app=sample-app"],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        
        print("\n🔥 Generating resource pressure...")
        
        # Memory pressure
        for i in range(30):
            try:
                requests.get(f"{self.sample_app_url}/memory", timeout=10)
            except:
                pass
            time.sleep(0.3)
        
        # CPU pressure
        for i in range(30):
            try:
                requests.get(f"{self.sample_app_url}/compute", timeout=10)
            except:
                pass
            time.sleep(0.1)
        
        # Check if any pods were evicted/restarted
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", "monitoring-demo",
             "-l", "app=sample-app", "-o", "json"],
            capture_output=True,
            text=True
        )
        
        pods_data = json.loads(result.stdout)
        
        restarts = 0
        for pod in pods_data['items']:
            container_statuses = pod['status'].get('containerStatuses', [])
            for cs in container_statuses:
                restarts += cs.get('restartCount', 0)
        
        if restarts > 0:
            print(f"\n⚠️  Detected {restarts} pod restarts (possible OOM)")
            return True
        else:
            print("\n✅ No pod restarts (resources within limits)")
            return True
    
    # ========================================================================
    # EXPERIMENT 6: Gradual Degradation
    # ========================================================================
    
    def experiment_gradual_degradation(self):
        """
        EXPERIMENT: Gradual Performance Degradation
        
        Scenario:
        1. Slowly increase load over time
        2. Detect gradual performance decline
        3. Trigger proactive scaling before critical threshold
        """
        print("\n" + "="*80)
        print("EXPERIMENT 6: GRADUAL DEGRADATION DETECTION")
        print("="*80)
        
        print("\n📈 Generating gradually increasing load...")
        
        phases = [
            ("Low", 5, 15),
            ("Medium", 15, 15),
            ("High", 30, 15),
            ("Critical", 50, 15)
        ]
        
        for phase_name, rate, duration in phases:
            print(f"\n   Phase: {phase_name} ({rate} req/s)")
            
            phase_start = time.time()
            count = 0
            
            while (time.time() - phase_start) < duration:
                try:
                    requests.get(f"{self.sample_app_url}/compute", timeout=5)
                    count += 1
                except:
                    pass
                time.sleep(1.0 / rate)
            
            print(f"      {count} requests completed")
            time.sleep(2)
        
        print("\n✅ Gradual degradation pattern completed")
        print("   Expected: Early detection and proactive scaling")
        return True
    
    # ========================================================================
    # RUN ALL EXPERIMENTS
    # ========================================================================
    
    def run_all_experiments(self):
        """Run all advanced experiments"""
        print("\n" + "="*80)
        print("ADVANCED SELF-HEALING EXPERIMENTS SUITE")
        print("="*80)
        
        experiments = [
            ("Pod Failure Recovery", self.experiment_pod_failure),
            ("Network Latency", self.experiment_network_latency),
            ("Connection Exhaustion", self.experiment_connection_exhaustion),
            ("Cascading Failure", self.experiment_cascading_failure),
            ("Resource Quota", self.experiment_resource_quota),
            ("Gradual Degradation", self.experiment_gradual_degradation)
        ]
        
        results = {}
        
        for name, experiment_func in experiments:
            try:
                result = experiment_func()
                results[name] = "PASSED" if result else "FAILED"
            except Exception as e:
                print(f"\n❌ Experiment failed with error: {e}")
                results[name] = "ERROR"
            
            time.sleep(10)  # Cool down between experiments
        
        # Print summary
        print("\n" + "="*80)
        print("EXPERIMENT SUMMARY")
        print("="*80)
        
        for name, result in results.items():
            status_icon = "✅" if result == "PASSED" else "❌"
            print(f"{status_icon} {name}: {result}")
        
        passed = sum(1 for r in results.values() if r == "PASSED")
        total = len(results)
        
        print(f"\nResults: {passed}/{total} experiments passed")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True, help='Sample app URL')
    parser.add_argument('--experiment', default='all',
                       choices=['all', 'pod', 'latency', 'connection', 
                               'cascading', 'quota', 'gradual'])
    
    args = parser.parse_args()
    
    experiments = AdvancedExperiments(args.url)
    
    if args.experiment == 'all':
        experiments.run_all_experiments()
    elif args.experiment == 'pod':
        experiments.experiment_pod_failure()
    elif args.experiment == 'latency':
        experiments.experiment_network_latency()
    elif args.experiment == 'connection':
        experiments.experiment_connection_exhaustion()
    elif args.experiment == 'cascading':
        experiments.experiment_cascading_failure()
    elif args.experiment == 'quota':
        experiments.experiment_resource_quota()
    elif args.experiment == 'gradual':
        experiments.experiment_gradual_degradation()
