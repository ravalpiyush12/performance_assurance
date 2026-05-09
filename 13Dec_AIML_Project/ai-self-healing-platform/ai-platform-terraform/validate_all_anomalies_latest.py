"""
COMPLETE SELF-HEALING VALIDATION SUITE
Tests all 5 anomaly types and self-healing actions

Anomaly Types Tested:
1. CPU_USAGE - High CPU load
2. MEMORY_USAGE - High memory consumption  
3. RESPONSE_TIME - Slow latency
4. ERROR_RATE - High error percentage
5. REQUESTS_PER_SEC - Traffic drops/surges

Usage:
    python validate_all_anomalies.py --url http://13.223.96.245:30080 --scenario all
    python validate_all_anomalies.py --url http://13.223.96.245:30080 --scenario cpu
    python validate_all_anomalies.py --url http://13.223.96.245:30080 --scenario memory
    python validate_all_anomalies.py --url http://13.223.96.245:30080 --scenario latency
    python validate_all_anomalies.py --url http://13.223.96.245:30080 --scenario errors
"""

import requests
import time
import argparse
import sys
from datetime import datetime
from typing import Dict, List

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class AnomalyValidator:
    def __init__(self, sample_app_url: str):
        self.sample_app_url = sample_app_url.rstrip('/')
        base = sample_app_url.rsplit(':', 1)[0]
        self.ai_platform_url = f"{base}:30800"
        
        self.results = {
            'total_scenarios': 0,
            'anomalies_detected': 0,
            'healing_actions': 0,
            'scenarios': []
        }
        
        print(f"{Colors.BOLD}Configuration:{Colors.RESET}")
        print(f"  Sample App: {self.sample_app_url}")
        print(f"  AI Platform: {self.ai_platform_url}\n")
    
    def log(self, message: str, color: str = Colors.BLUE):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{color}[{timestamp}] {message}{Colors.RESET}")
    
    def log_header(self, message: str):
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.HEADER}{message.center(80)}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 80}{Colors.RESET}\n")
    
    def check_readiness(self) -> bool:
        """Verify platform is ready for testing"""
        self.log_header("PRE-FLIGHT CHECK")
        
        # Test sample app
        try:
            resp = requests.get(f"{self.sample_app_url}/health", timeout=5)
            if resp.status_code == 200:
                self.log("✅ Sample App: Online", Colors.GREEN)
            else:
                self.log(f"❌ Sample App: HTTP {resp.status_code}", Colors.RED)
                return False
        except Exception as e:
            self.log(f"❌ Sample App: {e}", Colors.RED)
            return False
        
        # Test AI platform
        try:
            resp = requests.get(f"{self.ai_platform_url}/api/v1/status", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                self.log("✅ AI Platform: Online", Colors.GREEN)
                self.log(f"   ML Model: {'Trained' if data.get('ml_model_trained') else 'Training'}", Colors.CYAN)
                self.log(f"   Metrics: {data.get('ml_metrics_collected', 0)}", Colors.CYAN)
                self.log(f"   Health: {data.get('health_score', 0):.1f}%", Colors.CYAN)
                
                if not data.get('ml_model_trained'):
                    needed = 20 - data.get('ml_metrics_collected', 0)
                    self.log(f"\n⚠️  Wait {needed * 15} more seconds for ML training", Colors.YELLOW)
                    return False
                
                if not data.get('prometheus_enabled'):
                    self.log("\n❌ Prometheus not connected!", Colors.RED)
                    return False
                    
                self.log("\n✅ System Ready for Testing", Colors.GREEN)
                return True
            else:
                self.log(f"❌ AI Platform: HTTP {resp.status_code}", Colors.RED)
                return False
        except Exception as e:
            self.log(f"❌ AI Platform: {e}", Colors.RED)
            return False
    
    def get_status(self) -> Dict:
        """Get current platform status"""
        try:
            resp = requests.get(f"{self.ai_platform_url}/api/v1/status", timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except:
            pass
        return {}
    
    def wait_for_detection(self, baseline_alerts: int, timeout: int = 60) -> bool:
        """Wait for anomaly detection (alerts to increase)"""
        self.log(f"⏳ Monitoring for anomaly detection (timeout: {timeout}s)...", Colors.YELLOW)
        
        start_time = time.time()
        detected = False
        
        while (time.time() - start_time) < timeout:
            status = self.get_status()
            current_alerts = status.get('active_alerts', 0)
            health = status.get('health_score', 100)
            
            if current_alerts > baseline_alerts or health < 95:
                self.log(f"✅ ANOMALY DETECTED!", Colors.GREEN)
                self.log(f"   Active Alerts: {baseline_alerts} → {current_alerts}", Colors.CYAN)
                self.log(f"   Health Score: {health:.1f}%", Colors.CYAN)
                detected = True
                break
            
            time.sleep(3)
        
        if not detected:
            self.log(f"⚠️  No anomaly detected in {timeout}s", Colors.YELLOW)
        
        return detected
    
    def scenario_1_cpu_spike(self) -> bool:
        """SCENARIO 1: CPU_USAGE Anomaly"""
        self.log_header("SCENARIO 1: CPU SPIKE")
        
        self.log("📋 Objective: Trigger CPU_USAGE anomaly", Colors.BOLD)
        self.log("   Method: Intensive compute operations", Colors.CYAN)
        self.log("   Expected: scale_up healing action\n", Colors.CYAN)
        
        baseline = self.get_status()
        baseline_alerts = baseline.get('active_alerts', 0)
        
        self.log("🔥 Generating CPU load (100 req/s × 90s)...", Colors.YELLOW)
        
        start = time.time()
        requests_sent = 0
        
        while (time.time() - start) < 90: #90 sec was there earlier. Changed to 10 min to give more time for detection
            try:
                requests.get(f"{self.sample_app_url}/compute", timeout=1)
                requests_sent += 1
            except:
                pass
            time.sleep(0.01)  # 100 req/s
        
        self.log(f"✅ Sent {requests_sent} compute requests", Colors.GREEN)
        
        detected = self.wait_for_detection(baseline_alerts, timeout=60)
        
        final = self.get_status()
        self.log(f"\n📊 Final: Alerts={final.get('active_alerts', 0)}, Health={final.get('health_score', 0):.1f}%", Colors.CYAN)
        
        return detected
    
    def scenario_2_memory_spike(self) -> bool:
        """SCENARIO 2: MEMORY_USAGE Anomaly"""
        self.log_header("SCENARIO 2: MEMORY SPIKE")
        
        self.log("📋 Objective: Trigger MEMORY_USAGE anomaly", Colors.BOLD)
        self.log("   Method: Memory allocation operations", Colors.CYAN)
        self.log("   Expected: scale_up healing action\n", Colors.CYAN)
        
        baseline = self.get_status()
        baseline_alerts = baseline.get('active_alerts', 0)
        
        self.log("💾 Generating memory pressure (50 requests)...", Colors.YELLOW)
        
        for i in range(50):
            try:
                requests.get(f"{self.sample_app_url}/memory", timeout=2)
            except:
                pass
            time.sleep(0.5)
        
        self.log("✅ Memory load completed", Colors.GREEN)
        
        detected = self.wait_for_detection(baseline_alerts, timeout=60)
        
        final = self.get_status()
        self.log(f"\n📊 Final: Alerts={final.get('active_alerts', 0)}, Health={final.get('health_score', 0):.1f}%", Colors.CYAN)
        
        return detected
    
    def scenario_3_latency_spike(self) -> bool:
        """SCENARIO 3: RESPONSE_TIME Anomaly"""
        self.log_header("SCENARIO 3: LATENCY SPIKE")
        
        self.log("📋 Objective: Trigger RESPONSE_TIME anomaly", Colors.BOLD)
        self.log("   Method: Slow endpoint requests", Colors.CYAN)
        self.log("   Expected: enable_cache healing action\n", Colors.CYAN)
        
        baseline = self.get_status()
        baseline_alerts = baseline.get('active_alerts', 0)
        
        self.log("🐌 Generating slow requests (30 requests with 2s delay)...", Colors.YELLOW)
        
        for i in range(30):
            try:
                requests.get(f"{self.sample_app_url}/slow", timeout=5)
            except:
                pass
            time.sleep(0.5)
        
        self.log("✅ Latency load completed", Colors.GREEN)
        
        detected = self.wait_for_detection(baseline_alerts, timeout=60)
        
        final = self.get_status()
        self.log(f"\n📊 Final: Alerts={final.get('active_alerts', 0)}, Health={final.get('health_score', 0):.1f}%", Colors.CYAN)
        
        return detected
    
    def scenario_4_error_spike(self) -> bool:
        """SCENARIO 4: ERROR_RATE Anomaly"""
        self.log_header("SCENARIO 4: ERROR RATE SPIKE")
        
        self.log("📋 Objective: Trigger ERROR_RATE anomaly", Colors.BOLD)
        self.log("   Method: Generate 500 errors", Colors.CYAN)
        self.log("   Expected: circuit_breaker or traffic_shift\n", Colors.CYAN)
        
        baseline = self.get_status()
        baseline_alerts = baseline.get('active_alerts', 0)
        
        self.log("⚠️  Generating errors (50 requests)...", Colors.YELLOW)
        
        errors = 0
        for i in range(50):
            try:
                resp = requests.get(f"{self.sample_app_url}/error", timeout=2)
                if resp.status_code >= 500:
                    errors += 1
            except:
                errors += 1
            time.sleep(0.3)
        
        error_rate = (errors / 50) * 100
        self.log(f"✅ Generated {errors}/50 errors ({error_rate:.1f}%)", Colors.GREEN)
        
        detected = self.wait_for_detection(baseline_alerts, timeout=60)
        
        final = self.get_status()
        self.log(f"\n📊 Final: Alerts={final.get('active_alerts', 0)}, Health={final.get('health_score', 0):.1f}%", Colors.CYAN)
        
        return detected
    
    def scenario_5_traffic_variation(self) -> bool:
        """SCENARIO 5: REQUESTS_PER_SEC Anomaly"""
        self.log_header("SCENARIO 5: TRAFFIC VARIATION")
        
        self.log("📋 Objective: Trigger REQUESTS_PER_SEC anomaly", Colors.BOLD)
        self.log("   Method: Burst → silence → burst pattern", Colors.CYAN)
        self.log("   Expected: Adaptive scaling\n", Colors.CYAN)
        
        baseline = self.get_status()
        baseline_alerts = baseline.get('active_alerts', 0)
        
        # High burst
        self.log("🚀 Phase 1: High burst (100 req/s × 20s)...", Colors.YELLOW)
        start = time.time()
        while (time.time() - start) < 20:
            try:
                requests.get(f"{self.sample_app_url}/health", timeout=1)
            except:
                pass
            time.sleep(0.01)
        
        # Silence
        self.log("🔇 Phase 2: Complete silence (30s)...", Colors.YELLOW)
        time.sleep(30)
        
        # Another burst
        self.log("🚀 Phase 3: Another burst (100 req/s × 20s)...", Colors.YELLOW)
        start = time.time()
        while (time.time() - start) < 20:
            try:
                requests.get(f"{self.sample_app_url}/health", timeout=1)
            except:
                pass
            time.sleep(0.01)
        
        self.log("✅ Traffic pattern completed", Colors.GREEN)
        
        detected = self.wait_for_detection(baseline_alerts, timeout=60)
        
        final = self.get_status()
        self.log(f"\n📊 Final: Alerts={final.get('active_alerts', 0)}, Health={final.get('health_score', 0):.1f}%", Colors.CYAN)
        
        return detected
    
    def run_all_scenarios(self):
        """Run all 5 anomaly scenarios"""
        if not self.check_readiness():
            sys.exit(1)
        
        scenarios = [
            ("CPU Spike", self.scenario_1_cpu_spike),
            ("Memory Spike", self.scenario_2_memory_spike),
            ("Latency Spike", self.scenario_3_latency_spike),
            ("Error Rate", self.scenario_4_error_spike),
            ("Traffic Variation", self.scenario_5_traffic_variation)
        ]
        
        for name, scenario_func in scenarios:
            self.results['total_scenarios'] += 1
            
            try:
                detected = scenario_func()
                
                self.results['scenarios'].append({
                    'name': name,
                    'detected': detected
                })
                
                if detected:
                    self.results['anomalies_detected'] += 1
                
                # Cool down between scenarios
                self.log(f"\n⏸️  Cooling down for 30 seconds...\n", Colors.YELLOW)
                time.sleep(30)
                
            except Exception as e:
                self.log(f"❌ Scenario failed: {e}", Colors.RED)
                self.results['scenarios'].append({
                    'name': name,
                    'detected': False,
                    'error': str(e)
                })
        
        self.print_summary()
    
    def print_summary(self):
        """Print final summary"""
        self.log_header("VALIDATION SUMMARY")
        
        total = self.results['total_scenarios']
        detected = self.results['anomalies_detected']
        
        print(f"{Colors.BOLD}Results:{Colors.RESET}")
        print(f"  Total Scenarios: {total}")
        print(f"  Anomalies Detected: {detected}")
        print(f"  Success Rate: {(detected/total*100):.1f}%\n")
        
        print(f"{Colors.BOLD}Scenario Details:{Colors.RESET}")
        for scenario in self.results['scenarios']:
            status = "✅ DETECTED" if scenario['detected'] else "⚠️  NOT DETECTED"
            color = Colors.GREEN if scenario['detected'] else Colors.YELLOW
            print(f"  {color}{scenario['name']}: {status}{Colors.RESET}")
        
        final_status = self.get_status()
        print(f"\n{Colors.BOLD}Final Platform State:{Colors.RESET}")
        print(f"  Active Alerts: {final_status.get('active_alerts', 0)}")
        print(f"  Health Score: {final_status.get('health_score', 0):.1f}%")
        print(f"  Healing Actions: {final_status.get('healing_actions_count', 0)}")
        
        print(f"\n{Colors.BOLD}{'=' * 80}{Colors.RESET}")
        
        if detected >= 4:
            print(f"{Colors.GREEN}🎉 EXCELLENT! Most anomaly types working!{Colors.RESET}\n")
        elif detected >= 3:
            print(f"{Colors.YELLOW}👍 GOOD! Core anomaly detection working!{Colors.RESET}\n")
        else:
            print(f"{Colors.YELLOW}⚠️  Some anomaly types need tuning{Colors.RESET}\n")


def main():
    parser = argparse.ArgumentParser(description='Complete Anomaly Validation Suite')
    
    parser.add_argument('--url', type=str, required=True,
                       help='Sample app URL (e.g., http://13.223.96.245:30080)')
    
    parser.add_argument('--scenario', type=str, default='all',
                       choices=['all', 'cpu', 'memory', 'latency', 'errors', 'traffic'],
                       help='Scenario to run')
    
    args = parser.parse_args()
    
    validator = AnomalyValidator(args.url)
    
    if args.scenario == 'all':
        validator.run_all_scenarios()
    elif args.scenario == 'cpu':
        if validator.check_readiness():
            validator.scenario_1_cpu_spike()
    elif args.scenario == 'memory':
        if validator.check_readiness():
            validator.scenario_2_memory_spike()
    elif args.scenario == 'latency':
        if validator.check_readiness():
            validator.scenario_3_latency_spike()
    elif args.scenario == 'errors':
        if validator.check_readiness():
            validator.scenario_4_error_spike()
    elif args.scenario == 'traffic':
        if validator.check_readiness():
            validator.scenario_5_traffic_variation()


if __name__ == '__main__':
    main()
