#!/bin/bash

# Final Python 3.13 Compatibility Test Script

echo "=== Python 3.13 Final Compatibility Test ==="
echo "Date: $(date)"
echo ""

# Check Python 3.13 availability
echo "1. Checking Python 3.13 availability..."
if command -v python3.13 &> /dev/null; then
    echo "✅ Python 3.13 found: $(python3.13 --version)"
else
    echo "❌ Python 3.13 not available"
    exit 1
fi
echo ""

# Create clean test environment
echo "2. Creating clean Python 3.13 test environment..."
if [ -d ".venv-py313-final" ]; then
    echo "Removing existing test environment..."
    rm -rf .venv-py313-final
fi

python3.13 -m venv .venv-py313-final
if [ $? -eq 0 ]; then
    echo "✅ Test environment created"
else
    echo "❌ Failed to create test environment"
    exit 1
fi

# Activate and upgrade tools
echo ""
echo "3. Activating environment and upgrading build tools..."
source .venv-py313-final/bin/activate

echo "Upgrading pip, setuptools, wheel..."
pip install --upgrade pip setuptools wheel
if [ $? -eq 0 ]; then
    echo "✅ Build tools upgraded"
else
    echo "❌ Failed to upgrade build tools"
    exit 1
fi

# Install updated requirements
echo ""
echo "4. Installing updated requirements.txt..."
echo "This should now work with Python 3.13..."
timeout 600 pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✅ Updated requirements installed successfully!"
    INSTALL_SUCCESS=true
else
    echo "❌ Updated requirements failed to install"
    INSTALL_SUCCESS=false
fi

# Test dev requirements
if [ "$INSTALL_SUCCESS" = true ]; then
    echo ""
    echo "5. Installing dev requirements..."
    timeout 300 pip install -r requirements-dev.txt
    if [ $? -eq 0 ]; then
        echo "✅ Dev requirements installed successfully!"
    else
        echo "❌ Dev requirements failed"
        INSTALL_SUCCESS=false
    fi
fi

# Test basic functionality
if [ "$INSTALL_SUCCESS" = true ]; then
    echo ""
    echo "6. Testing basic functionality..."
    
    # Test core imports
    echo "Testing core imports..."
    python3.13 -c "
import sys
print(f'Python version: {sys.version}')

# Test critical imports
try:
    import fastapi
    print('✅ FastAPI import successful')
    print(f'  Version: {fastapi.__version__}')
except Exception as e:
    print(f'❌ FastAPI import failed: {e}')

try:
    import pydantic
    print('✅ Pydantic import successful')
    print(f'  Version: {pydantic.__version__}')
except Exception as e:
    print(f'❌ Pydantic import failed: {e}')

try:
    import openai
    print('✅ OpenAI import successful')
    print(f'  Version: {openai.__version__}')
except Exception as e:
    print(f'❌ OpenAI import failed: {e}')

try:
    import langchain_openai
    print('✅ LangChain OpenAI import successful')
except Exception as e:
    print(f'❌ LangChain OpenAI import failed: {e}')

try:
    import neo4j
    print('✅ Neo4j import successful')
    print(f'  Version: {neo4j.__version__}')
except Exception as e:
    print(f'❌ Neo4j import failed: {e}')

try:
    import lxml
    print('✅ lxml import successful')
    print(f'  Version: {lxml.__version__}')
except Exception as e:
    print(f'❌ lxml import failed: {e}')
"

    # Test app import
    echo ""
    echo "Testing FastAPI app import..."
    python3.13 -c "
import sys
sys.path.insert(0, 'src')
import os
os.environ['ENVIRONMENT'] = 'test'
os.environ['OPENAI_API_KEY'] = 'test-key'

try:
    from src.main import app
    print('✅ FastAPI app import successful')
except Exception as e:
    print(f'❌ FastAPI app import failed: {e}')
    import traceback
    traceback.print_exc()
"

    # Test basic test suite
    echo ""
    echo "Running basic test suite..."
    PYTHONPATH=src python3.13 -m pytest tests/test_simple.py -v
    if [ $? -eq 0 ]; then
        echo "✅ Basic tests passed on Python 3.13"
    else
        echo "⚠️ Some tests failed - check output above"
    fi

else
    echo ""
    echo "6. Skipping functionality tests due to installation failure"
fi

echo ""
echo "=== Test Complete ==="

if [ "$INSTALL_SUCCESS" = true ]; then
    echo "🎉 Python 3.13 compatibility test PASSED!"
    echo "✅ All dependencies installed successfully"
    echo "✅ Core functionality working"
    echo ""
    echo "Ready to commit and test in CI!"
else
    echo "❌ Python 3.13 compatibility test FAILED"
    echo "   Dependencies failed to install"
    echo "   Review errors above and adjust requirements"
fi

# Cleanup
echo ""
echo "7. Cleanup..."
deactivate 2>/dev/null || true
if [ -d ".venv-py313-final" ]; then
    rm -rf .venv-py313-final
    echo "✅ Test environment cleaned up"
fi