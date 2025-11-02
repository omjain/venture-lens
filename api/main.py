"""
FastAPI service for Venture Lens Scoring
Provides /score endpoint for startup evaluation with weighted scoring
Also provides /analyze-pitchdeck for PDF pitch deck analysis
And /ingest for data ingestion agent
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List, Any
import os
from dotenv import load_dotenv
import json
import asyncio
import tempfile
import shutil
from pathlib import Path
import sys

# Add agents directory to path for imports
agents_path = os.path.join(os.path.dirname(__file__), '..', 'agents')
if os.path.exists(agents_path):
    sys.path.insert(0, agents_path)

# Load environment variables (check both api/ and root directory)
load_dotenv()  # Try api/.env first
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))  # Then root/.env

app = FastAPI(
    title="Venture Lens Scoring API",
    description="AI-powered startup scoring with weighted Venture Lens metrics",
    version="1.0.0"
)

# CORS configuration - Allow all localhost ports for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:8081",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8081",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ============================================================================
# Request/Response Models
# ============================================================================

class StartupInput(BaseModel):
    """Input model for startup scoring"""
    idea: str = Field(..., description="Business idea, concept, or value proposition", min_length=10)
    team: str = Field(..., description="Team composition, experience, and capabilities", min_length=10)
    traction: str = Field(..., description="Current traction, metrics, users, revenue", min_length=10)
    market: str = Field(..., description="Market size, opportunity, competition analysis", min_length=10)
    startup_name: Optional[str] = Field(None, description="Optional startup name")

    @field_validator('idea', 'team', 'traction', 'market')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v or len(v.strip()) < 10:
            raise ValueError('Field must be at least 10 characters')
        return v.strip()


class ScoreBreakdown(BaseModel):
    """Individual category scores"""
    idea_score: float = Field(..., ge=0, le=10, description="Idea quality score (0-10)")
    team_score: float = Field(..., ge=0, le=10, description="Team strength score (0-10)")
    traction_score: float = Field(..., ge=0, le=10, description="Traction score (0-10)")
    market_score: float = Field(..., ge=0, le=10, description="Market opportunity score (0-10)")
    qualitative_assessment: Dict[str, Any] = Field(..., description="LLM qualitative analysis")


class ScoreResponse(BaseModel):
    """Response model with Venture Lens Score"""
    overall_score: float = Field(..., ge=0, le=10, description="Weighted Venture Lens Score (0-10)")
    breakdown: ScoreBreakdown
    weights: Dict[str, float] = Field(..., description="Weights used for each category")
    recommendation: str = Field(..., description="Investment recommendation based on score")
    confidence: float = Field(..., ge=0, le=1, description="Confidence level in the assessment")
    assessment_source: Optional[Dict[str, Any]] = Field(None, description="Metadata about the assessment source (API or mock)")


# ============================================================================
# Normalization & Scoring Functions
# ============================================================================

def normalize_text_length(text: str, max_length: int = 500) -> str:
    """Normalize text to reasonable length for LLM processing"""
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


def normalize_metrics(idea: str, team: str, traction: str, market: str) -> Dict[str, str]:
    """Normalize all input metrics for consistent processing"""
    return {
        "idea": normalize_text_length(idea, 1000),
        "team": normalize_text_length(team, 1000),
        "traction": normalize_text_length(traction, 1000),
        "market": normalize_text_length(market, 1000)
    }


def compute_weighted_score(
    idea_score: float,
    team_score: float,
    traction_score: float,
    market_score: float
) -> Dict[str, Any]:
    """
    Compute weighted Venture Lens Score
    Weights: Idea (25%), Team (30%), Traction (25%), Market (20%)
    """
    weights = {
        "idea": 0.25,
        "team": 0.30,  # Highest weight - team is critical
        "traction": 0.25,
        "market": 0.20
    }
    
    overall = (
        idea_score * weights["idea"] +
        team_score * weights["team"] +
        traction_score * weights["traction"] +
        market_score * weights["market"]
    )
    
    return {
        "overall_score": round(overall, 2),
        "weights": weights,
        "breakdown_scores": {
            "idea": round(idea_score, 2),
            "team": round(team_score, 2),
            "traction": round(traction_score, 2),
            "market": round(market_score, 2)
        }
    }


def get_recommendation(score: float) -> str:
    """Get investment recommendation based on score"""
    if score >= 8.0:
        return "Strong Investment Opportunity - Highly recommended for further due diligence"
    elif score >= 6.5:
        return "Good Investment Opportunity - Worth exploring with additional research"
    elif score >= 5.0:
        return "Moderate Opportunity - Requires careful evaluation and risk assessment"
    elif score >= 3.5:
        return "Weak Opportunity - High risk, consider alternatives or pass"
    else:
        return "Not Recommended - Significant concerns across multiple dimensions"


def calculate_confidence(
    idea_score: float,
    team_score: float,
    traction_score: float,
    market_score: float,
    llm_used: bool = True
) -> float:
    """
    Calculate confidence based on:
    - LLM usage (higher if real LLM vs mock)
    - Score consistency (more consistent = higher confidence)
    - Data completeness (all fields provided = higher confidence)
    """
    scores = [idea_score, team_score, traction_score, market_score]
    
    # Base confidence on LLM usage
    if llm_used:
        base_confidence = 0.85  # Real LLM assessment
    else:
        base_confidence = 0.65  # Mock assessment
    
    # Adjust based on score variance (consistency)
    # If scores are very different, we're less confident
    mean_score = sum(scores) / len(scores)
    variance = sum((s - mean_score)**2 for s in scores) / len(scores)
    
    # Lower variance = more consistent = slightly higher confidence
    # But variance shouldn't dominate - even consistent low scores can be confident
    variance_factor = max(0.9, 1.0 - (variance / 20.0))
    
    # Final confidence combines base and consistency
    confidence = base_confidence * variance_factor
    
    # Cap between 0.5 and 0.95 (never 100% confidence)
    return round(max(0.5, min(0.95, confidence)), 2)


# ============================================================================
# LLM Integration (Vertex AI / Gemini)
# ============================================================================

async def call_llm_for_assessment(
    idea: str,
    team: str,
    traction: str,
    market: str,
    startup_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Call LLM (Vertex AI/Gemini) for qualitative assessment and scoring
    Returns scores for each category and qualitative analysis
    """
    try:
        from google.auth import default
        from google.auth.transport.requests import Request
        import httpx
        
        # Get credentials
        print("[LLM] Attempting to authenticate with Google Cloud...")
        credentials, project = default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
        credentials.refresh(Request())
        
        project_id = os.getenv("GEMINI_PROJECT_ID", project)
        location = os.getenv("GEMINI_LOCATION", "us-central1")
        model_name = "gemini-2.0-flash-exp"
        
        if not project_id or project_id == "your_project_id_here":
            print("[LLM] WARNING: GEMINI_PROJECT_ID not set or using placeholder. Using default project.")
        
        print(f"[LLM] Using Vertex AI: project={project_id}, location={location}, model={model_name}")
        
        endpoint = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model_name}:generateContent"
        
        prompt = f"""You are a venture capital analyst evaluating a startup investment opportunity.

Startup Name: {startup_name or "Unnamed Startup"}

Idea/Concept:
{idea}

Team:
{team}

Traction:
{traction}

Market:
{market}

Evaluate this startup across four dimensions and provide:
1. Idea Quality Score (0-10): Innovation, differentiation, problem-solving ability
2. Team Score (0-10): Experience, skills, execution capability, complementary strengths
3. Traction Score (0-10): Current metrics, growth, validation, milestones achieved
4. Market Score (0-10): Market size, opportunity, competition, defensibility

For each category, provide:
- A numerical score (0-10)
- 2-3 sentence qualitative assessment
- Key strengths
- Key concerns/risks

Respond ONLY with valid JSON in this exact format:
{{
  "idea": {{
    "score": 7.5,
    "assessment": "The idea shows strong innovation...",
    "strengths": ["Unique approach", "Solves real problem"],
    "concerns": ["Market validation needed"]
  }},
  "team": {{
    "score": 8.0,
    "assessment": "Strong team with relevant experience...",
    "strengths": ["Technical expertise", "Domain knowledge"],
    "concerns": ["Limited sales experience"]
  }},
  "traction": {{
    "score": 6.5,
    "assessment": "Early traction is promising...",
    "strengths": ["Growing user base"],
    "concerns": ["Revenue still low"]
  }},
  "market": {{
    "score": 7.0,
    "assessment": "Large addressable market...",
    "strengths": ["Large TAM", "Growing market"],
    "concerns": ["Competitive landscape"]
  }}
}}"""

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048,
            }
        }
        
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"[LLM] Calling Vertex AI endpoint: {endpoint[:80]}...")
            response = await client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract text from response
            if "candidates" in result and len(result["candidates"]) > 0:
                text_content = ""
                for part in result["candidates"][0].get("content", {}).get("parts", []):
                    text_content += part.get("text", "")
                
                # Parse JSON from response
                # Try to extract JSON if wrapped in markdown
                if "```json" in text_content:
                    json_start = text_content.find("```json") + 7
                    json_end = text_content.find("```", json_start)
                    text_content = text_content[json_start:json_end].strip()
                elif "```" in text_content:
                    json_start = text_content.find("```") + 3
                    json_end = text_content.find("```", json_start)
                    text_content = text_content[json_start:json_end].strip()
                
                assessment = json.loads(text_content)
                # Add metadata to indicate this came from real API
                assessment["_metadata"] = {
                    "source": "vertex_ai_gemini",
                    "model": model_name,
                    "project_id": project_id
                }
                print("[LLM] SUCCESS: Received assessment from Vertex AI/Gemini API")
                return assessment
        
        raise Exception("Failed to parse LLM response")
        
    except ImportError as e:
        # Fallback to mock assessment if Google Cloud libraries not available
        print(f"[LLM] WARNING: Google Cloud libraries not available (ImportError: {e})")
        print("[LLM] Falling back to mock assessment")
        return get_mock_assessment(idea, team, traction, market)
    except Exception as e:
        print(f"[LLM] ERROR: LLM call failed: {e}")
        print(f"[LLM] Error type: {type(e).__name__}")
        print("[LLM] Falling back to mock assessment")
        # Fallback to intelligent mock assessment
        return get_mock_assessment(idea, team, traction, market)


