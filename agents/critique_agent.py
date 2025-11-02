"""
AI Critique Agent for Venture Lens
Analyzes startups critically as a VC, identifies red flags with severity levels
"""
import os
import json
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime

from rich.console import Console
from rich.logging import RichHandler
import logging

# Import LLM service
try:
    from llm_service import llm_service
except ImportError:
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

logger = logging.getLogger("critique_agent")
console = Console()


class SeverityLevel(str, Enum):
    """Red flag severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLabel(str, Enum):
    """Overall risk assessment labels"""
    LOW_RISK = "low_risk"
    MODERATE_RISK = "moderate_risk"
    HIGH_RISK = "high_risk"
    VERY_HIGH_RISK = "very_high_risk"


async def analyze_critique(
    score_report: Dict[str, Any],
    pitchdeck_summary: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze startup critically as a VC, identify red flags
    
    Args:
        score_report: Startup scoring report with breakdown
        pitchdeck_summary: Pitch deck analysis summary
        
    Returns:
        Structured critique with red flags and overall risk label
    """
    logger.info("🔍 Starting critical VC analysis")
    
    # Prepare combined context for LLM
    combined_context = {
        "score_report": score_report,
        "pitchdeck_summary": pitchdeck_summary
    }
    
    # Format context for LLM prompt
    context_text = format_context_for_prompt(score_report, pitchdeck_summary)
    
    # Generate critique prompt
    critique_prompt = f"""You are an experienced venture capitalist performing due diligence on a startup.

Analyze this startup critically and identify up to 5 red flags that would concern an investor.

SCORING REPORT:
{json.dumps(score_report, indent=2)}

PITCH DECK SUMMARY:
{json.dumps(pitchdeck_summary, indent=2)}

Your task:
1. Identify up to 5 red flags from the scoring report and pitch deck summary
2. For each red flag, assign a severity level: "low", "medium", "high", or "critical"
3. Provide a brief explanation for each red flag
4. Determine an overall risk label: "low_risk", "moderate_risk", "high_risk", or "very_high_risk"

Red flags can include but are not limited to:
- Low scores in key areas (idea, team, traction, market)
- Missing or vague information
- Unrealistic projections
- Weak competitive positioning
- Team concerns
- Market size or timing issues
- Business model concerns
- Financial red flags
- Technical or product risks

Respond ONLY with valid JSON in this exact format:
{{
    "red_flags": [
        {{
            "flag": "Brief description of the red flag",
            "severity": "low|medium|high|critical",
            "explanation": "Detailed explanation of why this is a concern",
            "category": "idea|team|traction|market|financial|technical|other"
        }}
    ],
    "overall_risk_label": "low_risk|moderate_risk|high_risk|very_high_risk",
    "summary": "Brief overall assessment (2-3 sentences)"
}}

Be critical but fair. Only flag genuine concerns, not minor issues."""

    try:
        logger.info("🤖 Calling LLM for critical analysis")
        
        response = await llm_service.invoke(
            prompt=critique_prompt,
            model="gemini-2.0-flash",
            temperature=0.5,  # Balanced for critical but fair analysis
            max_tokens=2048,
            system_prompt="You are an experienced venture capitalist with 15+ years of investment experience. You are thorough, critical, and detail-oriented."
        )
        
        # Parse JSON response
        json_text = response.strip()
        
        # Extract JSON if wrapped in markdown
        if "```json" in json_text:
            json_start = json_text.find("```json") + 7
            json_end = json_text.find("```", json_start)
            json_text = json_text[json_start:json_end].strip()
        elif "```" in json_text:
            json_start = json_text.find("```") + 3
            json_end = json_text.find("```", json_start)
            json_text = json_text[json_start:json_end].strip()
        
        # Parse JSON
        critique_data = json.loads(json_text)
        
        # Validate and normalize structure
        critique_result = normalize_critique_response(critique_data)
        
        logger.info(f"✅ Identified {len(critique_result['red_flags'])} red flags")
        logger.info(f"   Overall Risk: {critique_result['overall_risk_label']}")
        
        return critique_result
        
    except json.JSONDecodeError as e:
        logger.error(f"✗ Failed to parse LLM JSON response: {e}")
        logger.info("   Using fallback critique")
        return generate_fallback_critique(score_report, pitchdeck_summary)
    except Exception as e:
        logger.error(f"✗ LLM critique failed: {e}")
        return generate_fallback_critique(score_report, pitchdeck_summary)


