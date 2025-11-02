"""
AI Narrative Agent for Venture Lens
Uses LangChain SDK agent framework to generate 3-part startup narratives
"""
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, UTC
from pydantic import BaseModel, Field

from rich.console import Console
from rich.logging import RichHandler
import logging

# Redis client (optional - graceful fallback if not available)
redis_client = None
REDIS_AVAILABLE = False

try:
    import redis
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        redis_client = redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()
        REDIS_AVAILABLE = True
        logging.info("✅ Redis connection established")
    except Exception as e:
        REDIS_AVAILABLE = False
except ImportError:
    REDIS_AVAILABLE = False

# Setup rich logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, show_path=False)]
)

logger = logging.getLogger("narrative_agent")
console = Console()


# Pydantic model for structured output
class NarrativeStructure(BaseModel):
    """Structured output model for 3-part narrative"""
    vision: str = Field(..., description="Company's vision - where they want to be, the future they're building (2-3 sentences)")
    differentiation: str = Field(..., description="What makes this startup unique - competitive advantage, unique value proposition (2-3 sentences)")
    timing: str = Field(..., description="Why now is the right time - market timing, technology readiness, trend alignment (2-3 sentences)")


def create_narrative_agent():
    """
    Create a LangChain agent for narrative generation
    Uses structured output and agent framework
    """
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.prompts import ChatPromptTemplate
        
        # Check credentials
        project_id = os.getenv("GEMINI_PROJECT_ID")
        location = os.getenv("GEMINI_LOCATION")
        api_key = os.getenv("GEMINI_API_KEY")
        
        # Initialize LLM
        if project_id and location:
            # Vertex AI
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                project=project_id,
                location=location,
                temperature=0.7,
                max_output_tokens=1024,
            )
            logger.info("✅ Narrative agent initialized with Vertex AI")
        elif api_key and api_key.startswith("AIza"):
            # Gemini API
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                google_api_key=api_key,
                temperature=0.7,
                max_output_tokens=1024,
            )
            logger.info("✅ Narrative agent initialized with Gemini API")
        else:
            logger.warning("⚠️ No valid credentials, using mock agent")
            return None
        
        # Create prompt template for agent (no format instructions needed - SDK handles structure)
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an expert narrative agent specializing in creating compelling startup stories for investors.

Your task is to analyze startup information and generate a crisp, compelling 3-part narrative.

Generate narratives that are:
- Concise (2-3 sentences per part)
- Investor-focused
- Compelling and memorable
- Based on the actual startup data provided"""),
            ("user", """Analyze this startup and create a 3-part narrative:

Startup Data:
{startup_data}

Create the narrative with these three parts:
1. VISION: Where they're heading, the future state (2-3 sentences)
2. DIFFERENTIATION: What makes them unique (2-3 sentences)
3. TIMING: Why now is the right time (2-3 sentences)""")
        ])
        
        # Create agent chain with structured output (SDK handles schema automatically)
        chain = prompt_template | llm.with_structured_output(NarrativeStructure)
        
        logger.info("✅ Narrative agent chain created successfully")
        return chain
        
    except ImportError as e:
        logger.warning(f"⚠️ LangChain not available: {e}. Install: pip install langchain-google-genai langchain-core")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to create narrative agent: {e}")
        return None


# Global agent instance (lazy initialization)
_narrative_agent = None


def get_narrative_agent():
    """Get or create narrative agent instance"""
    global _narrative_agent
    if _narrative_agent is None:
        _narrative_agent = create_narrative_agent()
    return _narrative_agent


async def generate_narrative(
    startup_data: Dict[str, Any],
    startup_id: Optional[str] = None,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Generate 3-part narrative using LangChain agent framework
    
    Args:
        startup_data: Startup information as dictionary
        startup_id: Unique identifier for caching (optional)
        use_cache: Whether to use Redis cache (default: True)
        
    Returns:
        Dictionary with vision, differentiation, and timing narratives
    """
    logger.info("📖 Starting narrative generation with agent")
    
    # Check cache if Redis available and startup_id provided
    if use_cache and REDIS_AVAILABLE and startup_id:
        try:
            cache_key = f"narrative:{startup_id}"
            cached = redis_client.get(cache_key)
            if cached:
                logger.info(f"   ✓ Found cached narrative for startup_id: {startup_id}")
                cached_data = json.loads(cached)
                # Add model info if missing
                if "model" not in cached_data:
                    cached_data["model"] = "cached"
                return cached_data
        except Exception as e:
            logger.warning(f"   ⚠️ Cache read failed: {e}")
    
    # Get agent
    agent = get_narrative_agent()
    
    if agent is None:
        logger.warning("⚠️ Agent not available, using fallback")
        return generate_fallback_narrative(startup_data)
    
    try:
        logger.info("🤖 Invoking narrative agent")
        
        # Format startup data for agent
        startup_data_str = json.dumps(startup_data, indent=2)
        
        # Invoke agent with structured output (SDK handles Pydantic conversion automatically)
        result = await agent.ainvoke({
            "startup_data": startup_data_str
        })
        
        # Convert Pydantic model to dict (use model_dump for Pydantic V2)
        if hasattr(result, 'model_dump'):
            narrative_dict = result.model_dump()
        elif hasattr(result, 'dict'):
            narrative_dict = result.dict()  # Fallback for older Pydantic
        else:
            narrative_dict = {
                "vision": getattr(result, "vision", ""),
                "differentiation": getattr(result, "differentiation", ""),
                "timing": getattr(result, "timing", "")
            }
        
        # Add metadata
        narrative_result = {
            **narrative_dict,
            "generated_at": datetime.now(UTC).isoformat(),
            "model": "gemini-2.0-flash-exp"
        }
        
        # Validate structure
        narrative_result = normalize_narrative_response(narrative_result)
        
        # Cache the result
        if use_cache and REDIS_AVAILABLE and startup_id:
            try:
                cache_key = f"narrative:{startup_id}"
                redis_client.setex(
                    cache_key,
                    86400,  # 24 hours
                    json.dumps(narrative_result)
                )
                logger.info(f"   ✓ Cached narrative for startup_id: {startup_id}")
            except Exception as e:
                logger.warning(f"   ⚠️ Cache write failed: {e}")
        
        logger.info("✅ Narrative generation completed successfully")
        return narrative_result
        
    except Exception as e:
        logger.error(f"✗ Agent invocation failed: {e}")
        logger.info("   Using fallback narrative")
        return generate_fallback_narrative(startup_data)


