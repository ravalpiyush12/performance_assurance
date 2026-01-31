#!/bin/bash

# ============================================================================
# Test Runner Script
# Runs all tests for the AI/ML Self-Healing Platform
# Usage: ./run_tests.sh [unit|integration|all|coverage]
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}  AI/ML Self-Healing Platform - Test Suite${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest not found${NC}"
    echo "Install with: pip install pytest pytest-cov pytest-asyncio"
    exit 1
fi

# Get test type from argument
TEST_TYPE=${1:-all}

case $TEST_TYPE in
    unit)
        echo -e "${YELLOW}Running unit tests...${NC}"
        pytest tests/unit/ -v --tb=short
        ;;
    
    integration)
        echo -e "${YELLOW}Running integration tests...${NC}"
        pytest tests/integration/ -v --tb=short
        ;;
    
    coverage)
        echo -e "${YELLOW}Running tests with coverage report...${NC}"
        pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing
        echo ""
        echo -e "${GREEN}Coverage report generated: htmlcov/index.html${NC}"
        ;;
    
    all)
        echo -e "${YELLOW}Running all tests...${NC}"
        pytest tests/ -v --tb=short
        ;;
    
    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        echo "Usage: ./run_tests.sh [unit|integration|all|coverage]"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}  Test Run Complete!${NC}"
echo -e "${GREEN}============================================================================${NC}"