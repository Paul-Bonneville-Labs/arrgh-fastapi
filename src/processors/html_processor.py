"""HTML processing utilities for newsletter content."""
from bs4 import BeautifulSoup
import html2text
from typing import Dict, List
import structlog

logger = structlog.get_logger()


def clean_html_content(html_content: str) -> str:
    """Clean and extract text from HTML content."""
    try:
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Convert to text using html2text for better formatting
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.body_width = 0  # Don't wrap lines
        
        # Get text content
        text_content = h.handle(str(soup))
        
        # Clean up extra whitespace
        cleaned_text = ' '.join(text_content.split())
        
        logger.info("HTML content cleaned", content_length=len(cleaned_text))
        return cleaned_text
    
    except Exception as e:
        logger.error("Error cleaning HTML", error=str(e))
        return ""


def extract_text_sections(html_content: str) -> Dict[str, any]:
    """Extract different sections of the newsletter."""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        sections = {
            'title': '',
            'headers': [],
            'paragraphs': [],
            'links': []
        }
        
        # Extract title
        title_tag = soup.find('title') or soup.find('h1')
        if title_tag:
            sections['title'] = title_tag.get_text().strip()
        
        # Extract headers
        for header in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            sections['headers'].append(header.get_text().strip())
        
        # Extract paragraphs
        for para in soup.find_all('p'):
            text = para.get_text().strip()
            if text:
                sections['paragraphs'].append(text)
        
        # Extract links
        for link in soup.find_all('a', href=True):
            sections['links'].append({
                'text': link.get_text().strip(),
                'url': link['href']
            })
        
        logger.info(
            "Text sections extracted",
            headers_count=len(sections['headers']),
            paragraphs_count=len(sections['paragraphs']),
            links_count=len(sections['links'])
        )
        
        return sections
    
    except Exception as e:
        logger.error("Error extracting sections", error=str(e))
        return {}