"""
Load Testing Script for AI Self-Healing Platform (Production Mode)
Simulates JMeter-style load testing with realistic metrics and anomaly injection

Usage:
    python test_load.py --duration 60 --rate 10 --anomaly-chance 0.1

Features:
    - Sends realistic metrics to production platform
    - Injects anomalies at specified rate
    - Shows real-time statistics
    - Color-coded output
    - Summary report at end

Requirements:
    pip install requests colorama
"""

import requests
import time
import random
import argparse
import json
from datetime import datetime
from typing import Dict, List
from collections import defaultdict
import sys

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    print("Warning: colorama not installed. Install with: pip install colorama")
    print("Continuing without colors...\n")


class LoadTester:
    """
    Load testing utility for AI Self-Healing Platform
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", verbose: bool = True):
        self.base_url = base_url.rstrip('/')
        self.verbose = verbose
        
        # Statistics
        self.stats = {
            'total_sent': 0,
            'successful': 0,
            'failed': 0,
            'anomalies_injected': 0,
            'response_times': [],
            'anomaly_types': defaultdict(int)
        }
        
        # Metric ranges (normal)
        self.normal_ranges = {
            'cpu_usage': (30, 70),
            'memory_usage': (40, 75),
            'response_time': (100, 400),
            'error_rate': (0.1, 3.0),
            'requests_per_sec': (80, 150),
            'disk_io': (500, 1500),
            'network_throughput': (300, 700)
        }
        
        # Anomaly ranges
        self.anomaly_ranges = {
            'cpu_usage': (85, 98),
            'memory_usage': (85, 95),
            'response_time': (800, 1500),
            'error_rate': (5.0, 15.0),
            'requests_per_sec': (200, 300),  # High load
            'disk_io': (3000, 5000),
            'network_throughput': (1500, 2500)
        }
        
    def _print(self, message: str, color: str = None, level: str = "INFO"):
        """Print with optional color"""
        if not self.verbose:
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if COLORAMA_AVAILABLE and color:
            color_map = {
                'green': Fore.GREEN,
                'red': Fore.RED,
                'yellow': Fore.YELLOW,
                'blue': Fore.BLUE,
                'cyan': Fore.CYAN,
                'magenta': Fore.MAGENTA
            }
            print(f"{color_map.get(color, '')}{timestamp} [{level}] {message}{Style.RESET_ALL}")
        else:
            print(f"{timestamp} [{level}] {message}")
    
    def check_health(self) -> bool:
        """Check if platform is accessible"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                mode = data.get('mode', 'unknown')
                auto_metrics = data.get('auto_metrics', False)
                
                self._print(f"Platform Status: {data.get('status', 'unknown')}", 'green', 'OK')
                self._print(f"Mode: {mode}", 'cyan', 'INFO')
                self._print(f"Auto-Metrics: {auto_metrics}", 'cyan', 'INFO')
                
                if mode == 'development' and auto_metrics:
                    self._print("WARNING: Platform is in DEVELOPMENT mode with auto-metrics enabled!", 'yellow', 'WARN')
                    self._print("Load test metrics will mix with auto-generated ones.", 'yellow', 'WARN')
                    return True
                elif mode == 'production':
                    self._print("Platform is in PRODUCTION mode - ready for load testing!", 'green', 'OK')
                    return True
                else:
                    self._print(f"Platform mode is {mode}", 'yellow', 'WARN')
                    return True
            else:
                self._print(f"Health check failed: HTTP {response.status_code}", 'red', 'ERROR')
                return False
        except Exception as e:
            self._print(f"Cannot connect to platform: {e}", 'red', 'ERROR')
            return False
    
    def generate_normal_metric(self) -> Dict:
        """Generate a normal metric"""
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_usage': round(random.uniform(*self.normal_ranges['cpu_usage']), 2),
            'memory_usage': round(random.uniform(*self.normal_ranges['memory_usage']), 2),
            'response_time': round(random.uniform(*self.normal_ranges['response_time']), 2),
            'error_rate': round(random.uniform(*self.normal_ranges['error_rate']), 2),
            'requests_per_sec': round(random.uniform(*self.normal_ranges['requests_per_sec']), 2),
            'disk_io': round(random.uniform(*self.normal_ranges['disk_io']), 2),
            'network_throughput': round(random.uniform(*self.normal_ranges['network_throughput']), 2)
        }
    
    def generate_anomaly_metric(self, anomaly_type: str = None) -> Dict:
        """Generate an anomalous metric"""
        if anomaly_type is None:
            anomaly_type = random.choice(['cpu', 'memory', 'latency', 'error', 'disk', 'network'])
        
        metric = self.generate_normal_metric()
        
        # Inject anomaly
        if anomaly_type == 'cpu':
            metric['cpu_usage'] = round(random.uniform(*self.anomaly_ranges['cpu_usage']), 2)
        elif anomaly_type == 'memory':
            metric['memory_usage'] = round(random.uniform(*self.anomaly_ranges['memory_usage']), 2)
        elif anomaly_type == 'latency':
            metric['response_time'] = round(random.uniform(*self.anomaly_ranges['response_time']), 2)
        elif anomaly_type == 'error':
            metric['error_rate'] = round(random.uniform(*self.anomaly_ranges['error_rate']), 2)
        elif anomaly_type == 'disk':
            metric['disk_io'] = round(random.uniform(*self.anomaly_ranges['disk_io']), 2)
        elif anomaly_type == 'network':
            metric['network_throughput'] = round(random.uniform(*self.anomaly_ranges['network_throughput']), 2)
        
        return metric, anomaly_type
    
    def send_metric(self, metric: Dict) -> bool:
        """Send a metric to the platform"""
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/v1/metrics",
                json=metric,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            response_time = (time.time() - start_time) * 1000  # ms
            
            self.stats['response_times'].append(response_time)
            
            if response.status_code == 200:
                self.stats['successful'] += 1
                return True
            else:
                self.stats['failed'] += 1
                self._print(f"Failed to send metric: HTTP {response.status_code}", 'red', 'ERROR')
                return False
                
        except Exception as e:
            self.stats['failed'] += 1
            self._print(f"Error sending metric: {e}", 'red', 'ERROR')
            return False
    
    def run_load_test(
        self,
        duration: int = 60,
        rate: int = 10,
        anomaly_chance: float = 0.1,
        burst_mode: bool = False
    ):
        """
        Run load test
        
        Args:
            duration: Test duration in seconds
            rate: Metrics per second
            anomaly_chance: Probability of injecting anomaly (0.0 - 1.0)
            burst_mode: If True, send bursts of traffic
        """
        self._print("=" * 70, 'cyan')
        self._print("AI SELF-HEALING PLATFORM - LOAD TEST", 'cyan', 'INFO')
        self._print("=" * 70, 'cyan')
        self._print(f"Target: {self.base_url}", 'cyan', 'INFO')
        self._print(f"Duration: {duration} seconds", 'cyan', 'INFO')
        self._print(f"Rate: {rate} metrics/second", 'cyan', 'INFO')
        self._print(f"Anomaly Chance: {anomaly_chance * 100}%", 'cyan', 'INFO')
        self._print(f"Burst Mode: {'Yes' if burst_mode else 'No'}", 'cyan', 'INFO')
        self._print("=" * 70, 'cyan')
        
        # Check platform health
        if not self.check_health():
            self._print("Platform health check failed. Aborting.", 'red', 'ERROR')
            return
        
        self._print("=" * 70, 'cyan')
        self._print("Starting load test in 3 seconds...", 'yellow', 'INFO')
        time.sleep(3)
        
        start_time = time.time()
        interval = 1.0 / rate
        
        try:
            while (time.time() - start_time) < duration:
                iteration_start = time.time()
                
                # Determine if this is an anomaly
                is_anomaly = random.random() < anomaly_chance
                
                if is_anomaly:
                    metric, anomaly_type = self.generate_anomaly_metric()
                    self.stats['anomalies_injected'] += 1
                    self.stats['anomaly_types'][anomaly_type] += 1
                    
                    self._print(
                        f"🔥 ANOMALY INJECTED: {anomaly_type.upper()} | "
                        f"CPU={metric['cpu_usage']}% Memory={metric['memory_usage']}% "
                        f"Latency={metric['response_time']}ms Error={metric['error_rate']}%",
                        'red',
                        'ANOMALY'
                    )
                else:
                    metric = self.generate_normal_metric()
                    
                    if self.stats['total_sent'] % 10 == 0:  # Print every 10th normal metric
                        self._print(
                            f"📊 Normal metric | "
                            f"CPU={metric['cpu_usage']}% Memory={metric['memory_usage']}% "
                            f"Latency={metric['response_time']}ms",
                            'green',
                            'METRIC'
                        )
                
                # Send metric
                self.send_metric(metric)
                self.stats['total_sent'] += 1
                
                # Progress update every 10 metrics
                if self.stats['total_sent'] % 10 == 0:
                    elapsed = time.time() - start_time
                    remaining = duration - elapsed
                    self._print(
                        f"Progress: {self.stats['total_sent']} metrics sent | "
                        f"Time remaining: {int(remaining)}s | "
                        f"Success rate: {(self.stats['successful']/self.stats['total_sent']*100):.1f}%",
                        'blue',
                        'PROGRESS'
                    )
                
                # Rate limiting (unless burst mode)
                if not burst_mode:
                    elapsed = time.time() - iteration_start
                    sleep_time = max(0, interval - elapsed)
                    time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            self._print("\nLoad test interrupted by user", 'yellow', 'WARN')
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        self._print("\n" + "=" * 70, 'cyan')
        self._print("LOAD TEST SUMMARY", 'cyan', 'SUMMARY')
        self._print("=" * 70, 'cyan')
        
        total = self.stats['total_sent']
        success = self.stats['successful']
        failed = self.stats['failed']
        success_rate = (success / total * 100) if total > 0 else 0
        
        self._print(f"Total Metrics Sent: {total}", 'blue')
        self._print(f"Successful: {success} ({success_rate:.1f}%)", 'green')
        self._print(f"Failed: {failed}", 'red' if failed > 0 else 'green')
        
        self._print(f"\nAnomalies Injected: {self.stats['anomalies_injected']}", 'yellow')
        if self.stats['anomaly_types']:
            self._print("Anomaly Breakdown:", 'yellow')
            for anomaly_type, count in self.stats['anomaly_types'].items():
                self._print(f"  - {anomaly_type.upper()}: {count}", 'yellow')
        
        if self.stats['response_times']:
            avg_response = sum(self.stats['response_times']) / len(self.stats['response_times'])
            min_response = min(self.stats['response_times'])
            max_response = max(self.stats['response_times'])
            
            self._print(f"\nResponse Times:", 'blue')
            self._print(f"  - Average: {avg_response:.2f}ms", 'blue')
            self._print(f"  - Min: {min_response:.2f}ms", 'blue')
            self._print(f"  - Max: {max_response:.2f}ms", 'blue')
        
        self._print("\n" + "=" * 70, 'cyan')
        self._print("Check platform dashboard for detected anomalies and healing actions!", 'green')
        self._print(f"Dashboard: {self.base_url}", 'cyan')
        self._print(f"Metrics: {self.base_url}/api/v1/metrics", 'cyan')
        self._print(f"Anomalies: {self.base_url}/api/v1/anomalies", 'cyan')
        self._print(f"Healing: {self.base_url}/api/v1/healing-actions", 'cyan')
        self._print("=" * 70, 'cyan')


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Load testing script for AI Self-Healing Platform (Production Mode)'
    )
    
    parser.add_argument(
        '--url',
        type=str,
        default='http://localhost:8000',
        help='Platform base URL (default: http://localhost:8000)'
    )
    
    parser.add_argument(
        '--duration',
        type=int,
        default=60,
        help='Test duration in seconds (default: 60)'
    )
    
    parser.add_argument(
        '--rate',
        type=int,
        default=10,
        help='Metrics per second (default: 10)'
    )
    
    parser.add_argument(
        '--anomaly-chance',
        type=float,
        default=0.1,
        help='Probability of anomaly injection 0.0-1.0 (default: 0.1 = 10%%)'
    )
    
    parser.add_argument(
        '--burst',
        action='store_true',
        help='Enable burst mode (send as fast as possible)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Reduce output verbosity'
    )
    
    args = parser.parse_args()
    
    # Validate anomaly chance
    if not 0.0 <= args.anomaly_chance <= 1.0:
        print("Error: --anomaly-chance must be between 0.0 and 1.0")
        sys.exit(1)
    
    # Create tester
    tester = LoadTester(base_url=args.url, verbose=not args.quiet)
    
    # Run test
    tester.run_load_test(
        duration=args.duration,
        rate=args.rate,
        anomaly_chance=args.anomaly_chance,
        burst_mode=args.burst
    )


if __name__ == '__main__':
    main()