def get_mock_assessment(idea: str, team: str, traction: str, market: str) -> Dict[str, Any]:
    """Intelligent mock assessment when LLM is not available"""
    print("[MOCK] Using mock assessment (LLM API not available or failed)")
    
    # This will be added to the assessment below
    # Simple scoring based on content length and keywords
    def score_category(text: str) -> float:
        text_lower = text.lower()
        score = 5.0  # Base score
        
        # Positive indicators
        if any(word in text_lower for word in ["experienced", "proven", "strong", "excellent", "track record"]):
            score += 1.5
        if any(word in text_lower for word in ["revenue", "customers", "growth", "traction", "users"]):
            score += 1.0
        if any(word in text_lower for word in ["market", "opportunity", "large", "growing", "billion"]):
            score += 0.5
        
        # Negative indicators
        if any(word in text_lower for word in ["early", "limited", "small", "unproven", "risky"]):
            score -= 0.5
        
        return max(0.0, min(10.0, round(score, 1)))
    
    return {
        "idea": {
            "score": score_category(idea),
            "assessment": f"Idea evaluation: {idea[:100]}... shows potential.",
            "strengths": ["Innovative concept"] if len(idea) > 100 else ["Early stage idea"],
            "concerns": ["Needs validation"] if len(idea) < 200 else []
        },
        "team": {
            "score": score_category(team),
            "assessment": f"Team assessment: {team[:100]}... demonstrates capability.",
            "strengths": ["Relevant experience"] if "experienced" in team.lower() else ["Building team"],
            "concerns": ["Team expansion needed"] if len(team) < 150 else []
        },
        "traction": {
            "score": score_category(traction),
            "assessment": f"Traction analysis: {traction[:100]}... shows progress.",
            "strengths": ["Early metrics"] if "revenue" in traction.lower() or "users" in traction.lower() else ["In development"],
            "concerns": ["Limited traction"] if len(traction) < 150 else []
        },
        "market": {
            "score": score_category(market),
            "assessment": f"Market analysis: {market[:100]}... presents opportunity.",
            "strengths": ["Addressable market"] if "market" in market.lower() else ["Market research ongoing"],
            "concerns": ["Market validation needed"] if len(market) < 150 else []
        },
        "_metadata": {
            "source": "mock_fallback",
            "reason": "LLM API not available or failed"
        }
    }


