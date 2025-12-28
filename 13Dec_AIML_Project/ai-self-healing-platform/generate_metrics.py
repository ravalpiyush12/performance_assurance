"""
Metrics Generator - For Testing the Platform
Save as: generate_metrics.py

Run with: python generate_metrics.py

This script sends realistic metrics to the API for testing
"""

import requests
import time
import random
from datetime import datetime
import json

API_URL = "http://localhost:8000"

def generate_metric(anomaly=False):
    """Generate a metric data point"""
    if anomaly:
        # Generate anomalous data
        cpu = random.uniform(85, 98)
        memory = random.uniform(80, 95)
        response_time = random.uniform(800, 1500)
        error_rate = random.uniform(5, 15)
        requests_per_sec = random.uniform(20, 50)
    else:
        # Generate normal data
        cpu = random.uniform(40, 70)
        memory = random.uniform(50, 75)
        response_time = random.uniform(150, 400)
        error_rate = random.uniform(0, 3)
        requests_per_sec = random.uniform(80, 150)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "cpu_usage": round(cpu, 2),
        "memory_usage": round(memory, 2),
        "response_time": round(response_time, 2),
        "error_rate": round(error_rate, 2),
        "requests_per_sec": round(requests_per_sec, 2),
        "disk_io": round(random.uniform(500, 1500), 2),
        "network_throughput": round(random.uniform(300, 700), 2)
    }

def send_metric(metric):
    """Send metric to API"""
    try:
        response = requests.post(
            f"{API_URL}/api/v1/metrics",
            json=metric,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print(f"✓ Sent: CPU={metric['cpu_usage']:.1f}% | "
                  f"Memory={metric['memory_usage']:.1f}% | "
                  f"Response={metric['response_time']:.0f}ms | "
                  f"Errors={metric['error_rate']:.1f}%")
            return True
        else:
            print(f"✗ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Failed to send metric: {e}")
        return False

def main():
    print("=" * 70)
    print("  Metrics Generator - AI Self-Healing Platform Testing")
    print("=" * 70)
    print()
    print(f"Sending metrics to: {API_URL}")
    print("Injecting anomalies every ~15-20 metrics")
    print("Press Ctrl+C to stop")
    print()
    print("-" * 70)
    print()
    
    # Check if API is accessible
    try:
        response = requests.get(f"{API_URL}/api/v1/status")
        print(f"✓ API is running (Health Score: {response.json()['health_score']:.0f}%)")
        print()
    except Exception as e:
        print(f"✗ Cannot connect to API at {API_URL}")
        print(f"  Make sure the platform is running: python run_platform.py")
        print(f"  Error: {e}")
        return
    
    counter = 0
    
    try:
        while True:
            counter += 1
            
            # Inject anomaly every 15-20 metrics
            should_anomaly = counter % random.randint(15, 20) == 0
            
            if should_anomaly:
                print()
                print("🔴 INJECTING ANOMALY...")
            
            metric = generate_metric(anomaly=should_anomaly)
            send_metric(metric)
            
            if should_anomaly:
                print("⚠️  Anomaly sent - check dashboard for detection and healing!")
                print()
            
            # Wait 2 seconds between metrics
            time.sleep(2)
            
    except KeyboardInterrupt:
        print()
        print()
        print("-" * 70)
        print(f"Stopped after sending {counter} metrics")
        print("=" * 70)
    except Exception as e:
        print(f"\n✗ Error: {e}")

if __name__ == "__main__":
    main()
    