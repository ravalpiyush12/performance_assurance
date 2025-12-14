#!/usr/bin/env python3
"""
Main runner for AI Self-Healing Platform

Usage: python run_platform.py

This script starts the FastAPI server and initializes all components.
Save as: run_platform.py (in the root of ai-self-healing-platform folder)
"""

import sys
import os
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required")
        logger.error(f"Current version: {sys.version}")
        return False
    logger.info(f"Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_required_files():
    """Check if all required Python files exist"""
    required_files = [
        'src/api/main.py',
        'src/ml/anomaly_detector.py',
        'src/orchestrator/self_healing.py',
        'src/monitoring/collector.py',
        'src/chaos/chaos_engine.py'
    ]
    
    missing = []
    placeholder_files = []
    
    for file_path in required_files:
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            missing.append(file_path)
        else:
            # Check if it's still a placeholder
            try:
                content = path.read_text(encoding='utf-8')
                if 'PLACEHOLDER FILE' in content or 'TODO: Copy code' in content:
                    placeholder_files.append(file_path)
            except Exception as e:
                logger.warning(f"Could not read {file_path}: {e}")
    
    if missing:
        logger.error("❌ Missing required files:")
        for file in missing:
            logger.error(f"   - {file}")
        return False
    
    if placeholder_files:
        logger.error("❌ These files still contain placeholder code:")
        for file in placeholder_files:
            logger.error(f"   - {file}")
        logger.error("\n📝 Please copy the actual code from Claude artifacts into these files.")
        return False
    
    logger.info("✅ All required files found")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = {
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn',
        'pydantic': 'pydantic',
        'sklearn': 'scikit-learn',
        'numpy': 'numpy',
        'psutil': 'psutil'
    }
    
    missing_packages = []
    
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        logger.error("❌ Missing required packages:")
        for package in missing_packages:
            logger.error(f"   - {package}")
        logger.error("\n💡 Install with: pip install -r requirements.txt")
        return False
    
    logger.info("✅ All required packages installed")
    return True

def check_directory_structure():
    """Check if directory structure is correct"""
    required_dirs = [
        'src',
        'src/api',
        'src/ml',
        'src/orchestrator',
        'src/monitoring',
        'src/chaos',
        'config',
        'logs'
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        logger.error("❌ Missing required directories:")
        for dir_name in missing_dirs:
            logger.error(f"   - {dir_name}")
        logger.error("\n💡 Run setup.bat or create directories manually")
        return False
    
    logger.info("✅ Directory structure correct")
    return True

def create_logs_directory():
    """Ensure logs directory exists"""
    logs_dir = Path('logs')
    if not logs_dir.exists():
        logs_dir.mkdir(parents=True)
        logger.info("Created logs directory")

def main():
    """Main entry point"""
    print("=" * 60)
    print("  AI/ML-Driven Self-Healing Platform")
    print("=" * 60)
    print()
    
    # Run checks
    logger.info("Running pre-flight checks...")
    print()
    
    if not check_python_version():
        sys.exit(1)
    
    if not check_directory_structure():
        sys.exit(1)
    
    if not check_required_files():
        print()
        print("=" * 60)
        print("📋 SETUP INSTRUCTIONS:")
        print("=" * 60)
        print()
        print("Copy these artifacts from the Claude conversation:")
        print()
        print("1. src/api/main.py")
        print("   → Artifact: 'FastAPI Integration Server'")
        print()
        print("2. src/ml/anomaly_detector.py")
        print("   → Artifact: 'ML Anomaly Detection Service'")
        print()
        print("3. src/orchestrator/self_healing.py")
        print("   → Artifact: 'Self-Healing Orchestration Engine'")
        print()
        print("4. src/monitoring/collector.py")
        print("   → Artifact: 'Observability & Metrics Collector'")
        print()
        print("5. src/chaos/chaos_engine.py")
        print("   → Artifact: 'Chaos Engineering & Automated Testing'")
        print()
        print("=" * 60)
        sys.exit(1)
    
    if not check_dependencies():
        print()
        print("💡 To install dependencies, run:")
        print("   pip install -r requirements.txt")
        print()
        sys.exit(1)
    
    # Create logs directory
    create_logs_directory()
    
    # All checks passed
    print()
    logger.info("✅ All checks passed!")
    print()
    print("=" * 60)
    print("  Starting Platform...")
    print("=" * 60)
    print()
    print("📊 Dashboard:     http://localhost:8000")
    print("📚 API Docs:      http://localhost:8000/docs")
    print("🔧 Interactive:   http://localhost:8000/redoc")
    print()
    print("Press Ctrl+C to stop")
    print()
    print("=" * 60)
    print()
    
    # Start the server
    try:
        import uvicorn
        
        # Import the FastAPI app
        sys.path.insert(0, str(Path.cwd()))
        
        uvicorn.run(
            "src.api.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True
        )
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("\n💡 Make sure uvicorn is installed:")
        logger.error("   pip install uvicorn")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print()
        logger.info("Platform stopped by user")
        print()
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"❌ Error starting platform: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
    