# AI Critique Agent

Venture Lens AI Critique Agent analyzes startups critically from a VC perspective, identifying red flags with severity levels and logging findings to PostgreSQL.

## Features

- ✅ **POST /critique endpoint** - FastAPI endpoint for critique analysis
- ✅ **Red Flag Identification** - Identifies up to 5 red flags with severity levels
- ✅ **Severity Classification** - low, medium, high, critical
- ✅ **Overall Risk Assessment** - low_risk, moderate_risk, high_risk, very_high_risk
- ✅ **PostgreSQL Logging** - Saves all red flags to `startup_critique` table
- ✅ **LLM-Powered Analysis** - Uses Gemini 1.5 Pro for critical VC analysis
- ✅ **Fallback Analysis** - Rule-based analysis if LLM unavailable
- ✅ **Comprehensive Tests** - Pytest suite for severity parsing and validation

## API Endpoint

**POST** `/critique`

### Request Body:
```json
{
  "score_report": {
    "overall_score": 6.5,
    "breakdown": {
      "qualitative_assessment": {
        "idea": {"score": 7, "concerns": []},
        "team": {"score": 5, "concerns": ["Lack of experience"]},
        "traction": {"score": 4, "concerns": ["Low growth"]},
        "market": {"score": 8, "concerns": []}
      }
    }
  },
  "pitchdeck_summary": {
    "missing_slides_report": "Missing: Financial Projections",
    "overall_summary": "..."
  },
  "startup_name": "TechVenture"  // Optional, for database logging
}
```

### Response:
```json
{
  "red_flags": [
    {
      "flag": "Low traction score",
      "severity": "high",
      "explanation": "Only 4/10 in traction indicates weak product-market fit",
      "category": "traction"
    },
    {
      "flag": "Missing financial projections",
      "severity": "medium",
      "explanation": "Pitch deck lacks financial projections",
      "category": "financial"
    }
  ],
  "overall_risk_label": "moderate_risk",
  "summary": "Several areas of concern identified",
  "analysis_timestamp": "2025-01-11T..."
}
```

## Severity Levels

- **low** - Minor concern, worth noting
- **medium** - Moderate concern, requires attention
- **high** - Significant concern, major red flag
- **critical** - Critical issue, deal-breaker

## Risk Labels

- **low_risk** - Generally positive assessment
- **moderate_risk** - Some concerns but manageable
- **high_risk** - Multiple significant concerns
- **very_high_risk** - Critical issues identified

## Database Schema

The agent creates and logs to the `startup_critique` table:

```sql
CREATE TABLE startup_critique (
    id SERIAL PRIMARY KEY,
    startup_name VARCHAR(255) NOT NULL,
    red_flag TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL,
    explanation TEXT,
    category VARCHAR(50),
    overall_risk_label VARCHAR(50) NOT NULL,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Configuration

### Required Environment Variables:

```env
# For LLM (same as other agents)
GEMINI_PROJECT_ID=your_project_id
GEMINI_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# OR
GEMINI_API_KEY=your_api_key

# Optional: PostgreSQL for logging
DATABASE_URL=postgresql://user:password@localhost:5432/venture_lens
# OR
POSTGRES_URL=postgresql://user:password@localhost:5432/venture_lens
```

## Installation

```bash
cd api
pip install -r requirements.txt
```

New dependencies:
- `asyncpg` - Async PostgreSQL driver
- `psycopg2-binary` - Sync PostgreSQL driver (fallback)

## Testing

```bash
# Run all critique agent tests
pytest agents/test_critique_agent.py -v

# Test specific functionality
pytest agents/test_critique_agent.py::test_normalize_critique_response_valid -v
pytest agents/test_critique_agent.py::test_normalize_critique_response_invalid_severity -v
```

## Usage Examples

### Python:
```python
from critique_agent import analyze_critique

result = await analyze_critique(
    score_report={...},
    pitchdeck_summary={...}
)

print(result["red_flags"])
print(result["overall_risk_label"])
```

### cURL:
```bash
curl -X POST "http://localhost:8000/critique" \
  -H "Content-Type: application/json" \
  -d '{
    "score_report": {...},
    "pitchdeck_summary": {...},
    "startup_name": "TechVenture"
  }'
```

### PowerShell:
```powershell
$body = @{
    score_report = @{...}
    pitchdeck_summary = @{...}
    startup_name = "TechVenture"
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:8000/critique" `
  -Method Post `
  -Body $body `
  -ContentType "application/json"
```

## Integration

The critique agent integrates with:
- **Scoring Service** (`/score`) - Uses score reports for analysis
- **Pitch Deck Analysis** (`/analyze-pitchdeck`) - Uses pitch deck summaries
- **Data Ingestion Agent** (`/ingest`) - Can critique ingested startup data

## Error Handling

- **LLM Failures**: Falls back to rule-based analysis
- **Database Failures**: Logs warning but doesn't fail request
- **Invalid Inputs**: Returns 400 with descriptive error
- **Missing Fields**: Uses sensible defaults

## Red Flag Categories

- **idea** - Product/concept concerns
- **team** - Team-related issues
- **traction** - Growth/metrics concerns
- **market** - Market size/timing issues
- **financial** - Financial red flags
- **technical** - Technical/product risks
- **other** - Other concerns

