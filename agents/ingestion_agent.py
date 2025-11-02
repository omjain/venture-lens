"""
Data Ingestion Agent for Venture Lens GenAI
Handles PDF and URL ingestion, extracts structured startup data
"""
import os
import tempfile
import shutil
from typing import Dict, Any, Optional, List
from pathlib import Path
import re
import json

import httpx
from bs4 import BeautifulSoup
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn
import logging

# Import LLM service - handle relative import
try:
    from llm_service import llm_service
except ImportError:
    # Try absolute import
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from llm_service import llm_service

# Setup rich logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, show_path=False)]
)

logger = logging.getLogger("ingestion_agent")
console = Console()


# Standard pitch deck slide patterns for chunking
SLIDE_MARKERS = [
    r'^#+\s+',  # Markdown headers
    r'^\d+[\.\)]\s+',  # Numbered lists
    r'^Slide\s+\d+',  # "Slide 1" pattern
    r'^Page\s+\d+',  # "Page 1" pattern
]


def chunk_slides_by_headings(content: str) -> List[Dict[str, Any]]:
    """
    Chunk content into slides based on headings or visual separation
    
    Args:
        content: Raw text content from PDF
        
    Returns:
        List of slide chunks with metadata
    """
    logger.info("📄 Chunking slides by headings and visual separation")
    
    slides = []
    
    # Try splitting by multiple newlines (visual separation)
    chunks = re.split(r'\n{3,}', content)  # 3+ newlines indicate slide break
    
    if len(chunks) == 1:
        # Try splitting by page break markers
        chunks = re.split(r'\f|\x0c', content)  # Form feed character
    
    if len(chunks) == 1:
        # Try splitting by slide number patterns
        chunks = re.split(r'(?=Slide\s+\d+|Page\s+\d+)', content, flags=re.IGNORECASE)
    
    if len(chunks) == 1:
        # Fallback: split by double newlines and chunk by length
        paragraphs = content.split('\n\n')
        current_chunk = []
        current_length = 0
        chunk_num = 1
        
        for para in paragraphs:
            para_length = len(para)
            # If adding paragraph exceeds 1500 chars, start new slide
            if current_length > 0 and current_length + para_length > 1500:
                slides.append({
                    "slide_number": chunk_num,
                    "content": '\n\n'.join(current_chunk),
                    "length": current_length
                })
                chunk_num += 1
                current_chunk = [para]
                current_length = para_length
            else:
                current_chunk.append(para)
                current_length += para_length
        
        if current_chunk:
            slides.append({
                "slide_number": chunk_num,
                "content": '\n\n'.join(current_chunk),
                "length": current_length
            })
    else:
        # Content was successfully split
        for idx, chunk in enumerate(chunks, 1):
            if chunk.strip():
                slides.append({
                    "slide_number": idx,
                    "content": chunk.strip(),
                    "length": len(chunk)
                })
    
    logger.info(f"   ✓ Segmented into {len(slides)} slides")
    return slides


