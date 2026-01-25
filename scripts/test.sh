#!/bin/bash

# CI/CD test script for zugspaet
# Run this locally before pushing to verify everything works

set -e  # Exit on first error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

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
if ruff check .; then
    print_success "Ruff linting passed"
else
    print_error "Ruff linting failed"
    exit 1
fi

echo ""
print_step "Running ruff format check..."
if ruff format --check .; then
    print_success "Ruff format check passed"
else
    print_error "Ruff format check failed (run 'ruff format .' to fix)"
    exit 1
fi

echo ""
print_step "Running backend tests (pytest)..."
if pytest tests/ -v --cov=. --cov-report=term-missing; then
    print_success "Backend tests passed"
else
    print_error "Backend tests failed"
    exit 1
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
