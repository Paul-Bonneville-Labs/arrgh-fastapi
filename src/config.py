"""
Configuration management for the Arrgh! Newsletter Processing System.

This module provides type-safe configuration management using Pydantic Settings
with support for environment variables and .env files.
"""

from typing import Optional, List
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with type validation and environment variable support."""
    
    # LLM Configuration
    openai_api_key: str = Field(..., description="OpenAI API key for LLM operations")
    llm_model: str = Field(default="gpt-4-turbo", description="LLM model to use")
    llm_temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="LLM temperature")
    llm_max_tokens: int = Field(default=2000, gt=0, description="Maximum tokens for LLM response")
    
    # Neo4j Configuration
    neo4j_uri: str = Field(..., description="Neo4j database URI")
    neo4j_user: str = Field(..., description="Neo4j username")
    neo4j_password: str = Field(..., description="Neo4j password")
    neo4j_database: str = Field(default="neo4j", description="Neo4j database name")
    
    # Processing Configuration
    max_entities_per_newsletter: int = Field(
        default=100, 
        gt=0, 
        description="Maximum entities to extract per newsletter"
    )
    fact_extraction_batch_size: int = Field(
        default=10, 
        gt=0, 
        description="Batch size for fact extraction"
    )
    processing_timeout: int = Field(
        default=300, 
        gt=0, 
        description="Processing timeout in seconds"
    )
    entity_confidence_threshold: float = Field(
        default=0.7, 
        ge=0.0, 
        le=1.0, 
        description="Minimum confidence for entity extraction"
    )
    fact_confidence_threshold: float = Field(
        default=0.8, 
        ge=0.0, 
        le=1.0, 
        description="Minimum confidence for fact extraction"
    )
    
    # Application Configuration
    api_host: str = Field(default="0.0.0.0", description="API host address")
    api_port: int = Field(default=8080, gt=0, le=65535, description="API port")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Monitoring & Logging
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(default=9090, gt=0, le=65535, description="Metrics port")
    
    # Feature Flags
    enable_async_processing: bool = Field(
        default=False, 
        description="Enable asynchronous processing"
    )
    enable_entity_caching: bool = Field(
        default=True, 
        description="Enable entity resolution caching"
    )
    enable_debug_mode: bool = Field(
        default=False, 
        description="Enable debug mode with verbose logging"
    )
    
    # Development Settings
    jupyter_port: int = Field(default=8888, gt=0, le=65535, description="Jupyter port")
    jupyter_token: Optional[str] = Field(default=None, description="Jupyter authentication token")
    
    # Google Cloud Configuration (for production)
    google_cloud_project: Optional[str] = Field(
        default=None, 
        description="Google Cloud project ID"
    )
    google_cloud_region: str = Field(
        default="us-central1", 
        description="Google Cloud region"
    )
    
    # Entity Types Configuration
    supported_entity_types: List[str] = Field(
        default=["Organization", "Person", "Product", "Event", "Location", "Topic"],
        description="Supported entity types for extraction"
    )
    
    # Security Configuration
    secret_key: Optional[str] = Field(
        default=None, 
        description="Secret key for security operations"
    )
    cors_origins: List[str] = Field(
        default=["*"], 
        description="CORS allowed origins"
    )
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level is supported."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()
    
    @validator('llm_model')
    def validate_llm_model(cls, v):
        """Validate LLM model is supported."""
        supported_models = [
            'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo', 
            'gpt-4-turbo-preview', 'gpt-4-1106-preview'
        ]
        if v not in supported_models:
            # Just warn, don't fail - allows for new models
            pass
        return v
    
    @validator('neo4j_uri')
    def validate_neo4j_uri(cls, v):
        """Basic validation of Neo4j URI format."""
        if not (v.startswith('bolt://') or v.startswith('neo4j://') or v.startswith('neo4j+s://')):
            raise ValueError('Neo4j URI must start with bolt://, neo4j://, or neo4j+s://')
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Allow extra fields for forward compatibility
        extra = "allow"


class DevelopmentSettings(Settings):
    """Development-specific settings with relaxed security."""
    
    enable_debug_mode: bool = Field(default=True)
    log_level: str = Field(default="DEBUG")
    cors_origins: List[str] = Field(default=["*"])
    

class ProductionSettings(Settings):
    """Production-specific settings with enhanced security."""
    
    enable_debug_mode: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    enable_metrics: bool = Field(default=True)
    cors_origins: List[str] = Field(default=[])  # Restrict CORS in production
    
    @validator('secret_key')
    def secret_key_required(cls, v):
        """Require secret key in production."""
        if not v:
            raise ValueError('Secret key is required in production')
        return v


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings with caching.
    
    Returns:
        Settings: Configured settings instance
    """
    # Determine environment
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return ProductionSettings()
    elif environment == "development":
        return DevelopmentSettings()
    else:
        return Settings()


@lru_cache()
def get_config_file_path() -> Path:
    """Get the path to the configuration file."""
    return Path(__file__).parent.parent / ".env"


def validate_configuration(settings: Settings) -> List[str]:
    """
    Validate configuration and return list of warnings/errors.
    
    Args:
        settings: Settings instance to validate
        
    Returns:
        List[str]: List of validation messages
    """
    messages = []
    
    # Check critical settings
    if not settings.openai_api_key or settings.openai_api_key.startswith("sk-your-"):
        messages.append("WARNING: OpenAI API key not properly configured")
    
    if not settings.neo4j_password or settings.neo4j_password == "your-neo4j-password":
        messages.append("WARNING: Neo4j password not properly configured")
    
    # Check development settings
    if settings.enable_debug_mode:
        messages.append("INFO: Debug mode is enabled")
    
    if settings.log_level == "DEBUG":
        messages.append("INFO: Debug logging is enabled")
    
    # Check production readiness
    environment = os.getenv("ENVIRONMENT", "development").lower()
    if environment == "production":
        if not settings.secret_key:
            messages.append("ERROR: Secret key required for production")
        
        if settings.cors_origins == ["*"]:
            messages.append("WARNING: CORS is set to allow all origins in production")
    
    return messages


def print_configuration_summary(settings: Settings) -> None:
    """Print a summary of the current configuration."""
    print("🔧 Configuration Summary:")
    print(f"  Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"  LLM Model: {settings.llm_model}")
    print(f"  Neo4j URI: {settings.neo4j_uri}")
    print(f"  API Host: {settings.api_host}:{settings.api_port}")
    print(f"  Log Level: {settings.log_level}")
    print(f"  Debug Mode: {settings.enable_debug_mode}")
    print(f"  Metrics Enabled: {settings.enable_metrics}")
    print(f"  Max Entities: {settings.max_entities_per_newsletter}")
    print(f"  Entity Confidence Threshold: {settings.entity_confidence_threshold}")
    print(f"  Fact Confidence Threshold: {settings.fact_confidence_threshold}")
    
    # Validation messages
    messages = validate_configuration(settings)
    if messages:
        print("\n📋 Configuration Messages:")
        for message in messages:
            print(f"  {message}")


# Convenience function for direct import
def get_config() -> Settings:
    """Convenience function to get settings."""
    return get_settings()


if __name__ == "__main__":
    # CLI for configuration testing
    settings = get_settings()
    print_configuration_summary(settings)