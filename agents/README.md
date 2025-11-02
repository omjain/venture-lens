# Data Ingestion Agent

Complete data ingestion agent for Venture Lens GenAI that processes PDF files and URLs to extract structured startup information.

## Features

- ✅ **FastAPI Endpoint**: `/ingest` accepts multipart PDF uploads or URLs
- ✅ **PDF Processing**: Uses LangChain's UnstructuredPDFLoader with PyPDF fallback
- ✅ **Slide Chunking**: Intelligent slide segmentation by headings and visual separation
- ✅ **URL Scraping**: BeautifulSoup-based web scraping with meta tag extraction
- ✅ **LLM Summarization**: Uses Gemini 1.5 Pro via `llm_service.invoke()`
- ✅ **Structured Extraction**: Returns JSON with startup_name, description, problem, solution, traction, etc.
- ✅ **Rich Logging**: Beautiful console logging with progress indicators
- ✅ **Comprehensive Tests**: Pytest test suite for both PDF and URL modes

## Structure

```
agents/
├── ingestion_agent.py    # Main ingestion agent implementation
├── llm_service.py       # Unified LLM service for Gemini/Vertex AI
├── test_ingestion_agent.py  # Pytest test suite
└── __init__.py          # Package initialization
```

## Usage

### FastAPI Endpoint

**POST** `/ingest`

#### PDF Upload:
```bash
curl -X POST "http://localhost:8000/ingest" \
  -F "file=@pitchdeck.pdf"
```

#### URL Scraping:
```bash
curl -X POST "http://localhost:8000/ingest" \
  -F "url=https://example.com/startup"
```

### Python Usage

```python
from ingestion_agent import ingest_data

# PDF mode
result = await ingest_data(
    pdf_file=pdf_bytes,
    pdf_filename="startup.pdf"
)

# URL mode
result = await ingest_data(url="https://startup.com")
```

## Response Format

```json
{
  "startup_name": "TechVenture",
  "description": "AI-powered data processing platform...",
  "problem": "Current solutions are slow and expensive",
  "solution": "Our platform processes data 10x faster",
  "traction": "1,000 users, $100K MRR, 20% MoM growth",
  "team": "Founded by ex-Google and ex-Microsoft engineers",
  "market": "Data processing market worth $50B",
  "business_model": "SaaS subscription model",
  "competition": "Competing against legacy solutions",
  "funding": "Seed round: $2M from ABC Ventures",
  "stage": "Seed",
  "technology": "AI, Machine Learning, Cloud",
  "sector": "SaaS",
  "_metadata": {
    "source_type": "PDF",
    "file_path": "...",
    "total_slides": 12,
    "content_length": 5000
  }
}
```

## Installation

```bash
cd api
pip install -r requirements.txt
```

New dependencies:
- `langchain` - LangChain framework
- `langchain-community` - Community loaders
- `beautifulsoup4` - HTML parsing
- `lxml` - XML/HTML parser
- `rich` - Beautiful terminal output
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-mock` - Mocking support

## Testing

Run the test suite:

```bash
# From project root
pytest agents/test_ingestion_agent.py -v

# With coverage
pytest agents/test_ingestion_agent.py --cov=agents --cov-report=html
```

## Configuration

Requires same environment variables as other services:

```env
GEMINI_PROJECT_ID=your_project_id
GEMINI_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
```

OR

```env
GEMINI_API_KEY=your_api_key
```

## Logging

The agent uses Rich logging for beautiful console output:

- 📚 PDF extraction
- 📄 Slide chunking
- 🌐 URL scraping
- 🧹 Text cleaning
- 🤖 LLM summarization
- ✅ Success indicators

## Error Handling

- **PDF parsing failures**: Falls back to PyPDF2
- **LLM failures**: Falls back to rule-based extraction
- **URL scraping failures**: Raises descriptive errors
- **Invalid inputs**: Returns 400 with clear error messages

