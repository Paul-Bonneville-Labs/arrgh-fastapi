#!/bin/bash

# FastAPI Development Environment Setup
# This script sets up the complete development environment

echo "🛠️  Setting up FastAPI Development Environment..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3.13 -m venv .venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Install all dependencies
echo "📥 Installing dependencies..."
echo "  - Core runtime dependencies..."
pip install -r requirements.txt

echo "  - Development dependencies..."
pip install -r requirements-dev.txt

echo "  - Notebook dependencies..."
pip install -r requirements-notebook.txt

# Set up environment configuration
if [ ! -f ".env" ]; then
    echo "⚙️  Setting up environment configuration..."
    cp .env.example .env
    echo "📝 Please edit .env with your actual configuration values"
else
    echo "✅ Environment configuration already exists"
fi

# Create tmux session for development (optional)
echo ""
echo "🚀 Development environment ready!"
echo ""
echo "💡 Quick start options:"
echo "  1. Start development server:  ./scripts/dev-server.sh"
echo "  2. Start continuous testing:   ./scripts/dev-test.sh"
echo "  3. Start both in tmux:         ./scripts/dev-tmux.sh"
echo "  4. Open notebook:              jupyter lab notebooks/"
echo ""
echo "📚 Useful commands:"
echo "  - Run tests once:              python -m pytest tests/ -v"
echo "  - Check entity extraction:     python -m pytest tests/test_entity_extractor.py -v"
echo "  - Start Neo4j:                 ./scripts/start-neo4j.sh"
echo "  - Deploy to production:        ./scripts/deploy-production.sh"