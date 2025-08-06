#!/bin/bash

# Script to run tests by category
# Usage: ./run_tests.sh [unit|integration|e2e|all]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function print_header() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
}

function run_unit_tests() {
    print_header "Running Unit Tests (Mocked Dependencies)"
    pdm run pytest tests/analysis/unit/ -v --tb=short -m "unit"
}

function run_integration_tests() {
    print_header "Running Integration Tests (Real Services)"
    echo -e "${YELLOW}Note: These tests require real services to be configured:${NC}"
    echo -e "${YELLOW}  - Google Cloud Storage (GCS_BUCKET_NAME)${NC}"
    echo -e "${YELLOW}  - Gemini API (GEMINI_API_KEY or GOOGLE_API_KEY)${NC}"
    echo -e "${YELLOW}  - Neon Database (DATABASE_URL)${NC}"
    echo ""
    pdm run pytest tests/analysis/integration/ -v --tb=short -m "integration"
}

function run_e2e_tests() {
    print_header "Running E2E Tests (HTTP Endpoints)"
    pdm run pytest tests/analysis/e2e/ -v --tb=short -m "e2e"
}

function run_all_tests() {
    print_header "Running All Tests"
    run_unit_tests
    run_integration_tests
    run_e2e_tests
}

# Main script logic
case "${1:-all}" in
    unit)
        run_unit_tests
        ;;
    integration)
        run_integration_tests
        ;;
    e2e)
        run_e2e_tests
        ;;
    all)
        run_all_tests
        ;;
    *)
        echo -e "${RED}Invalid option: $1${NC}"
        echo "Usage: $0 [unit|integration|e2e|all]"
        echo ""
        echo "Options:"
        echo "  unit         - Run unit tests (mocked dependencies)"
        echo "  integration  - Run integration tests (real services)"
        echo "  e2e          - Run end-to-end tests (HTTP endpoints)"
        echo "  all          - Run all tests (default)"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Tests completed!${NC}"