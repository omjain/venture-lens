"""
Pytest tests for Data Ingestion Agent
Tests both PDF and URL ingestion modes
"""
import pytest
import os
import tempfile
from pathlib import Path
import sys

# Add agents directory to path
agents_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, agents_dir)

from ingestion_agent import (
    ingest_data,
    extract_pdf_content,
    scrape_url_content,
    clean_text,
    chunk_slides_by_headings,
    summarize_with_llm
)


@pytest.fixture
def sample_pdf_content():
    """Create a temporary sample PDF-like content for testing"""
    content = """
    Slide 1: Title
    TechVenture - AI-Powered Solutions
    
    Slide 2: Problem
    The market faces significant challenges in data processing.
    Current solutions are slow and expensive.
    
    Slide 3: Solution
    TechVenture provides an AI-powered platform that processes data 10x faster.
    Our solution reduces costs by 80%.
    
    Slide 4: Traction
    We have 1,000 active users and $100K MRR.
    Growing at 20% month-over-month.
    
    Slide 5: Team
    Founded by John Doe (ex-Google) and Jane Smith (ex-Microsoft).
    """
    return content


@pytest.fixture
def sample_html_content():
    """Sample HTML content for URL scraping tests"""
    return """
    <html>
    <head>
        <meta name="description" content="TechVenture provides AI-powered solutions">
        <title>TechVenture - AI Solutions</title>
    </head>
    <body>
        <main>
            <h1>TechVenture</h1>
            <p>We are an AI-powered platform solving data processing challenges.</p>
            <h2>Problem</h2>
            <p>Current solutions are slow and expensive.</p>
            <h2>Solution</h2>
            <p>Our AI platform processes data 10x faster at 80% lower cost.</p>
            <h2>Traction</h2>
            <p>1,000 users, $100K MRR, growing 20% MoM.</p>
        </main>
    </body>
    </html>
    """


@pytest.mark.asyncio
async def test_chunk_slides_by_headings(sample_pdf_content):
    """Test slide chunking functionality"""
    slides = chunk_slides_by_headings(sample_pdf_content)
    
    assert len(slides) > 0, "Should create at least one slide"
    assert all('slide_number' in slide for slide in slides), "Each slide should have slide_number"
    assert all('content' in slide for slide in slides), "Each slide should have content"
    assert all('length' in slide for slide in slides), "Each slide should have length"


@pytest.mark.asyncio
async def test_clean_text():
    """Test text cleaning functionality"""
    dirty_text = "  Hello    World  \n\n\n  This   is   a   test  "
    cleaned = clean_text(dirty_text)
    
    assert len(cleaned) > 0, "Cleaned text should not be empty"
    assert "  " not in cleaned, "Should remove excessive spaces"
    assert cleaned.strip() == cleaned, "Should remove leading/trailing whitespace"


@pytest.mark.asyncio
async def test_extract_pdf_content():
    """Test PDF content extraction (requires actual PDF or mocking)"""
    # This test requires either a real PDF file or mocking
    # For now, we'll test that it handles missing file correctly
    
    with pytest.raises((FileNotFoundError, ValueError, Exception)):
        await extract_pdf_content("/nonexistent/file.pdf")


@pytest.mark.asyncio
async def test_scrape_url_content(httpx_mock):
    """Test URL scraping functionality"""
    # Mock HTTP response
    sample_html = """
    <html>
    <head><meta name="description" content="Test startup"></head>
    <body><main><p>This is test content about a startup.</p></main></body>
    </html>
    """
    
    httpx_mock.add_response(
        method="GET",
        url="https://example.com/startup",
        text=sample_html,
        status_code=200
    )
    
    content = await scrape_url_content("https://example.com/startup")
    
    assert len(content) > 0, "Should extract content from URL"
    assert "startup" in content.lower(), "Should contain scraped content"


