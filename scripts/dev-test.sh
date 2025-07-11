#!/bin/bash

# FastAPI Development Testing with Watch Mode
# This script runs tests continuously, re-running them when files change

echo "🧪 Starting Continuous Testing for FastAPI Development..."

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not detected. Activating .venv..."
    source .venv/bin/activate
fi

# Set test environment
export ENVIRONMENT=test

# Ensure test dependencies are installed
echo "📦 Installing test dependencies..."
pip install -r requirements-dev.txt > /dev/null 2>&1

echo "🔄 Starting pytest with watch mode..."
echo "  - Tests will re-run automatically when code changes"
echo "  - Watching: src/ and tests/ directories"
echo "  - Stop with Ctrl+C"
echo ""

# Check if pytest-watch is available
if command -v ptw > /dev/null 2>&1; then
    # Use pytest-watch if available
    ptw --runner "python -m pytest tests/ -v --tb=short" src/ tests/
else
    echo "📋 pytest-watch not found. Installing..."
    pip install pytest-watch
    ptw --runner "python -m pytest tests/ -v --tb=short" src/ tests/
fi