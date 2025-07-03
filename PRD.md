# Arrgh! Aggregated Research Repository
## Product Requirements Document (PRD)

### Executive Summary

**Arrgh! Aggregated Research Repository** is an intelligent knowledge management application that automatically extracts entities and temporal facts from email newsletters. The system receives HTML content from newsletters via an n8n workflow, uses LangGraph for sophisticated multi-step entity and fact extraction, and builds a comprehensive knowledge graph in Neo4j.

### Problem Statement

Organizations receive hundreds of newsletters containing valuable business intelligence about companies, people, products, and events. This information is currently siloed in email inboxes and not systematically captured for organizational knowledge management. Manual extraction is time-intensive and inconsistent. **Arrgh! Aggregated Research Repository** solves this by automatically building a searchable knowledge graph from newsletter content.

### Solution Overview

**Arrgh! Aggregated Research Repository** provides an automated pipeline that:
1. Receives newsletter HTML content via FastAPI endpoint
2. Extracts structured entities using LLM-powered analysis
3. Builds and maintains a temporal knowledge graph
4. Enables intelligent querying of extracted business intelligence

*"Shiver me timbers! From scattered newsletters to organized treasure troves of knowledge!"*

---

## System Architecture

### Data Flow
```
AWS SES → n8n Workflow → /process-newsletter → LangGraph Pipeline → Neo4j Database
                ↑                                                        ↓
                └─────────── Text Summary Response ←─────────────────────┘
```

### Core Components

#### 1. FastAPI Endpoint (`/process-newsletter`)
- **Input**: Newsletter HTML content, subject, sender metadata
- **Processing**: Orchestrates LangGraph workflow
- **Output**: Extraction results, entity/fact counts, and text summary for n8n workflow

#### 2. LangGraph Workflow
Multi-step stateful pipeline handling:
- HTML content cleaning and preprocessing
- Entity extraction and classification
- Database entity resolution
- Fact extraction with temporal context
- Knowledge graph updates

#### 3. Neo4j Knowledge Graph
- **Nodes**: Entities (Organizations, People, Products, Events, Newsletters)
- **Relationships**: Temporal facts connecting entities
- **Properties**: Metadata, timestamps, confidence scores

#### 4. n8n Workflow Integration
- **Response Handling**: Receives text summary for workflow decisions
- **Logging**: Uses summary for audit trails and notifications
- **Conditional Logic**: Can route based on extraction results
- **Error Handling**: Processes error messages for retry logic

---

## Entity Types

### Primary Entities
| Entity Type | Description | Examples |
|-------------|-------------|----------|
| **Organization** | Companies, institutions, government bodies | "OpenAI", "Microsoft", "U.S. Department of Energy" |
| **Person** | Individuals mentioned in content | "Sam Altman", "Satya Nadella" |
| **Product** | Software, hardware, services | "GPT-4", "Azure", "iPhone 15" |
| **Event** | Conferences, announcements, launches | "Apple WWDC 2024", "OpenAI Dev Day" |
| **Location** | Geographic locations | "San Francisco", "Silicon Valley" |
| **Topic** | Subject areas, technologies | "AI Safety", "Quantum Computing" |

### Entity Properties
- **Name**: Canonical entity name
- **Type**: Entity classification
- **Aliases**: Alternative names/mentions
- **Confidence**: Extraction confidence score (0-1)
- **Source**: Newsletter/email reference
- **First_Seen**: Initial extraction timestamp
- **Last_Updated**: Most recent mention timestamp

---

## Fact Extraction

### Fact Types
- **Relationships**: "Person X works at Organization Y"
- **Events**: "Organization X announced Product Y on Date Z"
- **Attributes**: "Product X has feature Y"
- **Changes**: "Person X moved from Organization Y to Organization Z"

### Temporal Context
- **Date**: When the fact was reported
- **Validity**: Temporal scope of the fact
- **Source**: Newsletter containing the information
- **Confidence**: LLM assessment of fact reliability

---

## LangGraph Workflow Design

### State Schema
```python
class ExtractionState(TypedDict):
    html_content: str
    newsletter_subject: str
    newsletter_sender: str
    processed_content: str
    extracted_entities: List[Entity]
    existing_entities: List[Entity]
    new_entities: List[Entity]
    extracted_facts: List[Fact]
    text_summary: str
    processing_errors: List[str]
    completion_status: str
```

### Workflow Steps

#### 1. **Content Preprocessing**
- Clean HTML content
- Extract readable text
- Identify key sections (headlines, body, etc.)

#### 2. **Entity Extraction**
- Use LLM to identify entities by type
- Extract entity mentions and context
- Resolve entity aliases and variations

#### 3. **Entity Resolution**
- Query Neo4j for existing entities
- Match extracted entities to existing nodes
- Identify truly new entities

#### 4. **Entity Persistence**
- Create new entity nodes in Neo4j
- Update existing entities with new information
- Link entities to newsletter source

#### 5. **Fact Extraction**
- Analyze content for entity relationships
- Extract temporal facts and events
- Determine fact confidence and validity

#### 6. **Fact Persistence**
- Create relationship edges in Neo4j
- Attach temporal metadata
- Link facts to source newsletter

#### 7. **Summary Generation**
- Generate human-readable processing summary
- Include key extracted entities and notable mentions
- Format summary for n8n workflow consumption
- Prepare final response payload

#### 8. **Quality Assurance**
- Validate extracted data consistency
- Log processing metrics
- Handle extraction errors

---

## API Specification

### POST `/process-newsletter`

