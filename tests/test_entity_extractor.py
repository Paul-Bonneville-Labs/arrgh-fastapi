"""Tests for entity extraction functionality."""
import sys
import os
import json
from unittest.mock import Mock, patch, MagicMock

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["OPENAI_API_KEY"] = "sk-test-key"

import pytest
from src.processors.entity_extractor import EntityExtractor
from src.models.newsletter import Entity
from src.config_wrapper import Config


class TestEntityExtractor:
    """Test entity extraction functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        config = Mock(spec=Config)
        config.OPENAI_API_KEY = "sk-test-key"
        config.LLM_MODEL = "gpt-4-turbo"
        config.LLM_TEMPERATURE = 0.1
        config.LLM_MAX_TOKENS = 2000
        config.ENTITY_CONFIDENCE_THRESHOLD = 0.7
        config.MAX_ENTITIES_PER_NEWSLETTER = 100
        return config
    
    @pytest.fixture
    def mock_openai_response(self):
        """Create a mock OpenAI response with valid entity data."""
        return {
            "entities": [
                {
                    "name": "OpenAI",
                    "type": "Organization",
                    "aliases": ["Open AI"],
                    "confidence": 0.95,
                    "context": "OpenAI announced GPT-4 at their developer conference",
                    "properties": {"sector": "AI"}
                },
                {
                    "name": "GPT-4",
                    "type": "Product",
                    "aliases": ["GPT 4"],
                    "confidence": 0.98,
                    "context": "OpenAI announced GPT-4 at their developer conference",
                    "properties": {"category": "LLM"}
                },
                {
                    "name": "Sam Altman",
                    "type": "Person",
                    "aliases": ["Samuel Altman"],
                    "confidence": 0.92,
                    "context": "CEO Sam Altman presented the new capabilities",
                    "properties": {"role": "CEO"}
                }
            ]
        }
    
    def test_entity_extractor_initialization_success(self, mock_config):
        """Test successful EntityExtractor initialization."""
        with patch('src.processors.entity_extractor.OpenAI') as mock_openai:
            
            mock_openai.return_value = MagicMock()
            
            extractor = EntityExtractor(mock_config)
            
            assert extractor.config == mock_config
            assert extractor.client is not None
            mock_openai.assert_called_once_with(
                api_key=mock_config.OPENAI_API_KEY,
                timeout=30.0
            )
    
    def test_entity_extractor_initialization_no_api_key(self):
        """Test EntityExtractor initialization without API key."""
        config = Mock(spec=Config)
        config.OPENAI_API_KEY = None
        
        extractor = EntityExtractor(config)
        
        assert extractor.client is None
    
    def test_entity_extractor_initialization_failure(self, mock_config):
        """Test EntityExtractor initialization failure."""
        with patch('src.processors.entity_extractor.OpenAI', side_effect=Exception("API Error")):
            extractor = EntityExtractor(mock_config)
            assert extractor.client is None
    
    @patch('src.processors.entity_extractor.OpenAI')
    def test_extract_entities_success(self, mock_openai_class, mock_config, mock_openai_response):
        """Test successful entity extraction."""
        # Setup mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock the completion response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(mock_openai_response, separators=(',', ':'))
        mock_client.chat.completions.create.return_value = mock_response
        
        extractor = EntityExtractor(mock_config)
        
        test_content = "OpenAI announced GPT-4 at their developer conference. CEO Sam Altman presented the new capabilities."
        entities = extractor.extract_entities(test_content)
        
        assert len(entities) == 3
        assert entities[0].name == "OpenAI"
        assert entities[0].type == "Organization"
        assert entities[0].confidence == 0.95
        assert entities[1].name == "GPT-4"
        assert entities[2].name == "Sam Altman"
    
    @patch('src.processors.entity_extractor.OpenAI')
    def test_extract_entities_with_code_blocks(self, mock_openai_class, mock_config, mock_openai_response):
        """Test entity extraction with JSON wrapped in code blocks."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock response with code block markers
        response_with_blocks = f"```json\n{json.dumps(mock_openai_response, separators=(',', ':'))}\n```"
        mock_response = MagicMock()
        mock_response.choices[0].message.content = response_with_blocks
        mock_client.chat.completions.create.return_value = mock_response
        
        extractor = EntityExtractor(mock_config)
        entities = extractor.extract_entities("Test content")
        
        assert len(entities) == 3
        assert entities[0].name == "OpenAI"
    
    @patch('src.processors.entity_extractor.OpenAI')
    def test_extract_entities_malformed_json(self, mock_openai_class, mock_config):
        """Test entity extraction with malformed JSON response."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock malformed JSON response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "This is not valid JSON"
        mock_client.chat.completions.create.return_value = mock_response
        
        extractor = EntityExtractor(mock_config)
        entities = extractor.extract_entities("Test content")
        
        assert entities == []
    
    @patch('src.processors.entity_extractor.OpenAI')
    def test_extract_entities_json_with_extra_text(self, mock_openai_class, mock_config, mock_openai_response):
        """Test entity extraction with JSON embedded in extra text."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock response with JSON buried in text
        json_str = json.dumps(mock_openai_response, separators=(',', ':'))
        response_with_text = f"Here are the entities I found: {json_str} That's all!"
        mock_response = MagicMock()
        mock_response.choices[0].message.content = response_with_text
        mock_client.chat.completions.create.return_value = mock_response
        
        extractor = EntityExtractor(mock_config)
        entities = extractor.extract_entities("Test content")
        
        assert len(entities) == 3
        assert entities[0].name == "OpenAI"
    
    @patch('src.processors.entity_extractor.OpenAI')
    def test_extract_entities_confidence_filtering(self, mock_openai_class, mock_config):
        """Test entity extraction filters low confidence entities."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Create response with mix of high and low confidence entities
        low_confidence_response = {
            "entities": [
                {
                    "name": "HighConf",
                    "type": "Organization",
                    "confidence": 0.95,
                    "context": "test"
                },
                {
                    "name": "LowConf",
                    "type": "Organization", 
                    "confidence": 0.5,  # Below threshold
                    "context": "test"
                }
            ]
        }
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(low_confidence_response, separators=(',', ':'))
        mock_client.chat.completions.create.return_value = mock_response
        
        extractor = EntityExtractor(mock_config)
        entities = extractor.extract_entities("Test content")
        
        # Should only get high confidence entity
        assert len(entities) == 1
        assert entities[0].name == "HighConf"
    
    @patch('src.processors.entity_extractor.OpenAI')
    def test_extract_entities_missing_required_fields(self, mock_openai_class, mock_config):
        """Test entity extraction filters entities missing required fields."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Create response with entities missing required fields
        incomplete_response = {
            "entities": [
                {
                    "name": "ValidEntity",
                    "type": "Organization",
                    "confidence": 0.95,
                    "context": "test"
                },
                {
                    # Missing name
                    "type": "Organization",
                    "confidence": 0.95,
                    "context": "test"
                },
                {
                    "name": "NoType",
                    # Missing type
                    "confidence": 0.95,
                    "context": "test"
                }
            ]
        }
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(incomplete_response, separators=(',', ':'))
        mock_client.chat.completions.create.return_value = mock_response
        
        extractor = EntityExtractor(mock_config)
        entities = extractor.extract_entities("Test content")
        
        # Should only get valid entity
        assert len(entities) == 1
        assert entities[0].name == "ValidEntity"
    
    @patch('src.processors.entity_extractor.OpenAI')
    def test_extract_entities_limit_enforcement(self, mock_openai_class, mock_config):
        """Test entity extraction enforces maximum entity limit."""
        mock_config.MAX_ENTITIES_PER_NEWSLETTER = 2  # Set low limit
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Create response with more entities than limit
        many_entities_response = {
            "entities": [
                {
                    "name": f"Entity{i}",
                    "type": "Organization",
                    "confidence": 0.9 - (i * 0.1),  # Varying confidence
                    "context": "test"
                }
                for i in range(5)
            ]
        }
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(many_entities_response, separators=(',', ':'))
        mock_client.chat.completions.create.return_value = mock_response
        
        extractor = EntityExtractor(mock_config)
        entities = extractor.extract_entities("Test content")
        
        # Should be limited to 2 entities with highest confidence
        assert len(entities) == 2
        assert entities[0].confidence >= entities[1].confidence
    
    def test_extract_entities_no_client(self, mock_config):
        """Test entity extraction returns empty list when client not initialized."""
        extractor = EntityExtractor(mock_config)
        extractor.client = None  # Simulate failed initialization
        
        entities = extractor.extract_entities("Test content")
        assert entities == []
    
    @patch('src.processors.entity_extractor.OpenAI')
    def test_extract_entities_api_error(self, mock_openai_class, mock_config):
        """Test entity extraction handles API errors gracefully."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        extractor = EntityExtractor(mock_config)
        entities = extractor.extract_entities("Test content")
        
        assert entities == []
    
    @patch('src.processors.entity_extractor.OpenAI')
    def test_extract_entities_empty_content(self, mock_openai_class, mock_config):
        """Test entity extraction with empty content."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        extractor = EntityExtractor(mock_config)
        entities = extractor.extract_entities("")
        
        assert entities == []
    
    @patch('src.processors.entity_extractor.OpenAI')
    def test_extract_entities_content_truncation(self, mock_openai_class, mock_config, mock_openai_response):
        """Test entity extraction truncates long content."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(mock_openai_response, separators=(',', ':'))
        mock_client.chat.completions.create.return_value = mock_response
        
        extractor = EntityExtractor(mock_config)
        
        # Create very long content
        long_content = "A" * 5000  # Longer than 3000 char limit
        entities = extractor.extract_entities(long_content)
        
        # Should still work and extract entities
        assert len(entities) == 3
        
        # Verify that the API was called with truncated content
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        prompt_content = call_args[1]["messages"][1]["content"]
        # The content in the prompt should be truncated
        assert len(prompt_content) < 5000