"""
Platform Debug Script - Windows Compatible
Save as: debug_platform.py

Run with: python debug_platform.py
"""

import sys
import os
from pathlib import Path
import time

# Windows UTF-8 fix
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 70)
print("  AI Self-Healing Platform - System Debug")
print("=" * 70)
print()

# Simple status indicators (no emojis)
def ok(text): return f"[OK] {text}"
def err(text): return f"[ERROR] {text}"
def warn(text): return f"[WARNING] {text}"

# Check 1: Python version
print("1. Checking Python Version...")
version = sys.version_info
if version.major >= 3 and version.minor >= 9:
    print(ok(f"Python {version.major}.{version.minor}.{version.micro}"))
else:
    print(err(f"Python {version.major}.{version.minor}.{version.micro} (Need 3.9+)"))
print()

# Check 2: Directory structure
print("2. Checking Directory Structure...")
required_dirs = {
    'src': 'Source code',
    'src/api': 'API server',
    'src/ml': 'ML models',
    'src/orchestrator': 'Self-healing',
    'config': 'Configuration',
    'logs': 'Log files'
}

for dir_path, desc in required_dirs.items():
    if Path(dir_path).exists():
        print(ok(f"{dir_path} ({desc})"))
    else:
        print(err(f"{dir_path} MISSING ({desc})"))
        if dir_path == 'logs':
            print(f"   Creating {dir_path}...")
            Path(dir_path).mkdir(exist_ok=True)
print()

# Check 3: Required files
print("3. Checking Required Files...")
required_files = {
    'src/api/main.py': 'Main API server',
    'src/ml/anomaly_detector.py': 'ML detector',
    'src/orchestrator/self_healing.py': 'Orchestrator',
    'run_platform.py': 'Main runner'
}

for file_path, desc in required_files.items():
    path = Path(file_path)
    if path.exists():
        size = path.stat().st_size
        print(ok(f"{file_path} ({desc}) - {size} bytes"))
    else:
        print(err(f"{file_path} MISSING ({desc})"))
print()

# Check 4: Dependencies
print("4. Checking Dependencies...")
required_packages = {
    'fastapi': 'Web framework',
    'uvicorn': 'ASGI server',
    'sklearn': 'ML library',
    'numpy': 'Numerical computing',
    'psutil': 'System monitoring'
}

missing = []
for pkg, desc in required_packages.items():
    try:
        __import__(pkg)
        print(ok(f"{pkg} ({desc})"))
    except ImportError:
        print(err(f"{pkg} MISSING ({desc})"))
        missing.append(pkg)

if missing:
    print()
    print(warn("Install missing packages:"))
    print(f"  pip install {' '.join(missing)}")
print()

# Check 5: Logs directory
print("5. Checking Logs...")
log_file = Path('logs/platform.log')
if log_file.exists():
    size = log_file.stat().st_size
    print(ok(f"Log file exists: {log_file.absolute()}"))
    print(f"   Size: {size} bytes")
    
    if size > 0:
        print(f"   Last modified: {time.ctime(log_file.stat().st_mtime)}")
        print()
        print("   Last 10 lines:")
        print("   " + "-" * 60)
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                for line in lines[-10:]:
                    print(f"   {line.rstrip()}")
        except Exception as e:
            print(f"   [ERROR] reading log: {e}")
        print("   " + "-" * 60)
    else:
        print(warn("Log file is empty (platform not started yet?)"))
else:
    print(warn("Log file doesn't exist yet"))
    print("   Will be created when platform starts")
print()

# Check 6: Port availability
print("6. Checking Port 8000...")
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(('localhost', 8000))
sock.close()

if result == 0:
    print(ok("Port 8000 is IN USE (platform is running)"))
    print()
    print("   Testing API...")
    try:
        import requests
        response = requests.get('http://localhost:8000/api/v1/status', timeout=2)
        data = response.json()
        print(ok(f"API responding!"))
        print(f"   Health Score: {data.get('health_score', 0):.0f}%")
        print(f"   Total Metrics: {data.get('total_metrics', 0)}")
        print(f"   Active Alerts: {data.get('active_alerts', 0)}")
        print(f"   Healing Actions: {data.get('healing_actions_count', 0)}")
        print(f"   ML Model Trained: {data.get('ml_model_trained', False)}")
    except Exception as e:
        print(err(f"Port in use but API not responding: {e}"))
else:
    print(warn("Port 8000 is FREE (platform not running)"))
    print("   Start with: python run_platform.py")
print()

# Check 7: Check for anomalies (if running)
if result == 0:
    print("7. Checking Data...")
    try:
        import requests
        
        # Get anomalies
        anomalies = requests.get('http://localhost:8000/api/v1/anomalies', timeout=2).json()
        print(f"   Anomalies detected: {len(anomalies)}")
        
        if len(anomalies) > 0:
            latest = anomalies[-1]
            print(f"   Latest: {latest.get('anomaly_type')} ({latest.get('severity')})")
        
        # Get healing actions
        healing = requests.get('http://localhost:8000/api/v1/healing-actions', timeout=2).json()
        print(f"   Healing actions: {len(healing)}")
        
        if len(healing) > 0:
            latest = healing[-1]
            print(f"   Latest: {latest.get('action_type')} -> {latest.get('status')}")
        
    except Exception as e:
        print(err(f"Error checking data: {e}"))
    print()

# Summary
print("=" * 70)
print("  Summary")
print("=" * 70)
print()

if missing:
    print(err(f"Missing {len(missing)} dependencies"))
    print("   Run: pip install -r requirements.txt")
else:
    print(ok("All dependencies installed"))

if not Path('src/api/main.py').exists():
    print(err("Missing main.py - copy from Claude artifacts"))
else:
    print(ok("All required files present"))

if result == 0:
    print(ok("Platform is RUNNING"))
    print()
    print("   Dashboard: http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs")
else:
    print(warn("Platform is NOT running"))
    print()
    print("   Start with: python run_platform.py")

print()
print("=" * 70)

# Instructions
print()
print("Next Steps:")
print()

if missing:
    print("1. Install dependencies:")
    print(f"   pip install {' '.join(missing)}")
    print()

if result != 0:
    print("2. Start the platform:")
    print("   python run_platform.py")
    print()
    print("3. Open dashboard:")
    print("   http://localhost:8000")
    print()

print("4. Monitor logs:")
print("   Windows: Get-Content logs\\platform.log -Wait -Tail 20")
print("   Linux/Mac: tail -f logs/platform.log")
print()

print("5. Check for issues:")
print("   - Open browser console (F12)")
print("   - Click 'Check API' button on dashboard")
print("   - Look for errors in terminal")
print()