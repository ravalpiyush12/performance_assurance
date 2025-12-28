#!/usr/bin/env python3
"""
Main Platform Runner
Save as: run_platform.py

Run with: python run_platform.py
"""

import sys
import os
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 9):
        logger.error("❌ Python 3.9+ required")
        logger.error(f"Current version: {sys.version}")
        return False
    logger.info(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_dependencies():
    """Check required packages"""
    required = {
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn',
        'sklearn': 'scikit-learn',
        'numpy': 'numpy',
        'psutil': 'psutil'
    }
    
    missing = []
    for import_name, package_name in required.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)
    
    if missing:
        logger.error("❌ Missing packages:")
        for pkg in missing:
            logger.error(f"   - {pkg}")
        logger.error("\n💡 Install with: pip install -r requirements.txt")
        return False
    
    logger.info("✅ All dependencies installed")
    return True

def check_structure():
    """Check directory structure"""
    required_dirs = [
        'src',
        'src/api',
        'src/ml',
        'src/orchestrator',
        'src/monitoring',
        'config',
        'logs'
    ]
    
    missing = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing.append(dir_path)
    
    if missing:
        logger.error("❌ Missing directories:")
        for dir_name in missing:
            logger.error(f"   - {dir_name}")
        logger.error("\n💡 Create with: mkdir -p src/{api,ml,orchestrator,monitoring,chaos} config logs")
        return False
    
    logger.info("✅ Directory structure correct")
    return True

def check_files():
    """Check required files"""
    required_files = {
        'src/api/main.py': 'Main API server',
        'src/ml/anomaly_detector.py': 'ML anomaly detector',
        'src/orchestrator/self_healing.py': 'Self-healing orchestrator'
    }
    
    missing = []
    for file_path, description in required_files.items():
        if not Path(file_path).exists():
            missing.append((file_path, description))
    
    if missing:
        logger.error("❌ Missing files:")
        for file_path, desc in missing:
            logger.error(f"   - {file_path} ({desc})")
        logger.error("\n💡 Copy files from Claude artifacts")
        return False
    
    logger.info("✅ All required files present")
    return True

def create_logs_dir():
    """Ensure logs directory exists"""
    Path('logs').mkdir(exist_ok=True)

def main():
    """Main entry point"""
    print("=" * 70)
    print("  🤖 AI/ML-Driven Self-Healing Platform")
    print("=" * 70)
    print()
    
    logger.info("Running pre-flight checks...")
    print()
    
    # Run checks
    if not check_python_version():
        sys.exit(1)
    
    if not check_structure():
        sys.exit(1)
    
    if not check_files():
        print()
        print("=" * 70)
        print("📋 SETUP INSTRUCTIONS:")
        print("=" * 70)
        print()
        print("Copy these files from Claude artifacts:")
        print()
        print("1. src/api/main.py")
        print("   → Artifact: 'Main API Server - Complete Integration'")
        print()
        print("2. src/ml/anomaly_detector.py")
        print("   → Artifact: 'Complete ML Anomaly Detector'")
        print()
        print("3. src/orchestrator/self_healing.py")
        print("   → Artifact: 'Self-Healing Orchestration Engine'")
        print()
        print("4. src/monitoring/collector.py")
        print("   → Artifact: 'Observability & Metrics Collector'")
        print()
        print("=" * 70)
        sys.exit(1)
    
    if not check_dependencies():
        sys.exit(1)
    
    # Create logs directory
    create_logs_dir()
    
    # All checks passed
    print()
    logger.info("✅ All checks passed!")
    print()
    print("=" * 70)
    print("  🚀 Starting Platform...")
    print("=" * 70)
    print()
    print("📊 Dashboard:     http://localhost:8000")
    print("📚 API Docs:      http://localhost:8000/docs")
    print("🔧 Health Check:  http://localhost:8000/api/v1/status")
    print()
    print("Press Ctrl+C to stop")
    print()
    print("=" * 70)
    print()
    
    # Start the server
    try:
        import uvicorn
        
        uvicorn.run(
            "src.api.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("\n💡 Make sure all files are copied correctly")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print()
        logger.info("✋ Platform stopped by user")
        print()
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"❌ Error starting platform: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
    