"""
Test Logging Setup - Windows Compatible Version
Save as: test_logging.py

Run with: python test_logging.py
"""

import logging
import os
import sys
from pathlib import Path

# Windows UTF-8 fix
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Create logs directory
logs_dir = Path('logs')
logs_dir.mkdir(exist_ok=True)

print("=" * 60)
print("Testing Logging Setup - Windows Compatible")
print("=" * 60)
print()

# Setup logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/platform.log', mode='a', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Test logs
print("1. Checking logs directory...")
if logs_dir.exists():
    print(f"   [OK] Logs directory exists: {logs_dir.absolute()}")
else:
    print(f"   [ERROR] Logs directory missing!")

print()
print("2. Testing logging...")
logger.info("[OK] This is a test INFO log")
logger.warning("[WARNING] This is a test WARNING log")
logger.error("[ERROR] This is a test ERROR log")

print()
print("3. Checking log file...")
log_file = Path('logs/platform.log')
if log_file.exists():
    print(f"   [OK] Log file exists: {log_file.absolute()}")
    print(f"   [INFO] File size: {log_file.stat().st_size} bytes")
    
    # Show last few lines
    if log_file.stat().st_size > 0:
        print()
        print("   Last 5 lines from log file:")
        print("   " + "-" * 50)
        try:
            with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
                for line in lines[-5:]:
                    print(f"   {line.rstrip()}")
        except Exception as e:
            print(f"   [ERROR] Could not read log file: {e}")
        print("   " + "-" * 50)
    else:
        print("   [WARNING] Log file is empty")
else:
    print(f"   [ERROR] Log file not found!")

print()
print("=" * 60)
print("Logging Test Complete!")
print("=" * 60)
print()

# Summary
if log_file.exists() and log_file.stat().st_size > 0:
    print("[SUCCESS] Logging is working correctly!")
    print()
    print("You should see:")
    print("  - Log messages above")
    print("  - Same messages in logs/platform.log")
    print()
else:
    print("[WARNING] Log file exists but is empty or missing")
    print()
    print("Possible causes:")
    print("  1. First time running (this is normal)")
    print("  2. Permission issues")
    print("  3. Encoding problems (should be fixed now)")
    print()

# Instructions
print("=" * 60)
print("How to view logs:")
print("=" * 60)
print()
print("PowerShell:")
print("  Get-Content logs\\platform.log")
print("  Get-Content logs\\platform.log -Wait    # Real-time")
print()
print("CMD:")
print("  type logs\\platform.log")
print()
print("Notepad:")
print("  notepad logs\\platform.log")
print()
print("=" * 60)
print()

# Platform-specific tips
if sys.platform == 'win32':
    print("Windows Tips:")
    print("  1. Run 'chcp 65001' before starting platform (UTF-8)")
    print("  2. Use PowerShell for better Unicode support")
    print("  3. Logs also appear in terminal when platform runs")
    print()
    