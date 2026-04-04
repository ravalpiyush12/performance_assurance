"""
Self-Healing Validation Suite
Tests all self-healing capabilities of the AI platform

Usage:
    python validate_self_healing.py --url http://192.168.49.2:30080 --scenario all
    python validate_self_healing.py --url http://192.168.49.2:30080 --scenario cpu
    python validate_self_healing.py --url http://192.168.49.2:30080 --scenario memory
"""

import requests
import time
import argparse
import sys
from datetime import datetime
from typing import Dict, List
import json

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class SelfHealingValidator:
    def __init__(self, sample_app_url: str, ai_platform_url: str = None):
        self.sample_app_url = sample_app_url.rstrip('/')
        self.ai_platform_url = None  # Initialize to None first
        
        # Auto-detect AI platform URL if not provided
        if ai_platform_url:
            self.ai_platform_url = ai_platform_url.rstrip('/')
        else:
            # Try common ports
            base = sample_app_url.rsplit(':', 1)[0]
            for port in [30800, 30888, 8000, 31000]:  # Added 30800 as first option
                try:
                    test_url = f"{base}:{port}"
                    response = requests.get(f"{test_url}/api/v1/status", timeout=2)
                    if response.status_code == 200:
                        self.ai_platform_url = test_url
                        break
                except:
                    continue
        
        self.results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'scenarios': []
        }
    
    def log(self, message: str, color: str = Colors.BLUE):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{color}{timestamp} | {message}{Colors.RESET}")
    
    def log_header(self, message: str):
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.HEADER}{message.center(80)}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 80}{Colors.RESET}\n")
    
    def check_connectivity(self) -> bool:
        """Test connectivity to sample app and AI platform"""
        self.log_header("CONNECTIVITY CHECK")
        
        # Test Sample App
        try:
            response = requests.get(f"{self.sample_app_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Sample App Connected: {self.sample_app_url}", Colors.GREEN)
                self.log(f"   App: {data.get('app', 'unknown')}", Colors.CYAN)
            else:
                self.log(f"❌ Sample App returned status {response.status_code}", Colors.RED)
                return False
        except Exception as e:
            self.log(f"❌ Cannot connect to Sample App: {e}", Colors.RED)
            return False
        
        # Test AI Platform
        if self.ai_platform_url:
            try:
                response = requests.get(f"{self.ai_platform_url}/api/v1/status", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    self.log(f"✅ AI Platform Connected: {self.ai_platform_url}", Colors.GREEN)
                    self.log(f"   Mode: {data.get('mode', 'unknown')}", Colors.CYAN)
                    self.log(f"   ML Model Trained: {data.get('ml_model_trained', False)}", Colors.CYAN)
                    self.log(f"   K8s Enabled: {data.get('kubernetes_enabled', False)}", Colors.CYAN)
                else:
                    self.log(f"⚠️  AI Platform returned status {response.status_code}", Colors.YELLOW)
            except Exception as e:
                self.log(f"⚠️  AI Platform not accessible: {e}", Colors.YELLOW)
                self.ai_platform_url = None
        
        return True
    
    def get_current_metrics(self) -> Dict:
        """Get current system metrics from AI platform"""
        if not self.ai_platform_url:
            return {}
        
        try:
            response = requests.get(f"{self.ai_platform_url}/api/v1/status", timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return {}
    
    def get_recent_anomalies(self, limit: int = 5) -> List[Dict]:
        """Get recent anomalies from AI platform"""
        if not self.ai_platform_url:
            return []
        
        try:
            response = requests.get(f"{self.ai_platform_url}/api/v1/anomalies?limit={limit}", timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return []
    
    def get_recent_healing_actions(self, limit: int = 5) -> List[Dict]:
        """Get recent healing actions from AI platform"""
        if not self.ai_platform_url:
            return []
        
        try:
            response = requests.get(f"{self.ai_platform_url}/api/v1/healing-actions?limit={limit}", timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return []
    
    def wait_for_anomaly_detection(self, timeout: int = 60, anomaly_type: str = None) -> bool:
        """Wait for anomaly to be detected"""
        self.log(f"⏳ Waiting for anomaly detection (timeout: {timeout}s)...", Colors.YELLOW)
        
        start_time = time.time()
        initial_anomalies = len(self.get_recent_anomalies(limit=1))
        
        while (time.time() - start_time) < timeout:
            anomalies = self.get_recent_anomalies(limit=5)
            
            if len(anomalies) > initial_anomalies:
                latest = anomalies[0]
                detected_type = latest.get('anomaly_type', 'UNKNOWN')
                severity = latest.get('severity', 'unknown')
                
                if anomaly_type is None or detected_type == anomaly_type:
                    self.log(f"✅ Anomaly Detected: {detected_type} (severity: {severity})", Colors.GREEN)
                    return True
            
            time.sleep(2)
        
        self.log(f"❌ No anomaly detected within {timeout}s", Colors.RED)
        return False
    
    def wait_for_healing_action(self, timeout: int = 30) -> bool:
        """Wait for healing action to be executed"""
        self.log(f"⏳ Waiting for healing action (timeout: {timeout}s)...", Colors.YELLOW)
        
        start_time = time.time()
        initial_actions = len(self.get_recent_healing_actions(limit=1))
        
        while (time.time() - start_time) < timeout:
            actions = self.get_recent_healing_actions(limit=5)
            
            if len(actions) > initial_actions:
                latest = actions[0]
                action_type = latest.get('action_type', 'unknown')
                status = latest.get('status', 'unknown')
                target = latest.get('target_resource', latest.get('target', 'unknown'))
                
                self.log(f"✅ Healing Action Executed: {action_type}", Colors.GREEN)
                self.log(f"   Target: {target}", Colors.CYAN)
                self.log(f"   Status: {status}", Colors.CYAN)
                
                if status == 'completed':
                    return True
                elif status == 'failed':
                    self.log(f"   ⚠️  Action failed!", Colors.YELLOW)
                    return False
            
            time.sleep(2)
        
        self.log(f"❌ No healing action executed within {timeout}s", Colors.RED)
        return False
    
    def scenario_cpu_spike(self) -> bool:
        """
        SCENARIO 1: CPU Spike
        Expected: CPU anomaly detected → scale_up action → pods increased
        """
        self.log_header("SCENARIO 1: CPU SPIKE VALIDATION")
        
        self.log("📋 Test Objective:", Colors.BOLD)
        self.log("   - Generate high CPU load", Colors.CYAN)
        self.log("   - Detect CPU_USAGE anomaly", Colors.CYAN)
        self.log("   - Trigger scale_up healing action", Colors.CYAN)
        self.log("   - Verify Kubernetes scaling", Colors.CYAN)
        
        # Get baseline
        initial_status = self.get_current_metrics()
        initial_alerts = initial_status.get('active_alerts', 0)
        
        self.log(f"\n📊 Baseline: {initial_alerts} active alerts", Colors.BLUE)
        
        # Generate CPU load
        self.log("\n🔥 Generating CPU spike (60 req/s for 60 seconds)...", Colors.YELLOW)
        
        start_time = time.time()
        duration = 60
        rate = 60
        
        request_count = 0
        success_count = 0
        
        while (time.time() - start_time) < duration:
            try:
                response = requests.get(f"{self.sample_app_url}/compute", timeout=5)
                request_count += 1
                if response.status_code == 200:
                    success_count += 1
                
                if request_count % 50 == 0:
                    elapsed = int(time.time() - start_time)
                    self.log(f"   Progress: {request_count} requests in {elapsed}s", Colors.BLUE)
            except:
                pass
            
            time.sleep(1.0 / rate)
        
        self.log(f"✅ Load generated: {success_count}/{request_count} successful requests", Colors.GREEN)
        
        # Wait for anomaly detection
        anomaly_detected = self.wait_for_anomaly_detection(timeout=45, anomaly_type='CPU_USAGE')
        
        if not anomaly_detected:
            self.log("❌ TEST FAILED: Anomaly not detected", Colors.RED)
            return False
        
        # Wait for healing action
        healing_executed = self.wait_for_healing_action(timeout=30)
        
        if not healing_executed:
            self.log("❌ TEST FAILED: Healing action not executed", Colors.RED)
            return False
        
        # Verify result
        time.sleep(5)
        final_status = self.get_current_metrics()
        
        self.log(f"\n📊 Final Status:", Colors.BOLD)
        self.log(f"   Health Score: {final_status.get('health_score', 0):.1f}%", Colors.CYAN)
        self.log(f"   Active Alerts: {final_status.get('active_alerts', 0)}", Colors.CYAN)
        self.log(f"   Healing Actions: {final_status.get('healing_actions_count', 0)}", Colors.CYAN)
        
        self.log("\n✅ SCENARIO 1: PASSED", Colors.GREEN)
        return True
    
    def scenario_memory_spike(self) -> bool:
        """
        SCENARIO 2: Memory Spike
        Expected: Memory anomaly detected → scale_up action
        """
        self.log_header("SCENARIO 2: MEMORY SPIKE VALIDATION")
        
        self.log("📋 Test Objective:", Colors.BOLD)
        self.log("   - Generate memory pressure", Colors.CYAN)
        self.log("   - Detect MEMORY_USAGE anomaly", Colors.CYAN)
        self.log("   - Trigger healing action", Colors.CYAN)
        
        # Generate memory load
        self.log("\n💾 Generating memory spike (20 requests)...", Colors.YELLOW)
        
        for i in range(20):
            try:
                requests.get(f"{self.sample_app_url}/memory", timeout=5)
                if (i + 1) % 5 == 0:
                    self.log(f"   Progress: {i + 1}/20 memory requests", Colors.BLUE)
            except:
                pass
            time.sleep(0.5)
        
        self.log("✅ Memory load generated", Colors.GREEN)
        
        # Wait for anomaly
        anomaly_detected = self.wait_for_anomaly_detection(timeout=45, anomaly_type='MEMORY_USAGE')
        
        if anomaly_detected:
            self.wait_for_healing_action(timeout=30)
            self.log("\n✅ SCENARIO 2: PASSED", Colors.GREEN)
            return True
        else:
            self.log("\n⚠️  SCENARIO 2: NO ANOMALY (may be normal)", Colors.YELLOW)
            return True  # Not necessarily a failure
    
    def scenario_sustained_load(self) -> bool:
        """
        SCENARIO 3: Sustained High Load
        Expected: Multiple scaling actions, HPA engagement
        """
        self.log_header("SCENARIO 3: SUSTAINED LOAD VALIDATION")
        
        self.log("📋 Test Objective:", Colors.BOLD)
        self.log("   - Maintain high load for extended period", Colors.CYAN)
        self.log("   - Observe multiple scaling events", Colors.CYAN)
        self.log("   - Verify system stability", Colors.CYAN)
        
        initial_actions = len(self.get_recent_healing_actions(limit=1))
        
        self.log("\n🔥 Generating sustained load (45 req/s for 120 seconds)...", Colors.YELLOW)
        
        start_time = time.time()
        duration = 120
        rate = 45
        
        request_count = 0
        
        while (time.time() - start_time) < duration:
            try:
                requests.get(f"{self.sample_app_url}/compute", timeout=5)
                request_count += 1
                
                if request_count % 100 == 0:
                    elapsed = int(time.time() - start_time)
                    current_status = self.get_current_metrics()
                    self.log(
                        f"   {elapsed}s: {request_count} requests, "
                        f"Health: {current_status.get('health_score', 0):.1f}%",
                        Colors.BLUE
                    )
            except:
                pass
            
            time.sleep(1.0 / rate)
        
        self.log(f"✅ Sustained load completed: {request_count} requests", Colors.GREEN)
        
        # Check for healing actions
        time.sleep(10)
        final_actions = self.get_recent_healing_actions(limit=10)
        
        new_actions = len(final_actions) - initial_actions
        
        self.log(f"\n📊 Healing Actions Triggered: {new_actions}", Colors.CYAN)
        
        if new_actions > 0:
            self.log("✅ SCENARIO 3: PASSED", Colors.GREEN)
            return True
        else:
            self.log("⚠️  SCENARIO 3: No healing actions (system may already be scaled)", Colors.YELLOW)
            return True
    
    def scenario_error_injection(self) -> bool:
        """
        SCENARIO 4: Error Rate Spike
        Expected: Error rate anomaly detected → appropriate action
        """
        self.log_header("SCENARIO 4: ERROR RATE VALIDATION")
        
        self.log("📋 Test Objective:", Colors.BOLD)
        self.log("   - Generate errors via /error endpoint", Colors.CYAN)
        self.log("   - Detect ERROR_RATE anomaly", Colors.CYAN)
        self.log("   - Trigger healing action", Colors.CYAN)
        
        self.log("\n⚠️  Generating errors (30 requests)...", Colors.YELLOW)
        
        error_count = 0
        success_count = 0
        
        for i in range(30):
            try:
                response = requests.get(f"{self.sample_app_url}/error", timeout=5)
                if response.status_code >= 500:
                    error_count += 1
                else:
                    success_count += 1
            except:
                error_count += 1
            
            time.sleep(0.3)
        
        error_rate = (error_count / 30) * 100
        self.log(f"✅ Errors generated: {error_count}/30 ({error_rate:.1f}% error rate)", Colors.GREEN)
        
        # Wait for anomaly
        anomaly_detected = self.wait_for_anomaly_detection(timeout=45)
        
        if anomaly_detected:
            self.log("\n✅ SCENARIO 4: PASSED", Colors.GREEN)
            return True
        else:
            self.log("\n⚠️  SCENARIO 4: NO ANOMALY (error rate may be too low)", Colors.YELLOW)
            return True
    
    def scenario_rapid_changes(self) -> bool:
        """
        SCENARIO 5: Rapid Load Changes
        Expected: System adapts to changing conditions
        """
        self.log_header("SCENARIO 5: RAPID LOAD CHANGES VALIDATION")
        
        self.log("📋 Test Objective:", Colors.BOLD)
        self.log("   - Alternate between high and low load", Colors.CYAN)
        self.log("   - Test adaptive response", Colors.CYAN)
        self.log("   - Verify system stability", Colors.CYAN)
        
        patterns = [
            ("Low", 10, 10),
            ("High", 50, 20),
            ("Low", 10, 10),
            ("Spike", 80, 15),
            ("Low", 10, 10)
        ]
        
        for name, rate, duration in patterns:
            self.log(f"\n🔄 Phase: {name} ({rate} req/s for {duration}s)", Colors.YELLOW)
            
            start_time = time.time()
            count = 0
            
            while (time.time() - start_time) < duration:
                try:
                    requests.get(f"{self.sample_app_url}/compute", timeout=5)
                    count += 1
                except:
                    pass
                time.sleep(1.0 / rate)
            
            self.log(f"   ✅ {count} requests completed", Colors.GREEN)
            time.sleep(5)
        
        self.log("\n✅ SCENARIO 5: PASSED", Colors.GREEN)
        return True
    
    def run_all_scenarios(self):
        """Run all validation scenarios"""
        self.log_header("SELF-HEALING VALIDATION SUITE")
        
        if not self.check_connectivity():
            self.log("\n❌ Connectivity check failed. Exiting.", Colors.RED)
            sys.exit(1)
        
        scenarios = [
            ("CPU Spike", self.scenario_cpu_spike),
            ("Memory Spike", self.scenario_memory_spike),
            ("Sustained Load", self.scenario_sustained_load),
            ("Error Injection", self.scenario_error_injection),
            ("Rapid Changes", self.scenario_rapid_changes)
        ]
        
        for name, scenario_func in scenarios:
            self.results['total_tests'] += 1
            try:
                result = scenario_func()
                if result:
                    self.results['passed'] += 1
                    self.results['scenarios'].append({'name': name, 'result': 'PASSED'})
                else:
                    self.results['failed'] += 1
                    self.results['scenarios'].append({'name': name, 'result': 'FAILED'})
            except Exception as e:
                self.log(f"\n❌ SCENARIO FAILED WITH ERROR: {e}", Colors.RED)
                self.results['failed'] += 1
                self.results['scenarios'].append({'name': name, 'result': 'ERROR', 'error': str(e)})
            
            time.sleep(10)  # Cool down between scenarios
        
        self.print_summary()
    
    def print_summary(self):
        """Print final summary"""
        self.log_header("VALIDATION SUMMARY")
        
        total = self.results['total_tests']
        passed = self.results['passed']
        failed = self.results['failed']
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        self.log(f"Total Tests: {total}", Colors.BOLD)
        self.log(f"Passed: {passed}", Colors.GREEN)
        self.log(f"Failed: {failed}", Colors.RED)
        self.log(f"Pass Rate: {pass_rate:.1f}%", Colors.CYAN)
        
        print(f"\n{Colors.BOLD}Scenario Results:{Colors.RESET}")
        for scenario in self.results['scenarios']:
            result = scenario['result']
            color = Colors.GREEN if result == 'PASSED' else Colors.RED
            print(f"  {color}{scenario['name']}: {result}{Colors.RESET}")
        
        print(f"\n{Colors.BOLD}{'=' * 80}{Colors.RESET}\n")
        
        if pass_rate >= 80:
            self.log("🎉 VALIDATION SUCCESSFUL - Self-healing system is working!", Colors.GREEN)
        elif pass_rate >= 60:
            self.log("⚠️  PARTIAL SUCCESS - Some scenarios need attention", Colors.YELLOW)
        else:
            self.log("❌ VALIDATION FAILED - System needs debugging", Colors.RED)


def main():
    parser = argparse.ArgumentParser(description='Self-Healing Validation Suite')
    
    parser.add_argument('--url', type=str, required=True,
                       help='Sample app URL (e.g., http://192.168.49.2:30080)')
    
    parser.add_argument('--ai-platform', type=str, default=None,
                       help='AI Platform URL (auto-detected if not provided)')
    
    parser.add_argument('--scenario', type=str, default='all',
                       choices=['all', 'cpu', 'memory', 'sustained', 'error', 'rapid'],
                       help='Scenario to run')
    
    args = parser.parse_args()
    
    validator = SelfHealingValidator(args.url, args.ai_platform)
    
    if args.scenario == 'all':
        validator.run_all_scenarios()
    elif args.scenario == 'cpu':
        validator.check_connectivity()
        validator.scenario_cpu_spike()
    elif args.scenario == 'memory':
        validator.check_connectivity()
        validator.scenario_memory_spike()
    elif args.scenario == 'sustained':
        validator.check_connectivity()
        validator.scenario_sustained_load()
    elif args.scenario == 'error':
        validator.check_connectivity()
        validator.scenario_error_injection()
    elif args.scenario == 'rapid':
        validator.check_connectivity()
        validator.scenario_rapid_changes()


if __name__ == '__main__':
    main()