async def extract_pdf_content(pdf_path: str) -> str:
    """
    Extract text from PDF using LangChain's UnstructuredPDFLoader
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Extracted text content
    """
    logger.info(f"📚 Extracting content from PDF: {Path(pdf_path).name}")
    
    content = ""
    
    # Try LangChain UnstructuredPDFLoader first
    try:
        from langchain_community.document_loaders import UnstructuredPDFLoader
        logger.info("   Using LangChain UnstructuredPDFLoader")
        
        loader = UnstructuredPDFLoader(pdf_path)
        documents = loader.load()
        content = "\n\n".join([doc.page_content for doc in documents])
        
        logger.info(f"   ✓ Loaded {len(documents)} pages")
        
    except ImportError:
        logger.warning("   ⚠️ LangChain not available, using PyPDF fallback")
        try:
            import pypdf
            with open(pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                for page in pdf_reader.pages:
                    content += page.extract_text() + "\n\n"
            logger.info(f"   ✓ Loaded {len(pdf_reader.pages)} pages using PyPDF")
        except Exception as e:
            logger.error(f"   ✗ PDF extraction failed: {e}")
            raise
    
    if not content or len(content.strip()) < 50:
        raise ValueError("PDF appears to be empty or unreadable")
    
    return content


async def scrape_url_content(url: str) -> str:
    """
    Scrape content from URL using requests + BeautifulSoup
    
    Args:
        url: URL to scrape
        
    Returns:
        Scraped text content with metadata
    """
    logger.info(f"🌐 Scraping content from URL: {url}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                follow_redirects=True
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Extract key meta tags
            meta_data = []
            for meta in soup.find_all('meta'):
                if meta.get('name') in ['description', 'keywords', 'og:description', 'og:title']:
                    content = meta.get('content', '')
                    if content:
                        meta_data.append(content)
            
            # Extract main content
            # Try to find main content area
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main|article', re.I))
            
            if main_content:
                paragraphs = main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                text_content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            else:
                # Fallback: extract all paragraphs
                paragraphs = soup.find_all(['p', 'h1', 'h2', 'h3'])
                text_content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            
            # Combine meta data and content
            full_content = '\n\n'.join(meta_data) + '\n\n' + text_content
            
            logger.info(f"   ✓ Scraped {len(full_content)} characters")
            
            return full_content
            
    except Exception as e:
        logger.error(f"   ✗ URL scraping failed: {e}")
        raise Exception(f"Failed to scrape URL: {str(e)}")


def clean_text(text: str) -> str:
    """
    Clean extracted text: remove excessive whitespace, normalize
    
    Args:
        text: Raw text content
        
    Returns:
        Cleaned text
    """
    logger.info("🧹 Cleaning extracted text")
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\:\;\(\)\-\']', ' ', text)
    
    # Normalize multiple spaces
    text = re.sub(r' +', ' ', text)
    
    # Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text = '\n'.join(lines)
    
    logger.info(f"   ✓ Cleaned text: {len(text)} characters")
    
    return text.strip()


async def summarize_with_llm(text: str, content_type: str = "PDF") -> Dict[str, Any]:
    """
    Clean and summarize text using LLM call
    
    Args:
        text: Text content to summarize
        content_type: Type of content (PDF or URL)
        
    Returns:
        Structured summary with startup information
    """
    logger.info(f"🤖 Summarizing {content_type} content with LLM")
    
    # Truncate if too long (keep first 8000 chars for prompt)
    truncated_text = text[:8000] if len(text) > 8000 else text
    
    system_prompt = """You are a data extraction agent for Venture Lens, an AI startup analysis platform.
Your task is to extract structured information about a startup from the provided content.
Be precise and extract only information that is explicitly mentioned."""

    prompt = f"""Extract structured information about a startup from this {content_type} content:

{truncated_text}

Extract and structure the following information in JSON format:
{{
    "startup_name": "Name of the startup/company",
    "description": "Brief description of what the company does (2-3 sentences)",
    "problem": "The problem the startup is solving",
    "solution": "The solution/product the startup offers",
    "traction": "Current traction, metrics, users, revenue, growth, milestones",
    "team": "Founding team members and their backgrounds",
    "market": "Target market, market size, opportunity",
    "business_model": "How the company makes money",
    "competition": "Competitive landscape or differentiation",
    "funding": "Funding status, amount raised, investors (if mentioned)",
    "stage": "Company stage (e.g., Pre-seed, Seed, Series A, etc.)",
    "technology": "Technology stack or key technologies used",
    "sector": "Industry sector (e.g., SaaS, Fintech, Healthcare, etc.)"
}}

If information is not available in the content, use null or empty string.
Be accurate and only extract information that is clearly stated in the content."""

    try:
        response = await llm_service.invoke(
            prompt=prompt,
            model="gemini-2.0-flash",
            temperature=0.3,  # Lower temperature for more factual extraction
            max_tokens=2048,
            system_prompt=system_prompt
        )
        
        # Parse JSON response
        json_text = response.strip()
        
        # Try to extract JSON if wrapped in markdown code blocks
        if "```json" in json_text:
            json_start = json_text.find("```json") + 7
            json_end = json_text.find("```", json_start)
            json_text = json_text[json_start:json_end].strip()
        elif "```" in json_text:
            json_start = json_text.find("```") + 3
            json_end = json_text.find("```", json_start)
            json_text = json_text[json_start:json_end].strip()
        
        # Parse JSON
        structured_data = json.loads(json_text)
        
        logger.info("   ✓ Successfully extracted structured data from LLM")
        return structured_data
        
    except json.JSONDecodeError as e:
        logger.error(f"   ✗ Failed to parse LLM JSON response: {e}")
        logger.info("   Using fallback extraction")
        return _fallback_extraction(text)
    except Exception as e:
        logger.error(f"   ✗ LLM summarization failed: {e}")
        return _fallback_extraction(text)


def _fallback_extraction(text: str) -> Dict[str, Any]:
    """Fallback extraction using rule-based patterns"""
    logger.info("   Using rule-based extraction fallback")
    
    text_lower = text.lower()
    
    # Extract startup name (look for company/startup name patterns)
    name_match = re.search(r'(?:company|startup|founded|name)[:\s]+([A-Z][a-zA-Z\s]+?)(?:\n|\.|,|$)', text, re.IGNORECASE)
    startup_name = name_match.group(1).strip() if name_match else "Unknown Startup"
    
    # Extract problem (look for problem/pain point keywords)
    problem_pattern = r'(?:problem|pain point|challenge|issue)[:\s]+(.+?)(?:\n\n|solution|$|\d+\.)'
    problem_match = re.search(problem_pattern, text, re.IGNORECASE | re.DOTALL)
    problem = problem_match.group(1).strip()[:500] if problem_match else ""
    
    # Extract solution
    solution_pattern = r'(?:solution|product|service|offering)[:\s]+(.+?)(?:\n\n|market|$|\d+\.)'
    solution_match = re.search(solution_pattern, text, re.IGNORECASE | re.DOTALL)
    solution = solution_match.group(1).strip()[:500] if solution_match else ""
    
    # Extract traction (look for metrics)
    traction_pattern = r'(?:traction|users|customers|revenue|growth|metrics?)[:\s]+(.+?)(?:\n\n|team|$|\d+\.)'
    traction_match = re.search(traction_pattern, text, re.IGNORECASE | re.DOTALL)
    traction = traction_match.group(1).strip()[:500] if traction_match else ""
    
    # Extract sector (industry keywords)
    sectors = ["SaaS", "Fintech", "Healthcare", "E-commerce", "EdTech", "AI", "Blockchain"]
    sector = "Technology"
    for sec in sectors:
        if sec.lower() in text_lower:
            sector = sec
            break
    
    return {
        "startup_name": startup_name,
        "description": text[:300] + "..." if len(text) > 300 else text,
        "problem": problem,
        "solution": solution,
        "traction": traction,
        "team": "",
        "market": "",
        "business_model": "",
        "competition": "",
        "funding": "",
        "stage": "",
        "technology": "",
        "sector": sector
    }


async def process_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Process PDF file: extract, chunk, clean, summarize
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Structured startup data
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Processing PDF...", total=None)
        
        # Step 1: Extract PDF content
        raw_content = await extract_pdf_content(pdf_path)
        progress.update(task, description="Extracting PDF content... ✓")
        
        # Step 2: Chunk slides
        slides = chunk_slides_by_headings(raw_content)
        progress.update(task, description=f"Chunked into {len(slides)} slides... ✓")
        
        # Step 3: Combine all slides
        combined_content = "\n\n--- Slide {} ---\n\n{}".join(
            [slide["content"] for slide in slides]
        )
        
        # Step 4: Clean text
        cleaned_content = clean_text(combined_content)
        progress.update(task, description="Cleaned text... ✓")
        
        # Step 5: Summarize with LLM
        structured_data = await summarize_with_llm(cleaned_content, "PDF")
        progress.update(task, description="Summarized with LLM... ✓")
        
        # Add metadata
        structured_data["_metadata"] = {
            "source_type": "PDF",
            "file_path": pdf_path,
            "total_slides": len(slides),
            "content_length": len(cleaned_content)
        }
        
        progress.update(task, description="✓ PDF processing complete")
    
    logger.info("✅ PDF processing completed successfully")
    return structured_data


async def process_url(url: str) -> Dict[str, Any]:
    """
    Process URL: scrape, clean, summarize
    
    Args:
        url: URL to scrape
        
    Returns:
        Structured startup data
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Processing URL...", total=None)
        
        # Step 1: Scrape URL content
        raw_content = await scrape_url_content(url)
        progress.update(task, description="Scraped URL content... ✓")
        
        # Step 2: Clean text
        cleaned_content = clean_text(raw_content)
        progress.update(task, description="Cleaned text... ✓")
        
        # Step 3: Summarize with LLM
        structured_data = await summarize_with_llm(cleaned_content, "URL")
        progress.update(task, description="Summarized with LLM... ✓")
        
        # Add metadata
        structured_data["_metadata"] = {
            "source_type": "URL",
            "url": url,
            "content_length": len(cleaned_content)
        }
        
        progress.update(task, description="✓ URL processing complete")
    
    logger.info("✅ URL processing completed successfully")
    return structured_data


# FastAPI endpoint integration will be added to main.py
# This function can be called from the endpoint

async def ingest_data(
    pdf_file: Optional[bytes] = None,
    pdf_filename: Optional[str] = None,
    url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main ingestion function - processes PDF or URL
    
    Args:
        pdf_file: PDF file bytes (if uploading PDF)
        pdf_filename: PDF filename
        url: URL string (if scraping URL)
        
    Returns:
        Structured startup data
    """
    logger.info("🚀 Starting data ingestion")
    
    if pdf_file and pdf_filename:
        # Process PDF
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, pdf_filename)
        
        try:
            # Save uploaded file
            with open(temp_file_path, "wb") as f:
                f.write(pdf_file)
            
            result = await process_pdf(temp_file_path)
            return result
            
        finally:
            # Cleanup
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
                
    elif url:
        # Process URL
        result = await process_url(url)
        return result
    
    else:
        raise ValueError("Either PDF file or URL must be provided")

