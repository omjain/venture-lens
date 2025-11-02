"""
Pytest tests for AI Narrative Agent
Tests narrative generation, structure validation, and Redis caching
"""
import pytest
import os
import sys
import json
from unittest.mock import AsyncMock, MagicMock, patch

# Add agents directory to path
agents_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, agents_dir)

from narrative_agent import (
    generate_narrative,
    normalize_narrative_response,
    generate_fallback_narrative,
    get_cached_narrative,
    clear_narrative_cache
)


@pytest.fixture
def sample_startup_data():
    """Sample startup data for testing"""
    return {
        "name": "TechVenture",
        "description": "AI-powered data processing platform",
        "problem": "Current data processing is slow and expensive",
        "solution": "Our platform processes data 10x faster at lower cost",
        "traction": "1,000 users, $100K MRR, 20% MoM growth",
        "market": "Data processing market worth $50B",
        "sector": "SaaS"
    }


@pytest.fixture
def sample_startup_id():
    """Sample startup ID for caching tests"""
    return "startup_123"


def test_normalize_narrative_response_valid():
    """Test normalizing valid narrative response"""
    valid_response = {
        "vision": "TechVenture envisions transforming data processing through AI innovation.",
        "differentiation": "Unique approach combining speed and cost efficiency.",
        "timing": "Market is ready for AI-powered solutions."
    }
    
    result = normalize_narrative_response(valid_response)
    
    assert "vision" in result
    assert "differentiation" in result
    assert "timing" in result
    assert len(result["vision"]) > 10
    assert len(result["differentiation"]) > 10
    assert len(result["timing"]) > 10
    assert "generated_at" in result
    assert "model" in result


def test_normalize_narrative_response_missing_fields():
    """Test normalizing response with missing fields"""
    incomplete_response = {
        "vision": "Some vision"
    }
    
    result = normalize_narrative_response(incomplete_response)
    
    # Should have all required fields with fallbacks
    assert "vision" in result
    assert "differentiation" in result
    assert "timing" in result
    assert "[Differentiation]" in result["differentiation"] or len(result["differentiation"]) > 10


def test_normalize_narrative_response_empty_fields():
    """Test normalizing response with empty fields"""
    empty_response = {
        "vision": "",
        "differentiation": "   ",
        "timing": "x"  # Too short
    }
    
    result = normalize_narrative_response(empty_response)
    
    # Should have meaningful content for all fields
    assert len(result["vision"]) > 10
    assert len(result["differentiation"]) > 10
    assert len(result["timing"]) > 10


def test_generate_fallback_narrative(sample_startup_data):
    """Test fallback narrative generation"""
    result = generate_fallback_narrative(sample_startup_data)
    
    assert "vision" in result
    assert "differentiation" in result
    assert "timing" in result
    assert len(result["vision"]) > 10
    assert len(result["differentiation"]) > 10
    assert len(result["timing"]) > 10
    assert "generated_at" in result
    assert result["model"] == "fallback"
    
    # Check that startup name appears in narrative
    assert "TechVenture" in result["vision"] or "TechVenture" in result["differentiation"]


@pytest.mark.asyncio
async def test_generate_narrative_with_mock_agent(sample_startup_data, sample_startup_id):
    """Test narrative generation with mocked LangChain agent"""
    from narrative_agent import NarrativeStructure
    
    mock_narrative = NarrativeStructure(
        vision="TechVenture aims to revolutionize data processing.",
        differentiation="Unique AI-powered approach sets them apart.",
        timing="Market timing is perfect for AI solutions."
    )
    
    # Mock agent chain
    with patch('narrative_agent.get_narrative_agent') as mock_get_agent:
        mock_agent = AsyncMock()
        mock_agent.ainvoke = AsyncMock(return_value=mock_narrative)
        mock_get_agent.return_value = mock_agent
        
        # Mock Redis to return None (cache miss)
        with patch('narrative_agent.redis_client') as mock_redis:
            mock_redis.get.return_value = None
            
            result = await generate_narrative(
                startup_data=sample_startup_data,
                startup_id=sample_startup_id,
                use_cache=True
            )
            
            assert "vision" in result
            assert "differentiation" in result
            assert "timing" in result
            assert result["vision"] == mock_narrative.vision
            assert result["differentiation"] == mock_narrative.differentiation
            assert result["timing"] == mock_narrative.timing


@pytest.mark.asyncio
async def test_generate_narrative_cache_hit(sample_startup_data, sample_startup_id):
    """Test narrative generation with cache hit"""
    cached_narrative = {
        "vision": "Cached vision",
        "differentiation": "Cached differentiation",
        "timing": "Cached timing",
        "generated_at": "2025-01-11T00:00:00",
        "model": "cached"
    }
    
    with patch('narrative_agent.REDIS_AVAILABLE', True):
        with patch('narrative_agent.redis_client') as mock_redis:
            mock_redis.get.return_value = json.dumps(cached_narrative)
            
            result = await generate_narrative(
                startup_data=sample_startup_data,
                startup_id=sample_startup_id,
                use_cache=True
            )
            
            assert result["vision"] == "Cached vision"
            assert result["differentiation"] == "Cached differentiation"
            assert result["timing"] == "Cached timing"
            # LLM should not be called if cache hit
            mock_redis.get.assert_called_once()


