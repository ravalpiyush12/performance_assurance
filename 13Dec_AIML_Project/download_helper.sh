#!/bin/bash

# Download Helper Script for AI Self-Healing Platform
# This script creates the directory structure and file templates

echo "======================================================"
echo "  AI Self-Healing Platform - Download Helper"
echo "======================================================"
echo ""

# Create directory structure
echo "Creating directory structure..."
mkdir -p ai-self-healing-platform/{src/{api,ml,orchestrator,monitoring,chaos},config,logs,tests/{unit,integration},docs}

cd ai-self-healing-platform

# Create README with download instructions
cat > README.md << 'EOF'
# AI/ML-Driven Self-Healing Cloud Platform

## 📥 Download Instructions

You need to copy the code from the Claude conversation artifacts into these files:

### Required Files:

1. **src/ml/anomaly_detector.py**
   - Artifact: "ML Anomaly Detection Service (Python)"
   - Contains: Isolation Forest, time-series forecasting

2. **src/orchestrator/self_healing.py**
   - Artifact: "Self-Healing Orchestration Engine (Python)"
   - Contains: Automated remediation logic

3. **src/monitoring/collector.py**
   - Artifact: "Observability & Metrics Collector (Python)"
   - Contains: Metrics collection, logging, tracing

4. **src/chaos/chaos_engine.py**
   - Artifact: "Chaos Engineering & Automated Testing (Python)"
   - Contains: Failure injection, automated tests

5. **src/api/main.py**
   - Artifact: "FastAPI Integration Server (Python)"
   - Contains: REST API, WebSocket endpoints

6. **dashboard.jsx** (Optional - Frontend)
   - Artifact: "AI-Driven Self-Healing Cloud Dashboard"
   - Contains: React dashboard with real-time charts

7. **setup.sh** (Optional - Auto setup)
   - Artifact: "Quick Start Setup Script (Bash)"
   - Contains: Automated environment setup

### Documentation Files:

8. **docs/DEPLOYMENT_GUIDE.md**
   - Artifact: "Complete Deployment Guide & Setup"

9. **docs/IMPLEMENTATION_CHECKLIST.md**
   - Artifact: "Complete Implementation Checklist"

## 🚀 Quick Start After Downloading

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# OR: venv\Scripts\activate  # On Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the platform
python run_platform.py

# 4. Access the dashboard
# Open: http://localhost:8000
```

## 📝 File Checklist

Mark as you copy each file:

- [ ] src/ml/anomaly_detector.py
- [ ] src/orchestrator/self_healing.py
- [ ] src/monitoring/collector.py
- [ ] src/chaos/chaos_engine.py
- [ ] src/api/main.py
- [ ] dashboard.jsx
- [ ] setup.sh
- [ ] docs/DEPLOYMENT_GUIDE.md
- [ ] docs/IMPLEMENTATION_CHECKLIST.md

## 🔍 How to Verify

After copying all files:

```bash
# Check all files exist
ls -R src/

