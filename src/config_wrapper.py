"""Config wrapper for backwards compatibility with notebook code."""
from .config import get_settings

class Config:
    """Wrapper class for settings to maintain compatibility with notebook code."""
    
    def __init__(self):
        settings = get_settings()
        
        # LLM Configuration
        self.OPENAI_API_KEY = settings.openai_api_key
        self.LLM_MODEL = settings.llm_model
        self.LLM_TEMPERATURE = settings.llm_temperature
        self.LLM_MAX_TOKENS = settings.llm_max_tokens
        
        # Neo4j Configuration
        self.NEO4J_URI = settings.neo4j_uri
        self.NEO4J_USER = settings.neo4j_user
        self.NEO4J_PASSWORD = settings.neo4j_password
        self.NEO4J_DATABASE = settings.neo4j_database
        self.NEO4J_CONNECTION_TIMEOUT = settings.neo4j_connection_timeout
        self.NEO4J_ACQUISITION_TIMEOUT = settings.neo4j_acquisition_timeout
        
        # Processing Configuration
        self.MAX_ENTITIES_PER_NEWSLETTER = settings.max_entities_per_newsletter
        self.FACT_EXTRACTION_BATCH_SIZE = settings.fact_extraction_batch_size
        self.PROCESSING_TIMEOUT = settings.processing_timeout
        self.ENTITY_CONFIDENCE_THRESHOLD = settings.entity_confidence_threshold
        self.FACT_CONFIDENCE_THRESHOLD = settings.fact_confidence_threshold
        
        # Feature Flags
        self.ENABLE_DEBUG_MODE = settings.enable_debug_mode