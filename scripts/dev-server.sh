#!/bin/bash

# FastAPI Development Server with Hot Reload
# This script starts the FastAPI development server with automatic reloading

echo "🚀 Starting FastAPI Development Server with Hot Reload..."

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not detected. Activating .venv..."
    source .venv/bin/activate
fi

# Set development environment
export ENVIRONMENT=local

# Ensure all dependencies are installed
echo "📦 Checking dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

echo "🔄 Starting uvicorn with hot reload..."
echo "  - Server will restart automatically when code changes"
echo "  - Access your API at: http://localhost:8000"
echo "  - API documentation at: http://localhost:8000/docs"
echo "  - Stop with Ctrl+C"
echo ""

# Start the development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug