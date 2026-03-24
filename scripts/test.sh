#!/bin/bash

# CI/CD test script for zugspaet
# Run this locally before pushing to verify everything works

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
RUFF_BIN="$PROJECT_ROOT/.venv/bin/ruff"

cd "$PROJECT_ROOT"

if [ ! -x "$PYTHON_BIN" ]; then
    echo "Missing virtualenv python at $PYTHON_BIN"
    echo "Create it first, for example: python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt -r test_requirements.txt"
    exit 1
fi

if [ ! -x "$RUFF_BIN" ]; then
    echo "Missing ruff at $RUFF_BIN"
    echo "Install test/dev dependencies into .venv first."
    exit 1
fi

echo "================================================"
echo "  zugspaet CI/CD Local Test Runner"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${YELLOW}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Backend tests
echo ""
print_step "Running backend linting (ruff)..."
if "$RUFF_BIN" check .; then
    print_success "Ruff linting passed"
else
    print_error "Ruff linting failed"
    exit 1
fi

echo ""
print_step "Running ruff format check..."
if "$RUFF_BIN" format --check .; then
    print_success "Ruff format check passed"
else
    print_error "Ruff format check failed (run 'ruff format .' to fix)"
    exit 1
fi

echo ""
print_step "Running backend tests (pytest)..."
if "$PYTHON_BIN" -m pytest tests/ -v -m "not integration" --cov=. --cov-report=term-missing; then
    print_success "Backend tests passed"
else
    print_error "Backend tests failed"
    exit 1
fi

if [ "${RUN_INTEGRATION_TESTS:-0}" = "1" ]; then
    echo ""
    print_step "Running integration tests..."
    if "$SCRIPT_DIR/test-integration.sh"; then
        print_success "Integration tests passed"
    else
        print_error "Integration tests failed"
        exit 1
    fi
fi

# Frontend tests
echo ""
print_step "Installing frontend dependencies..."
cd frontend
if npm ci; then
    print_success "Frontend dependencies installed"
else
    print_error "Frontend dependency installation failed"
    exit 1
fi

echo ""
print_step "Running TypeScript check..."
if npx tsc --noEmit; then
    print_success "TypeScript check passed"
else
    print_error "TypeScript check failed"
    exit 1
fi

echo ""
print_step "Building frontend..."
if npm run build; then
    print_success "Frontend build passed"
else
    print_error "Frontend build failed"
    exit 1
fi

cd "$PROJECT_ROOT"

echo ""
echo "================================================"
echo -e "${GREEN}  All checks passed! Ready to push.${NC}"
echo "================================================"