# Should show:
# src/api/main.py
# src/ml/anomaly_detector.py
# src/orchestrator/self_healing.py
# src/monitoring/collector.py
# src/chaos/chaos_engine.py
```

## 📚 Need Help?

Refer to docs/IMPLEMENTATION_CHECKLIST.md for step-by-step setup guide.
EOF

# Create requirements.txt
cat > requirements.txt << 'EOF'
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
EOF

# Create configuration
cat > config/config.yaml << 'EOF'
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
EOF

# Create .env template
cat > .env.template << 'EOF'
# Environment Variables Template
# Copy to .env and customize

ENVIRONMENT=development
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# Optional: Cloud Integration
# AWS_ACCESS_KEY_ID=your_key
# AWS_SECRET_ACCESS_KEY=your_secret
# AZURE_SUBSCRIPTION_ID=your_subscription
EOF

# Create __init__.py files
touch src/__init__.py
touch src/{api,ml,orchestrator,monitoring,chaos}/__init__.py
touch tests/__init__.py

# Create placeholder files with instructions
for file in src/ml/anomaly_detector.py src/orchestrator/self_healing.py src/monitoring/collector.py src/chaos/chaos_engine.py src/api/main.py; do
    cat > "$file" << 'PLACEHOLDER'
"""
PLACEHOLDER FILE - REPLACE WITH ACTUAL CODE

Copy the code from the Claude conversation artifact into this file.

Artifact name corresponds to the file path:
- src/ml/anomaly_detector.py          → "ML Anomaly Detection Service"
- src/orchestrator/self_healing.py    → "Self-Healing Orchestration Engine"
- src/monitoring/collector.py         → "Observability & Metrics Collector"
- src/chaos/chaos_engine.py           → "Chaos Engineering & Automated Testing"
- src/api/main.py                     → "FastAPI Integration Server"

After copying, delete this comment block and verify the code.
"""

# TODO: Copy code from Claude conversation artifact
pass
PLACEHOLDER
done

# Create run script
cat > run_platform.py << 'EOF'
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
        # Check if it's still a placeholder
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
EOF

chmod +x run_platform.py

# Create Docker files
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/
COPY run_platform.py .

RUN mkdir -p logs

EXPOSE 8000

CMD ["python", "run_platform.py"]
EOF

cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  platform:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
      - ./config:/app/config
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
EOF

# Create .gitignore
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
*$py.class
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
EOF

# Create download checklist
cat > DOWNLOAD_CHECKLIST.txt << 'EOF'
AI Self-Healing Platform - Download Checklist
==============================================

STEP 1: Copy Python Files from Claude Artifacts
------------------------------------------------
[ ] src/ml/anomaly_detector.py
    Artifact: "ML Anomaly Detection Service (Python)"
    
[ ] src/orchestrator/self_healing.py
    Artifact: "Self-Healing Orchestration Engine (Python)"
    
[ ] src/monitoring/collector.py
    Artifact: "Observability & Metrics Collector (Python)"
    
[ ] src/chaos/chaos_engine.py
    Artifact: "Chaos Engineering & Automated Testing (Python)"
    
[ ] src/api/main.py
    Artifact: "FastAPI Integration Server (Python)"

STEP 2: Copy Optional Files
----------------------------
[ ] dashboard.jsx (Frontend)
    Artifact: "AI-Driven Self-Healing Cloud Dashboard"
    
[ ] setup.sh (Auto setup)
    Artifact: "Quick Start Setup Script (Bash)"

STEP 3: Copy Documentation
---------------------------
[ ] docs/DEPLOYMENT_GUIDE.md
    Artifact: "Complete Deployment Guide & Setup"
    
[ ] docs/IMPLEMENTATION_CHECKLIST.md
    Artifact: "Complete Implementation Checklist"

STEP 4: Verify Installation
----------------------------
[ ] All files copied (no PLACEHOLDER content)
[ ] Virtual environment created
[ ] Dependencies installed (pip install -r requirements.txt)
[ ] Configuration reviewed (config/config.yaml)

STEP 5: Test Run
----------------
[ ] Run: python run_platform.py
[ ] Access: http://localhost:8000
[ ] Check: http://localhost:8000/docs
[ ] Verify: curl http://localhost:8000/api/v1/status

==============================================
After completing all steps, you're ready to go!
EOF

# Create success message
echo ""
echo "======================================================"
echo "✅ Directory structure created successfully!"
echo "======================================================"
echo ""
echo "📁 Location: $(pwd)"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Copy code from Claude artifacts into src/ files"
echo "   (See DOWNLOAD_CHECKLIST.txt for detailed list)"
echo ""
echo "2. Create virtual environment:"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo ""
echo "3. Install dependencies:"
echo "   pip install -r requirements.txt"
echo ""
echo "4. Run the platform:"
echo "   python run_platform.py"
echo ""
echo "📝 Files to review:"
echo "   - README.md (Overview and instructions)"
echo "   - DOWNLOAD_CHECKLIST.txt (Step-by-step checklist)"
echo "   - requirements.txt (Python dependencies)"
echo "   - config/config.yaml (Configuration)"
echo ""
echo "🎯 All placeholder files are marked with instructions"
echo "   Replace them with code from Claude conversation"
echo ""
echo "======================================================"
