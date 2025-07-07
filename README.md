# Arrgh! Aggregated Research Repository

**Newsletter Processing System with AI-Powered Entity Extraction and Graph Database**

A FastAPI-based system that processes newsletters to extract entities (organizations, people, products, events, locations, topics) using large language models and stores relationships in a Neo4j graph database.

## 🚀 Quick Start (30 seconds)

```bash
git clone <repository-url>
cd arrgh-fastapi
./scripts/setup-local.sh
```

**Or see [Quick Start Guide](docs/QUICK-START.md) for detailed setup.**

## 📋 System Overview

This system processes newsletter content through an AI-powered pipeline:

1. **HTML Processing** → Clean and extract text content
2. **Entity Extraction** → Use OpenAI GPT-4 to identify entities 
3. **Graph Storage** → Store entities and relationships in Neo4j
4. **API Endpoints** → FastAPI interface for processing
5. **Development Notebooks** → Jupyter notebooks for pipeline development

### Integration with arrgh-n8n

This API is designed to work with the **arrgh-n8n** project, which contains n8n workflows that:
- Monitor and receive newsletter emails
- Extract content and forward to this processing API
- Handle the complete email-to-graph pipeline automation

The n8n workflow calls this service's `/process` endpoint with newsletter content for entity extraction and graph storage.

## 🏗️ Architecture

### Core Components
- **FastAPI Application** (`src/`) - REST API for newsletter processing
- **Processing Pipeline** - Entity extraction and graph operations
- **Neo4j Graph Database** - Entity relationship storage
- **Jupyter Notebooks** (`notebooks/`) - Development and analysis
- **Docker Deployment** - Google Cloud Run ready

### Entity Types Extracted
- **Organization** - Companies, institutions, government bodies
- **Person** - Individuals mentioned in content
- **Product** - Software, hardware, services, models
- **Event** - Conferences, announcements, launches
- **Location** - Geographic locations (cities, countries, regions)
- **Topic** - Subject areas, technologies, fields of study

## 🛠️ Prerequisites

- **Python 3.11+**
- **Docker** (for Neo4j)
- **OpenAI API Key**
- **direnv** (optional, for auto-activation)

## 🚀 Local Development

### Automatic Setup (Recommended)
```bash
# Installs dependencies, sets up environment, starts Neo4j
./scripts/setup-local.sh
```

### Manual Setup
```bash
# 1. Environment setup
cp .env.example .env.local
# Edit .env.local with your OpenAI API key

# 2. Dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt              # Core
pip install -r requirements-notebook.txt     # + Notebooks  
pip install -r requirements-dev.txt         # + Testing

# 3. Database
./scripts/start-neo4j.sh

# 4. Run services
export ENVIRONMENT=local
uvicorn src.main:app --reload --port 8000   # API
jupyter lab notebooks/                      # Notebooks
```

### Auto-Activation with direnv
```bash
# One-time setup
brew install direnv
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
direnv allow

# Now virtual environment activates automatically when you cd into project
```

## 📊 Usage

### API Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Newsletter service health
curl http://localhost:8000/newsletter/health

# Get graph statistics
curl http://localhost:8000/newsletter/stats

# Process newsletter (requires API key authentication)
curl -X POST http://localhost:8000/newsletter/process \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{"html_content": "...", "subject": "Newsletter Title"}'
```

### Development Notebooks
```bash
# Start Jupyter Lab
jupyter lab notebooks/

# Main development notebook
open notebooks/newsletter_processing.ipynb
```

### Database Access
- **Neo4j Browser**: http://localhost:7474
- **Credentials**: `neo4j` / `your-neo4j-password` (from .env.local)

## 🧪 Testing

```bash
# Run test suite
python -m pytest tests/ -v

