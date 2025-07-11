import os
import signal
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from .routers import newsletter

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
VERSION = os.getenv("VERSION", "1.0.0")

# Global shutdown flag
shutdown_event = False

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_event
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_event = True

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting FastAPI app - Environment: {ENVIRONMENT}, Version: {VERSION}")
    yield
    # Shutdown
    logger.info("Shutting down FastAPI app")
    # Cleanup newsletter processor
    newsletter.shutdown_processor()

app = FastAPI(
    title="Arrgh! Newsletter Processing API",
    description="Process newsletters to extract entities and build knowledge graph",
    version=VERSION,
    lifespan=lifespan
)

# Include routers
app.include_router(newsletter.router)

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    return {
        "message": "Arrgh! Newsletter Processing API",
        "description": "Extract entities from newsletters and build knowledge graphs",
        "endpoints": {
            "/newsletter/process": "Process a newsletter (POST)",
            "/newsletter/stats": "Get graph statistics (GET)",
            "/newsletter/health": "Check service health (GET)",
            "/docs": "API documentation"
        },
        "environment": ENVIRONMENT,
        "version": VERSION
    }

@app.get("/health")
def health_check():
    """Health check endpoint for Cloud Run."""
    if shutdown_event:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "message": "Service is shutting down"}
        )
    
    return {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "version": VERSION,
        "service": "fastapi-cloud-run"
    }

@app.get("/ready")
def readiness_check():
    """Readiness check endpoint for Cloud Run."""
    # Add any application-specific readiness checks here
    # (database connections, external services, etc.)
    return {
        "status": "ready",
        "environment": ENVIRONMENT,
        "version": VERSION
    }

@app.get("/test-connectivity")
def test_connectivity():
    """Test connectivity to various ports to debug Cloud Run networking."""
    from .test_connectivity import run_connectivity_tests
    
    logger.info("Running connectivity tests")
    results = run_connectivity_tests()
    
    # Summary
    total_tests = len(results["tests"])
    successful_tests = sum(1 for test in results["tests"] if test["success"])
    
    return {
        "summary": {
            "total_tests": total_tests,
            "successful": successful_tests,
            "failed": total_tests - successful_tests
        },
        "results": results["tests"],
        "environment": ENVIRONMENT
    }

@app.get("/test-openai")
def test_openai_connectivity():
    """Test OpenAI API connectivity with detailed error reporting."""
    from .config_wrapper import Config
    from .processors.entity_extractor import EntityExtractor
    from openai import OpenAI
    import traceback
    
    logger.info("Testing OpenAI connectivity")
    
    try:
        # Load config
        config = Config()
        
        # Test 1: Basic client initialization
        test_results = {
            "config_loaded": bool(config.OPENAI_API_KEY),
            "api_key_present": bool(config.OPENAI_API_KEY and len(config.OPENAI_API_KEY) > 0),
            "api_key_format": config.OPENAI_API_KEY[:10] + "..." if config.OPENAI_API_KEY else None,
            "client_init": False,
            "simple_request": False,
            "entity_extractor": False,
            "errors": []
        }
        
        # Test 2: Initialize OpenAI client directly
        try:
            client = OpenAI(
                api_key=config.OPENAI_API_KEY,
                timeout=10.0
            )
            test_results["client_init"] = True
            logger.info("OpenAI client initialized successfully")
            
            # Test 3: Make a simple API call
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Say hello"}],
                    max_tokens=10,
                    timeout=10
                )
                test_results["simple_request"] = True
                test_results["response_content"] = response.choices[0].message.content
                logger.info("Simple OpenAI request successful")
            except Exception as e:
                error_info = {
                    "test": "simple_request",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "traceback": traceback.format_exc()
                }
                if hasattr(e, 'status_code'):
                    error_info["status_code"] = e.status_code
                if hasattr(e, 'response'):
                    error_info["response"] = str(e.response)[:500] if e.response else None
                test_results["errors"].append(error_info)
                logger.error("Simple OpenAI request failed", error=error_info)
                
        except Exception as e:
            error_info = {
                "test": "client_init",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc()
            }
            test_results["errors"].append(error_info)
            logger.error("OpenAI client initialization failed", error=error_info)
        
        # Test 4: Test EntityExtractor
        try:
            extractor = EntityExtractor(config)
            test_results["entity_extractor"] = bool(extractor.client)
            if extractor.client:
                logger.info("EntityExtractor initialized successfully")
            else:
                logger.error("EntityExtractor client is None")
        except Exception as e:
            error_info = {
                "test": "entity_extractor",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc()
            }
            test_results["errors"].append(error_info)
            logger.error("EntityExtractor initialization failed", error=error_info)
        
        return {
            "summary": {
                "all_tests_passed": all([
                    test_results["config_loaded"],
                    test_results["api_key_present"],
                    test_results["client_init"],
                    test_results["simple_request"],
                    test_results["entity_extractor"]
                ]),
                "critical_failures": len([e for e in test_results["errors"] if e["test"] in ["client_init", "simple_request"]])
            },
            "results": test_results,
            "environment": ENVIRONMENT
        }
        
    except Exception as e:
        logger.error("Test setup failed", error=str(e), traceback=traceback.format_exc())
        return {
            "summary": {"all_tests_passed": False, "critical_failures": 1},
            "results": {"setup_error": str(e)},
            "environment": ENVIRONMENT
        } 