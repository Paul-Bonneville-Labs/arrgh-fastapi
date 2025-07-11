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
.env                          # Your real local development config
.env.production               # Your real production config (for Cloud Secrets reference)
```

### Modern Development Workflow (FastAPI-First)

**Quick Setup:**
```bash
# Automated setup for complete development environment
./scripts/dev-setup.sh

# Start development server with hot reload
./scripts/dev-server.sh

# Start continuous testing (in another terminal)
./scripts/dev-test.sh

# OR start both in tmux
./scripts/dev-tmux.sh
```

**Manual Setup:**
```bash
# 1. Create and activate virtual environment
python3.13 -m venv .venv
source .venv/bin/activate  # On macOS/Linux

# 2. Copy environment template and customize
cp .env.example .env
# Edit .env with your real OpenAI API key

# 3. Install all dependencies
pip install -r requirements.txt -r requirements-dev.txt -r requirements-notebook.txt

# 4. Start development server with hot reload
uvicorn src.main:app --reload --port 8000

# 5. Start continuous testing (separate terminal)
ptw --runner "python -m pytest tests/ -v" src/ tests/
```

**Notebook Development:**
The notebook now imports actual FastAPI modules instead of duplicating code:
```bash
# Open notebook for interactive testing and analysis
jupyter lab notebooks/newsletter_development.ipynb

# The notebook imports from src/ modules:
# - from processors.entity_extractor import EntityExtractor
# - from models.newsletter import Entity, Newsletter
# - from graph.neo4j_client import Neo4jClient
```

**📚 For detailed development workflow documentation, see: [docs/DEVELOPMENT-WORKFLOW.md](docs/DEVELOPMENT-WORKFLOW.md)**

### Local Development with Docker
```bash
# Quick development script that builds and runs Docker container
./scripts/dev-local.sh

# Or manually:
docker build -t arrgh-fastapi .
docker run -p 8080:8080 arrgh-fastapi
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

**Automated Deployment with Pre-Testing:**
```bash
# Verify all secrets are configured
./scripts/verify-secrets.sh

# Deploy to Google Cloud Run with automatic pre-deployment testing
./scripts/deploy-production.sh

# View deployment logs
gcloud logs tail --follow --service arrgh-fastapi --region us-central1
```

**Pre-Deployment Testing (automatically run by deploy script):**
```bash
# Run comprehensive pre-deployment tests manually
./scripts/pre-deployment-tests.sh

# The tests include:
# - Environment and configuration validation
# - Unit tests (pytest)
# - OpenAI API connectivity testing
# - Entity extraction end-to-end testing
# - Docker build verification
# - Production health checks (if deployed)
```

**Manual Deployment (if needed):**
```bash
gcloud run deploy arrgh-fastapi \
  --image gcr.io/paulbonneville-com/arrgh-fastapi \
  --platform managed \
  --region us-central1 \
  --set-secrets OPENAI_API_KEY=newsletter-openai-api-key:latest \
  --set-secrets NEO4J_PASSWORD=newsletter-neo4j-password:latest \
  --set-secrets NEO4J_URI=newsletter-neo4j-uri:latest \
  --set-secrets SECRET_KEY=newsletter-secret-key:latest \
  --no-allow-unauthenticated
```

## Architecture

### Project Structure
- `src/main.py` - Core FastAPI application entry point
- `tests/` - Unit tests using FastAPI's TestClient
- `scripts/dev-local.sh` - Docker development automation
- Service runs on port 8080 (Google Cloud Run standard)

### Key Technical Details
- **Framework**: FastAPI with Uvicorn server
- **Python**: 3.13.5
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
- **Service**: arrgh-fastapi
- **Region**: us-central1
- **Service Account**: 860937201650-compute@developer.gserviceaccount.com (default)
- **Service URL**: https://arrgh-fastapi-860937201650.us-central1.run.app

## Important Notes

- The application requires authentication via service account for Cloud Run access
- No linting or type checking is currently configured
- Tests should be run before committing changes
- The Docker container exposes port 8080 as required by Google Cloud Run
- Continuous deployment is enabled - changes to main branch automatically deploy