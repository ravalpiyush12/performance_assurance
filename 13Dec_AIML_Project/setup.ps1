# Windows Setup Script for AI Self-Healing Platform
# Run in PowerShell: .\setup.ps1

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  AI Self-Healing Platform - Windows Setup" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Create directory structure
Write-Host "Creating directory structure..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "ai-self-healing-platform" | Out-Null
Set-Location "ai-self-healing-platform"

$directories = @(
    "src\api",
    "src\ml",
    "src\orchestrator",
    "src\monitoring",
    "src\chaos",
    "config",
    "logs",
    "tests\unit",
    "tests\integration",
    "docs"
)

foreach ($dir in $directories) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

Write-Host "[✓] Directories created" -ForegroundColor Green

# Create requirements.txt
Write-Host "Creating requirements.txt..." -ForegroundColor Yellow
@"
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6

# Machine Learning
scikit-learn==1.3.2
numpy==1.26.2
pandas==2.1.3

# System Monitoring
psutil==5.9.6

# Async & HTTP
aiohttp==3.9.1
websockets==12.0
httpx==0.25.2

# Configuration
pyyaml==6.0.1
python-dotenv==1.0.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0

# Optional: Monitoring
prometheus-client==0.19.0
"@ | Out-File -FilePath "requirements.txt" -Encoding UTF8

Write-Host "[✓] requirements.txt created" -ForegroundColor Green

# Create config.yaml
Write-Host "Creating configuration..." -ForegroundColor Yellow
@"
app:
  name: "AI Self-Healing Platform"
  version: "1.0.0"
  host: "0.0.0.0"
  port: 8000
  debug: true

anomaly_detection:
  contamination: 0.1
  window_size: 100
  training_threshold: 20

metrics:
  collection_interval: 5
  buffer_size: 1000

healing:
  cooldown_duration: 60
  max_retries: 3
  enabled: true

chaos:
  enabled: true
  auto_run_tests: false

logging:
  level: "INFO"
  file: "logs/platform.log"
"@ | Out-File -FilePath "config\config.yaml" -Encoding UTF8

Write-Host "[✓] Configuration created" -ForegroundColor Green

# Create __init__.py files
Write-Host "Creating __init__.py files..." -ForegroundColor Yellow
$initFiles = @(
    "src\__init__.py",
    "src\api\__init__.py",
    "src\ml\__init__.py",
    "src\orchestrator\__init__.py",
    "src\monitoring\__init__.py",
    "src\chaos\__init__.py",
    "tests\__init__.py"
)

foreach ($file in $initFiles) {
    New-Item -ItemType File -Force -Path $file | Out-Null
}

Write-Host "[✓] __init__.py files created" -ForegroundColor Green

# Create placeholder files
Write-Host "Creating placeholder files..." -ForegroundColor Yellow

$placeholderContent = @"
"""
PLACEHOLDER FILE - REPLACE WITH ACTUAL CODE

Copy the code from the Claude conversation artifact into this file.

Artifact mapping:
- src\ml\anomaly_detector.py          → "ML Anomaly Detection Service"
- src\orchestrator\self_healing.py    → "Self-Healing Orchestration Engine"
- src\monitoring\collector.py         → "Observability & Metrics Collector"
- src\chaos\chaos_engine.py           → "Chaos Engineering & Automated Testing"
- src\api\main.py                     → "FastAPI Integration Server"

After copying, delete this comment and verify the code works.
"""

# TODO: Copy code from Claude conversation artifact
pass
"@

$placeholderFiles = @(
    "src\ml\anomaly_detector.py",
    "src\orchestrator\self_healing.py",
    "src\monitoring\collector.py",
    "src\chaos\chaos_engine.py",
    "src\api\main.py"
)

foreach ($file in $placeholderFiles) {
    $placeholderContent | Out-File -FilePath $file -Encoding UTF8
}

Write-Host "[✓] Placeholder files created" -ForegroundColor Green

# Create run_platform.py
Write-Host "Creating run script..." -ForegroundColor Yellow
@"
#!/usr/bin/env python3
"""
Main runner for AI Self-Healing Platform

Usage: python run_platform.py
"""

import sys
from pathlib import Path

# Check if required files exist
required_files = [
    'src/api/main.py',
    'src/ml/anomaly_detector.py',
    'src/orchestrator/self_healing.py',
    'src/monitoring/collector.py',
    'src/chaos/chaos_engine.py'
]

missing = []
for file in required_files:
    path = Path(file)
    if not path.exists():
        missing.append(file)
    else:
        content = path.read_text()
        if 'PLACEHOLDER FILE' in content:
            missing.append(f"{file} (placeholder - needs actual code)")

if missing:
    print("❌ Missing or incomplete files:")
    for file in missing:
        print(f"   - {file}")
    print("\n📝 Please copy the code from Claude artifacts into these files.")
    print("   See README.md for detailed instructions.")
    sys.exit(1)

print("✅ All files present. Starting platform...")

try:
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
except ImportError:
    print("❌ uvicorn not installed. Run: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error starting platform: {e}")
    sys.exit(1)
"@ | Out-File -FilePath "run_platform.py" -Encoding UTF8

Write-Host "[✓] Run script created" -ForegroundColor Green

# Create README.md
Write-Host "Creating README..." -ForegroundColor Yellow
@"
# AI/ML-Driven Self-Healing Cloud Platform

## 📥 Windows Installation Guide

### Step 1: Copy Code Files

Copy code from Claude conversation artifacts into these files:

1. **src\ml\anomaly_detector.py**
   - Artifact: "ML Anomaly Detection Service (Python)"

2. **src\orchestrator\self_healing.py**
   - Artifact: "Self-Healing Orchestration Engine (Python)"