# ============================================================================
# Main Scoring Endpoint
# ============================================================================

@app.post("/score", response_model=ScoreResponse)
async def score_startup(startup: StartupInput):
    """
    Score a startup across four dimensions (Idea, Team, Traction, Market)
    Uses LLM for qualitative assessment and computes weighted Venture Lens Score
    """
    try:
        # Step 1: Normalize metrics
        normalized = normalize_metrics(
            startup.idea,
            startup.team,
            startup.traction,
            startup.market
        )
        
        # Step 2: Call LLM for qualitative assessment and scoring
        llm_assessment = await call_llm_for_assessment(
            normalized["idea"],
            normalized["team"],
            normalized["traction"],
            normalized["market"],
            startup.startup_name
        )
        
        # Check if we used real LLM or mock
        assessment_metadata = llm_assessment.get("_metadata", {})
        llm_used = assessment_metadata.get("source") != "mock"
        
        if llm_used:
            print("✅ Using real LLM assessment from Vertex AI/Gemini")
        else:
            print(f"ℹ️  Using mock assessment: {assessment_metadata.get('reason', 'unknown')}")
        
        # Extract scores from LLM assessment
        idea_score = float(llm_assessment["idea"]["score"])
        team_score = float(llm_assessment["team"]["score"])
        traction_score = float(llm_assessment["traction"]["score"])
        market_score = float(llm_assessment["market"]["score"])
        
        # Step 3: Compute weighted Venture Lens Score
        scoring_result = compute_weighted_score(
            idea_score,
            team_score,
            traction_score,
            market_score
        )
        
        # Step 4: Calculate confidence (pass whether LLM was used)
        confidence = calculate_confidence(
            idea_score,
            team_score,
            traction_score,
            market_score,
            llm_used=llm_used
        )
        
        # Step 5: Get recommendation
        recommendation = get_recommendation(scoring_result["overall_score"])
        
        # Extract metadata from LLM assessment (if available)
        assessment_metadata = llm_assessment.get("_metadata", {})
        
        # Remove metadata from qualitative assessment before including in breakdown
        qualitative_assessment = {
            "idea": {k: v for k, v in llm_assessment["idea"].items() if k != "_metadata"},
            "team": {k: v for k, v in llm_assessment["team"].items() if k != "_metadata"},
            "traction": {k: v for k, v in llm_assessment["traction"].items() if k != "_metadata"},
            "market": {k: v for k, v in llm_assessment["market"].items() if k != "_metadata"}
        }
        
        # Log what we're using
        source_type = "Real LLM (Vertex AI)" if llm_used else "Mock Assessment"
        print(f"📊 Scoring complete: Overall={scoring_result['overall_score']}/10, Confidence={confidence*100:.0f}%, Source={source_type}")
        if not llm_used:
            print(f"   Reason: {assessment_metadata.get('reason', 'unknown')}")
        
        # Build response
        return ScoreResponse(
            overall_score=scoring_result["overall_score"],
            breakdown=ScoreBreakdown(
                idea_score=scoring_result["breakdown_scores"]["idea"],
                team_score=scoring_result["breakdown_scores"]["team"],
                traction_score=scoring_result["breakdown_scores"]["traction"],
                market_score=scoring_result["breakdown_scores"]["market"],
                qualitative_assessment=qualitative_assessment
            ),
            weights=scoring_result["weights"],
            recommendation=recommendation,
            confidence=confidence
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scoring failed: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "OK",
        "service": "Venture Lens Scoring API",
        "version": "1.0.0"
    }


