"""Newsletter data models."""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class Entity(BaseModel):
    """Represents an extracted entity from newsletter content."""
    name: str
    type: str  # Organization, Person, Product, Event, Location, Topic
    aliases: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    context: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)


class Fact(BaseModel):
    """Represents a relationship or fact between entities."""
    subject_entity: str
    predicate: str  # relationship type
    object_entity: str
    confidence: float = Field(ge=0.0, le=1.0)
    temporal_context: Optional[str] = None
    date_mentioned: Optional[datetime] = None
    source_context: Optional[str] = None


class Newsletter(BaseModel):
    """Represents a newsletter to be processed."""
    html_content: str
    subject: str
    sender: str
    received_date: Optional[datetime] = None
    newsletter_id: Optional[str] = None


class NewsletterProcessingRequest(BaseModel):
    """Request model for newsletter processing endpoint."""
    html_content: str
    subject: str
    sender: str
    received_date: Optional[datetime] = None


class NewsletterProcessingResponse(BaseModel):
    """Response model for newsletter processing endpoint."""
    status: str
    newsletter_id: str
    processing_time: float
    entities_extracted: int
    entities_new: int
    entities_updated: int
    entity_summary: Dict[str, int]
    text_summary: str
    errors: List[str] = Field(default_factory=list)


class ExtractionState(BaseModel):
    """State for the processing workflow."""
    # Input
    newsletter: Newsletter
    
    # Processing stages
    cleaned_text: str = ""
    extracted_entities: List[Entity] = Field(default_factory=list)
    resolved_entities: List[Entity] = Field(default_factory=list)
    extracted_facts: List[Fact] = Field(default_factory=list)
    
    # Results
    neo4j_updates: Dict[str, Any] = Field(default_factory=dict)
    processing_metrics: Dict[str, Any] = Field(default_factory=dict)
    text_summary: str = ""
    errors: List[str] = Field(default_factory=list)
    
    # Metadata
    processing_start_time: datetime = Field(default_factory=datetime.now)
    current_step: str = "initialized"