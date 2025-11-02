# Pitch Deck Analysis API

## Overview

The `/analyze-pitchdeck` endpoint analyzes PDF pitch decks using LangChain's UnstructuredPDFLoader. It segments slides, classifies each slide, summarizes content, and generates a missing-slide report.

## Installation

Install required dependencies:

```bash
cd api
pip install -r requirements.txt
```

New dependencies added:
- `langchain` - LangChain framework
- `langchain-community` - Community loaders (including UnstructuredPDFLoader)
- `unstructured` - PDF processing backend
- `pypdf` - Fallback PDF extraction
- `pdf2image` - Image extraction (optional)
- `Pillow` - Image processing

## Usage

### Endpoint 1: Upload PDF File

**POST** `/analyze-pitchdeck`

Upload a PDF file directly:

```bash
curl -X POST "http://localhost:8000/analyze-pitchdeck" \
  -F "file=@/path/to/pitchdeck.pdf"
```

### Endpoint 2: Analyze by File Path

**POST** `/analyze-pitchdeck-path`

Provide a file path (for testing with local files):

```bash
curl -X POST "http://localhost:8000/analyze-pitchdeck-path" \
  -H "Content-Type: application/json" \
  -d '{"pdf_path": "/path/to/pitchdeck.pdf"}'
```

## Response Format

```json
{
  "total_slides": 12,
  "slides": [
    {
      "slide_number": 1,
      "slide_type": "Title",
      "content": "Startup Name: TechVenture...",
      "summary": "Title slide introducing TechVenture...",
      "key_points": ["Company name", "Tagline", "Year founded"],
      "confidence": 0.85
    },
    {
      "slide_number": 2,
      "slide_type": "Problem",
      "content": "Market problem description...",
      "summary": "Identifies key pain points...",
      "key_points": ["Problem 1", "Problem 2", "Impact"],
      "confidence": 0.9
    }
  ],
  "missing_slide_report": {
    "missing_types": ["Financial Projections", "Competition"],
    "recommended_slides": [
      "Add financial projections to demonstrate revenue potential",
      "Add competitive analysis to show differentiation"
    ],
    "completeness_score": 0.83,
    "analysis": "Found 8 unique slide types. Missing 2 standard slides: Financial Projections, Competition"
  },
  "overall_summary": "Analyzed pitch deck with 12 slides. Identified sections: Title, Problem, Solution, Market Opportunity, Product/Service, Business Model, Traction, Team. Completeness score: 83%.",
  "identified_sections": ["Title", "Problem", "Solution", "Market Opportunity", "Product/Service", "Business Model", "Traction", "Team"]
}
```

## Slide Types

The analyzer recognizes these standard pitch deck slide types:

1. **Title** - Opening slide with company name
2. **Problem** - Market problem/pain points
3. **Solution** - Product/solution description
4. **Market Opportunity** - TAM/SAM/SOM analysis
5. **Product/Service** - Product features/benefits
6. **Business Model** - Revenue model
7. **Traction** - Metrics, growth, validation
8. **Team** - Founding team and advisors
9. **Competition** - Competitive analysis
10. **Financial Projections** - Revenue forecasts
11. **Funding Ask** - Investment request
12. **Roadmap** - Future milestones
13. **Contact** - Contact information
14. **Other** - Uncategorized slides

## How It Works

1. **PDF Loading**: Uses LangChain's `UnstructuredPDFLoader` (falls back to PyPDF2)
2. **Slide Segmentation**: Identifies slide boundaries using page breaks and content patterns
3. **Classification**: Uses LLM (Vertex AI/Gemini) to classify each slide type (falls back to rule-based)
4. **Summarization**: Generates summaries and extracts key points for each slide (uses LLM if available)
5. **Missing Slide Report**: Compares found slides against standard deck structure

## Configuration

Requires Vertex AI or Gemini API credentials (same as scoring endpoint):

```env
GEMINI_PROJECT_ID=your_project_id
GEMINI_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
```

If LLM is not available, the system uses:
- Rule-based classification (keyword matching)
- Extractive summarization (first sentences, key metrics)

## Example Python Usage

```python
import httpx

# Upload PDF
with open("pitchdeck.pdf", "rb") as f:
    files = {"file": ("pitchdeck.pdf", f, "application/pdf")}
    response = httpx.post("http://localhost:8000/analyze-pitchdeck", files=files)
    result = response.json()

print(f"Total slides: {result['total_slides']}")
print(f"Completeness: {result['missing_slide_report']['completeness_score'] * 100}%")
print(f"Missing: {result['missing_slide_report']['missing_types']}")
```

## Error Handling

- **400 Bad Request**: Invalid file format or empty PDF
- **404 Not Found**: File path not found (for path endpoint)
- **500 Internal Server Error**: Analysis failed (check logs)

## Performance

- Small PDFs (< 10 pages): ~5-10 seconds
- Medium PDFs (10-20 pages): ~15-30 seconds
- Large PDFs (> 20 pages): ~30-60 seconds

Processing time depends on:
- PDF complexity
- Number of slides
- LLM availability (faster with LLM for classification/summarization)