# ============================================================================
# Pitch Deck Analysis
# ============================================================================

from pitchdeck_analysis import analyze_pitchdeck


@app.post("/analyze-pitchdeck")
async def analyze_pitchdeck_endpoint(file: UploadFile = File(...)):
    """
    Analyze a pitch deck PDF file
    Upload a PDF file and get slide-by-slide analysis with missing slide report
    """
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Save uploaded file to temporary location
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, file.filename or "uploaded.pdf")
    
    try:
        # Save uploaded file
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Analyze the PDF
        result = await analyze_pitchdeck(temp_file_path)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pitch deck analysis failed: {str(e)}"
        )
    finally:
        # Clean up temporary file
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except:
            pass  # Ignore cleanup errors


class PitchDeckPathRequest(BaseModel):
    """Request model for path-based pitch deck analysis"""
    pdf_path: str = Field(..., description="Path to PDF file")


@app.post("/analyze-pitchdeck-path")
async def analyze_pitchdeck_path_endpoint(request: PitchDeckPathRequest):
    """
    Analyze a pitch deck PDF from file path
    Useful for testing with local files
    
    Example: POST {"pdf_path": "/path/to/pitchdeck.pdf"}
    """
    pdf_path = request.pdf_path
    
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    if not pdf_path.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        result = await analyze_pitchdeck(pdf_path)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pitch deck analysis failed: {str(e)}"
        )


