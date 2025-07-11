# FastAPI-First Development Workflow

This document describes the modern development workflow for the arrgh-fastapi project, which has been redesigned to eliminate code duplication and streamline development.

## Overview

**Previous Approach**: Notebook with duplicated code → Manual sync to FastAPI  
**New Approach**: FastAPI as single source of truth → Notebook imports production modules

## Benefits

✅ **Single Source of Truth**: All logic lives only in FastAPI codebase  
✅ **Zero Code Duplication**: Notebook imports production modules directly  
✅ **Instant Synchronization**: Changes in FastAPI immediately available in notebook  
✅ **Real Testing**: Notebook tests actual production behavior  
✅ **Reduced Maintenance**: No need to manually sync two codebases  
✅ **Faster Development**: Hot reload + immediate notebook feedback  

## Development Environment Setup

### 1. Initial Setup

```bash
# Clone and setup the project
git clone <repository-url>
cd arrgh-fastapi

# Run the automated setup script
./scripts/dev-setup.sh

# OR manually setup:
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
# Edit .env with your configuration
```

### 2. Start Development Environment

**Option A: Single Terminal Development**
```bash
# Start FastAPI development server with hot reload
./scripts/dev-server.sh

# In another terminal, run tests continuously
./scripts/dev-test.sh
```

**Option B: tmux Multi-pane Development**
```bash
# Start both server and tests in tmux
./scripts/dev-tmux.sh
```

**Option C: Manual Commands**
```bash
# Start FastAPI server with hot reload
uvicorn src.main:app --reload --port 8000

# Run tests with watch mode
ptw --runner "python -m pytest tests/ -v" src/ tests/
```

## Development Workflow

### Primary Development (FastAPI)

1. **Edit Code**: Make changes directly in `src/` directory
2. **Instant Feedback**: uvicorn automatically reloads the server
3. **Write Tests**: Add/update tests in `tests/` directory
4. **Continuous Testing**: Tests re-run automatically on file changes

### Interactive Testing (Notebook)

1. **Open Notebook**: `jupyter lab notebooks/newsletter_development.ipynb`
2. **Import Updates**: Restart kernel to get latest FastAPI changes
3. **Test Interactively**: Use real data to test production modules
4. **Analyze Results**: Visualize entity extraction and graph data

## File Structure

```
src/                              # Production code (single source of truth)
├── processors/
│   ├── entity_extractor.py       # Entity extraction with OpenAI
│   └── html_processor.py         # HTML processing and cleaning
├── graph/
│   └── neo4j_client.py           # Neo4j graph database operations
├── workflows/
│   └── newsletter_processor.py   # Complete processing pipeline
├── models/
│   └── newsletter.py             # Pydantic data models
└── config.py                     # Configuration management

tests/                            # Comprehensive test suite
├── test_entity_extractor.py      # Entity extraction unit tests
├── test_newsletter.py            # Integration tests
└── test_simple.py               # Basic functionality tests

notebooks/                       # Interactive analysis (imports from src/)
└── newsletter_development.ipynb  # Analysis and testing notebook

scripts/                         # Development automation
├── dev-setup.sh                 # Complete environment setup
├── dev-server.sh                # Start FastAPI with hot reload
├── dev-test.sh                  # Continuous testing
└── dev-tmux.sh                  # Multi-pane development session
```

## Development Patterns

### Making Changes to Core Logic

1. **Edit FastAPI Module**: Modify code in `src/processors/entity_extractor.py`
2. **Server Reloads**: uvicorn automatically reloads with changes
3. **Tests Re-run**: pytest-watch automatically runs relevant tests
4. **Test in Notebook**: Restart kernel and test with real data

### Adding New Features

1. **Write Tests First**: Add tests in `tests/` directory
2. **Implement in FastAPI**: Add functionality to appropriate `src/` module
3. **Validate with Notebook**: Test interactively with real data
4. **Update Documentation**: Update CLAUDE.md if needed

### Debugging Issues

1. **Check Tests**: Review test failures for specific issues
2. **Use Notebook**: Import modules and debug interactively
3. **Add Logging**: Use structlog for detailed debugging information
4. **Neo4j Browser**: Visualize graph data at http://localhost:7474

## Testing Strategy

### Unit Tests (`tests/`)
- **Entity Extraction**: Comprehensive tests for all extraction scenarios
- **HTML Processing**: Tests for cleaning and text extraction
- **Integration**: End-to-end pipeline testing
- **Continuous**: Tests run automatically on file changes

### Interactive Testing (Notebook)
- **Real Data**: Test with actual newsletter content
- **Graph Analysis**: Query and visualize Neo4j results
- **Prompt Engineering**: Experiment with OpenAI prompts
- **Performance**: Analyze processing times and quality metrics

## Deployment

### Development to Production

1. **Run All Tests**: Ensure all tests pass
   ```bash
   python -m pytest tests/ -v
   ```

2. **Test with Notebook**: Validate with real data in notebook

3. **Commit Changes**: 
   ```bash
   git add .
   git commit -m "Description of changes"
   ```

4. **Deploy**: Push to main branch for automatic deployment
   ```bash
   git push origin main
   ```

### Production Monitoring

- **Entity Extraction**: Monitor success rates and confidence scores
- **Neo4j Graph**: Track entity relationships and growth
- **Performance**: Monitor processing times and API response times

## Common Commands

### Development
```bash
# Start complete development environment
./scripts/dev-setup.sh

# Start server only
./scripts/dev-server.sh

# Start tests only  
./scripts/dev-test.sh

# Start both in tmux
./scripts/dev-tmux.sh
```

### Testing
```bash
# Run all tests once
python -m pytest tests/ -v

# Test entity extraction specifically
python -m pytest tests/test_entity_extractor.py -v

# Test with coverage
python -m pytest tests/ --cov=src
```

### Database
```bash
# Start Neo4j for development
./scripts/start-neo4j.sh

# Stop Neo4j
./scripts/stop-neo4j.sh

# Access Neo4j Browser
open http://localhost:7474
```

### Deployment
```bash
# Deploy to production
./scripts/deploy-production.sh

# Check production logs
gcloud logs tail --follow --service arrgh-fastapi
```

## Troubleshooting

### Common Issues

**"Module not found" errors in notebook**
- Restart Jupyter kernel to reload updated modules
- Check that FastAPI modules can be imported in terminal

**Tests failing after changes**
- Review test output for specific failure details
- Check that new code follows existing patterns

**Entity extraction not working**
- Verify OpenAI API key is configured in `.env`
- Check that `ENVIRONMENT=local` or `ENVIRONMENT=test` is set
- Review entity extraction logs for specific errors

**Neo4j connection issues**
- Ensure Neo4j is running: `./scripts/start-neo4j.sh`
- Check password configuration in `.env`
- Verify Neo4j is accessible at http://localhost:7474

### Getting Help

1. **Check Logs**: Review FastAPI and Neo4j logs for errors
2. **Run Tests**: Use test output to identify specific issues
3. **Use Notebook**: Debug interactively with real data
4. **Review Documentation**: Check CLAUDE.md for configuration details

## Migration from Old Workflow

If you were using the previous notebook-centric approach:

1. **Save Your Work**: Backup any custom notebook code
2. **Update Notebook**: The notebook now imports from FastAPI
3. **Move Custom Logic**: Add any custom code to appropriate FastAPI modules
4. **Update Development Habits**: Primary development now happens in FastAPI
5. **Use Notebook for Analysis**: Notebook is now for testing and visualization

The new workflow is more efficient and eliminates the synchronization issues of the previous approach.