@pytest.mark.asyncio
async def test_generate_narrative_no_cache(sample_startup_data):
    """Test narrative generation without caching"""
    from narrative_agent import NarrativeStructure
    
    mock_narrative = NarrativeStructure(
        vision="Test vision",
        differentiation="Test differentiation",
        timing="Test timing"
    )
    
    # Mock agent chain
    with patch('narrative_agent.get_narrative_agent') as mock_get_agent:
        mock_agent = AsyncMock()
        mock_agent.ainvoke = AsyncMock(return_value=mock_narrative)
        mock_get_agent.return_value = mock_agent
        
        result = await generate_narrative(
            startup_data=sample_startup_data,
            startup_id=None,  # No ID = no caching
            use_cache=False
        )
        
        assert "vision" in result
        assert "differentiation" in result
        assert "timing" in result


@pytest.mark.asyncio
async def test_get_cached_narrative():
    """Test retrieving cached narrative"""
    cached_data = {
        "vision": "Cached vision",
        "differentiation": "Cached diff",
        "timing": "Cached timing"
    }
    
    with patch('narrative_agent.REDIS_AVAILABLE', True):
        with patch('narrative_agent.redis_client') as mock_redis:
            mock_redis.get.return_value = json.dumps(cached_data)
            
            result = await get_cached_narrative("test_id")
            
            assert result is not None
            assert result["vision"] == "Cached vision"
            mock_redis.get.assert_called_once_with("narrative:test_id")


@pytest.mark.asyncio
async def test_get_cached_narrative_not_found():
    """Test retrieving non-existent cached narrative"""
    with patch('narrative_agent.REDIS_AVAILABLE', True):
        with patch('narrative_agent.redis_client') as mock_redis:
            mock_redis.get.return_value = None
            
            result = await get_cached_narrative("nonexistent_id")
            
            assert result is None


@pytest.mark.asyncio
async def test_clear_narrative_cache():
    """Test clearing cached narrative"""
    with patch('narrative_agent.REDIS_AVAILABLE', True):
        with patch('narrative_agent.redis_client') as mock_redis:
            mock_redis.delete.return_value = 1
            
            result = await clear_narrative_cache("test_id")
            
            assert result is True
            mock_redis.delete.assert_called_once_with("narrative:test_id")


@pytest.mark.asyncio
async def test_clear_narrative_cache_redis_unavailable():
    """Test clearing cache when Redis unavailable"""
    with patch('narrative_agent.REDIS_AVAILABLE', False):
        result = await clear_narrative_cache("test_id")
        assert result is False


def test_narrative_structure_comparison(sample_startup_data):
    """Test that narrative has correct structure"""
    # Generate fallback narrative (not async)
    result = generate_fallback_narrative(sample_startup_data)
    
    # Verify structure
    required_fields = ["vision", "differentiation", "timing"]
    for field in required_fields:
        assert field in result, f"Missing required field: {field}"
        assert isinstance(result[field], str), f"Field {field} must be string"
        assert len(result[field]) > 10, f"Field {field} too short"
    
    # Verify metadata
    assert "generated_at" in result
    assert "model" in result
    
    # Verify all three parts are present and distinct
    assert result["vision"] != result["differentiation"]
    assert result["differentiation"] != result["timing"]
    assert result["vision"] != result["timing"]


def test_narrative_with_minimal_data():
    """Test narrative generation with minimal startup data"""
    minimal_data = {
        "name": "StartupX"
    }
    
    result = generate_fallback_narrative(minimal_data)
    
    assert "vision" in result
    assert "differentiation" in result
    assert "timing" in result
    assert "StartupX" in result["vision"] or "StartupX" in result["differentiation"] or "StartupX" in result["timing"]


@pytest.mark.asyncio
async def test_narrative_fallback_on_agent_error(sample_startup_data):
    """Test that fallback is used when agent fails"""
    with patch('narrative_agent.get_narrative_agent') as mock_get_agent:
        mock_agent = AsyncMock()
        mock_agent.ainvoke = AsyncMock(side_effect=Exception("Agent error"))
        mock_get_agent.return_value = mock_agent
        
        result = await generate_narrative(
            startup_data=sample_startup_data,
            startup_id=None,
            use_cache=False
        )
        
        # Should still return valid structure
        assert "vision" in result
        assert "differentiation" in result
        assert "timing" in result
        assert result.get("model") == "fallback"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

