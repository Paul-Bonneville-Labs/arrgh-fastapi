"""Newsletter processing API endpoints."""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict
import structlog
from ..models.newsletter import NewsletterProcessingRequest, NewsletterProcessingResponse
from ..workflows.newsletter_processor import NewsletterProcessor
from ..config_wrapper import Config

logger = structlog.get_logger()

# Create router
router = APIRouter(
    prefix="/newsletter",
    tags=["newsletter"],
    responses={404: {"description": "Not found"}},
)

# Lazy initialization
config = None
processor = None
initialized = False


def ensure_initialized():
    """Ensure processor is initialized."""
    global initialized, config, processor
    if not initialized:
        config = Config()
        processor = NewsletterProcessor(config)
        if processor.initialize():
            initialized = True
            logger.info("Newsletter processor initialized")
        else:
            raise HTTPException(status_code=503, detail="Newsletter processor initialization failed")


@router.post("/process", response_model=NewsletterProcessingResponse)
async def process_newsletter(request: NewsletterProcessingRequest):
    """
    Process a newsletter through the entity extraction pipeline.
    
    This endpoint:
    1. Cleans the HTML content
    2. Extracts entities using LLM
    3. Stores entities in Neo4j graph database
    4. Creates relationships between entities and newsletter
    5. Returns processing summary
    """
    ensure_initialized()
    
    try:
        logger.info("Processing newsletter", subject=request.subject, sender=request.sender)
        response = processor.process_newsletter(request)
        
        if response.status == "error":
            logger.error("Newsletter processing failed", errors=response.errors)
            raise HTTPException(status_code=422, detail={
                "message": "Newsletter processing failed",
                "errors": response.errors
            })
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error processing newsletter", error=str(e))
        raise HTTPException(status_code=500, detail={
            "message": "Internal server error during newsletter processing",
            "error": str(e)
        })


@router.get("/stats")
async def get_graph_stats() -> Dict[str, int]:
    """
    Get current statistics from the graph database.
    
    Returns counts of:
    - Organizations
    - People  
    - Products
    - Events
    - Locations
    - Topics
    - Newsletters
    - Relationships
    """
    ensure_initialized()
    
    try:
        stats = processor.get_graph_stats()
        logger.info("Graph stats retrieved", stats=stats)
        return stats
        
    except Exception as e:
        logger.error("Error retrieving graph stats", error=str(e))
        raise HTTPException(status_code=500, detail={
            "message": "Failed to retrieve graph statistics",
            "error": str(e)
        })


@router.get("/health")
async def health_check():
    """Check health of newsletter processing service."""
    try:
        ensure_initialized()
        
        # Check Neo4j connection
        stats = processor.get_graph_stats()
        
        return {
            "status": "healthy",
            "initialized": initialized,
            "neo4j_connected": True,
            "entity_confidence_threshold": config.ENTITY_CONFIDENCE_THRESHOLD
        }
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "initialized": initialized,
            "neo4j_connected": False,
            "error": str(e)
        }


# Cleanup on shutdown
def shutdown_processor():
    """Shutdown processor connections."""
    global initialized
    if initialized:
        processor.shutdown()
        initialized = False
        logger.info("Newsletter processor shutdown")