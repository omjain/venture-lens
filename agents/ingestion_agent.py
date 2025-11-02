"""
End-to-End Multi-Modal Ingestion Agent for Venture Lens
Uses Gemini-native multimodal API with PDF support
"""
import os
import tempfile
import shutil
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

# Import core LLM service
try:
    import sys
    core_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core')
    if os.path.exists(core_path):
        sys.path.insert(0, core_path)
    from llm_service import get_service
    CORE_LLM_AVAILABLE = True
except ImportError as e:
    CORE_LLM_AVAILABLE = False
    logging.warning(f"Core LLM service not available: {e}")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ingestion_agent")


def extract_pdf_text(pdf_path: str) -> str:
    """
    Extract text from PDF using PyPDFLoader or pdfplumber
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Extracted text content
    """
    logger.info(f"📚 Extracting text from PDF: {Path(pdf_path).name}")
    
    content = ""
    
    # Try PyPDFLoader first (LangChain)
    try:
        from langchain_community.document_loaders import PyPDFLoader
        logger.info("   Using PyPDFLoader")
        
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        content = "\n\n".join([doc.page_content for doc in documents])
        
        logger.info(f"   ✓ Extracted {len(documents)} pages")
        
    except ImportError:
        logger.info("   PyPDFLoader not available, trying pdfplumber")
        
        # Fallback to pdfplumber
        try:
            import pdfplumber
            
            with pdfplumber.open(pdf_path) as pdf:
                pages_text = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        pages_text.append(page_text)
                
                content = "\n\n".join(pages_text)
                logger.info(f"   ✓ Extracted {len(pages_text)} pages using pdfplumber")
                
        except ImportError:
            logger.warning("   pdfplumber not available, trying pypdf fallback")
            
            # Final fallback: pypdf
            try:
                import pypdf
                with open(pdf_path, 'rb') as file:
                    pdf_reader = pypdf.PdfReader(file)
                    for page in pdf_reader.pages:
                        content += page.extract_text() + "\n\n"
                logger.info(f"   ✓ Extracted {len(pdf_reader.pages)} pages using pypdf")
                
            except ImportError:
                raise ImportError(
                    "No PDF extraction library available. "
                    "Please install one of: langchain-community, pdfplumber, or pypdf"
                )
            except Exception as e:
                logger.error(f"   ✗ PyPDF extraction failed: {e}")
                raise Exception(f"PDF extraction failed: {str(e)}")
    
    except Exception as e:
        logger.error(f"   ✗ PyPDFLoader extraction failed: {e}")
        raise Exception(f"PDF extraction failed: {str(e)}")
    
    if not content or len(content.strip()) < 50:
        raise ValueError("PDF appears to be empty or unreadable")
    
    return content.strip()


async def scrape_urls(urls: List[str]) -> str:
    """
    Scrape content from multiple URLs
    
    Args:
        urls: List of URLs to scrape
        
    Returns:
        Combined scraped text content
    """
    import httpx
    from bs4 import BeautifulSoup
    
    logger.info(f"🌐 Scraping {len(urls)} URL(s)")
    
    all_content = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for url in urls:
            try:
                logger.info(f"   Scraping: {url}")
                response = await client.get(
                    url,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    },
                    follow_redirects=True
                )
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'lxml')
                
                # Extract main content
                main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=lambda x: x and ('content' in x.lower() or 'main' in x.lower()))
                
                if main_content:
                    paragraphs = main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    text_content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                else:
                    # Fallback: extract all paragraphs
                    paragraphs = soup.find_all(['p', 'h1', 'h2', 'h3'])
                    text_content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                
                all_content.append(f"--- Content from {url} ---\n\n{text_content}")
                logger.info(f"   ✓ Scraped {len(text_content)} characters from {url}")
                
            except Exception as e:
                logger.warning(f"   ⚠️ Failed to scrape {url}: {e}")
                all_content.append(f"--- Error scraping {url}: {str(e)} ---")
    
    return "\n\n".join(all_content)