# ============================================================================
# Data Ingestion Agent
# ============================================================================

try:
    from ingestion_agent import ingest_data
    INGESTION_AGENT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Ingestion agent not available: {e}")
    INGESTION_AGENT_AVAILABLE = False

try:
    from critique_agent import analyze_critique, save_critique_to_db, normalize_critique_response
    CRITIQUE_AGENT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Critique agent not available: {e}")
    CRITIQUE_AGENT_AVAILABLE = False

try:
    from narrative_agent import generate_narrative, get_cached_narrative, clear_narrative_cache
    NARRATIVE_AGENT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Narrative agent not available: {e}")
    NARRATIVE_AGENT_AVAILABLE = False


class IngestionURLRequest(BaseModel):
    """Request model for URL ingestion"""
    url: str = Field(..., description="URL to scrape and ingest")


@app.post("/ingest")
async def ingest_endpoint(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None)
):
    """
    Data Ingestion Agent endpoint
    Accepts either PDF file upload or URL for scraping
    
    Usage:
    - PDF upload: POST with multipart/form-data, include 'file' field
    - URL scraping: POST with form-data, include 'url' field
    """
    if not INGESTION_AGENT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Ingestion agent not available. Make sure agents/ingestion_agent.py exists."
        )
    
    try:
        # Validate input
        if not file and not url:
            raise HTTPException(
                status_code=400,
                detail="Either 'file' (PDF) or 'url' must be provided"
            )
        
        if file and url:
            raise HTTPException(
                status_code=400,
                detail="Provide either 'file' OR 'url', not both"
            )
        
        # Process PDF
        if file:
            if not file.filename or not file.filename.lower().endswith('.pdf'):
                raise HTTPException(status_code=400, detail="File must be a PDF")
            
            file_bytes = await file.read()
            result = await ingest_data(
                pdf_file=file_bytes,
                pdf_filename=file.filename
            )
            return result
        
        # Process URL
        if url:
            if not url.startswith(('http://', 'https://')):
                raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
            
            result = await ingest_data(url=url)
            return result
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}"
        )


# ============================================================================
# AI Critique Agent
# ============================================================================

class CritiqueRequest(BaseModel):
    """Request model for critique analysis"""
    score_report: Dict[str, Any] = Field(..., description="Startup scoring report")
    pitchdeck_summary: Dict[str, Any] = Field(..., description="Pitch deck analysis summary")
    startup_name: Optional[str] = Field(None, description="Startup name for database logging")