#### Request Body
```json
{
  "html_content": "string (required)",
  "subject": "string (required)",
  "sender": "string (required)",
  "received_date": "ISO 8601 timestamp (optional)",
  "newsletter_id": "string (optional)"
}
```

#### Response
```json
{
  "status": "success|error",
  "processing_time": "float (seconds)",
  "entities_extracted": "integer",
  "entities_new": "integer", 
  "entities_updated": "integer",
  "facts_extracted": "integer",
  "facts_new": "integer",
  "newsletter_node_id": "string",
  "summary": {
    "organizations": "integer",
    "people": "integer", 
    "products": "integer",
    "events": "integer",
    "locations": "integer",
    "topics": "integer"
  },
  "text_summary": "string (human-readable processing summary)",
  "errors": ["string array"]
}
```

#### Text Summary Format
The `text_summary` field provides a human-readable overview for n8n workflow logging and notifications:

**Example Summary:**
```
"Processed newsletter 'AI Weekly #245' from TechCrunch. Extracted 8 entities (3 organizations, 2 people, 2 products, 1 event) and 12 facts. Notable mentions: OpenAI announced GPT-5, Microsoft expanded Azure AI services, Sam Altman spoke at Stanford. Processing completed in 45.2 seconds."
```

---

## Technical Requirements

### Dependencies
- **FastAPI**: Web framework with `/process-newsletter` endpoint
- **LangGraph**: LLM workflow orchestration
- **Neo4j Python Driver**: Database connectivity
- **LangChain**: LLM integrations
- **BeautifulSoup4**: HTML parsing
- **Pydantic**: Data validation
- **python-dateutil**: Date parsing

### Environment Variables
```env
# LLM Configuration
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4-turbo

# Neo4j Configuration  
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Processing Configuration
MAX_ENTITIES_PER_NEWSLETTER=100
FACT_EXTRACTION_BATCH_SIZE=10
PROCESSING_TIMEOUT=300
```

### Database Schema

#### Neo4j Node Labels
- `Newsletter`: Source newsletter metadata
- `Organization`: Company/institution entities
- `Person`: Individual entities
- `Product`: Product/service entities
- `Event`: Event/announcement entities
- `Location`: Geographic entities
- `Topic`: Subject area entities

#### Neo4j Relationships
- `MENTIONED_IN`: Entity → Newsletter
- `WORKS_AT`: Person → Organization
- `LOCATED_IN`: Entity → Location
- `PARTICIPATED_IN`: Entity → Event
- `ANNOUNCED`: Organization → Product/Event
- `RELATED_TO`: Entity → Entity (temporal)

---

## Success Metrics

### Processing Metrics
- **Throughput**: Newsletters processed per hour
- **Latency**: Average processing time per newsletter
- **Success Rate**: Percentage of successful extractions
- **Error Rate**: Failed processing attempts

### Quality Metrics
- **Entity Accuracy**: Manual validation of extracted entities
- **Fact Precision**: Accuracy of extracted relationships
- **Duplicate Detection**: Effectiveness of entity resolution
- **Temporal Accuracy**: Correctness of temporal fact assignment

### Business Metrics
- **Knowledge Growth**: Rate of new entity discovery
- **Relationship Density**: Average facts per entity
- **Source Coverage**: Newsletter sources integrated
- **Query Performance**: Knowledge graph query speed

---

## Implementation Phases

### Phase 1: Core Pipeline (Week 1-2)
- FastAPI endpoint implementation
- Basic LangGraph workflow
- Simple entity extraction
- Neo4j integration

### Phase 2: Enhanced Extraction (Week 3-4)
- Advanced entity resolution
- Fact extraction pipeline
- Temporal relationship handling
- Error handling and logging

### Phase 3: Production Optimization (Week 5-6)
- Performance optimization
- Batch processing capabilities
- Monitoring and alerting
- Documentation and testing

### Phase 4: Intelligence Features (Week 7-8)
- Entity disambiguation
- Confidence scoring
- Duplicate detection
- Query API endpoints

---

## Risk Assessment

### Technical Risks
- **LLM Reliability**: Inconsistent entity extraction quality
- **Database Performance**: Neo4j query performance at scale
- **Processing Latency**: Time limits for n8n workflow integration

### Mitigation Strategies
- Implement confidence scoring and manual review queues
- Database indexing and query optimization
- Asynchronous processing with status callbacks

### Operational Risks
- **API Rate Limits**: OpenAI usage costs and limits
- **Data Quality**: Newsletter format variations
- **System Dependencies**: Neo4j availability

### Mitigation Strategies  
- Cost monitoring and usage optimization
- Robust HTML parsing with fallback strategies
- Database backup and recovery procedures

---

## Future Enhancements

### Advanced Features
- **Entity Disambiguation**: ML-powered entity matching
- **Relationship Inference**: Implied relationship detection
- **Trend Analysis**: Temporal pattern recognition
- **Query Interface**: Natural language knowledge queries

### Integration Opportunities
- **Slack Bot**: Knowledge graph queries via chat
- **Dashboard**: Visualization of extracted insights
- **API Gateway**: External system integrations
- **Export Functions**: Knowledge graph data export

---

## Conclusion

**Arrgh! Aggregated Research Repository** provides automated intelligence gathering from email newsletters, building a comprehensive temporal knowledge graph. The LangGraph-powered pipeline ensures reliable, stateful processing while Neo4j enables sophisticated relationship modeling and querying capabilities. This system transforms scattered newsletter content into organized, searchable business intelligence.