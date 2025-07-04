# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a minimal FastAPI application designed for deployment on Google Cloud Run. The project serves as a foundation for building a larger application, potentially related to generative AI.

## Key Commands

### Environment Configuration

The project uses a clean environment file structure:

```bash
# Template files (committed to repo)
.env.example                  # "Copy me for local development"
.env.production.example       # "Copy me for production setup"

# Your actual configs (gitignored)
.env.local                    # Your real local development config
.env.production               # Your real production config (for Cloud Secrets reference)
```

### Local Development Setup
```bash
# 1. Create and activate virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # On macOS/Linux

# 2. Copy environment template and customize
cp .env.example .env.local
# Edit .env.local with your real OpenAI API key

# 3. Install dependencies (core runtime)
pip install -r requirements.txt

# 4. For notebook development, also install
pip install -r requirements-notebook.txt

# 5. Set environment and run
export ENVIRONMENT=local
uvicorn src.main:app --reload --port 8000
```

### Local Development with Docker
```bash
# Quick development script that builds and runs Docker container
./scripts/dev-local.sh

# Or manually:
docker build -t genai .
docker run -p 8080:8080 genai
```

### Neo4j Database (for notebook development)
```bash
# Start Neo4j database for development
./scripts/start-neo4j.sh

# Stop Neo4j database
./scripts/stop-neo4j.sh

# Access Neo4j Browser: http://localhost:7474
# Username: neo4j, Password: your-neo4j-password
```

### Dependencies

The project uses a modular dependency structure:

```bash
# Core runtime dependencies (required)
pip install -r requirements.txt

# Notebook development (optional)
pip install -r requirements-notebook.txt

# Testing and development (optional)
pip install -r requirements-dev.txt

# Install everything for full development
pip install -r requirements.txt -r requirements-notebook.txt -r requirements-dev.txt
```

### Testing
```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
export ENVIRONMENT=local
python -m pytest tests/ -v

# Run specific test files
python -m pytest tests/test_simple.py -v
python -m pytest tests/test_newsletter.py -v

# Test newsletter processing functionality
python -m pytest tests/test_simple.py::TestHTMLProcessor -v
```

### Deployment

```bash
# Verify all secrets are configured
./scripts/verify-secrets.sh

# Deploy to Google Cloud Run with production secrets
./scripts/deploy-production.sh

# Manual deployment (if needed)
gcloud run deploy arrgh-newsletter \
  --image gcr.io/paulbonneville-com/arrgh-newsletter \
  --platform managed \
  --region us-central1 \
  --set-secrets OPENAI_API_KEY=newsletter-openai-api-key:latest \
  --set-secrets NEO4J_PASSWORD=newsletter-neo4j-password:latest \
  --set-secrets NEO4J_URI=newsletter-neo4j-uri:latest \
  --set-secrets SECRET_KEY=newsletter-secret-key:latest \
  --no-allow-unauthenticated

# View deployment logs
gcloud logs tail --follow --service arrgh-newsletter --region us-central1
```

## Architecture

### Project Structure
- `src/main.py` - Core FastAPI application entry point
- `tests/` - Unit tests using FastAPI's TestClient
- `scripts/dev-local.sh` - Docker development automation
- Service runs on port 8080 (Google Cloud Run standard)

### Key Technical Details
- **Framework**: FastAPI with Uvicorn server
- **Python**: 3.11
- **Deployment**: Docker on Google Cloud Run
- **Authentication**: Service account required (no public access)
- **CI/CD**: Automatic deployment on push to main branch

### Testing Approach
Tests use manual path manipulation to import the app. When adding new tests, follow the pattern in `tests/test_main.py`:
```python
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
```

### Google Cloud Configuration
- **Project**: paulbonneville-com
- **Service**: genai
- **Region**: us-central1
- **Service Account**: genai-app@paulbonneville-com.iam.gserviceaccount.com
- **Service URL**: https://genai-860937201650.us-central1.run.app

## Important Notes

- The application requires authentication via service account for Cloud Run access
- No linting or type checking is currently configured
- Tests should be run before committing changes
- The Docker container exposes port 8080 as required by Google Cloud Run
- Continuous deployment is enabled - changes to main branch automatically deploy