async def ingest_with_gemini(
    startup_name: str,
    description: str,
    pdf_bytes: Optional[bytes] = None,
    urls: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Ingest startup data using multimodal Gemini API
    
    Args:
        startup_name: Name of the startup
        description: Text description of the startup
        pdf_bytes: Optional PDF file bytes
        urls: Optional list of URLs to scrape
        
    Returns:
        Structured JSON with extracted information
    """
    logger.info(f"🚀 Starting multimodal ingestion for: {startup_name}")
    
    if not CORE_LLM_AVAILABLE:
        raise ImportError(
            "Core LLM service not available. "
            "Please ensure core/llm_service.py exists and google-generativeai is installed."
        )
    
    # Step 1: Prepare text content
    text_content = description
    
    # Step 2: Scrape URLs if provided
    if urls:
        logger.info(f"   Scraping {len(urls)} URL(s)")
        url_content = await scrape_urls(urls)
        text_content = f"{description}\n\n--- Additional Information from URLs ---\n\n{url_content}"
    
    # Step 3: Compose prompt for Gemini
    prompt = f"""You are a venture capital analyst specializing in startup evaluation.

Analyze the provided startup information and extract structured data.

Startup Name: {startup_name}

Startup Information:
{text_content}

Extract and structure the following information in JSON format:
{{
    "startup_name": "{startup_name}",
    "problem": "The problem or pain point the startup is solving (2-3 sentences)",
    "solution": "The solution, product, or service the startup offers (2-3 sentences)",
    "traction": "Current traction, metrics, users, revenue, growth, milestones, achievements",
    "team": "Founding team members, their backgrounds, expertise, and relevant experience",
    "market": "Target market, market size, opportunity, addressable market, market trends",
    "financials": "Financial information including revenue, funding, burn rate, projections, or financial health indicators"
}}

Be precise and extract only information that is explicitly mentioned or can be reasonably inferred.
If information for a section is not available, use an empty string or "Not provided".
Return ONLY valid JSON, no markdown formatting."""
    
    # Step 4: Call Gemini 1.5 Pro with multimodal request
    try:
        llm_service = get_service()
        
        logger.info("🤖 Calling Gemini 1.5 Pro with multimodal request")
        
        # Call with PDF bytes if present, otherwise text only
        if pdf_bytes:
            logger.info(f"   Including PDF in multimodal request ({len(pdf_bytes)} bytes)")
            response_text = llm_service.invoke(
                model="gemini-1.5-pro",
                prompt=prompt,
                pdf_bytes=pdf_bytes
            )
        else:
            logger.info("   Text-only request")
            response_text = llm_service.invoke(
                model="gemini-1.5-pro",
                prompt=prompt,
                pdf_bytes=None
            )
        
        logger.info("✅ Gemini API call successful")
        
    except Exception as e:
        logger.error(f"❌ Gemini API call failed: {e}")
        raise Exception(f"Failed to call Gemini API: {str(e)}")
    
    # Step 5: Parse JSON response
    try:
        # Clean response text (remove markdown code blocks if present)
        json_text = response_text.strip()
        
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
        
        logger.info("✅ Successfully parsed JSON response")
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Failed to parse JSON response: {e}")
        logger.error(f"   Response text: {response_text[:500]}...")
        raise Exception(f"Failed to parse JSON response: {str(e)}")
    
    # Step 6: Validate and structure response
    required_keys = ["startup_name", "problem", "solution", "traction", "team", "market", "financials"]
    
    validated_data = {}
    for key in required_keys:
        validated_data[key] = structured_data.get(key, "")
        if not validated_data[key]:
            validated_data[key] = "Not provided"
    
    logger.info("✅ Ingestion complete")
    
    return validated_data


async def ingest_endpoint(
    startup_name: str,
    description: str,
    file: Optional[bytes] = None,
    filename: Optional[str] = None,
    urls: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    FastAPI-compatible ingestion endpoint handler
    
    Args:
        startup_name: Name of the startup
        description: Text description
        file: Optional PDF file bytes
        filename: Optional filename (for validation)
        urls: Optional list of URLs
        
    Returns:
        Structured JSON response
    """
    temp_file_path = None
    temp_dir = None
    
    try:
        # Validate inputs
        if not startup_name or not startup_name.strip():
            raise ValueError("startup_name is required")
        
        if not description or not description.strip():
            raise ValueError("description is required")
        
        pdf_bytes = None
        
        # Step 1: Handle PDF file if present
        if file:
            if filename and not filename.lower().endswith('.pdf'):
                raise ValueError("File must be a PDF")
            
            logger.info(f"📄 Processing PDF file: {filename or 'uploaded.pdf'}")
            
            # Save temporarily to /tmp (or temp directory)
            temp_dir = tempfile.mkdtemp()
            temp_file_path = os.path.join(temp_dir, filename or "uploaded.pdf")
            
            with open(temp_file_path, 'wb') as f:
                f.write(file)
            
            logger.info(f"   Saved to temporary file: {temp_file_path}")
            
            # Extract text from PDF
            extracted_text = extract_pdf_text(temp_file_path)
            
            # Merge extracted text into description
            description = f"{description}\n\n--- Content from PDF ---\n\n{extracted_text}"
            
            logger.info(f"   Extracted {len(extracted_text)} characters from PDF")
            
            # Keep PDF bytes for multimodal call
            pdf_bytes = file
        
        # Step 2: Call multimodal Gemini ingestion
        result = await ingest_with_gemini(
            startup_name=startup_name,
            description=description,
            pdf_bytes=pdf_bytes,
            urls=urls or []
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}")
        raise
    
    finally:
        # Step 3: Clean up temporary files
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"   ✓ Deleted temporary file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"   ⚠️ Failed to delete temp file: {e}")
        
        if temp_dir and os.path.exists(temp_dir):
            try:
                os.rmdir(temp_dir)
                logger.info(f"   ✓ Deleted temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"   ⚠️ Failed to delete temp dir: {e}")


# Alias for backward compatibility
async def ingest(*args, **kwargs):
    """Alias for ingest_endpoint for compatibility"""
    return await ingest_endpoint(*args, **kwargs)


# Backward compatibility functions
async def ingest_data(
    pdf_file: Optional[bytes] = None,
    pdf_filename: Optional[str] = None,
    url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Legacy function for backward compatibility
    """
    if url:
        return await ingest_endpoint(
            startup_name="Unknown Startup",
            description=f"Information from URL: {url}",
            urls=[url]
        )
    elif pdf_file:
        return await ingest_endpoint(
            startup_name="Unknown Startup",
            description="Information from PDF",
            file=pdf_file,
            filename=pdf_filename
        )
    else:
        raise ValueError("Either pdf_file or url must be provided")
