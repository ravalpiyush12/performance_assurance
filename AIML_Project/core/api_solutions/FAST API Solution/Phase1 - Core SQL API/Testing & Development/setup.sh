#!/bin/bash

# Oracle SQL API - Setup Script
# This script sets up the development environment

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Oracle SQL API - Setup${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    echo -e "${RED}Error: Python 3.11+ required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"
echo ""

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists${NC}"
fi
echo ""

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip > /dev/null
echo -e "${GREEN}✓ Pip upgraded${NC}"
echo ""

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp .env.template .env
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}⚠ Please edit .env with your Oracle credentials${NC}"
else
    echo -e "${YELLOW}.env file already exists${NC}"
fi
echo ""

# Create logs directory
echo -e "${YELLOW}Creating logs directory...${NC}"
mkdir -p logs/audit
echo -e "${GREEN}✓ Logs directory created${NC}"
echo ""

# Make scripts executable
echo -e "${YELLOW}Setting script permissions...${NC}"
chmod +x deploy-to-ecs.sh
echo -e "${GREEN}✓ Scripts are executable${NC}"
echo ""

# Test imports
echo -e "${YELLOW}Testing Python imports...${NC}"
python3 -c "
import cx_Oracle
import fastapi
import uvicorn
print('All imports successful')
" 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ All Python packages installed correctly${NC}"
else
    echo -e "${RED}✗ Some imports failed${NC}"
fi
echo ""

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Edit .env file with your Oracle credentials:"
echo "   nano .env"
echo ""
echo "2. Start the API locally:"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "3. Or use Docker:"
echo "   docker-compose up -d"
echo ""
echo "4. Run tests:"
echo "   python test_api.py"
echo ""
echo "5. View API documentation:"
echo "   http://localhost:8000/docs"
echo ""
echo -e "${GREEN}For deployment to ECS:${NC}"
echo "   ./deploy-to-ecs.sh"
echo ""