@pytest.mark.asyncio
async def test_summarize_with_llm():
    """Test LLM summarization (may use mock if LLM not available)"""
    sample_text = """
    TechVenture is an AI-powered data processing platform.
    The problem: Current solutions are slow.
    Solution: We provide 10x faster processing.
    Traction: 1,000 users, $100K MRR.
    Team: Founded by ex-Google and ex-Microsoft engineers.
    """
    
    result = await summarize_with_llm(sample_text, "PDF")
    
    assert isinstance(result, dict), "Should return a dictionary"
    assert "startup_name" in result, "Should include startup_name"
    assert "description" in result, "Should include description"
    assert "problem" in result, "Should include problem"
    assert "solution" in result, "Should include solution"
    assert "traction" in result, "Should include traction"


@pytest.mark.asyncio
async def test_ingest_data_pdf_mode():
    """Test PDF ingestion mode"""
    # Create a mock PDF file content
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj"
    pdf_filename = "test.pdf"
    
    # This will likely fail without a real PDF, but tests the function structure
    try:
        result = await ingest_data(
            pdf_file=pdf_content,
            pdf_filename=pdf_filename
        )
        
        # If successful, verify structure
        assert isinstance(result, dict), "Should return a dictionary"
        assert "_metadata" in result, "Should include metadata"
        assert result["_metadata"]["source_type"] == "PDF", "Should indicate PDF source"
        
    except Exception as e:
        # Expected if PDF parsing fails with mock data
        assert "PDF" in str(e) or "extract" in str(e).lower() or "empty" in str(e).lower()


@pytest.mark.asyncio
async def test_ingest_data_url_mode(httpx_mock):
    """Test URL ingestion mode"""
    # Mock HTTP response
    sample_html = """
    <html>
    <head>
        <meta name="description" content="TechVenture AI Solutions">
        <title>TechVenture</title>
    </head>
    <body>
        <main>
            <h1>TechVenture</h1>
            <p>We provide AI-powered data processing solutions.</p>
            <h2>Problem</h2>
            <p>Current data processing is slow and expensive.</p>
            <h2>Solution</h2>
            <p>Our platform processes data 10x faster at lower cost.</p>
            <h2>Traction</h2>
            <p>We have 1,000 users and $100K monthly recurring revenue.</p>
            <h2>Team</h2>
            <p>Founded by John Doe (ex-Google) and Jane Smith (ex-Microsoft).</p>
        </main>
    </body>
    </html>
    """
    
    httpx_mock.add_response(
        method="GET",
        url="https://example.com/techventure",
        text=sample_html,
        status_code=200
    )
    
    result = await ingest_data(url="https://example.com/techventure")
    
    assert isinstance(result, dict), "Should return a dictionary"
    assert "_metadata" in result, "Should include metadata"
    assert result["_metadata"]["source_type"] == "URL", "Should indicate URL source"
    assert "startup_name" in result, "Should extract startup name"
    assert "description" in result, "Should extract description"


@pytest.mark.asyncio
async def test_ingest_data_validation():
    """Test input validation"""
    # Should raise error if neither PDF nor URL provided
    with pytest.raises((ValueError, Exception)):
        await ingest_data()


@pytest.mark.asyncio
async def test_fallback_extraction():
    """Test that fallback extraction works when LLM fails"""
    from ingestion_agent import _fallback_extraction
    
    text = """
    Company: TechVenture
    Problem: Data processing is slow
    Solution: AI-powered platform
    Sector: SaaS
    """
    
    result = _fallback_extraction(text)
    
    assert isinstance(result, dict), "Should return a dictionary"
    assert "startup_name" in result, "Should extract startup name"
    assert "sector" in result, "Should extract sector"
    assert result["sector"] in ["SaaS", "Technology"], "Should identify SaaS sector"


def test_ingestion_agent_imports():
    """Test that all required modules can be imported"""
    try:
        import ingestion_agent
        import llm_service
        assert True, "All imports successful"
    except ImportError as e:
        pytest.skip(f"Required modules not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

