"""
Gemini-native Benchmark Agent for Venture Lens
Compares startup metrics against global sector averages
"""
import os
import json
from typing import Dict, Any, Optional, List
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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("benchmark_agent")


def validate_numeric_value(value: Any, metric_name: str) -> Optional[float]:
    """
    Validate and convert metric value to numeric
    
    Args:
        value: Value to validate (can be string, number, or None)
        metric_name: Name of metric for error messages
        
    Returns:
        Numeric value or None if invalid
    """
    if value is None:
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        # Try to extract number from string (e.g., "$1.5M" -> 1500000)
        value = value.strip()
        
        # Remove common prefixes/suffixes
        value = value.replace("$", "").replace(",", "").replace("%", "")
        
        # Handle multipliers
        multipliers = {
            "K": 1000,
            "M": 1000000,
            "B": 1000000000
        }
        
        multiplier = 1
        for suffix, mult in multipliers.items():
            if value.upper().endswith(suffix):
                multiplier = mult
                value = value[:-1].strip()
                break
        
        try:
            return float(value) * multiplier
        except ValueError:
            logger.warning(f"⚠️ Could not parse {metric_name} value: {value}")
            return None
    
    return None


async def benchmark(
    score_report: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Benchmark startup against global sector averages
    
    Args:
        score_report: Structured JSON from scoring_agent with industry, stage, metrics
        
    Returns:
        Benchmark analysis with comparisons and percentile rankings
    """
    logger.info("📈 Starting benchmark analysis")
    
    if not CORE_LLM_AVAILABLE:
        raise ImportError(
            "Core LLM service not available. "
            "Please ensure core/llm_service.py exists and google-generativeai is installed."
        )
    
    # Extract required fields
    industry = score_report.get("industry") or score_report.get("sector") or "Technology"
    stage = score_report.get("stage") or "Seed"
    metrics = score_report.get("metrics", {})
    
    # Prepare JSON content for prompt
    json_content = {
        "industry": industry,
        "stage": stage,
        "metrics": metrics
    }
    
    json_content_str = json.dumps(json_content, indent=2)
    
    # Compose prompt for Gemini
    prompt = f"""You are a financial analyst comparing this startup to global sector averages.
Analyze the metrics and estimate how they rank relative to similar startups in the same industry.

Return ONLY valid JSON like:
{{
  "industry": "<string>",
  "comparisons": [
    {{"metric": "funding", "startup_value": "<val>", "sector_avg": "<val>", "percentile": "<int>", "insight": "<short text>"}},
    {{"metric": "CAC", "startup_value": "<val>", "sector_avg": "<val>", "percentile": "<int>", "insight": "<short text>"}}
  ],
  "overall_position": "<Below Average|Average|Above Average>",
  "summary": "<one-paragraph insight>"
}}

Startup Data:
{json_content_str}

For each metric in the data, provide:
- startup_value: The startup's actual value (use numeric if available)
- sector_avg: Typical value for similar startups in the industry
- percentile: Where this startup ranks (0-100)
- insight: Brief explanation of the comparison

Ensure all numeric values are provided as numbers or parseable strings (e.g., "1000", "$1.5M", "45%")."""
    
    try:
        logger.info("🤖 Calling Gemini 1.5 Pro for benchmark analysis")
        
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
        benchmark_result = json.loads(json_text)
        
        logger.info("✅ Successfully parsed JSON response")
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Failed to parse JSON response: {e}")
        logger.error(f"   Response text: {response_text[:500]}...")
        raise Exception(f"Failed to parse JSON response: {str(e)}")
    
    # Validate required keys
    required_keys = ["industry", "comparisons", "overall_position", "summary"]
    for key in required_keys:
        if key not in benchmark_result:
            raise ValueError(f"Missing required key: {key}")
    
    # Validate comparisons array
    if not isinstance(benchmark_result["comparisons"], list):
        raise ValueError("comparisons must be a list")
    
    if len(benchmark_result["comparisons"]) == 0:
        raise ValueError("comparisons list cannot be empty")
    
    # Validate and normalize numeric values in comparisons
    for comparison in benchmark_result["comparisons"]:
        required_comparison_keys = ["metric", "startup_value", "sector_avg", "percentile", "insight"]
        for key in required_comparison_keys:
            if key not in comparison:
                raise ValueError(f"Missing required key in comparison: {key}")
        
        # Validate and normalize numeric values
        startup_value = comparison["startup_value"]
        sector_avg = comparison["sector_avg"]
        percentile = comparison["percentile"]
        
        # Parse startup_value
        parsed_startup_value = validate_numeric_value(startup_value, comparison["metric"])
        if parsed_startup_value is not None:
            comparison["startup_value_numeric"] = parsed_startup_value
        else:
            comparison["startup_value_numeric"] = None
        
        # Parse sector_avg
        parsed_sector_avg = validate_numeric_value(sector_avg, f"{comparison['metric']}_avg")
        if parsed_sector_avg is not None:
            comparison["sector_avg_numeric"] = parsed_sector_avg
        else:
            comparison["sector_avg_numeric"] = None
        
        # Validate percentile (0-100)
        try:
            percentile_int = int(percentile)
            if percentile_int < 0 or percentile_int > 100:
                logger.warning(f"⚠️ Percentile {percentile_int} out of range, clamping to 0-100")
                percentile_int = max(0, min(100, percentile_int))
            comparison["percentile"] = percentile_int
        except (ValueError, TypeError):
            logger.warning(f"⚠️ Invalid percentile value: {percentile}, setting to 50")
            comparison["percentile"] = 50
    
    # Validate overall_position
    valid_positions = ["Below Average", "Average", "Above Average"]
    if benchmark_result["overall_position"] not in valid_positions:
        logger.warning(f"⚠️ Invalid overall_position: {benchmark_result['overall_position']}, defaulting to Average")
        benchmark_result["overall_position"] = "Average"
    
    # Add metadata
    benchmark_result["analyzed_at"] = datetime.utcnow().isoformat()
    benchmark_result["model"] = "gemini-1.5-pro"
    
    logger.info(f"✅ Benchmark analysis complete: {len(benchmark_result['comparisons'])} metrics compared")
    
    return benchmark_result


async def log_to_database(
    startup_id: str,
    benchmark_result: Dict[str, Any]
) -> bool:
    """
    Log benchmark comparisons to startup_benchmarks table
    
    Args:
        startup_id: Unique identifier for the startup
        benchmark_result: Benchmark analysis result
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"💾 Logging benchmark to startup_benchmarks table for startup_id: {startup_id}")
    
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
                    CREATE TABLE IF NOT EXISTS startup_benchmarks (
                        id SERIAL PRIMARY KEY,
                        startup_id VARCHAR(255) NOT NULL,
                        industry VARCHAR(100) NOT NULL,
                        metric VARCHAR(100) NOT NULL,
                        startup_value TEXT,
                        startup_value_numeric NUMERIC,
                        sector_avg TEXT,
                        sector_avg_numeric NUMERIC,
                        percentile INTEGER NOT NULL,
                        insight TEXT,
                        overall_position VARCHAR(50) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert each comparison
                industry = benchmark_result.get("industry", "Unknown")
                overall_position = benchmark_result.get("overall_position", "Average")
                comparisons = benchmark_result.get("comparisons", [])
                
                for comparison in comparisons:
                    await conn.execute("""
                        INSERT INTO startup_benchmarks 
                        (startup_id, industry, metric, startup_value, startup_value_numeric, 
                         sector_avg, sector_avg_numeric, percentile, insight, overall_position)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """, 
                        startup_id,
                        industry,
                        comparison.get("metric"),
                        str(comparison.get("startup_value", "")),
                        comparison.get("startup_value_numeric"),
                        str(comparison.get("sector_avg", "")),
                        comparison.get("sector_avg_numeric"),
                        comparison.get("percentile"),
                        comparison.get("insight", ""),
                        overall_position
                    )
                
                logger.info(f"   ✓ Logged {len(comparisons)} benchmark comparisons to database (asyncpg)")
                return True
            finally:
                await conn.close()
                
        except ImportError:
            # Fallback to psycopg2 (sync)
            try:
                import psycopg2
                
                conn = psycopg2.connect(database_url)
                cursor = conn.cursor()
                
                # Create table if not exists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS startup_benchmarks (
                        id SERIAL PRIMARY KEY,
                        startup_id VARCHAR(255) NOT NULL,
                        industry VARCHAR(100) NOT NULL,
                        metric VARCHAR(100) NOT NULL,
                        startup_value TEXT,
                        startup_value_numeric NUMERIC,
                        sector_avg TEXT,
                        sector_avg_numeric NUMERIC,
                        percentile INTEGER NOT NULL,
                        insight TEXT,
                        overall_position VARCHAR(50) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert each comparison
                industry = benchmark_result.get("industry", "Unknown")
                overall_position = benchmark_result.get("overall_position", "Average")
                comparisons = benchmark_result.get("comparisons", [])
                
                for comparison in comparisons:
                    cursor.execute("""
                        INSERT INTO startup_benchmarks 
                        (startup_id, industry, metric, startup_value, startup_value_numeric, 
                         sector_avg, sector_avg_numeric, percentile, insight, overall_position)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        startup_id,
                        industry,
                        comparison.get("metric"),
                        str(comparison.get("startup_value", "")),
                        comparison.get("startup_value_numeric"),
                        str(comparison.get("sector_avg", "")),
                        comparison.get("sector_avg_numeric"),
                        comparison.get("percentile"),
                        comparison.get("insight", ""),
                        overall_position
                    ))
                
                conn.commit()
                cursor.close()
                conn.close()
                
                logger.info(f"   ✓ Logged {len(comparisons)} benchmark comparisons to database (psycopg2)")
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


async def benchmark_with_logging(
    score_report: Dict[str, Any],
    startup_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Benchmark startup and log to database
    
    Args:
        score_report: Structured JSON from scoring_agent
        startup_id: Optional startup identifier for database logging
        
    Returns:
        Benchmark analysis result
    """
    # Perform benchmark analysis
    result = await benchmark(score_report)
    
    # Log to database if startup_id provided
    if startup_id:
        await log_to_database(startup_id, result)
    
    return result
