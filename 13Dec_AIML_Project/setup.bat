@echo off
REM Windows Batch Setup Script for AI Self-Healing Platform
REM Double-click this file to run or: setup.bat

echo ======================================================
echo   AI Self-Healing Platform - Windows Setup
echo ======================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Python is not installed or not in PATH
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo [+] Python detected
python --version
echo.

REM Create directory structure
echo Creating project structure...
mkdir ai-self-healing-platform 2>nul
cd ai-self-healing-platform

mkdir src\api 2>nul
mkdir src\ml 2>nul
mkdir src\orchestrator 2>nul
mkdir src\monitoring 2>nul
mkdir src\chaos 2>nul
mkdir config 2>nul
mkdir logs 2>nul
mkdir tests\unit 2>nul
mkdir tests\integration 2>nul
mkdir docs 2>nul

echo [+] Directories created
echo.

REM Create requirements.txt
echo Creating requirements.txt...
(
echo # Web Framework
echo fastapi==0.104.1
echo uvicorn[standard]==0.24.0
echo pydantic==2.5.0
echo python-multipart==0.0.6
echo.
echo # Machine Learning
echo scikit-learn==1.3.2
echo numpy==1.26.2
echo pandas==2.1.3
echo.
echo # System Monitoring
echo psutil==5.9.6
echo.
echo # Async ^& HTTP
echo aiohttp==3.9.1
echo websockets==12.0
echo httpx==0.25.2
echo.
echo # Configuration
echo pyyaml==6.0.1
echo python-dotenv==1.0.0
echo.
echo # Testing
echo pytest==7.4.3
echo pytest-asyncio==0.21.1
echo pytest-cov==4.1.0
echo.
echo # Optional: Monitoring
echo prometheus-client==0.19.0
) > requirements.txt

echo [+] requirements.txt created
echo.

REM Create config.yaml
echo Creating configuration...
(
echo app:
echo   name: "AI Self-Healing Platform"
echo   version: "1.0.0"
echo   host: "0.0.0.0"
echo   port: 8000
echo   debug: true
echo.
echo anomaly_detection:
echo   contamination: 0.1
echo   window_size: 100
echo   training_threshold: 20
echo.
echo metrics:
echo   collection_interval: 5
echo   buffer_size: 1000
echo.
echo healing:
echo   cooldown_duration: 60
echo   max_retries: 3
echo   enabled: true
echo.
echo chaos:
echo   enabled: true
echo   auto_run_tests: false
echo.
echo logging:
echo   level: "INFO"
echo   file: "logs/platform.log"
) > config\config.yaml

echo [+] Configuration created
echo.

REM Create __init__.py files
echo Creating Python package files...
type nul > src\__init__.py
type nul > src\api\__init__.py
type nul > src\ml\__init__.py
type nul > src\orchestrator\__init__.py
type nul > src\monitoring\__init__.py
type nul > src\chaos\__init__.py
type nul > tests\__init__.py

echo [+] Package files created
echo.

REM Create placeholder Python files
echo Creating placeholder code files...

(
echo """
echo PLACEHOLDER FILE - REPLACE WITH ACTUAL CODE
echo.
echo Copy the code from Claude conversation artifact into this file.
echo.
echo Artifact: "ML Anomaly Detection Service %%LPAREN%%Python%%RPAREN%%"
echo.
echo After copying, delete this comment and verify the code.
echo """
echo.
echo # TODO: Copy code from Claude conversation artifact
echo pass
) > src\ml\anomaly_detector.py

(
echo """
echo PLACEHOLDER FILE - REPLACE WITH ACTUAL CODE
echo.
echo Copy the code from Claude conversation artifact into this file.
echo.
echo Artifact: "Self-Healing Orchestration Engine %%LPAREN%%Python%%RPAREN%%"
echo.
echo After copying, delete this comment and verify the code.
echo """
echo.
echo # TODO: Copy code from Claude conversation artifact
echo pass
) > src\orchestrator\self_healing.py

