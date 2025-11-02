"""
Gemini-native Scoring Agent for Venture Lens
Scores startups on Market, Product, Team, Traction, and Risk (0-20 each)
"""
import os
import json
from typing import Dict, Any, Optional
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
logger = logging.getLogger("scoring_agent")


def compute_weighted_venture_lens_score(
    market_score: float,
    product_score: float,
    team_score: float,
    traction_score: float,
    risk_score: float
) -> Dict[str, Any]:
    """
    Compute weighted Venture Lens Score
    
    Weights: Market (20%), Product (25%), Team (30%), Traction (15%), Risk (10%)
    Risk: Higher risk_score = Lower risk = Better (score used directly)
    """
    # Normalize scores from 0-20 to 0-10 for calculation
    market_norm = market_score / 2.0
    product_norm = product_score / 2.0
    team_norm = team_score / 2.0
    traction_norm = traction_score / 2.0
    risk_norm = risk_score / 2.0  # Higher risk_score = lower risk = better
    
    weights = {
        "market": 0.20,
        "product": 0.25,
        "team": 0.30,  # Highest weight - team is critical
        "traction": 0.15,
        "risk": 0.10
    }
    
    # Risk: higher score = lower risk = better (so use directly)
    overall = (
        market_norm * weights["market"] +
        product_norm * weights["product"] +
        team_norm * weights["team"] +
        traction_norm * weights["traction"] +
        risk_norm * weights["risk"]
    )
    
    return {
        "overall_score": round(overall, 2),
        "weights": weights,
        "breakdown_scores": {
            "market": round(market_score, 1),
            "product": round(product_score, 1),
            "team": round(team_score, 1),
            "traction": round(traction_score, 1),
            "risk": round(risk_score, 1)
        }
    }