3. **src\monitoring\collector.py**
   - Artifact: "Observability & Metrics Collector (Python)"

4. **src\chaos\chaos_engine.py**
   - Artifact: "Chaos Engineering & Automated Testing (Python)"

5. **src\api\main.py**
   - Artifact: "FastAPI Integration Server (Python)"

### Step 2: Setup Python Environment

``````powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
``````

### Step 3: Run the Platform

``````powershell
# Run the platform
python run_platform.py

# Access the dashboard
# Open browser: http://localhost:8000
# API docs: http://localhost:8000/docs
``````

### Step 4: Test the API

``````powershell
# Test health endpoint
curl http://localhost:8000/

# Or use PowerShell
Invoke-WebRequest -Uri http://localhost:8000/api/v1/status
``````

## 📋 File Checklist

- [ ] src\ml\anomaly_detector.py
- [ ] src\orchestrator\self_healing.py
- [ ] src\monitoring\collector.py
- [ ] src\chaos\chaos_engine.py
- [ ] src\api\main.py

## 🔧 Troubleshooting

**Issue: Python not found**
``````powershell
# Install Python from: https://www.python.org/downloads/
# Make sure to check "Add Python to PATH" during installation
``````

**Issue: Port 8000 in use**
``````powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID with actual process ID)
taskkill /PID <PID> /F
``````

**Issue: Module not found**
``````powershell
# Make sure virtual environment is activated
.\venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
``````

## 📚 Documentation

See docs\ folder for detailed guides:
- DEPLOYMENT_GUIDE.md
- IMPLEMENTATION_CHECKLIST.md

## 🎯 Quick Commands

``````powershell
# Activate environment
.\venv\Scripts\activate

# Run platform
python run_platform.py

# Run tests
pytest tests\ -v

# Deactivate environment
deactivate
``````
"@ | Out-File -FilePath "README.md" -Encoding UTF8

Write-Host "[✓] README created" -ForegroundColor Green

# Create .gitignore
@"
__pycache__/
*.py[cod]
*`$py.class
*.so
.Python
venv/
env/
*.egg-info/
dist/
build/
logs/
*.log
.vscode/
.idea/
*.swp
.DS_Store
.env
data/
"@ | Out-File -FilePath ".gitignore" -Encoding UTF8

# Create download checklist
@"
AI Self-Healing Platform - Windows Download Checklist
======================================================

STEP 1: Copy Python Files from Claude Artifacts
------------------------------------------------
[ ] src\ml\anomaly_detector.py
    Artifact: "ML Anomaly Detection Service (Python)"
    
[ ] src\orchestrator\self_healing.py
    Artifact: "Self-Healing Orchestration Engine (Python)"
    
[ ] src\monitoring\collector.py
    Artifact: "Observability & Metrics Collector (Python)"
    
[ ] src\chaos\chaos_engine.py
    Artifact: "Chaos Engineering & Automated Testing (Python)"
    
[ ] src\api\main.py
    Artifact: "FastAPI Integration Server (Python)"

STEP 2: Setup Environment
--------------------------
[ ] Open PowerShell as Administrator
[ ] Navigate to project folder
[ ] Create virtual environment: python -m venv venv
[ ] Activate: .\venv\Scripts\activate
[ ] Install dependencies: pip install -r requirements.txt

STEP 3: Verify Installation
----------------------------
[ ] All files copied (no PLACEHOLDER content)
[ ] Virtual environment activated (you'll see (venv) in prompt)
[ ] Dependencies installed successfully
[ ] Configuration reviewed (config\config.yaml)

STEP 4: Test Run
----------------
[ ] Run: python run_platform.py
[ ] Access: http://localhost:8000
[ ] Check API docs: http://localhost:8000/docs
[ ] Test endpoint: Invoke-WebRequest http://localhost:8000/

======================================================
After completing all steps, you're ready to go! 🚀
"@ | Out-File -FilePath "DOWNLOAD_CHECKLIST.txt" -Encoding UTF8

# Create quick start batch file
@"
@echo off
echo ====================================================
echo   AI Self-Healing Platform - Quick Start
echo ====================================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo [+] Virtual environment created
) else (
    echo [+] Virtual environment found
)

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing/updating dependencies...
pip install -r requirements.txt

echo.
echo ====================================================
echo   Starting platform...
echo ====================================================
echo.
echo Dashboard: http://localhost:8000
echo API Docs:  http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop
echo.

python run_platform.py

pause
"@ | Out-File -FilePath "start.bat" -Encoding UTF8

Write-Host "[✓] Batch file created" -ForegroundColor Green

# Final message
Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📁 Location: $PWD" -ForegroundColor Yellow
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Copy code from Claude artifacts to src\ files" -ForegroundColor White
Write-Host "   (See DOWNLOAD_CHECKLIST.txt)" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Double-click 'start.bat' to run everything" -ForegroundColor White
Write-Host "   OR run manually:" -ForegroundColor Gray
Write-Host "   - python -m venv venv" -ForegroundColor Gray
Write-Host "   - .\venv\Scripts\activate" -ForegroundColor Gray
Write-Host "   - pip install -r requirements.txt" -ForegroundColor Gray
Write-Host "   - python run_platform.py" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Access: http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "📝 Files created:" -ForegroundColor Yellow
Write-Host "   - README.md (Instructions)" -ForegroundColor Gray
Write-Host "   - DOWNLOAD_CHECKLIST.txt (Step-by-step)" -ForegroundColor Gray
Write-Host "   - start.bat (One-click start)" -ForegroundColor Gray
Write-Host "   - requirements.txt (Dependencies)" -ForegroundColor Gray
Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