(
echo """
echo PLACEHOLDER FILE - REPLACE WITH ACTUAL CODE
echo.
echo Copy the code from Claude conversation artifact into this file.
echo.
echo Artifact: "Observability ^& Metrics Collector %%LPAREN%%Python%%RPAREN%%"
echo.
echo After copying, delete this comment and verify the code.
echo """
echo.
echo # TODO: Copy code from Claude conversation artifact
echo pass
) > src\monitoring\collector.py

(
echo """
echo PLACEHOLDER FILE - REPLACE WITH ACTUAL CODE
echo.
echo Copy the code from Claude conversation artifact into this file.
echo.
echo Artifact: "Chaos Engineering ^& Automated Testing %%LPAREN%%Python%%RPAREN%%"
echo.
echo After copying, delete this comment and verify the code.
echo """
echo.
echo # TODO: Copy code from Claude conversation artifact
echo pass
) > src\chaos\chaos_engine.py

(
echo """
echo PLACEHOLDER FILE - REPLACE WITH ACTUAL CODE
echo.
echo Copy the code from Claude conversation artifact into this file.
echo.
echo Artifact: "FastAPI Integration Server %%LPAREN%%Python%%RPAREN%%"
echo.
echo After copying, delete this comment and verify the code.
echo """
echo.
echo # TODO: Copy code from Claude conversation artifact
echo pass
) > src\api\main.py

echo [+] Placeholder files created
echo.

REM Create run_platform.py
echo Creating run script...
(
echo #!/usr/bin/env python3
echo """Main runner for AI Self-Healing Platform"""
echo.
echo import sys
echo from pathlib import Path
echo.
echo # Check required files
echo required_files = [
echo     'src/api/main.py',
echo     'src/ml/anomaly_detector.py',
echo     'src/orchestrator/self_healing.py',
echo     'src/monitoring/collector.py',
echo     'src/chaos/chaos_engine.py'
echo ]
echo.
echo missing = []
echo for file in required_files:
echo     path = Path^(file^)
echo     if not path.exists^(^):
echo         missing.append^(file^)
echo     else:
echo         content = path.read_text^(^)
echo         if 'PLACEHOLDER FILE' in content:
echo             missing.append^(f"{file} %%LPAREN%%needs code%%RPAREN%%"^)
echo.
echo if missing:
echo     print^("Missing or incomplete files:"^)
echo     for file in missing:
echo         print^(f"   - {file}"^)
echo     print^("\nPlease copy code from Claude artifacts."^)
echo     sys.exit^(1^)
echo.
echo print^("Starting platform..."^)
echo.
echo try:
echo     import uvicorn
echo     uvicorn.run^("src.api.main:app", host="0.0.0.0", port=8000, reload=True^)
echo except ImportError:
echo     print^("uvicorn not installed. Run: pip install -r requirements.txt"^)
echo     sys.exit^(1^)
echo except Exception as e:
echo     print^(f"Error: {e}"^)
echo     sys.exit^(1^)
) > run_platform.py

echo [+] Run script created
echo.

REM Create README
echo Creating README...
(
echo # AI/ML-Driven Self-Healing Cloud Platform
echo.
echo ## Quick Start for Windows
echo.
echo ### Step 1: Copy Code Files
echo.
echo Copy these artifacts from Claude conversation:
echo.
echo 1. src\ml\anomaly_detector.py
echo    - Artifact: "ML Anomaly Detection Service"
echo.
echo 2. src\orchestrator\self_healing.py
echo    - Artifact: "Self-Healing Orchestration Engine"
echo.
echo 3. src\monitoring\collector.py
echo    - Artifact: "Observability ^& Metrics Collector"
echo.
echo 4. src\chaos\chaos_engine.py
echo    - Artifact: "Chaos Engineering ^& Automated Testing"
echo.
echo 5. src\api\main.py
echo    - Artifact: "FastAPI Integration Server"
echo.
echo ### Step 2: Setup Environment
echo.
echo Double-click: start.bat
echo.
echo OR manually:
echo ```
echo python -m venv venv
echo venv\Scripts\activate
echo pip install -r requirements.txt
echo python run_platform.py
echo ```
echo.
echo ### Step 3: Access Platform
echo.
echo - Dashboard: http://localhost:8000
echo - API Docs: http://localhost:8000/docs
echo.
echo ## Troubleshooting
echo.
echo **Python not found**: Install from https://www.python.org/downloads/
echo **Port in use**: netstat -ano ^| findstr :8000
echo **Dependencies fail**: Try: pip install --upgrade pip
) > README.md

