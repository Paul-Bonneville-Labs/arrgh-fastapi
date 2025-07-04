"""Entity extraction using LLM."""
import json
from typing import List, Optional
from openai import OpenAI
import structlog
from ..models.newsletter import Entity
from ..config_wrapper import Config

logger = structlog.get_logger()


class EntityExtractor:
    """Extract entities from newsletter content using LLM."""
    
    ENTITY_EXTRACTION_PROMPT = """
You are an expert at extracting structured information from newsletter content. 
Extract entities from the following newsletter text and classify them into these categories:

**Entity Types:**
- **Organization**: Companies, institutions, government bodies
- **Person**: Individuals mentioned in content
- **Product**: Software, hardware, services, models
- **Event**: Conferences, announcements, launches
- **Location**: Geographic locations (cities, countries, regions)
- **Topic**: Subject areas, technologies, fields of study

**Instructions:**
1. Extract entities with high confidence (>0.7)
2. Provide alternative names/aliases if mentioned
3. Include context where the entity was mentioned
4. Rate confidence from 0.0 to 1.0
5. Return results as valid JSON

**Newsletter Content:**
{content}

**Required JSON Format:**
```json
{
  "entities": [
    {
      "name": "Entity Name",
      "type": "Organization|Person|Product|Event|Location|Topic",
      "aliases": ["Alternative Name 1", "Alternative Name 2"],
      "confidence": 0.95,
      "context": "The sentence or phrase where this entity was mentioned",
      "properties": {
        "additional_info": "any relevant details"
      }
    }
  ]
}
```

Return only valid JSON, no additional text.
"""

    def __init__(self, config: Config):
        self.config = config
        self.client = None
        if config.OPENAI_API_KEY:
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        else:
            logger.warning("OpenAI API key not configured")
    
    def extract_entities(self, content: str) -> List[Entity]:
        """Extract entities from content using LLM."""
        if not self.client:
            logger.error("OpenAI client not initialized")
            return []
        
        try:
            # Truncate content if too long
            max_content_length = 3000
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."
                logger.info("Content truncated for entity extraction", 
                          original_length=len(content), 
                          truncated_length=max_content_length)
            
            # Create prompt
            prompt = self.ENTITY_EXTRACTION_PROMPT.format(content=content)
            
            # Get LLM response
            response = self.client.chat.completions.create(
                model=self.config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert entity extractor. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.LLM_TEMPERATURE,
                max_tokens=self.config.LLM_MAX_TOKENS
            )
            
            # Parse JSON response
            result_text = response.choices[0].message.content
            # Extract JSON from response (handle code blocks)
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            result = json.loads(result_text.strip())
            
            # Convert to Entity objects
            entities = []
            for entity_data in result.get('entities', []):
                # Filter by confidence threshold
                if entity_data.get('confidence', 0) < self.config.ENTITY_CONFIDENCE_THRESHOLD:
                    continue
                    
                entity = Entity(
                    name=entity_data['name'],
                    type=entity_data['type'],
                    aliases=entity_data.get('aliases', []),
                    confidence=entity_data['confidence'],
                    context=entity_data.get('context'),
                    properties=entity_data.get('properties', {})
                )
                entities.append(entity)
            
            # Limit entities to configured maximum
            if len(entities) > self.config.MAX_ENTITIES_PER_NEWSLETTER:
                entities = sorted(entities, key=lambda e: e.confidence, reverse=True)
                entities = entities[:self.config.MAX_ENTITIES_PER_NEWSLETTER]
                logger.info("Entities limited to maximum", 
                          total_extracted=len(entities),
                          limit=self.config.MAX_ENTITIES_PER_NEWSLETTER)
            
            logger.info("Entities extracted successfully", count=len(entities))
            return entities
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM response as JSON", error=str(e))
            return []
        except Exception as e:
            logger.error("Error extracting entities", error=str(e))
            return []