async def score(
    startup_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Score a startup using Gemini-native LLM assessment
    
    Args:
        startup_data: Structured startup JSON from ingestion agent
        
    Returns:
        Scoring report with overall score, breakdown, reasoning, and weighted VentureLensScore
    """
    logger.info("📊 Starting startup scoring")
    
    if not CORE_LLM_AVAILABLE:
        raise ImportError(
            "Core LLM service not available. "
            "Please ensure core/llm_service.py exists and google-generativeai is installed."
        )
    
    # Extract startup information
    startup_name = startup_data.get("startup_name") or startup_data.get("name") or "Unnamed Startup"
    
    # Format startup data for prompt
    startup_info = json.dumps(startup_data, indent=2)
    
    # Compose prompt for Gemini
    prompt = f"""Rate this startup on Market, Product, Team, Traction, and Risk (0-20 each) and provide numeric JSON output.

Startup Information:
{startup_info}

Rate each dimension from 0 to 20:
- Market (0-20): Market size, opportunity, growth potential, addressable market
- Product (0-20): Product quality, innovation, differentiation, solution effectiveness
- Team (0-20): Team experience, expertise, execution capability, complementary skills
- Traction (0-20): Current metrics, growth, revenue, users, milestones, validation
- Risk (0-20): Lower score = higher risk, higher score = lower risk. Consider market risks, execution risks, competition, technology risks

For each dimension, provide:
- A numerical score (0-20, as float)
- Brief reasoning (2-3 sentences explaining the score)

Respond ONLY with valid JSON in this exact format (no markdown, no code blocks):
{{
  "market": {{
    "score": 15.5,
    "reasoning": "Large and growing market opportunity with clear addressable segment..."
  }},
  "product": {{
    "score": 14.0,
    "reasoning": "Innovative solution with strong differentiation..."
  }},
  "team": {{
    "score": 16.0,
    "reasoning": "Experienced team with relevant background..."
  }},
  "traction": {{
    "score": 12.5,
    "reasoning": "Early traction showing promise..."
  }},
  "risk": {{
    "score": 13.0,
    "reasoning": "Moderate risk factors including..."
  }}
}}"""

    try:
        logger.info("🤖 Calling Gemini 1.5 Pro for startup scoring")
        
        llm_service = get_service()
        
        # Call Gemini with text-only (no PDF)
        response_text = llm_service.invoke(
            model="gemini-1.5-pro",
            prompt=prompt,
            pdf_bytes=None
        )
        
        logger.info("✅ Gemini API call successful")
        
    except Exception as e:
        logger.error(f"❌ Gemini API call failed: {e}")
        raise Exception(f"Failed to call Gemini API: {str(e)}")
    
    # Parse JSON response
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
        assessment = json.loads(json_text)
        
        logger.info("✅ Successfully parsed JSON response")
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Failed to parse JSON response: {e}")
        logger.error(f"   Response text: {response_text[:500]}...")
        raise Exception(f"Failed to parse JSON response: {str(e)}")
    
    # Extract scores as floats
    try:
        market_score = float(assessment["market"]["score"])
        product_score = float(assessment["product"]["score"])
        team_score = float(assessment["team"]["score"])
        traction_score = float(assessment["traction"]["score"])
        risk_score = float(assessment["risk"]["score"])
        
        # Validate and clamp scores to 0-20 range
        original_scores = {
            "market": market_score,
            "product": product_score,
            "team": team_score,
            "traction": traction_score,
            "risk": risk_score
        }
        
        market_score = max(0.0, min(20.0, market_score))
        product_score = max(0.0, min(20.0, product_score))
        team_score = max(0.0, min(20.0, team_score))
        traction_score = max(0.0, min(20.0, traction_score))
        risk_score = max(0.0, min(20.0, risk_score))
        
        # Log if any scores were clamped
        for name, original, clamped in [
            ("market", original_scores["market"], market_score),
            ("product", original_scores["product"], product_score),
            ("team", original_scores["team"], team_score),
            ("traction", original_scores["traction"], traction_score),
            ("risk", original_scores["risk"], risk_score)
        ]:
            if original != clamped:
                logger.warning(f"⚠️ {name} score {original} was outside 0-20 range, clamped to {clamped}")
        
        logger.info(f"   Scores - Market: {market_score}, Product: {product_score}, Team: {team_score}, Traction: {traction_score}, Risk: {risk_score}")
        
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"❌ Failed to extract scores from assessment: {e}")
        raise Exception(f"Failed to extract scores: {str(e)}")
    
    # Compute weighted VentureLensScore
    scoring_result = compute_weighted_venture_lens_score(
        market_score,
        product_score,
        team_score,
        traction_score,
        risk_score
    )
    
    logger.info(f"✅ VentureLensScore computed: {scoring_result['overall_score']}/10")
    
    # Build response with breakdown + reasoning
    score_report = {
        "startup_name": startup_name,
        "venture_lens_score": scoring_result["overall_score"],
        "weights": scoring_result["weights"],
        "breakdown": {
            "market": {
                "score": scoring_result["breakdown_scores"]["market"],
                "reasoning": assessment["market"].get("reasoning", "")
            },
            "product": {
                "score": scoring_result["breakdown_scores"]["product"],
                "reasoning": assessment["product"].get("reasoning", "")
            },
            "team": {
                "score": scoring_result["breakdown_scores"]["team"],
                "reasoning": assessment["team"].get("reasoning", "")
            },
            "traction": {
                "score": scoring_result["breakdown_scores"]["traction"],
                "reasoning": assessment["traction"].get("reasoning", "")
            },
            "risk": {
                "score": scoring_result["breakdown_scores"]["risk"],
                "reasoning": assessment["risk"].get("reasoning", "")
            }
        },
        "_metadata": {
            "source": "core_llm_service",
            "model": "gemini-1.5-pro"
        }
    }
    
    logger.info(f"✅ Scoring complete: VentureLensScore={scoring_result['overall_score']}/10")
    return score_report
