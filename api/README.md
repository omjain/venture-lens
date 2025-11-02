# Venture Lens Scoring API

FastAPI service providing `/score` endpoint for startup evaluation with weighted Venture Lens scoring.

## Features

- **Weighted Scoring**: Computes Venture Lens Score using weighted metrics (Idea 25%, Team 30%, Traction 25%, Market 20%)
- **LLM Assessment**: Uses Vertex AI/Gemini for qualitative analysis across all dimensions
- **Metric Normalization**: Normalizes input metrics for consistent processing
- **Detailed Breakdown**: Returns scores, assessments, strengths, and concerns for each category

## Setup

1. **Install Python dependencies:**
```bash
cd api
pip install -r requirements.txt
```

2. **Set environment variables** (or use `.env` file):
```bash
export GEMINI_PROJECT_ID="your-project-id"
export GEMINI_LOCATION="us-central1"
```

3. **Authenticate with Google Cloud:**
```bash
gcloud auth application-default login
```

## Running the Service

```bash
# Development mode
uvicorn main:app --reload --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Usage

### POST /score

Score a startup across four dimensions.

**Request:**
```json
{
  "idea": "AI-powered platform for healthcare data analysis...",
  "team": "Founding team includes 2 ex-Google engineers and 1 healthcare veteran...",
  "traction": "Currently have 50 paying customers, $50K MRR, growing 20% MoM...",
  "market": "Healthcare analytics market is $50B+ and growing at 15% CAGR...",
  "startup_name": "HealthTech AI"  // Optional
}
```

**Response:**
```json
{
  "overall_score": 7.5,
  "breakdown": {
    "idea_score": 7.5,
    "team_score": 8.0,
    "traction_score": 6.5,
    "market_score": 7.0,
    "qualitative_assessment": {
      "idea": {
        "score": 7.5,
        "assessment": "Strong innovation in healthcare AI...",
        "strengths": ["Unique approach", "Solves real problem"],
        "concerns": ["Market validation needed"]
      },
      "team": {
        "score": 8.0,
        "assessment": "Strong team with relevant experience...",
        "strengths": ["Technical expertise", "Domain knowledge"],
        "concerns": ["Limited sales experience"]
      },
      "traction": {
        "score": 6.5,
        "assessment": "Early traction is promising...",
        "strengths": ["Growing user base"],
        "concerns": ["Revenue still low"]
      },
      "market": {
        "score": 7.0,
        "assessment": "Large addressable market...",
        "strengths": ["Large TAM", "Growing market"],
        "concerns": ["Competitive landscape"]
      }
    }
  },
  "weights": {
    "idea": 0.25,
    "team": 0.30,
    "traction": 0.25,
    "market": 0.20
  },
  "recommendation": "Good Investment Opportunity - Worth exploring with additional research",
  "confidence": 0.85
}
```

## Scoring Weights

- **Idea**: 25% - Innovation, differentiation, problem-solving
- **Team**: 30% - Experience, skills, execution capability (highest weight)
- **Traction**: 25% - Metrics, growth, validation, milestones
- **Market**: 20% - Market size, opportunity, competition

## Recommendation Thresholds

- **≥ 8.0**: Strong Investment Opportunity
- **≥ 6.5**: Good Investment Opportunity
- **≥ 5.0**: Moderate Opportunity
- **≥ 3.5**: Weak Opportunity
- **< 3.5**: Not Recommended

## Health Check

```bash
GET /health
```

Returns service status and version.

