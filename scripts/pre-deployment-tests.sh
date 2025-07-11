#!/bin/bash

# Pre-deployment integration tests
# Run this script before deploying to production to catch connectivity and configuration issues

set -e

echo "🧪 Running pre-deployment tests..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    echo -n "  Testing $test_name... "
    
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Helper function to run a test with detailed output on failure
run_test_with_output() {
    local test_name="$1"
    local test_command="$2"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    echo -n "  Testing $test_name... "
    
    local output
    if output=$(eval "$test_command" 2>&1); then
        echo -e "${GREEN}PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        echo -e "${RED}    Error: $output${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

echo ""
echo "📋 1. Environment and Configuration Tests"
echo "============================================"

# Test 1: Environment variables
run_test "ENVIRONMENT variable set" 'test -n "$ENVIRONMENT"'
run_test "Environment file exists" 'test -f .env || test -f .env.production'

# Test 2: Dependencies installed
echo -n "  Testing dependencies installed... "
if python3 -c "import pydantic, fastapi, openai" > /dev/null 2>&1; then
    echo -e "${GREEN}PASS${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}FAIL - Installing dependencies${NC}"
    echo "    Installing required dependencies..."
    pip install -r requirements.txt -r requirements-dev.txt > /dev/null 2>&1 || {
        echo -e "${RED}    Failed to install dependencies${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    }
fi
TESTS_TOTAL=$((TESTS_TOTAL + 1))

# Test 3: Configuration loading
run_test_with_output "Configuration loads without errors" 'python3 -c "from src.config import get_settings; get_settings()"'

# Test 4: Critical secrets present
run_test_with_output "OpenAI API key configured" 'python3 -c "from src.config import get_settings; s=get_settings(); assert s.openai_api_key and not s.openai_api_key.startswith(\"sk-your-\")"'
run_test_with_output "Neo4j password configured" 'python3 -c "from src.config import get_settings; s=get_settings(); assert s.neo4j_password and s.neo4j_password != \"your-neo4j-password\""'

echo ""
echo "🔧 2. Unit Tests"
echo "================"

# Run existing unit tests
run_test_with_output "Entity extractor unit tests" 'python -m pytest tests/test_entity_extractor.py -v'
run_test_with_output "Simple functionality tests" 'python -m pytest tests/test_simple.py -v'

echo ""
echo "🔌 3. Integration Tests (Local)"
echo "==============================="

# Test 4: OpenAI connectivity
run_test_with_output "OpenAI API connectivity" 'python3 -c "
from src.config_wrapper import Config
from openai import OpenAI
import json

config = Config()
client = OpenAI(api_key=config.OPENAI_API_KEY, timeout=10.0)
response = client.chat.completions.create(
    model=\"gpt-3.5-turbo\",
    messages=[{\"role\": \"user\", \"content\": \"Say hello\"}],
    max_tokens=10
)
assert response.choices[0].message.content
print(\"✓ OpenAI connectivity confirmed\")
"'

# Test 5: Entity extraction end-to-end
run_test_with_output "Entity extraction end-to-end" 'python3 -c "
from src.processors.entity_extractor import EntityExtractor
from src.config_wrapper import Config

config = Config()
extractor = EntityExtractor(config)
entities = extractor.extract_entities(\"OpenAI announced GPT-4 at their conference.\")
assert isinstance(entities, list)
print(f\"✓ Extracted {len(entities)} entities\")
"'

echo ""
echo "🐳 4. Docker Build Test"
echo "======================="

# Test 6: Docker build
run_test_with_output "Docker image builds successfully" 'docker build -t arrgh-fastapi-test .'

# Test 7: Docker container starts
run_test_with_output "Docker container starts" '
if command -v timeout > /dev/null; then
    timeout 30s docker run --rm -d -p 8081:8080 --name arrgh-test arrgh-fastapi-test && sleep 5 && docker stop arrgh-test
elif command -v gtimeout > /dev/null; then
    gtimeout 30s docker run --rm -d -p 8081:8080 --name arrgh-test arrgh-fastapi-test && sleep 5 && docker stop arrgh-test
else
    # macOS fallback without timeout
    docker run --rm -d -p 8081:8080 --name arrgh-test arrgh-fastapi-test && sleep 10 && docker stop arrgh-test
fi'

echo ""
echo "🌐 5. Production Connectivity Tests (if deployed)"
echo "================================================="

# Check if service is deployed
if gcloud run services describe arrgh-fastapi --region=us-central1 --project=paulbonneville-com > /dev/null 2>&1; then
    SERVICE_URL="https://arrgh-fastapi-860937201650.us-central1.run.app"
    
    # Test health endpoint
    run_test_with_output "Production health check" "curl -sf '$SERVICE_URL/health'"
    
    # Test OpenAI connectivity endpoint
    run_test_with_output "Production OpenAI connectivity" 'curl -sf "'$SERVICE_URL'/test-openai" | python3 -c "
import json, sys
data = json.load(sys.stdin)
assert data[\"summary\"][\"all_tests_passed\"] == True
assert data[\"summary\"][\"critical_failures\"] == 0
print(\"✓ All production OpenAI tests passed\")
"'
else
    echo "  ${YELLOW}SKIP${NC} - Service not deployed yet"
fi

echo ""
echo "📊 Test Summary"
echo "==============="
echo "  Total tests: $TESTS_TOTAL"
echo -e "  Passed: ${GREEN}$TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "  Failed: ${RED}$TESTS_FAILED${NC}"
else
    echo -e "  Failed: $TESTS_FAILED"
fi

echo ""
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed! Safe to deploy to production.${NC}"
    exit 0
else
    echo -e "${RED}❌ $TESTS_FAILED test(s) failed. Do not deploy to production.${NC}"
    echo ""
    echo "🔧 Recommended actions:"
    echo "  1. Fix failing tests"
    echo "  2. Run tests again with: ./scripts/pre-deployment-tests.sh"
    echo "  3. Only deploy after all tests pass"
    exit 1
fi