def format_context_for_prompt(score_report: Dict[str, Any], pitchdeck_summary: Dict[str, Any]) -> str:
    """Format scoring report and pitch deck summary for LLM prompt"""
    context_parts = []
    
    # Extract key info from score report
    if isinstance(score_report, dict):
        overall_score = score_report.get("overall_score", "N/A")
        breakdown = score_report.get("breakdown", {})
        
        context_parts.append(f"Overall Score: {overall_score}/10")
        
        if isinstance(breakdown, dict):
            qualitative = breakdown.get("qualitative_assessment", {})
            if isinstance(qualitative, dict):
                for category, assessment in qualitative.items():
                    if isinstance(assessment, dict):
                        score = assessment.get("score", "N/A")
                        concerns = assessment.get("concerns", [])
                        if concerns:
                            context_parts.append(f"{category.title()}: {score}/10 - Concerns: {', '.join(concerns[:3])}")
    
    # Extract key info from pitch deck summary
    if isinstance(pitchdeck_summary, dict):
        missing_slides = pitchdeck_summary.get("missing_slides_report", "")
        if missing_slides and "missing" in missing_slides.lower():
            context_parts.append(f"Pitch Deck: {missing_slides}")
    
    return "\n".join(context_parts)


def normalize_critique_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize and validate critique response from LLM
    
    Args:
        data: Raw LLM response
        
    Returns:
        Normalized critique structure
    """
    red_flags = []
    
    # Extract red flags
    if "red_flags" in data and isinstance(data["red_flags"], list):
        for flag in data["red_flags"]:
            if isinstance(flag, dict):
                # Normalize severity
                severity = flag.get("severity", "medium").lower()
                if severity not in ["low", "medium", "high", "critical"]:
                    severity = "medium"
                
                # Normalize category
                category = flag.get("category", "other").lower()
                valid_categories = ["idea", "team", "traction", "market", "financial", "technical", "other"]
                if category not in valid_categories:
                    category = "other"
                
                red_flags.append({
                    "flag": flag.get("flag", "Unspecified concern"),
                    "severity": severity,
                    "explanation": flag.get("explanation", ""),
                    "category": category
                })
    
    # Limit to 5 red flags
    if len(red_flags) > 5:
        # Sort by severity (critical > high > medium > low) and take top 5
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        red_flags.sort(key=lambda x: severity_order.get(x["severity"], 0), reverse=True)
        red_flags = red_flags[:5]
    
    # Normalize overall risk label
    risk_label = data.get("overall_risk_label", "moderate_risk").lower()
    valid_labels = ["low_risk", "moderate_risk", "high_risk", "very_high_risk"]
    if risk_label not in valid_labels:
        # Infer from red flags
        if any(f["severity"] == "critical" for f in red_flags):
            risk_label = "very_high_risk"
        elif any(f["severity"] == "high" for f in red_flags):
            risk_label = "high_risk"
        elif any(f["severity"] == "medium" for f in red_flags):
            risk_label = "moderate_risk"
        else:
            risk_label = "low_risk"
    
    return {
        "red_flags": red_flags,
        "overall_risk_label": risk_label,
        "summary": data.get("summary", "No summary provided"),
        "analysis_timestamp": datetime.utcnow().isoformat()
    }


def generate_fallback_critique(score_report: Dict[str, Any], pitchdeck_summary: Dict[str, Any]) -> Dict[str, Any]:
    """Generate fallback critique using rule-based analysis"""
    logger.info("   Using rule-based fallback critique")
    
    red_flags = []
    
    # Analyze score report
    if isinstance(score_report, dict):
        overall_score = score_report.get("overall_score", 5)
        breakdown = score_report.get("breakdown", {})
        
        if overall_score < 4:
            red_flags.append({
                "flag": "Very low overall score",
                "severity": "high",
                "explanation": f"Overall score of {overall_score}/10 indicates significant concerns across multiple areas",
                "category": "other"
            })
        
        # Check category scores
        if isinstance(breakdown, dict):
            qualitative = breakdown.get("qualitative_assessment", {})
            if isinstance(qualitative, dict):
                for category, assessment in qualitative.items():
                    if isinstance(assessment, dict):
                        score = assessment.get("score", 5)
                        if score < 3:
                            red_flags.append({
                                "flag": f"Very low {category} score",
                                "severity": "high",
                                "explanation": f"{category.title()} scored only {score}/10, indicating significant weaknesses",
                                "category": category
                            })
    
    # Analyze pitch deck summary
    if isinstance(pitchdeck_summary, dict):
        missing_slides = pitchdeck_summary.get("missing_slides_report", "")
        if missing_slides and "missing" in missing_slides.lower():
            red_flags.append({
                "flag": "Incomplete pitch deck",
                "severity": "medium",
                "explanation": "Pitch deck appears to be missing key slides or sections",
                "category": "other"
            })
    
    # Determine overall risk
    if any(f["severity"] == "high" for f in red_flags):
        risk_label = "high_risk"
    elif any(f["severity"] == "medium" for f in red_flags):
        risk_label = "moderate_risk"
    else:
        risk_label = "low_risk"
    
    return {
        "red_flags": red_flags[:5],  # Limit to 5
        "overall_risk_label": risk_label,
        "summary": f"Identified {len(red_flags)} areas of concern requiring further investigation",
        "analysis_timestamp": datetime.utcnow().isoformat()
    }


async def save_critique_to_db(
    startup_name: str,
    critique_result: Dict[str, Any],
    db_connection
) -> bool:
    """
    Save critique results to PostgreSQL database
    
    Args:
        startup_name: Name of the startup
        critique_result: Critique analysis result
        db_connection: Database connection (asyncpg connection or psycopg2)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"💾 Saving critique to database for: {startup_name}")
        
        # Extract data
        red_flags = critique_result.get("red_flags", [])
        overall_risk = critique_result.get("overall_risk_label", "unknown")
        summary = critique_result.get("summary", "")
        
        # If using asyncpg (async)
        if hasattr(db_connection, 'execute'):
            try:
                # Check if table exists, create if not
                await db_connection.execute("""
                    CREATE TABLE IF NOT EXISTS startup_critique (
                        id SERIAL PRIMARY KEY,
                        startup_name VARCHAR(255) NOT NULL,
                        red_flag TEXT NOT NULL,
                        severity VARCHAR(20) NOT NULL,
                        explanation TEXT,
                        category VARCHAR(50),
                        overall_risk_label VARCHAR(50) NOT NULL,
                        summary TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert each red flag
                for flag in red_flags:
                    await db_connection.execute("""
                        INSERT INTO startup_critique 
                        (startup_name, red_flag, severity, explanation, category, overall_risk_label, summary)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """, startup_name, flag["flag"], flag["severity"], flag.get("explanation", ""),
                         flag.get("category", "other"), overall_risk, summary)
                
                logger.info(f"   ✓ Saved {len(red_flags)} red flags to database")
                return True
                
            except Exception as e:
                logger.warning(f"   ⚠️ Database save failed (async): {e}")
                return False
        
        # If using psycopg2 (sync)
        elif hasattr(db_connection, 'cursor'):
            try:
                cursor = db_connection.cursor()
                
                # Check if table exists, create if not
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS startup_critique (
                        id SERIAL PRIMARY KEY,
                        startup_name VARCHAR(255) NOT NULL,
                        red_flag TEXT NOT NULL,
                        severity VARCHAR(20) NOT NULL,
                        explanation TEXT,
                        category VARCHAR(50),
                        overall_risk_label VARCHAR(50) NOT NULL,
                        summary TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert each red flag
                for flag in red_flags:
                    cursor.execute("""
                        INSERT INTO startup_critique 
                        (startup_name, red_flag, severity, explanation, category, overall_risk_label, summary)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (startup_name, flag["flag"], flag["severity"], flag.get("explanation", ""),
                          flag.get("category", "other"), overall_risk, summary))
                
                db_connection.commit()
                cursor.close()
                
                logger.info(f"   ✓ Saved {len(red_flags)} red flags to database")
                return True
                
            except Exception as e:
                logger.warning(f"   ⚠️ Database save failed (sync): {e}")
                db_connection.rollback()
                return False
        
        return False
        
    except Exception as e:
        logger.error(f"   ✗ Database operation failed: {e}")
        return False

