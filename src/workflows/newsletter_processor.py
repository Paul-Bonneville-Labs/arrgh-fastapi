"""Newsletter processing workflow."""
import uuid
from datetime import datetime, timezone
from typing import Dict, List
import structlog
from ..models.newsletter import (
    Newsletter, Entity, ExtractionState, 
    NewsletterProcessingRequest, NewsletterProcessingResponse
)
from ..processors.html_processor import clean_html_content, extract_text_sections
from ..processors.entity_extractor import EntityExtractor
from ..graph.neo4j_client import Neo4jClient
from ..config_wrapper import Config

logger = structlog.get_logger()


class NewsletterProcessor:
    """Process newsletters through the complete pipeline."""
    
    def __init__(self, config: Config):
        self.config = config
        self.entity_extractor = None
        self.neo4j_client = Neo4jClient(config)
        
    def initialize(self) -> bool:
        """Initialize processor connections."""
        try:
            # Initialize entity extractor
            if not self.entity_extractor:
                self.entity_extractor = EntityExtractor(self.config)
            
            # Connect to Neo4j
            if not self.neo4j_client.connect():
                logger.error("Failed to connect to Neo4j")
                return False
            
            # Setup graph schema
            self.neo4j_client.setup_constraints_and_indexes()
            
            logger.info("Newsletter processor initialized")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize processor", error=str(e))
            return False
    
    def shutdown(self):
        """Shutdown processor connections."""
        if self.neo4j_client:
            self.neo4j_client.close()
        logger.info("Newsletter processor shutdown")
    
    def process_newsletter(self, request: NewsletterProcessingRequest) -> NewsletterProcessingResponse:
        """Process a newsletter through the complete pipeline."""
        start_time = datetime.now()
        newsletter_id = str(uuid.uuid4())
        
        # Create newsletter object
        newsletter = Newsletter(
            html_content=request.html_content,
            subject=request.subject,
            sender=request.sender,
            received_date=request.received_date or datetime.now(timezone.utc),
            newsletter_id=newsletter_id
        )
        
        # Initialize state
        state = ExtractionState(newsletter=newsletter)
        
        try:
            logger.info("Starting newsletter processing", 
                       newsletter_id=newsletter_id,
                       subject=newsletter.subject)
            
            # Step 1: Clean HTML content
            state.current_step = "cleaning_html"
            state.cleaned_text = clean_html_content(newsletter.html_content)
            if not state.cleaned_text:
                state.errors.append("Failed to clean HTML content")
                return self._create_error_response(state, start_time)
            
            # Extract sections for additional context
            sections = extract_text_sections(newsletter.html_content)
            
            # Step 2: Extract entities with LLM
            state.current_step = "extracting_entities"
            if not self.entity_extractor:
                state.errors.append("Entity extractor not initialized")
                return self._create_error_response(state, start_time)
            state.extracted_entities = self.entity_extractor.extract_entities(state.cleaned_text)
            logger.info("Entities extracted", count=len(state.extracted_entities))
            
            # Step 3: Create newsletter node in graph
            state.current_step = "creating_newsletter_node"
            newsletter_node = self.neo4j_client.create_newsletter_node(newsletter)
            if not newsletter_node:
                state.errors.append("Failed to create newsletter node")
            
            # Step 4: Process entities and create/update nodes
            state.current_step = "processing_entities"
            entity_summary = {
                'Organization': 0, 'Person': 0, 'Product': 0, 
                'Event': 0, 'Location': 0, 'Topic': 0
            }
            new_entities = 0
            updated_entities = 0
            
            for entity in state.extracted_entities:
                try:
                    # Create or update entity
                    result = self.neo4j_client.create_or_update_entity(entity)
                    if result:
                        if result.get('operation') == 'created':
                            new_entities += 1
                        else:
                            updated_entities += 1
                        
                        # Link to newsletter
                        self.neo4j_client.link_entity_to_newsletter(
                            entity.name, 
                            entity.type, 
                            newsletter.newsletter_id, 
                            entity.context
                        )
                        
                        # Update summary
                        entity_summary[entity.type] = entity_summary.get(entity.type, 0) + 1
                        
                except Exception as e:
                    error_msg = f"Error processing entity {entity.name}: {str(e)}"
                    state.errors.append(error_msg)
                    logger.error(error_msg)
            
            # Step 5: Generate summary
            state.current_step = "generating_summary"
            entity_mentions = []
            for entity_type, count in entity_summary.items():
                if count > 0:
                    entity_mentions.append(f"{count} {entity_type.lower()}{'s' if count > 1 else ''}")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            state.text_summary = (
                f"Processed newsletter '{newsletter.subject}' from {newsletter.sender}. "
                f"Extracted {len(state.extracted_entities)} entities "
                f"({', '.join(entity_mentions) if entity_mentions else 'none'}). "
                f"Created {new_entities} new entities, updated {updated_entities} existing entities. "
                f"Processing completed in {processing_time:.2f} seconds."
            )
            
            # Create response
            response = NewsletterProcessingResponse(
                status="success",
                newsletter_id=newsletter_id,
                processing_time=processing_time,
                entities_extracted=len(state.extracted_entities),
                entities_new=new_entities,
                entities_updated=updated_entities,
                entity_summary=entity_summary,
                text_summary=state.text_summary,
                errors=state.errors
            )
            
            logger.info("Newsletter processing completed", 
                       newsletter_id=newsletter_id,
                       processing_time=processing_time,
                       entities_extracted=len(state.extracted_entities))
            
            return response
            
        except Exception as e:
            error_msg = f"Pipeline error: {str(e)}"
            state.errors.append(error_msg)
            logger.error("Newsletter processing failed", 
                        newsletter_id=newsletter_id,
                        error=error_msg)
            return self._create_error_response(state, start_time)
    
    def _create_error_response(self, state: ExtractionState, start_time: datetime) -> NewsletterProcessingResponse:
        """Create an error response."""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return NewsletterProcessingResponse(
            status="error",
            newsletter_id=state.newsletter.newsletter_id,
            processing_time=processing_time,
            entities_extracted=len(state.extracted_entities),
            entities_new=0,
            entities_updated=0,
            entity_summary={},
            text_summary=f"Processing failed at step: {state.current_step}",
            errors=state.errors
        )
    
    def get_graph_stats(self) -> Dict[str, int]:
        """Get current graph statistics."""
        return self.neo4j_client.get_graph_stats()