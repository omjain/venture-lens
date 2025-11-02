"""
Gemini-native Narrative Agent for Venture Lens
Generates compelling 3-part narratives with tagline for investors
"""
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
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
        logging.warning(f"⚠️ Redis not available: {e}")
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("⚠️ Redis library not installed")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("narrative_agent")


async def generate_narrative(
    startup_data: Dict[str, Any],
    startup_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate 3-part narrative with tagline using Gemini 1.5 Pro
    
    Args:
        startup_data: Structured JSON with fields (name, description, problem, solution, traction, market, team, etc.)
        startup_id: Optional identifier for Redis caching
        
    Returns:
        Dictionary with vision, differentiation, timing, and tagline
    """
    logger.info("📖 Starting narrative generation")
    
    if not CORE_LLM_AVAILABLE:
        raise ImportError(
            "Core LLM service not available. "
            "Please ensure core/llm_service.py exists and google-generativeai is installed."
        )
    
    # Check Redis cache if startup_id provided
    if startup_id and REDIS_AVAILABLE:
        try:
            cache_key = f"narrative:{startup_id}"
            cached = redis_client.get(cache_key)
            if cached:
                logger.info(f"   ✓ Found cached narrative for startup_id: {startup_id}")
                cached_data = json.loads(cached)
                return cached_data
        except Exception as e:
            logger.warning(f"   ⚠️ Cache read failed: {e}")
    
    # Prepare JSON content
    json_content = json.dumps(startup_data, indent=2)
    
    # Compose prompt for Gemini
    prompt = f"""You are a professional pitch writer.
Create a concise 3-part narrative that an investor would love.

Return ONLY valid JSON like:
{{
  "vision": "<describe startup's purpose and mission>",
  "differentiation": "<what makes it unique or defensible>",
  "timing": "<why now is the right time for this product>",
  "tagline": "<a short 1-line summary pitch>"
}}

Startup Data:
{json_content}

Make the narrative compelling, concise, and investor-focused. Keep tagline under 100 characters."""
    
    try:
        logger.info("🤖 Calling Gemini 1.5 Pro for narrative generation")
        
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
        narrative_result = json.loads(json_text)
        
        logger.info("✅ Successfully parsed JSON response")
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Failed to parse JSON response: {e}")
        logger.error(f"   Response text: {response_text[:500]}...")
        raise Exception(f"Failed to parse JSON response: {str(e)}")
    
    # Validate required keys
    required_keys = ["vision", "differentiation", "timing", "tagline"]
    for key in required_keys:
        if key not in narrative_result:
            raise ValueError(f"Missing required key: {key}")
    
    # Validate tagline length
    tagline = narrative_result.get("tagline", "")
    if len(tagline) > 100:
        logger.warning(f"⚠️ Tagline length {len(tagline)} exceeds 100 chars, truncating")
        narrative_result["tagline"] = tagline[:97] + "..."
    
    # Add metadata
    narrative_result["generated_at"] = datetime.utcnow().isoformat()
    narrative_result["model"] = "gemini-1.5-pro"
    
    # Cache in Redis if startup_id provided
    if startup_id and REDIS_AVAILABLE:
        try:
            cache_key = f"narrative:{startup_id}"
            # TTL: 12 hours = 43200 seconds
            redis_client.setex(
                cache_key,
                43200,  # 12 hours
                json.dumps(narrative_result)
            )
            logger.info(f"   ✓ Cached narrative for startup_id: {startup_id} (TTL: 12h)")
        except Exception as e:
            logger.warning(f"   ⚠️ Cache write failed: {e}")
    
    logger.info("✅ Narrative generation complete")
    return narrative_result


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
            logger.info(f"   ✓ Retrieved cached narrative for startup_id: {startup_id}")
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
        deleted = redis_client.delete(cache_key)
        if deleted:
            logger.info(f"✓ Cleared cache for startup_id: {startup_id}")
            return True
        else:
            logger.info(f"   Cache key not found for startup_id: {startup_id}")
            return False
    except Exception as e:
        logger.warning(f"Cache clear failed: {e}")
        return False
