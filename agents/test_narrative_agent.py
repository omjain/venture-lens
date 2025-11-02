"""
Pytest tests for Gemini-native Narrative Agent
Tests JSON structure, required keys, and tagline length validation
"""
import pytest
import os
import sys
import json
from unittest.mock import patch, MagicMock

# Add agents directory to path
agents_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, agents_dir)

from narrative_agent import (
    generate_narrative,
    get_cached_narrative,
    clear_narrative_cache
)


@pytest.fixture
def sample_startup_data():
    """Sample startup data for testing"""
    return {
        "name": "TechVenture",
        "description": "AI-powered data processing platform",
        "problem": "Current solutions are slow and inefficient",
        "solution": "10x faster processing with AI",
        "traction": "1,000 users, $100K MRR",
        "market": "Data processing market worth $50B",
        "team": "Experienced founders from Google and Microsoft",
        "sector": "SaaS"
    }


@pytest.fixture
def sample_startup_id():
    """Sample startup ID for caching tests"""
    return "techventure_001"


@pytest.fixture
def valid_narrative_response():
    """Valid narrative response JSON"""
    return {
        "vision": "TechVenture envisions transforming data processing by making it accessible, fast, and intelligent for businesses of all sizes.",
        "differentiation": "Our unique AI-powered approach processes data 10x faster than competitors while maintaining accuracy, giving us a strong competitive moat.",
        "timing": "The market is ready for AI-driven solutions now, with growing data volumes and demand for real-time insights.",
        "tagline": "AI-powered data processing at lightning speed"
    }


def test_narrative_response_structure(valid_narrative_response):
    """Test that narrative response has all required keys"""
    required_keys = ["vision", "differentiation", "timing", "tagline"]
    for key in required_keys:
        assert key in valid_narrative_response, f"Missing required key: {key}"
        assert isinstance(valid_narrative_response[key], str), f"{key} must be a string"
        assert len(valid_narrative_response[key].strip()) > 0, f"{key} must not be empty"


def test_tagline_length_validation(valid_narrative_response):
    """Test that tagline is ≤ 100 characters"""
    tagline = valid_narrative_response["tagline"]
    assert len(tagline) <= 100, f"Tagline must be ≤ 100 characters, got {len(tagline)}"
    assert len(tagline) > 0, "Tagline must not be empty"


@pytest.mark.asyncio
async def test_generate_narrative_valid_json(sample_startup_data, valid_narrative_response):
    """Test that generate_narrative returns valid JSON with all required keys"""
    
    # Mock the LLM service
    mock_service = MagicMock()
    mock_service.invoke = MagicMock(return_value=json.dumps(valid_narrative_response))
    
    with patch('narrative_agent.get_service', return_value=mock_service):
        # Mock Redis to not be available for this test
        with patch('narrative_agent.REDIS_AVAILABLE', False):
            result = await generate_narrative(sample_startup_data)
    
    # Verify structure
    required_keys = ["vision", "differentiation", "timing", "tagline"]
    for key in required_keys:
        assert key in result, f"Missing required key: {key}"
        assert isinstance(result[key], str), f"{key} must be a string"
        assert len(result[key]) > 0, f"{key} must not be empty"
    
    # Verify tagline length
    assert len(result["tagline"]) <= 100, "Tagline must be ≤ 100 characters"
    
    # Verify metadata
    assert "generated_at" in result
    assert "model" in result
    assert result["model"] == "gemini-1.5-pro"


@pytest.mark.asyncio
async def test_generate_narrative_tagline_truncation(sample_startup_data):
    """Test that tagline exceeding 100 chars is truncated"""
    long_tagline_response = {
        "vision": "Test vision",
        "differentiation": "Test differentiation",
        "timing": "Test timing",
        "tagline": "A" * 150  # 150 characters
    }
    
    mock_service = MagicMock()
    mock_service.invoke = MagicMock(return_value=json.dumps(long_tagline_response))
    
    with patch('narrative_agent.get_service', return_value=mock_service):
        with patch('narrative_agent.REDIS_AVAILABLE', False):
            result = await generate_narrative(sample_startup_data)
    
    assert len(result["tagline"]) <= 100, "Tagline should be truncated to ≤ 100 characters"
    assert result["tagline"].endswith("..."), "Long tagline should end with ..."


@pytest.mark.asyncio
async def test_generate_narrative_missing_key_raises_error(sample_startup_data):
    """Test that missing required keys raise error"""
    incomplete_response = {
        "vision": "Test vision",
        "differentiation": "Test differentiation"
        # Missing timing and tagline
    }
    
    mock_service = MagicMock()
    mock_service.invoke = MagicMock(return_value=json.dumps(incomplete_response))
    
    with patch('narrative_agent.get_service', return_value=mock_service):
        with patch('narrative_agent.REDIS_AVAILABLE', False):
            with pytest.raises(ValueError, match="Missing required key"):
                await generate_narrative(sample_startup_data)


@pytest.mark.asyncio
async def test_generate_narrative_cache_hit(sample_startup_data, sample_startup_id, valid_narrative_response):
    """Test that cached narrative is returned when available"""
    
    # Mock Redis
    mock_redis = MagicMock()
    mock_redis.get = MagicMock(return_value=json.dumps(valid_narrative_response))
    
    with patch('narrative_agent.redis_client', mock_redis):
        with patch('narrative_agent.REDIS_AVAILABLE', True):
            result = await generate_narrative(sample_startup_data, startup_id=sample_startup_id)
    
    # Verify cached result
    assert result == valid_narrative_response
    mock_redis.get.assert_called_once_with(f"narrative:{sample_startup_id}")


