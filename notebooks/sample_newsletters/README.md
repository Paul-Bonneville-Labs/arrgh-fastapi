# Sample Newsletter Collection

This directory contains sample newsletter HTML files for testing the newsletter processing pipeline. Each newsletter represents a different format, style, and content focus to ensure robust entity extraction and processing.

## Newsletter Samples

### 1. `ai_weekly_245.html`
**Focus**: Artificial Intelligence and Technology
**Format**: Modern HTML with CSS styling and semantic markup
**Key Entity Types**:
- **Organizations**: OpenAI, Microsoft, Google, Anthropic, Stanford, MIT
- **People**: Sam Altman, Satya Nadella, Sundar Pichai, Fei-Fei Li
- **Products**: GPT-5, Azure AI, Gemini Pro, H200 GPU
- **Events**: OpenAI DevDay 2024, Microsoft Build 2024, Google I/O 2024, NeurIPS 2024
- **Locations**: San Francisco, Seattle, Mountain View, New Orleans
- **Topics**: AI Safety, Machine Learning, Quantum Computing, Neural Networks

### 2. `tech_crunch_startup_digest.html`
**Focus**: Startup Funding, Acquisitions, and Business News
**Format**: Newsletter-style HTML with section dividers and financial data
**Key Entity Types**:
- **Organizations**: Scale AI, Tempus, Runway ML, Adobe, Figma, Salesforce, Meta
- **People**: Alexandr Wang, Eric Lefkofsky, Dylan Field, Patrick Collison, Ivan Zhao
- **Products**: Precision Medicine Platform, Gen-2 Video Model, Stripe Tax, Notion AI
- **Events**: Stripe Sessions 2024, Notion BuildCon, AWS re:Invent 2024, CES 2025
- **Locations**: San Francisco, New York, Austin, Las Vegas, London, Toronto
- **Topics**: Series A Funding, Acquisitions, PropTech, FinTech, HealthTech, Climate Tech

### 3. `nature_research_highlights.html`
**Focus**: Scientific Research and Academic Publications
**Format**: Academic journal style with formal formatting and citations
**Key Entity Types**:
- **Organizations**: UC Berkeley, Harvard, MIT, Stanford, Google Quantum AI, NASA
- **People**: Jennifer Doudna, Carl June, Sara Seager, John Preskill, Miguel Nicolelis
- **Products**: CRISPR-Cas9, James Webb Space Telescope, CAR-T Cell Therapy
- **Events**: AAAS Annual Meeting, ICML, Gordon Research Conference
- **Locations**: Berkeley, Cambridge, Vienna, Hong Kong, Denver, Sydney
- **Topics**: Gene Editing, Quantum Computing, Exoplanets, Brain-Computer Interfaces

## Testing Strategy

These newsletters are designed to test:

1. **HTML Parsing Robustness**: Different HTML structures, CSS styles, and formatting
2. **Entity Extraction Accuracy**: Diverse entity types across different domains
3. **Context Understanding**: Varying sentence structures and technical terminology
4. **Relationship Detection**: Different types of relationships (employment, location, collaboration)
5. **Temporal Processing**: Event dates, funding rounds, and publication timelines

## Usage

Load these newsletters in the processing pipeline to:
- Test entity extraction prompts
- Validate graph database operations
- Measure processing performance
- Debug edge cases and formatting issues
- Evaluate confidence scoring accuracy

## Expected Extraction Results

Each newsletter should yield approximately:
- **AI Weekly**: 25-30 entities, 15-20 relationships
- **TechCrunch**: 30-35 entities, 20-25 relationships  
- **Nature Research**: 35-40 entities, 25-30 relationships

The variety ensures comprehensive testing of the processing pipeline across different content types and complexity levels.