# Python 3.13 Compatibility Research (July 2025)

## Current Dependency Analysis

### Web Framework (Likely Working)
- `fastapi==0.104.1` (Oct 2023) → Latest: ~0.115+ (should have Python 3.13 support)
- `uvicorn[standard]==0.24.0` (Oct 2023) → Latest: ~0.32+ (should have Python 3.13 support)
- `requests==2.31.0` (May 2023) → Latest: ~2.32+ (should have Python 3.13 support)
- `httpx<0.28` → Latest: ~0.30+ (constraint may be removable with newer FastAPI)

### Data Validation (Critical Update Needed)
- `pydantic==2.5.0` (Nov 2023) → Latest: ~2.8+ (should have Python 3.13 wheels)
- `pydantic-settings==2.1.0` (Nov 2023) → Latest: ~2.4+ (should have Python 3.13 wheels)
- `python-dotenv==1.0.0` (Sep 2023) → Latest: ~1.0.1+ (should work)

### AI/ML Framework (Major Updates Needed)
- `openai==1.35.3` (Jun 2024) → Latest: ~1.40+ (should have Python 3.13 support)
- `langchain==0.2.5` (Jun 2024) → Latest: ~0.3+ (major version bump, breaking changes possible)
- `langchain-community==0.2.5` (Jun 2024) → Latest: ~0.3+ (major version bump)
- `langchain-openai==0.1.8` (Jun 2024) → Latest: ~0.2+ (breaking changes possible)
- `langgraph==0.1.4` (Jun 2024) → Latest: ~0.2+ (breaking changes possible)

### Data Processing (Mixed)
- `beautifulsoup4==4.12.2` (Jan 2023) → Latest: ~4.12.3+ (should work)
- `lxml==4.9.4` (Jan 2024) → Latest: ~5.3+ (should have Python 3.13 wheels)
- `html2text==2020.1.16` (Jan 2020) → Latest: ~2024.2+ (very old, needs update)

### Cloud Dependencies (Should Work)
- `google-cloud-secret-manager==2.16.4` (Sep 2023) → Latest: ~2.20+ (should work)
- `google-cloud-logging==3.8.0` (Sep 2023) → Latest: ~3.11+ (should work)

### Utilities (Minor Updates)
- `typing-extensions==4.8.0` (Sep 2023) → Latest: ~4.12+ (important for Python 3.13)
- `structlog==23.2.0` (Oct 2023) → Latest: ~24.4+ (should work)
- `python-json-logger==2.0.7` (Mar 2023) → Latest: ~2.0.8+ (should work)

## Likely Root Causes of CI Failure

1. **Pydantic Core Compilation**: `pydantic==2.5.0` likely missing Python 3.13 wheels
2. **NumPy Dependency Chain**: LangChain dependencies may pull in numpy versions without Python 3.13 wheels  
3. **Build Tool Issues**: May need newer pip/setuptools/wheel versions
4. **lxml Compilation**: `lxml==4.9.4` may not have Python 3.13 wheels

## Update Strategy

### Phase 1: Core Dependencies (Most Likely to Fix Issues)
1. Update Pydantic ecosystem to latest versions
2. Update typing-extensions for Python 3.13 compatibility
3. Update build tools (pip, setuptools, wheel)

### Phase 2: Web Framework  
1. Update FastAPI to latest version
2. Remove httpx constraint if possible
3. Update uvicorn to latest

### Phase 3: AI/ML Framework (Handle Breaking Changes)
1. Update OpenAI client (minor changes expected)
2. Update LangChain ecosystem carefully (major version bump - expect breaking changes)

### Phase 4: Supporting Libraries
1. Update Google Cloud libraries
2. Update data processing libraries
3. Update logging libraries

## Expected Breaking Changes

### LangChain 0.2 → 0.3 (Major)
- Import path changes likely
- API method signature changes possible
- Configuration format changes possible
- Need to check migration guide

### Potential FastAPI Changes
- TestClient improvements may allow removing httpx constraint
- Minor API changes possible but unlikely to be breaking

## Testing Priority

1. **Critical**: Entity extraction pipeline (LangChain changes)
2. **High**: API endpoints and TestClient (FastAPI/httpx changes)  
3. **Medium**: Configuration loading (Pydantic changes)
4. **Low**: Data processing and utilities