#!/bin/bash
# Auto-activation script for the project environment
# Source this file when entering the project directory

# Check if we're in the right directory
if [ ! -f "requirements.txt" ] || [ ! -f "CLAUDE.md" ]; then
    echo "⚠️ Not in the arrgh-fastapi project directory"
    return 1
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️ Virtual environment not found. Run: python3 -m venv .venv"
    return 1
fi

# Set environment variables
export ENVIRONMENT=local
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"

echo "✅ Environment set to: $ENVIRONMENT"
echo "💡 Next steps:"
echo "  - Start Neo4j: ./scripts/start-neo4j.sh"
echo "  - Run API: uvicorn src.main:app --reload --port 8000"
echo "  - Run notebook: jupyter lab notebooks/"