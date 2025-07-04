# Environment Setup Guide

This guide explains how to configure different environments for the Arrgh! Newsletter Processing System.

## 🏗️ Environment Types

### Local Development (`.env.local`)
- **Neo4j**: Local Docker container (`bolt://localhost:7687`)
- **OpenAI**: Shared API key from arrgh-n8n project
- **Logging**: Debug level with verbose output
- **Features**: All debugging features enabled

### Production (`.env.production`)
- **Neo4j**: Neo4j Aura cloud instance (`neo4j+s://your-instance.databases.neo4j.io`)
- **OpenAI**: Production API key with rate limiting
- **Logging**: INFO level, structured logs
- **Features**: Enhanced security, metrics enabled

## 🔧 Configuration Files

```
.env.local       # Local development (gitignored)
.env.production  # Production secrets (gitignored)
.env.staging     # Staging environment (gitignored)
.env.example     # Template with placeholders (committed)
.env             # Default fallback (committed)
```

## 🐳 Neo4j Configuration Options

### Local Development (Docker)
```bash
# Start local Neo4j
./scripts/start-neo4j.sh

# Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password
```

### Production (Neo4j Aura)
```bash
# Configuration
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-aura-password
NEO4J_DATABASE=neo4j
```

### Production (Self-hosted)
```bash
# Configuration
NEO4J_URI=bolt://your-neo4j-server:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-production-password
NEO4J_DATABASE=neo4j
```

## 🚀 Usage Examples

### Switch to Local Development
```bash
export ENVIRONMENT=local
./scripts/set-environment.sh local

# Start dependencies
./scripts/start-neo4j.sh

# Run application
uvicorn src.main:app --reload --port 8000
```

### Deploy to Production
```bash
export ENVIRONMENT=production

# Verify configuration
python -c "from src.config import get_settings, print_configuration_summary; print_configuration_summary(get_settings())"

# Deploy
gcloud run deploy genai --image gcr.io/paulbonneville-com/genai
```

### Run Jupyter Notebook
```bash
export ENVIRONMENT=local
source .venv/bin/activate
jupyter lab notebooks/
```

## 🔐 Security Considerations

### Local Development
- ✅ Use placeholder passwords for local Docker
- ✅ Debug mode enabled for development
- ✅ CORS allows all origins

### Production
- ❌ Never commit real credentials
- ❌ Debug mode must be disabled
- ❌ Restrict CORS origins
- ✅ Use environment variables for secrets
- ✅ Enable metrics and monitoring

## 📊 Configuration Validation

The system automatically validates configuration on startup:

```python
from src.config import get_settings, validate_configuration

settings = get_settings()
messages = validate_configuration(settings)
for message in messages:
    print(message)
```

Common validation messages:
- `WARNING: OpenAI API key not properly configured`
- `WARNING: Neo4j password not properly configured`
- `ERROR: Secret key required for production`
- `INFO: Debug mode is enabled`

## 🔄 Environment Migration

To migrate from local to production:

1. **Set up production Neo4j** (Aura or self-hosted)
2. **Create `.env.production`** with production credentials
3. **Test configuration** locally with `ENVIRONMENT=production`
4. **Deploy** with production environment variables
5. **Monitor** application logs and metrics

## 📚 Reference

- **Neo4j Aura**: https://neo4j.com/cloud/aura/
- **OpenAI API**: https://platform.openai.com/
- **Google Cloud Run**: https://cloud.google.com/run
- **Environment Variables**: https://12factor.net/config