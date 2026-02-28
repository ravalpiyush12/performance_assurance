
"""
Advanced Load Generator for AI Self-Healing Demo
Generates different load patterns to trigger anomalies and auto-scaling

"""


import requests
import time
import argparse
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import random

class AdvancedLoadGenerator:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'cpu_intensive': 0,
            'memory_intensive': 0
        }
    
    def log(self, message, color='blue'):
        colors = {
            'blue': '\033[94m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'red': '\033[91m',
            'reset': '\033[0m'
        }
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{colors.get(color, '')}{timestamp} | {message}{colors['reset']}")
    
    def make_request(self, endpoint):
        """Make single request"""
        try:
            response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
            self.stats['total'] += 1
            if response.status_code == 200:
                self.stats['success'] += 1
                return True
            else:
                self.stats['failed'] += 1
                return False
        except Exception as e:
            self.stats['total'] += 1
            self.stats['failed'] += 1
            return False
    
    def scenario_1_gradual_increase(self, duration=180):
        """
        SCENARIO 1: Gradual CPU Increase
        Perfect for demonstrating CPU-based anomaly detection
        """
        self.log("=" * 70, 'green')
        self.log("SCENARIO 1: Gradual CPU Increase (Anomaly Detection)", 'green')
        self.log("=" * 70, 'green')
        self.log("Phase 1: Normal load (10 req/s) - 30 seconds", 'blue')
        self.log("Phase 2: Increase to 30 req/s - 60 seconds", 'yellow')
        self.log("Phase 3: SPIKE to 60 req/s - 60 seconds (TRIGGER ANOMALY)", 'red')
        self.log("Phase 4: Return to normal - 30 seconds", 'blue')
        self.log("=" * 70, 'green')
        
        start_time = time.time()
        
        phases = [
            {"duration": 30, "rate": 10, "desc": "Normal Load"},
            {"duration": 60, "rate": 30, "desc": "Increased Load"},
            {"duration": 60, "rate": 60, "desc": "SPIKE - Triggering Anomaly"},
            {"duration": 30, "rate": 10, "desc": "Recovery"}
        ]
        
        for phase in phases:
            phase_start = time.time()
            self.log(f"\n→ {phase['desc']} ({phase['rate']} req/s)", 'yellow')
            
            while (time.time() - phase_start) < phase['duration']:
                self.make_request('/compute')
                self.stats['cpu_intensive'] += 1
                
                if self.stats['total'] % 50 == 0:
                    elapsed = time.time() - start_time
                    success_rate = (self.stats['success'] / self.stats['total'] * 100) if self.stats['total'] > 0 else 0
                    self.log(
                        f"Progress: {self.stats['total']} reqs | "
                        f"Success: {success_rate:.1f}% | "
                        f"Elapsed: {int(elapsed)}s",
                        'blue'
                    )
                
                time.sleep(1.0 / phase['rate'])
        
        self.print_summary()
    
    def scenario_2_memory_spike(self, duration=120):
        """
        SCENARIO 2: Memory Spike
        Triggers memory-based anomaly detection
        """
        self.log("=" * 70, 'green')
        self.log("SCENARIO 2: Memory Spike (Memory Anomaly)", 'green')
        self.log("=" * 70, 'green')
        
        start_time = time.time()
        
        # Phase 1: Build up memory
        self.log("Phase 1: Building memory pressure...", 'yellow')
        for i in range(20):
            self.make_request('/memory')
            self.stats['memory_intensive'] += 1
            time.sleep(0.5)
        
        # Phase 2: Sustain + CPU
        self.log("Phase 2: Sustaining memory + CPU load...", 'red')
        phase_start = time.time()
        while (time.time() - phase_start) < 60:
            # Mix memory and CPU
            if random.random() < 0.3:
                self.make_request('/memory')
                self.stats['memory_intensive'] += 1
            else:
                self.make_request('/compute')
                self.stats['cpu_intensive'] += 1
            
            time.sleep(0.05)  # 20 req/s
        
        # Phase 3: Cleanup
        self.log("Phase 3: Cleanup...", 'blue')
        self.make_request('/cleanup')
        time.sleep(5)
        
        self.print_summary()
    
    def scenario_3_sustained_high_load(self, duration=300):
        """
        SCENARIO 3: Sustained High Load
        Best for demonstrating Kubernetes auto-scaling
        """
        self.log("=" * 70, 'green')
        self.log("SCENARIO 3: Sustained High Load (Auto-Scaling)", 'green')
        self.log("=" * 70, 'green')
        self.log(f"Duration: {duration} seconds at 60-150 req/s", 'yellow')
        self.log("Watch for: Kubernetes scaling 2 → 4 → 6+ pods", 'yellow')
        self.log("=" * 70, 'green')
        
        start_time = time.time()
        
        while (time.time() - start_time) < duration:
            # Random rate between 40-50 req/s
            rate = random.randint(60, 150)
            
            for _ in range(rate):
                self.make_request('/compute')
                self.stats['cpu_intensive'] += 1
            
            if self.stats['total'] % 100 == 0:
                elapsed = time.time() - start_time
                self.log(
                    f"Load Test: {self.stats['total']} reqs | "
                    f"Time: {int(elapsed)}/{duration}s | "
                    f"Rate: {rate} req/s",
                    'blue'
                )
            
            time.sleep(1)
        
        self.print_summary()
    
    def scenario_4_chaos_pattern(self, duration=240):
        """
        SCENARIO 4: Chaotic Pattern
        Random spikes and drops to test adaptive healing
        """
        self.log("=" * 70, 'green')
        self.log("SCENARIO 4: Chaos Pattern (Adaptive Response)", 'green')
        self.log("=" * 70, 'green')
        
        start_time = time.time()
        patterns = ['low', 'medium', 'high', 'spike']
        
        while (time.time() - start_time) < duration:
            pattern = random.choice(patterns)
            
            if pattern == 'low':
                rate = random.randint(5, 10)
                duration_sec = random.randint(15, 30)
                self.log(f"→ Low load: {rate} req/s for {duration_sec}s", 'blue')
            elif pattern == 'medium':
                rate = random.randint(20, 30)
                duration_sec = random.randint(20, 40)
                self.log(f"→ Medium load: {rate} req/s for {duration_sec}s", 'yellow')
            elif pattern == 'high':
                rate = random.randint(40, 50)
                duration_sec = random.randint(15, 25)
                self.log(f"→ High load: {rate} req/s for {duration_sec}s", 'red')
            else:  # spike
                rate = random.randint(70, 100)
                duration_sec = random.randint(10, 20)
                self.log(f"→ SPIKE: {rate} req/s for {duration_sec}s", 'red')
            
            pattern_start = time.time()
            while (time.time() - pattern_start) < duration_sec and (time.time() - start_time) < duration:
                self.make_request('/compute')
                self.stats['cpu_intensive'] += 1
                time.sleep(1.0 / rate)
        
        self.print_summary()
    
    def print_summary(self):
        """Print final summary"""
        self.log("\n" + "=" * 70, 'green')
        self.log("LOAD TEST SUMMARY", 'green')
        self.log("=" * 70, 'green')
        
        total = self.stats['total']
        success = self.stats['success']
        success_rate = (success / total * 100) if total > 0 else 0
        
        self.log(f"Total Requests: {total}", 'blue')
        self.log(f"Successful: {success} ({success_rate:.1f}%)", 'green')
        self.log(f"Failed: {self.stats['failed']}", 'red')
        self.log(f"CPU Intensive: {self.stats['cpu_intensive']}", 'yellow')
        self.log(f"Memory Intensive: {self.stats['memory_intensive']}", 'yellow')
        self.log("=" * 70, 'green')
        
        self.log("\n🔍 NOW CHECK:", 'green')
        self.log("1. AI Platform Dashboard: http://YOUR-AI-PLATFORM-URL", 'blue')
        self.log("2. Prometheus Metrics", 'blue')
        self.log("3. Kubernetes Pods: kubectl get pods -n monitoring-demo -w", 'blue')
        self.log("4. HPA Status: kubectl get hpa -n monitoring-demo", 'blue')
        self.log("=" * 70, 'green')


def main():
    parser = argparse.ArgumentParser(description='Advanced Load Generator for Self-Healing Demo')
    
    parser.add_argument('--url', type=str, required=True,
                       help='Sample app URL (e.g., http://192.168.49.2:30080)')
    
    parser.add_argument('--scenario', type=str, default='1',
                       choices=['1', '2', '3', '4', 'all'],
                       help='Scenario to run (1=gradual, 2=memory, 3=sustained, 4=chaos, all=run all)')
    
    parser.add_argument('--duration', type=int, default=None,
                       help='Override default duration (seconds)')
    
    args = parser.parse_args()
    
    # Test connection
    print(f"\n🔍 Testing connection to {args.url}...")
    try:
        response = requests.get(f"{args.url}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Connected!")
            data = response.json()
            print(f"   App: {data.get('app', 'unknown')}")
        else:
            print(f"⚠️  Warning: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect: {e}")
        sys.exit(1)
    
    print(f"\n🚀 Starting in 3 seconds...\n")
    time.sleep(3)
    
    generator = AdvancedLoadGenerator(args.url)
    
    if args.scenario == '1':
        duration = args.duration if args.duration else 180
        generator.scenario_1_gradual_increase(duration)
    elif args.scenario == '2':
        duration = args.duration if args.duration else 120
        generator.scenario_2_memory_spike(duration)
    elif args.scenario == '3':
        duration = args.duration if args.duration else 300
        generator.scenario_3_sustained_high_load(duration)
    elif args.scenario == '4':
        duration = args.duration if args.duration else 240
        generator.scenario_4_chaos_pattern(duration)
    elif args.scenario == 'all':
        print("\n🎬 Running ALL scenarios sequentially...\n")
        generator.scenario_1_gradual_increase(120)
        time.sleep(30)
        generator.scenario_2_memory_spike(90)
        time.sleep(30)
        generator.scenario_3_sustained_high_load(180)


if __name__ == '__main__':
    main()