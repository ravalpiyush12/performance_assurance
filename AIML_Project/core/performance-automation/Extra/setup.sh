#!/bin/bash

###############################################################################
# Performance Center Jenkins Automation - Quick Setup Script
# This script helps you set up the automation framework quickly
###############################################################################

set -e

echo "=========================================="
echo "Performance Center Automation Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check prerequisites
echo "Step 1: Checking prerequisites..."

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python 3 installed (version $PYTHON_VERSION)"
else
    print_error "Python 3 not found. Please install Python 3.7+"
    exit 1
fi

# Check pip
if command -v pip3 &> /dev/null; then
    print_success "pip3 is available"
else
    print_error "pip3 not found. Please install pip"
    exit 1
fi

echo ""
echo "Step 2: Installing Python dependencies..."

pip3 install --user -r scripts/requirements.txt

if [ $? -eq 0 ]; then
    print_success "Dependencies installed successfully"
else
    print_error "Failed to install dependencies"
    exit 1
fi

echo ""
echo "Step 3: Setting up directory structure..."

# Create necessary directories
mkdir -p results
mkdir -p logs

print_success "Directory structure created"

echo ""
echo "Step 4: Making scripts executable..."

chmod +x scripts/*.py

print_success "Scripts are now executable"

echo ""
echo "Step 5: Validating scripts..."

# Test Python scripts
python3 scripts/pc_automation.py --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    print_success "pc_automation.py validated"
else
    print_warning "pc_automation.py validation warning (may be normal)"
fi

python3 scripts/results_analyzer.py --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    print_success "results_analyzer.py validated"
else
    print_warning "results_analyzer.py validation warning (may be normal)"
fi

echo ""
echo "=========================================="
echo "✓ Setup completed successfully!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. Configure Jenkins credentials (ID: pc-credentials)"
echo "2. Create new Pipeline job in Jenkins"
echo "3. Copy Jenkinsfile content to pipeline script"
echo "4. Update default parameters in Jenkinsfile:"
echo "   - PC_SERVER"
echo "   - PC_DOMAIN"
echo "   - PC_PROJECT"
echo "   - EMAIL_RECIPIENTS"
echo "5. Run 'Build with Parameters' in Jenkins"
echo ""
echo "For detailed instructions, see README.md"
echo "=========================================="