def normalize_narrative_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize and validate narrative response
    
    Args:
        data: Raw narrative response
        
    Returns:
        Normalized narrative structure
    """
    required_fields = ["vision", "differentiation", "timing"]
    
    narrative = {}
    for field in required_fields:
        narrative[field] = data.get(field, "")
        if not narrative[field] or len(narrative[field].strip()) < 10:
            narrative[field] = f"[{field.title()}] Narrative not generated. Please provide more startup details."
    
    # Add metadata if not present
    if "generated_at" not in narrative:
        narrative["generated_at"] = datetime.now(UTC).isoformat()
    if "model" not in narrative:
        narrative["model"] = "unknown"
    
    return narrative


def generate_fallback_narrative(startup_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate fallback narrative using rule-based extraction"""
    logger.info("   Using rule-based fallback narrative")
    
    startup_name = startup_data.get("name") or startup_data.get("startup_name") or "the startup"
    description = startup_data.get("description", "")
    problem = startup_data.get("problem", "")
    solution = startup_data.get("solution", "")
    market = startup_data.get("market", "")
    traction = startup_data.get("traction", "")
    sector = startup_data.get("sector", "") or startup_data.get("industry", "")
    
    # Vision
    vision = f"{startup_name} envisions a future where {description.lower() if description else 'innovative solutions transform the market'}. "
    if solution:
        vision += f"By {solution.lower()[:100]}, they aim to revolutionize the {sector or 'industry'}. "
    vision += "Their mission is to create lasting impact through technology and innovation."
    
    # Differentiation
    differentiation = f"{startup_name} stands out through "
    if solution:
        differentiation += f"their unique approach to {solution.lower()[:80]}. "
    else:
        differentiation += "their innovative methodology. "
    if traction:
        differentiation += f"With {traction.lower()[:100]}, they've demonstrated early success. "
    differentiation += "Their competitive advantage lies in combining technical excellence with market insights."
    
    # Timing
    timing = f"The timing for {startup_name} is optimal because "
    if market:
        timing += f"the {market.lower()[:80]} is at an inflection point. "
    else:
        timing += "market conditions are favorable. "
    if traction:
        timing += f"Early indicators like {traction.lower()[:80]} show strong momentum. "
    timing += "Now is the moment to scale and capture market share."
    
    return {
        "vision": vision,
        "differentiation": differentiation,
        "timing": timing,
        "generated_at": datetime.now(UTC).isoformat(),
        "model": "fallback"
    }


async def get_cached_narrative(startup_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve cached narrative from Redis
    
    Args:
        startup_id: Unique startup identifier
        
    Returns:
        Cached narrative or None if not found
    """
    if not REDIS_AVAILABLE:
        return None
    
    try:
        cache_key = f"narrative:{startup_id}"
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        return None
    except Exception as e:
        logger.warning(f"Cache retrieval failed: {e}")
        return None


async def clear_narrative_cache(startup_id: str) -> bool:
    """
    Clear cached narrative for a startup
    
    Args:
        startup_id: Unique startup identifier
        
    Returns:
        True if successful, False otherwise
    """
    if not REDIS_AVAILABLE:
        return False
    
    try:
        cache_key = f"narrative:{startup_id}"
        redis_client.delete(cache_key)
        logger.info(f"✓ Cleared cache for startup_id: {startup_id}")
        return True
    except Exception as e:
        logger.warning(f"Cache clear failed: {e}")
        return False
