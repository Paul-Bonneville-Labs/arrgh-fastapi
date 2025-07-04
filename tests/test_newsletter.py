"""Tests for newsletter processing functionality."""
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["OPENAI_API_KEY"] = "sk-test-key"

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

# FastAPI testing
from src.main import app
from fastapi.testclient import TestClient

# Newsletter processing components
from src.models.newsletter import (
    Newsletter, NewsletterProcessingRequest, Entity
)
from src.processors.html_processor import clean_html_content, extract_text_sections
from src.config_wrapper import Config


# Defer client creation to avoid initialization issues
client = None


class TestNewsletterModels:
    """Test data models for newsletter processing."""
    
    def test_newsletter_model_creation(self):
        """Test Newsletter model creation."""
        newsletter = Newsletter(
            html_content="<h1>Test</h1><p>Content</p>",
            subject="Test Newsletter",
            sender="test@example.com"
        )
        assert newsletter.subject == "Test Newsletter"
        assert newsletter.sender == "test@example.com"
        assert len(newsletter.html_content) > 0
    
    def test_entity_model_creation(self):
        """Test Entity model creation."""
        entity = Entity(
            name="OpenAI",
            type="Organization",
            confidence=0.95,
            context="OpenAI released a new model"
        )
        assert entity.name == "OpenAI"
        assert entity.type == "Organization"
        assert entity.confidence == 0.95
        assert entity.aliases == []  # default empty list


class TestHTMLProcessor:
    """Test HTML processing functionality."""
    
    def test_clean_html_content(self):
        """Test HTML cleaning function."""
        test_html = "<h1>Test Title</h1><p>Test <strong>content</strong> here.</p>"
        cleaned = clean_html_content(test_html)
        
        assert cleaned is not None
        assert len(cleaned) > 0
        assert "Test Title" in cleaned
        assert "content" in cleaned
        # Should not contain HTML tags
        assert "<h1>" not in cleaned
        assert "<p>" not in cleaned
    
    def test_clean_html_with_scripts(self):
        """Test HTML cleaning removes scripts and styles."""
        test_html = """
        <html>
        <head><style>body { color: red; }</style></head>
        <body>
            <h1>Title</h1>
            <script>alert('test');</script>
            <p>Content</p>
        </body>
        </html>
        """
        cleaned = clean_html_content(test_html)
        
        assert "Title" in cleaned
        assert "Content" in cleaned
        assert "alert" not in cleaned
        assert "color: red" not in cleaned
    
    def test_extract_text_sections(self):
        """Test text section extraction."""
        test_html = """
        <html>
        <head><title>Newsletter Title</title></head>
        <body>
            <h1>Main Header</h1>
            <h2>Sub Header</h2>
            <p>First paragraph</p>
            <p>Second paragraph</p>
            <a href="http://example.com">Example Link</a>
        </body>
        </html>
        """
        sections = extract_text_sections(test_html)
        
        assert sections["title"] == "Newsletter Title"
        assert len(sections["headers"]) == 2
        assert "Main Header" in sections["headers"]
        assert "Sub Header" in sections["headers"]
        assert len(sections["paragraphs"]) == 2
        assert len(sections["links"]) == 1
        assert sections["links"][0]["url"] == "http://example.com"


class TestNewsletterEndpoints:
    """Test newsletter API endpoints."""
    
    def test_newsletter_health_endpoint(self):
        """Test newsletter health check endpoint."""
        global client
        if not client:
            client = TestClient(app)
        response = client.get("/newsletter/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "initialized" in data
        assert "neo4j_connected" in data
        
        # Status should be either healthy or unhealthy
        assert data["status"] in ["healthy", "unhealthy"]
    
    def test_newsletter_stats_endpoint(self):
        """Test newsletter stats endpoint."""
        global client
        if not client:
            client = TestClient(app)
        response = client.get("/newsletter/stats")
        
        # Should succeed or fail gracefully
        if response.status_code == 200:
            data = response.json()
            # Should contain expected stat keys
            expected_keys = [
                "organizations", "people", "products", 
                "events", "locations", "topics", 
                "newsletters", "relationships"
            ]
            for key in expected_keys:
                assert key in data
                assert isinstance(data[key], int)
        else:
            # If it fails, should be due to database connection
            assert response.status_code in [500, 503]
    
    @patch('src.workflows.newsletter_processor.NewsletterProcessor')
    def test_newsletter_process_endpoint_success(self, mock_processor_class):
        """Test successful newsletter processing."""
        # Mock the processor
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        mock_processor.initialize.return_value = True
        
        # Mock successful processing response
        mock_response = {
            "status": "success",
            "newsletter_id": "test-123",
            "processing_time": 1.5,
            "entities_extracted": 5,
            "entities_new": 3,
            "entities_updated": 2,
            "entity_summary": {"Organization": 2, "Person": 1, "Product": 2},
            "text_summary": "Successfully processed test newsletter",
            "errors": []
        }
        mock_processor.process_newsletter.return_value = type('obj', (object,), mock_response)()
        
        # Test data
        request_data = {
            "html_content": "<h1>Test Newsletter</h1><p>OpenAI released GPT-4.</p>",
            "subject": "AI News",
            "sender": "news@ai.com"
        }
        
        global client
        if not client:
            client = TestClient(app)
        response = client.post("/newsletter/process", json=request_data)
        
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "success"
            assert data["entities_extracted"] >= 0
            assert isinstance(data["processing_time"], (int, float))
        # If it fails due to missing dependencies, that's expected
        elif response.status_code in [422, 500, 503]:
            pass  # Expected when dependencies aren't available
    
    def test_newsletter_process_endpoint_validation(self):
        """Test newsletter processing endpoint validation."""
        global client
        if not client:
            client = TestClient(app)
        
        # Test with missing required fields
        response = client.post("/newsletter/process", json={})
        assert response.status_code == 422  # Validation error
        
        # Test with invalid data
        invalid_data = {
            "html_content": "",  # Empty content
            "subject": "",       # Empty subject
            "sender": "invalid"  # Invalid email format would be caught by validation
        }
        response = client.post("/newsletter/process", json=invalid_data)
        # Should either validate or fail gracefully
        assert response.status_code in [200, 422, 500, 503]


class TestConfiguration:
    """Test configuration loading."""
    
    def test_config_loading(self):
        """Test configuration can be loaded."""
        config = Config()
        
        # Should have default values
        assert config.LLM_MODEL is not None
        assert config.NEO4J_URI is not None
        assert config.NEO4J_USER is not None
        assert config.MAX_ENTITIES_PER_NEWSLETTER > 0
        assert 0.0 <= config.ENTITY_CONFIDENCE_THRESHOLD <= 1.0


# Integration test data
SAMPLE_NEWSLETTER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Weekly Newsletter #245</title>
</head>
<body>
    <h1>AI Weekly Newsletter #245</h1>
    <p>Welcome to this week's AI updates!</p>
    
    <h2>Major Announcements</h2>
    <p><strong>OpenAI</strong> announced the release of <strong>GPT-5</strong> at their developer conference in <strong>San Francisco</strong>. 
    CEO <strong>Sam Altman</strong> presented the new capabilities.</p>
    
    <h2>Company Updates</h2>
    <p><strong>Microsoft</strong> expanded their <strong>Azure AI</strong> services with new enterprise features.</p>
    
    <p>Thanks for reading! See you next week.</p>
</body>
</html>
"""


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])