"""
Gemini-native Critique Agent for Venture Lens
Analyzes startups critically, identifies red flags, and logs to database
"""
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum
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
logger = logging.getLogger("critique_agent")


class Severity(str, Enum):
    """Severity levels for red flags"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class RiskLevel(str, Enum):
    """Overall risk levels"""
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"


class RedFlag(BaseModel):
    """Pydantic model for red flag"""
    issue: str = Field(..., description="Short description of the red flag")
    severity: Severity = Field(..., description="Severity level")
    reason: str = Field(..., description="Why this is a risk")


class CritiqueResponse(BaseModel):
    """Pydantic model for critique response"""
    red_flags: List[RedFlag] = Field(..., min_length=1, max_length=5, description="List of red flags (3-5)")
    overall_risk_level: RiskLevel = Field(..., description="Overall risk assessment")
    summary: str = Field(..., description="One-paragraph overall assessment")
    
    @field_validator('red_flags')
    @classmethod
    def validate_red_flags_count(cls, v):
        if not (3 <= len(v) <= 5):
            raise ValueError("Must have 3-5 red flags")
        return v


async def analyze_critique(
    score_report: Dict[str, Any],
    pitchdeck_summary: str
) -> Dict[str, Any]:
    """
    Analyze startup critically and identify red flags
    
    Args:
        score_report: Structured JSON from scoring_agent (includes market, product, team, traction, risk)
        pitchdeck_summary: Pitch deck summary text
        
    Returns:
        Structured critique with red flags and overall risk level
    """
    logger.info("🔍 Starting critical VC analysis")
    
    if not CORE_LLM_AVAILABLE:
        raise ImportError(
            "Core LLM service not available. "
            "Please ensure core/llm_service.py exists and google-generativeai is installed."
        )
    
    # Prepare JSON content from score_report
    json_content = json.dumps(score_report, indent=2)
    
    # Compose prompt for Gemini
    prompt = f"""You are a venture capital analyst reviewing a startup.
Based on the following details, identify up to 5 key red flags or weaknesses.

Return ONLY valid JSON in this format:
{{
  "red_flags": [
    {{"issue": "<short description>", "severity": "<Low|Medium|High>", "reason": "<why this is a risk>"}}
  ],
  "overall_risk_level": "<Low|Moderate|High>",
  "summary": "<one-paragraph overall assessment>"
}}

Startup Details:
{json_content}

Pitch Deck Summary:
{pitchdeck_summary}

Analyze the scoring breakdown (market, product, team, traction, risk scores) and pitch deck summary.
Identify 3-5 key red flags or weaknesses that would concern an investor.
Be critical but fair. Only flag genuine concerns."""
    
    try:
        logger.info("🤖 Calling Gemini 1.5 Pro for critique analysis")
        
        llm_service = get_service()
        
        # Call Gemini with text-only
        response_text = llm_service.invoke(
            model="gemini-1.5-pro",
            prompt=prompt,
            pdf_bytes=None
        )
        
        logger.info("✅ Gemini API call successful")
        
    except Exception as e:
        logger.error(f"❌ Gemini API call failed: {e}")
        raise Exception(f"Failed to call Gemini API: {str(e)}")
    
    # Parse and validate JSON response
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
        raw_response = json.loads(json_text)
        
        logger.info("✅ Successfully parsed JSON response")
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Failed to parse JSON response: {e}")
        logger.error(f"   Response text: {response_text[:500]}...")
        raise Exception(f"Failed to parse JSON response: {str(e)}")
    
    # Validate with Pydantic
    try:
        validated_response = CritiqueResponse(**raw_response)
        
        logger.info(f"✅ Validated response: {len(validated_response.red_flags)} red flags, risk level: {validated_response.overall_risk_level}")
        
    except Exception as e:
        logger.error(f"❌ Pydantic validation failed: {e}")
        logger.error(f"   Raw response: {json.dumps(raw_response, indent=2)}")
        raise Exception(f"Response validation failed: {str(e)}")
    
    # Convert Pydantic model to dict
    result = validated_response.model_dump()
    
    # Add metadata
    result["analysis_timestamp"] = datetime.utcnow().isoformat()
    
    logger.info(f"✅ Critique analysis complete: {len(result['red_flags'])} red flags, risk: {result['overall_risk_level']}")
    
    return result


async def log_to_database(
    startup_id: str,
    risk_level: str,
    issues: List[str]
) -> bool:
    """
    Log severity counts to startup_risks table
    
    Args:
        startup_id: Unique identifier for the startup
        risk_level: Overall risk level (Low, Moderate, High)
        issues: List of issue descriptions
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"💾 Logging to startup_risks table for startup_id: {startup_id}")
    
    # Check if database is configured
    database_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if not database_url:
        logger.warning("⚠️ Database not configured (DATABASE_URL/POSTGRES_URL not set), skipping database log")
        return False
    
    try:
        # Try asyncpg first (async)
        try:
            import asyncpg
            
            conn = await asyncpg.connect(database_url)
            try:
                # Create table if not exists
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS startup_risks (
                        id SERIAL PRIMARY KEY,
                        startup_id VARCHAR(255) NOT NULL,
                        risk_level VARCHAR(50) NOT NULL,
                        issues TEXT[] NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert record
                await conn.execute("""
                    INSERT INTO startup_risks (startup_id, risk_level, issues)
                    VALUES ($1, $2, $3)
                """, startup_id, risk_level, issues)
                
                logger.info(f"   ✓ Logged to startup_risks table (asyncpg)")
                return True
            finally:
                await conn.close()
                
        except ImportError:
            # Fallback to psycopg2 (sync)
            try:
                import psycopg2
                from psycopg2.extras import execute_values
                
                conn = psycopg2.connect(database_url)
                cursor = conn.cursor()
                
                # Create table if not exists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS startup_risks (
                        id SERIAL PRIMARY KEY,
                        startup_id VARCHAR(255) NOT NULL,
                        risk_level VARCHAR(50) NOT NULL,
                        issues TEXT[] NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert record
                cursor.execute("""
                    INSERT INTO startup_risks (startup_id, risk_level, issues)
                    VALUES (%s, %s, %s)
                """, (startup_id, risk_level, issues))
                
                conn.commit()
                cursor.close()
                conn.close()
                
                logger.info(f"   ✓ Logged to startup_risks table (psycopg2)")
                return True
                
            except ImportError:
                logger.warning("⚠️ Neither asyncpg nor psycopg2 available, skipping database log")
                return False
            except Exception as e:
                logger.warning(f"   ⚠️ Database log failed (psycopg2): {e}")
                return False
                
    except Exception as e:
        logger.warning(f"   ⚠️ Database log failed (asyncpg): {e}")
        return False


async def critique_with_logging(
    score_report: Dict[str, Any],
    pitchdeck_summary: str,
    startup_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze critique and log to database
    
    Args:
        score_report: Structured JSON from scoring_agent
        pitchdeck_summary: Pitch deck summary text
        startup_id: Optional startup identifier for database logging
        
    Returns:
        Critique result with red flags and risk assessment
    """
    # Perform critique analysis
    result = await analyze_critique(score_report, pitchdeck_summary)
    
    # Log to database if startup_id provided
    if startup_id:
        # Extract issues from red flags
        issues = [flag["issue"] for flag in result["red_flags"]]
        risk_level = result["overall_risk_level"]
        
        await log_to_database(startup_id, risk_level, issues)
    
    return result