@pytest.mark.asyncio
async def test_generate_narrative_cache_write(sample_startup_data, sample_startup_id, valid_narrative_response):
    """Test that narrative is cached after generation"""
    
    mock_service = MagicMock()
    mock_service.invoke = MagicMock(return_value=json.dumps(valid_narrative_response))
    
    mock_redis = MagicMock()
    mock_redis.get = MagicMock(return_value=None)  # Cache miss
    mock_redis.setex = MagicMock()
    
    with patch('narrative_agent.get_service', return_value=mock_service):
        with patch('narrative_agent.redis_client', mock_redis):
            with patch('narrative_agent.REDIS_AVAILABLE', True):
                result = await generate_narrative(sample_startup_data, startup_id=sample_startup_id)
    
    # Verify cache write was called with 12h TTL (43200 seconds)
    mock_redis.setex.assert_called_once()
    call_args = mock_redis.setex.call_args
    assert call_args[0][0] == f"narrative:{sample_startup_id}"
    assert call_args[0][1] == 43200  # 12 hours in seconds
    assert json.loads(call_args[0][2]) == result


@pytest.mark.asyncio
async def test_get_cached_narrative_found():
    """Test retrieving cached narrative"""
    cached_data = {
        "vision": "Test vision",
        "differentiation": "Test differentiation",
        "timing": "Test timing",
        "tagline": "Test tagline"
    }
    
    mock_redis = MagicMock()
    mock_redis.get = MagicMock(return_value=json.dumps(cached_data))
    
    with patch('narrative_agent.redis_client', mock_redis):
        with patch('narrative_agent.REDIS_AVAILABLE', True):
            result = await get_cached_narrative("test_id")
    
    assert result == cached_data
    mock_redis.get.assert_called_once_with("narrative:test_id")


@pytest.mark.asyncio
async def test_get_cached_narrative_not_found():
    """Test retrieving non-existent cached narrative"""
    mock_redis = MagicMock()
    mock_redis.get = MagicMock(return_value=None)
    
    with patch('narrative_agent.redis_client', mock_redis):
        with patch('narrative_agent.REDIS_AVAILABLE', True):
            result = await get_cached_narrative("nonexistent_id")
    
    assert result is None


@pytest.mark.asyncio
async def test_get_cached_narrative_no_redis():
    """Test that get_cached_narrative returns None when Redis unavailable"""
    with patch('narrative_agent.REDIS_AVAILABLE', False):
        result = await get_cached_narrative("test_id")
    
    assert result is None


@pytest.mark.asyncio
async def test_clear_narrative_cache_success():
    """Test clearing cached narrative"""
    mock_redis = MagicMock()
    mock_redis.delete = MagicMock(return_value=1)  # Key existed and was deleted
    
    with patch('narrative_agent.redis_client', mock_redis):
        with patch('narrative_agent.REDIS_AVAILABLE', True):
            result = await clear_narrative_cache("test_id")
    
    assert result is True
    mock_redis.delete.assert_called_once_with("narrative:test_id")


@pytest.mark.asyncio
async def test_clear_narrative_cache_not_found():
    """Test clearing non-existent cached narrative"""
    mock_redis = MagicMock()
    mock_redis.delete = MagicMock(return_value=0)  # Key didn't exist
    
    with patch('narrative_agent.redis_client', mock_redis):
        with patch('narrative_agent.REDIS_AVAILABLE', True):
            result = await clear_narrative_cache("nonexistent_id")
    
    assert result is False


@pytest.mark.asyncio
async def test_clear_narrative_cache_no_redis():
    """Test that clear_narrative_cache returns False when Redis unavailable"""
    with patch('narrative_agent.REDIS_AVAILABLE', False):
        result = await clear_narrative_cache("test_id")
    
    assert result is False


@pytest.mark.asyncio
async def test_generate_narrative_invalid_json_raises_error(sample_startup_data):
    """Test that invalid JSON raises an error"""
    mock_service = MagicMock()
    mock_service.invoke = MagicMock(return_value="Invalid JSON content")
    
    with patch('narrative_agent.get_service', return_value=mock_service):
        with patch('narrative_agent.REDIS_AVAILABLE', False):
            with pytest.raises(Exception, match="Failed to parse JSON"):
                await generate_narrative(sample_startup_data)


@pytest.mark.asyncio
async def test_narrative_with_all_startup_fields(sample_startup_data, valid_narrative_response):
    """Test narrative generation with comprehensive startup data"""
    mock_service = MagicMock()
    mock_service.invoke = MagicMock(return_value=json.dumps(valid_narrative_response))
    
    with patch('narrative_agent.get_service', return_value=mock_service):
        with patch('narrative_agent.REDIS_AVAILABLE', False):
            result = await generate_narrative(sample_startup_data)
    
    # Verify all fields are present and valid
    assert "vision" in result and len(result["vision"]) > 0
    assert "differentiation" in result and len(result["differentiation"]) > 0
    assert "timing" in result and len(result["timing"]) > 0
    assert "tagline" in result and len(result["tagline"]) > 0 and len(result["tagline"]) <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