echo [+] README created
echo.

REM Create start.bat
echo Creating start.bat...
(
echo @echo off
echo echo ====================================================
echo echo   Starting AI Self-Healing Platform
echo echo ====================================================
echo echo.
echo.
echo if not exist "venv\" ^(
echo     echo Creating virtual environment...
echo     python -m venv venv
echo     if errorlevel 1 ^(
echo         echo [X] Failed to create virtual environment
echo         pause
echo         exit /b 1
echo     ^)
echo     echo [+] Virtual environment created
echo ^)
echo.
echo echo Activating virtual environment...
echo call venv\Scripts\activate.bat
echo.
echo echo Installing dependencies...
echo pip install -r requirements.txt
echo if errorlevel 1 ^(
echo     echo [X] Failed to install dependencies
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo.
echo echo ====================================================
echo echo   Platform Starting...
echo echo ====================================================
echo echo.
echo echo Dashboard: http://localhost:8000
echo echo API Docs:  http://localhost:8000/docs
echo echo.
echo echo Press Ctrl+C to stop
echo echo.
echo.
echo python run_platform.py
echo.
echo pause
) > start.bat

echo [+] start.bat created
echo.

REM Create checklist
(
echo AI Self-Healing Platform - Download Checklist
echo ======================================================
echo.
echo STEP 1: Copy Python Files from Claude
echo -----------------------------------------------------
echo [ ] src\ml\anomaly_detector.py
echo     Artifact: "ML Anomaly Detection Service"
echo.
echo [ ] src\orchestrator\self_healing.py
echo     Artifact: "Self-Healing Orchestration Engine"
echo.
echo [ ] src\monitoring\collector.py
echo     Artifact: "Observability ^& Metrics Collector"
echo.
echo [ ] src\chaos\chaos_engine.py
echo     Artifact: "Chaos Engineering ^& Automated Testing"
echo.
echo [ ] src\api\main.py
echo     Artifact: "FastAPI Integration Server"
echo.
echo STEP 2: Run Setup
echo -----------------------------------------------------
echo [ ] Double-click start.bat
echo     OR
echo [ ] python -m venv venv
echo [ ] venv\Scripts\activate
echo [ ] pip install -r requirements.txt
echo.
echo STEP 3: Test
echo -----------------------------------------------------
echo [ ] python run_platform.py
echo [ ] Open: http://localhost:8000
echo.
echo ======================================================
) > DOWNLOAD_CHECKLIST.txt

echo [+] Checklist created
echo.

REM Create .gitignore
(
echo __pycache__/
echo *.py[cod]
echo venv/
echo *.log
echo logs/
echo .env
) > .gitignore

echo [+] .gitignore created
echo.

REM Summary
echo ======================================================
echo [SUCCESS] Setup Complete!
echo ======================================================
echo.
echo Location: %CD%
echo.
echo Next Steps:
echo.
echo 1. Copy code from Claude artifacts to src\ files
echo    ^(See DOWNLOAD_CHECKLIST.txt^)
echo.
echo 2. Double-click start.bat to run everything
echo.
echo 3. Access http://localhost:8000
echo.
echo Files created:
echo   - README.md
echo   - DOWNLOAD_CHECKLIST.txt
echo   - start.bat ^(one-click start^)
echo   - requirements.txt
echo   - config\config.yaml
echo.
echo ======================================================
echo.
pause