@app.post("/critique")
async def critique_endpoint(request: CritiqueRequest):
    """
    AI Critique Agent endpoint
    Analyzes startup critically as a VC, identifies red flags with severity levels
    
    Input: Combined JSON with score_report and pitchdeck_summary
    Output: Structured JSON with red flags, severity levels, and overall risk label
    """
    if not CRITIQUE_AGENT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Critique agent not available. Make sure agents/critique_agent.py exists."
        )
    
    try:
        # Validate input
        if not request.score_report:
            raise HTTPException(status_code=400, detail="score_report is required")
        
        if not request.pitchdeck_summary:
            raise HTTPException(status_code=400, detail="pitchdeck_summary is required")
        
        # Perform critique analysis
        critique_result = await analyze_critique(
            score_report=request.score_report,
            pitchdeck_summary=request.pitchdeck_summary
        )
        
        # Save to database if PostgreSQL is configured (optional)
        startup_name = request.startup_name or "unknown"
        if has_db_config():
            try:
                db_connection = await get_db_connection()
                if db_connection:
                    await save_critique_to_db(startup_name, critique_result, db_connection)
            except Exception as db_error:
                # Log but don't fail the request if DB save fails
                print(f"⚠️ Database save failed: {db_error}")
        
        return critique_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Critique analysis failed: {str(e)}"
        )


# Database connection helpers (optional - only if PostgreSQL configured)
def has_db_config() -> bool:
    """Check if PostgreSQL is configured"""
    return bool(os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL"))


async def get_db_connection():
    """
    Get database connection (if configured)
    Returns asyncpg connection for async operations
    """
    if not has_db_config():
        return None
    
    try:
        import asyncpg
        database_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
        if database_url:
            try:
                connection = await asyncpg.connect(database_url)
                return connection
            except Exception as e:
                print(f"⚠️ Failed to connect to database: {e}")
                return None
        return None
    except ImportError:
        # asyncpg not installed, database logging disabled
        print("⚠️ asyncpg not installed. Database logging disabled.")
        return None


# ============================================================================
# AI Narrative Agent
# ============================================================================

class NarrativeRequest(BaseModel):
    """Request model for narrative generation"""
    startup_data: Dict[str, Any] = Field(..., description="Startup information as JSON")
    startup_id: Optional[str] = Field(None, description="Unique startup identifier for caching")
    use_cache: Optional[bool] = Field(True, description="Whether to use Redis cache")


@app.post("/narrative")
async def narrative_endpoint(request: NarrativeRequest):
    """
    AI Narrative Agent endpoint
    Generates a crisp 3-part narrative: Vision, Differentiation, Timing
    
    Input: Startup JSON data
    Output: Structured JSON with vision, differentiation, and timing narratives
    Uses Redis caching (optional) with startup_id as key
    """
    if not NARRATIVE_AGENT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Narrative agent not available. Make sure agents/narrative_agent.py exists."
        )
    
    try:
        # Validate input
        if not request.startup_data:
            raise HTTPException(status_code=400, detail="startup_data is required")
        
        # Generate narrative
        narrative_result = await generate_narrative(
            startup_data=request.startup_data,
            startup_id=request.startup_id,
            use_cache=request.use_cache
        )
        
        return narrative_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Narrative generation failed: {str(e)}"
        )


@app.get("/narrative/cache/{startup_id}")
async def get_cached_narrative_endpoint(startup_id: str):
    """
    Get cached narrative for a startup
    
    Returns cached narrative if available, 404 if not found
    """
    if not NARRATIVE_AGENT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Narrative agent not available"
        )
    
    try:
        cached = await get_cached_narrative(startup_id)
        if cached:
            return cached
        else:
            raise HTTPException(
                status_code=404,
                detail=f"No cached narrative found for startup_id: {startup_id}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve cached narrative: {str(e)}"
        )


@app.delete("/narrative/cache/{startup_id}")
async def clear_narrative_cache_endpoint(startup_id: str):
    """
    Clear cached narrative for a startup
    """
    if not NARRATIVE_AGENT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Narrative agent not available"
        )
    
    try:
        success = await clear_narrative_cache(startup_id)
        if success:
            return {"status": "success", "message": f"Cache cleared for startup_id: {startup_id}"}
        else:
            return {"status": "failed", "message": "Redis not available or cache clear failed"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

