#!/usr/bin/env python3
"""
Verify installation and dependencies
"""
import sys

def check_imports():
    """Check if all required packages are installed"""
    packages = {
        'cx_Oracle': 'Oracle database connectivity',
        'requests': 'HTTP requests',
        'pandas': 'Data processing',
        'jinja2': 'Template engine'
    }
    
    print("Checking Python packages...\n")
    
    all_ok = True
    for package, description in packages.items():
        try:
            __import__(package)
            print(f"✓ {package:20} - {description}")
        except ImportError:
            print(f"✗ {package:20} - {description} - NOT INSTALLED")
            all_ok = False
    
    return all_ok

def check_modules():
    """Check if all project modules are present"""
    print("\n\nChecking project modules...\n")
    
    modules = [
        'config.config',
        'utils.logger',
        'fetchers.appdynamics_fetcher',
        'fetchers.kibana_fetcher',
        'database.db_handler',
        'orchestrator.monitoring_orchestrator'
    ]
    
    all_ok = True
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module} - {e}")
            all_ok = False
    
    return all_ok

if __name__ == '__main__':
    print("=" * 60)
    print("Performance Monitoring System - Installation Verification")
    print("=" * 60)
    
    packages_ok = check_imports()
    modules_ok = check_modules()
    
    print("\n" + "=" * 60)
    if packages_ok and modules_ok:
        print("✓ All checks passed! System ready.")
        sys.exit(0)
    else:
        print("✗ Some checks failed. Please install missing dependencies.")
        sys.exit(1)