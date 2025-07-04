"""Simple tests that don't rely on TestClient."""
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["OPENAI_API_KEY"] = "sk-test-key"

import pytest
from src.models.newsletter import Newsletter, Entity, NewsletterProcessingRequest
from src.processors.html_processor import clean_html_content, extract_text_sections
from src.config_wrapper import Config


class TestModels:
    """Test data models."""
    
    def test_newsletter_creation(self):
        """Test Newsletter model creation."""
        newsletter = Newsletter(
            html_content="<h1>Test</h1><p>Content</p>",
            subject="Test Newsletter",
            sender="test@example.com"
        )
        assert newsletter.subject == "Test Newsletter"
        assert newsletter.sender == "test@example.com"
        assert newsletter.html_content == "<h1>Test</h1><p>Content</p>"
    
    def test_entity_creation(self):
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
        assert entity.context == "OpenAI released a new model"
        assert entity.aliases == []
    
    def test_request_model(self):
        """Test NewsletterProcessingRequest model."""
        request = NewsletterProcessingRequest(
            html_content="<h1>Test</h1>",
            subject="Test",
            sender="test@example.com"
        )
        assert request.html_content == "<h1>Test</h1>"
        assert request.subject == "Test"
        assert request.sender == "test@example.com"


class TestHTMLProcessor:
    """Test HTML processing."""
    
    def test_clean_simple_html(self):
        """Test cleaning simple HTML."""
        html = "<h1>Title</h1><p>Paragraph</p>"
        result = clean_html_content(html)
        
        assert result is not None
        assert len(result) > 0
        assert "Title" in result
        assert "Paragraph" in result
    
    def test_clean_html_removes_scripts(self):
        """Test that scripts are removed."""
        html = '<p>Content</p><script>alert("bad")</script>'
        result = clean_html_content(html)
        
        assert "Content" in result
        assert "alert" not in result
        assert "script" not in result.lower()
    
    def test_extract_sections(self):
        """Test section extraction."""
        html = """
        <html>
        <head><title>Test Title</title></head>
        <body>
            <h1>Header 1</h1>
            <p>Paragraph 1</p>
            <a href="http://example.com">Link</a>
        </body>
        </html>
        """
        sections = extract_text_sections(html)
        
        assert sections["title"] == "Test Title"
        assert "Header 1" in sections["headers"]
        assert "Paragraph 1" in sections["paragraphs"]
        assert len(sections["links"]) == 1
        assert sections["links"][0]["url"] == "http://example.com"


class TestConfiguration:
    """Test configuration."""
    
    def test_config_loads(self):
        """Test that configuration loads."""
        config = Config()
        
        assert config.LLM_MODEL is not None
        assert config.NEO4J_URI is not None
        assert config.NEO4J_USER is not None
        assert config.MAX_ENTITIES_PER_NEWSLETTER > 0
        assert 0.0 <= config.ENTITY_CONFIDENCE_THRESHOLD <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])