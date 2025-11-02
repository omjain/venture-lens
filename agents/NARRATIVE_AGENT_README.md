# AI Narrative Agent

Venture Lens AI Narrative Agent generates compelling 3-part startup narratives (Vision, Differentiation, Timing) with Redis caching support.

## Features

- ✅ **POST /narrative endpoint** - FastAPI endpoint for narrative generation
- ✅ **3-Part Narrative** - Vision, Differentiation, Timing
- ✅ **LLM-Powered** - Uses Gemini 2.0 Flash with temperature=0.7 for creativity
- ✅ **Redis Caching** - Caches narratives with startup_id key (24-hour TTL)
- ✅ **Fallback Generation** - Rule-based narrative if LLM unavailable
- ✅ **Cache Management** - GET/DELETE endpoints for cache control
- ✅ **Comprehensive Tests** - Pytest suite for structure validation

## API Endpoints

### POST `/narrative`

Generate narrative for a startup.

**Request:**
```json
{
  "startup_data": {
    "name": "TechVenture",
    "description": "AI-powered data processing platform",
    "problem": "Current solutions are slow",
    "solution": "10x faster processing",
    "traction": "1,000 users, $100K MRR",
    "market": "Data processing market worth $50B",
    "sector": "SaaS"
  },
  "startup_id": "techventure_001",  // Optional, for caching
  "use_cache": true  // Optional, default: true
}
```

**Response:**
```json
{
  "vision": "TechVenture envisions transforming data processing...",
  "differentiation": "Unique AI-powered approach sets them apart...",
  "timing": "Market timing is perfect for AI solutions...",
  "generated_at": "2025-01-11T...",
  "model": "gemini-2.0-flash"
}
```

### GET `/narrative/cache/{startup_id}`

Retrieve cached narrative for a startup.

### DELETE `/narrative/cache/{startup_id}`

Clear cached narrative for a startup.

## Configuration

### Environment Variables

```env
# For LLM (same as other agents)
GEMINI_API_KEY=your_api_key
# OR
GEMINI_PROJECT_ID=your_project_id
GEMINI_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS_JSON={...}

# For Redis caching (optional)
REDIS_URL=redis://localhost:6379
# Default: redis://localhost:6379
```

## Installation

```bash
cd api
pip install -r requirements.txt
```

New dependency:
- `redis` - Redis client for caching

## Redis Setup (Optional)

Narrative agent works without Redis but caching is disabled.

**Local Redis:**
```bash
# Install Redis (varies by OS)
# Windows: Download from https://redis.io/download
# Mac: brew install redis
# Linux: sudo apt-get install redis-server

# Start Redis
redis-server
```

**Cloud Redis (e.g., Redis Cloud):**
```env
REDIS_URL=redis://username:password@host:port
```

## Usage Examples

### Python:
```python
from narrative_agent import generate_narrative

result = await generate_narrative(
    startup_data={
        "name": "TechVenture",
        "description": "AI platform",
        "solution": "Fast processing"
    },
    startup_id="techventure_001"
)

print(result["vision"])
print(result["differentiation"])
print(result["timing"])
```

### cURL:
```bash
curl -X POST "http://localhost:8000/narrative" \
  -H "Content-Type: application/json" \
  -d '{
    "startup_data": {
      "name": "TechVenture",
      "description": "AI platform"
    },
    "startup_id": "techventure_001"
  }'
```

### PowerShell:
```powershell
$body = @{
    startup_data = @{
        name = "TechVenture"
        description = "AI platform"
    }
    startup_id = "techventure_001"
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:8000/narrative" `
  -Method Post `
  -Body $body `
  -ContentType "application/json"
```

## Testing

```bash
# Run all narrative agent tests
pytest agents/test_narrative_agent.py -v

# Test specific functionality
pytest agents/test_narrative_agent.py::test_narrative_structure_comparison -v
pytest agents/test_narrative_agent.py::test_generate_narrative_cache_hit -v
```

## Narrative Structure

The agent generates three distinct parts:

1. **Vision** - Where the company is heading, future state (2-3 sentences)
2. **Differentiation** - What makes them unique, competitive advantage (2-3 sentences)
3. **Timing** - Why now is the right time, market timing (2-3 sentences)

Each part is concise, compelling, and investor-focused.

## Caching Behavior

- **Cache Key Format:** `narrative:{startup_id}`
- **TTL:** 24 hours (86400 seconds)
- **Cache Strategy:** 
  - Check cache first if `startup_id` provided
  - Generate if cache miss
  - Store result in cache after generation
  - Cache can be disabled with `use_cache=false`

## Error Handling

- **LLM Failures:** Falls back to rule-based narrative
- **Redis Failures:** Logs warning, continues without caching
- **Invalid Input:** Returns 400 with descriptive error
- **Missing Fields:** Uses fallback content for missing narrative parts

## Integration

The narrative agent integrates with:
- **Scoring Service** (`/score`) - Can generate narrative from scoring results
- **Data Ingestion Agent** (`/ingest`) - Can generate narrative from ingested data
- **Critique Agent** (`/critique`) - Can enhance critique with narrative

## Temperature Setting

Uses `temperature=0.7` for balanced creativity:
- Creative enough for compelling narratives
- Consistent enough for reliable structure
- Optimized for investor-focused content