# Test specific components
python -c "from src.config import get_env_file; print('Config OK')"
```

## 📁 Project Structure

```
arrgh-fastapi/
├── src/                          # Core application
│   ├── main.py                   # FastAPI application
│   ├── config.py                 # Environment configuration
│   ├── models/                   # Data models
│   └── processors/               # Processing pipeline
├── notebooks/                    # Jupyter development
│   └── newsletter_processing.ipynb
├── tests/                        # Test suite
├── scripts/                      # Utility scripts
│   ├── setup-local.sh           # Automated setup
│   ├── start-neo4j.sh           # Start Neo4j Docker
│   └── stop-neo4j.sh            # Stop Neo4j Docker
├── docs/                         # Documentation
│   └── QUICK-START.md           # Detailed setup guide
├── requirements*.txt             # Dependencies (modular)
├── .env.example                  # Environment template
├── .envrc                        # direnv configuration
└── CLAUDE.md                     # AI assistant guidance
```

## 🌩️ Environment Files

- **`.env.example`** → Template for local development
- **`.env.production.example`** → Template for production
- **`.env.test.example`** → Template for testing
- **`.env.local`** → Your local development config (git-ignored)
- **`.env.production`** → Your production reference (git-ignored)
- **`.env.test`** → Your testing config (git-ignored)

## 🚀 Deployment

### Google Cloud Run
```bash
# Automatic deployment on push to main branch via Cloud Build
git push origin main

# Manual deployment
./scripts/dev-local.sh              # Test locally first
gcloud run deploy arrgh-fastapi \
  --image gcr.io/paulbonneville-com/arrgh-fastapi \
  --platform managed \
  --region us-central1 \
  --no-allow-unauthenticated
```

### Environment Variables for Production
Configure these in Google Cloud Run:
- `OPENAI_API_KEY` - Your OpenAI API key
- `NEO4J_URI` - Neo4j Aura connection string
- `NEO4J_USER` - Neo4j username
- `NEO4J_PASSWORD` - Neo4j password
- `ENVIRONMENT=production`

## 🧠 AI Processing Pipeline

1. **Input**: Newsletter HTML content
2. **Text Extraction**: Clean HTML → structured text
3. **Entity Recognition**: GPT-4 → identify entities with confidence scores
4. **Graph Operations**: Create/update Neo4j nodes and relationships
5. **Output**: Structured entity data + graph relationships

## 🔐 API Authentication

The newsletter processing endpoint requires API key authentication:

- **Environment Variable**: Set `API_KEY` in your environment file
- **Header Required**: Include `X-API-Key: your-api-key-here` in requests
- **Protected Endpoints**: `/newsletter/process` (other endpoints are public)
- **Production Setup**: API key managed via Google Cloud Secret Manager

```bash
# Example authenticated request
curl -X POST http://localhost:8000/newsletter/process \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{"html_content": "<html>...</html>", "subject": "Newsletter Title"}'
```

## 📈 Monitoring & Metrics

- **Health Endpoint**: `/health` - System status
- **Newsletter Health**: `/newsletter/health` - Service-specific status
- **Processing Metrics**: Entity counts, confidence scores, processing time
- **Database Stats**: Node counts by type, relationship metrics

## 🔧 Development

### Key Commands
```bash
# Environment management
export ENVIRONMENT=local                    # Set environment
./scripts/start-neo4j.sh                   # Start database
./scripts/stop-neo4j.sh                    # Stop database

# Development
uvicorn src.main:app --reload              # API with hot reload
jupyter lab notebooks/                     # Notebooks
python -m pytest tests/ -v                 # Tests
```

### Adding New Entity Types
1. Update entity type definitions in `src/models/`
2. Modify LLM prompts in processing pipeline
3. Add graph constraints in Neo4j setup
4. Update documentation

## 📚 Documentation

- **[QUICK-START.md](docs/QUICK-START.md)** - Detailed setup instructions
- **[CLAUDE.md](CLAUDE.md)** - Complete technical documentation
- **Jupyter Notebooks** - Interactive development examples

## 🤝 Contributing

1. Create feature branch from `main`
2. Follow existing code patterns and tests
3. Update documentation for new features
4. Ensure all tests pass before PR

## 📄 License

[Add your license information here]

---

- **Live Service**: https://arrgh-fastapi-mfmtscuo4q-uc.a.run.app (requires authentication)