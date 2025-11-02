"""
Pytest tests for Gemini-native Benchmark Agent
Tests schema integrity, numeric validation, and database logging
"""
import pytest
import os
import sys
import json
from unittest.mock import patch, MagicMock

# Add agents directory to path
agents_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, agents_dir)

from benchmark_agent import (
    benchmark,
    benchmark_with_logging,
    log_to_database,
    validate_numeric_value
)


@pytest.fixture
def sample_score_report():
    """Sample scoring report with industry, stage, and metrics"""
    return {
        "industry": "SaaS",
        "stage": "Series A",
        "metrics": {
            "funding": "$5M",
            "ARR": "$2M",
            "users": 10000,
            "CAC": "$50",
            "LTV": "$500",
            "churn": "5%"
        },
        "venture_lens_score": 7.5,
        "breakdown": {
            "market": {"score": 15.5},
            "product": {"score": 14.0},
            "team": {"score": 16.0},
            "traction": {"score": 12.5},
            "risk": {"score": 13.0}
        }
    }


@pytest.fixture
def valid_benchmark_response():
    """Valid benchmark response JSON"""
    return {
        "industry": "SaaS",
        "comparisons": [
            {
                "metric": "funding",
                "startup_value": "$5M",
                "sector_avg": "$3M",
                "percentile": 65,
                "insight": "Above average funding for Series A stage"
            },
            {
                "metric": "CAC",
                "startup_value": "$50",
                "sector_avg": "$75",
                "percentile": 70,
                "insight": "Lower CAC indicates efficient customer acquisition"
            },
            {
                "metric": "ARR",
                "startup_value": "$2M",
                "sector_avg": "$1.5M",
                "percentile": 60,
                "insight": "Above average revenue for stage"
            }
        ],
        "overall_position": "Above Average",
        "summary": "The startup shows strong performance across key metrics compared to sector averages, with particularly efficient customer acquisition and solid revenue growth."
    }


def test_validate_numeric_value_string():
    """Test numeric validation with string values"""
    assert validate_numeric_value("1000", "test") == 1000.0
    assert validate_numeric_value("1.5", "test") == 1.5
    assert validate_numeric_value("$1.5M", "test") == 1500000.0
    assert validate_numeric_value("50%", "test") == 50.0
    assert validate_numeric_value("1,000", "test") == 1000.0


def test_validate_numeric_value_numeric():
    """Test numeric validation with numeric values"""
    assert validate_numeric_value(1000, "test") == 1000.0
    assert validate_numeric_value(1.5, "test") == 1.5
    assert validate_numeric_value(50, "test") == 50.0


def test_validate_numeric_value_multipliers():
    """Test numeric validation with multipliers (K, M, B)"""
    assert validate_numeric_value("1K", "test") == 1000.0
    assert validate_numeric_value("2.5M", "test") == 2500000.0
    assert validate_numeric_value("1B", "test") == 1000000000.0
    assert validate_numeric_value("$1.5M", "test") == 1500000.0


def test_validate_numeric_value_invalid():
    """Test numeric validation with invalid values"""
    assert validate_numeric_value("invalid", "test") is None
    assert validate_numeric_value(None, "test") is None
    assert validate_numeric_value("", "test") is None


def test_benchmark_schema_structure(valid_benchmark_response):
    """Test that benchmark response has correct schema structure"""
    # Required top-level keys
    assert "industry" in valid_benchmark_response
    assert "comparisons" in valid_benchmark_response
    assert "overall_position" in valid_benchmark_response
    assert "summary" in valid_benchmark_response
    
    # Comparisons must be a list
    assert isinstance(valid_benchmark_response["comparisons"], list)
    assert len(valid_benchmark_response["comparisons"]) > 0
    
    # Each comparison must have required keys
    for comparison in valid_benchmark_response["comparisons"]:
        required_keys = ["metric", "startup_value", "sector_avg", "percentile", "insight"]
        for key in required_keys:
            assert key in comparison, f"Missing required key in comparison: {key}"


def test_benchmark_overall_position_values(valid_benchmark_response):
    """Test that overall_position has valid values"""
    valid_positions = ["Below Average", "Average", "Above Average"]
    assert valid_benchmark_response["overall_position"] in valid_positions


@pytest.mark.asyncio
async def test_benchmark_valid_json(sample_score_report, valid_benchmark_response):
    """Test that benchmark returns valid JSON with correct schema"""
    
    # Mock the LLM service
    mock_service = MagicMock()
    mock_service.invoke = MagicMock(return_value=json.dumps(valid_benchmark_response))
    
    with patch('benchmark_agent.get_service', return_value=mock_service):
        result = await benchmark(sample_score_report)
    
    # Verify required keys
    required_keys = ["industry", "comparisons", "overall_position", "summary"]
    for key in required_keys:
        assert key in result, f"Missing required key: {key}"
    
    # Verify comparisons structure
    assert isinstance(result["comparisons"], list)
    assert len(result["comparisons"]) > 0
    
    # Verify each comparison has required keys and numeric values
    for comparison in result["comparisons"]:
        assert "metric" in comparison
        assert "startup_value" in comparison
        assert "sector_avg" in comparison
        assert "percentile" in comparison
        assert "insight" in comparison
        
        # Verify numeric fields are added
        assert "startup_value_numeric" in comparison
        assert "sector_avg_numeric" in comparison
        
        # Verify percentile is integer 0-100
        assert isinstance(comparison["percentile"], int)
        assert 0 <= comparison["percentile"] <= 100


@pytest.mark.asyncio
async def test_benchmark_numeric_validation(sample_score_report, valid_benchmark_response):
    """Test that numeric values are properly validated and normalized"""
    
    mock_service = MagicMock()
    mock_service.invoke = MagicMock(return_value=json.dumps(valid_benchmark_response))
    
    with patch('benchmark_agent.get_service', return_value=mock_service):
        result = await benchmark(sample_score_report)
    
    # Check that numeric values are parsed
    for comparison in result["comparisons"]:
        # startup_value_numeric should be parsed if possible
        if comparison.get("startup_value"):
            # Should attempt to parse
            assert "startup_value_numeric" in comparison
        
        # sector_avg_numeric should be parsed if possible
        if comparison.get("sector_avg"):
            assert "sector_avg_numeric" in comparison


@pytest.mark.asyncio
async def test_benchmark_percentile_validation(sample_score_report):
    """Test that percentile values are validated and clamped to 0-100"""
    response_with_invalid_percentile = {
        "industry": "SaaS",
        "comparisons": [
            {
                "metric": "funding",
                "startup_value": "$5M",
                "sector_avg": "$3M",
                "percentile": 150,  # Invalid: > 100
                "insight": "Test"
            },
            {
                "metric": "CAC",
                "startup_value": "$50",
                "sector_avg": "$75",
                "percentile": -10,  # Invalid: < 0
                "insight": "Test"
            }
        ],
        "overall_position": "Above Average",
        "summary": "Test summary"
    }
    
    mock_service = MagicMock()
    mock_service.invoke = MagicMock(return_value=json.dumps(response_with_invalid_percentile))
    
    with patch('benchmark_agent.get_service', return_value=mock_service):
        result = await benchmark(sample_score_report)
    
    # Verify percentiles are clamped
    assert result["comparisons"][0]["percentile"] == 100  # Clamped from 150
    assert result["comparisons"][1]["percentile"] == 0  # Clamped from -10


@pytest.mark.asyncio
async def test_benchmark_missing_key_raises_error(sample_score_report):
    """Test that missing required keys raise error"""
    incomplete_response = {
        "industry": "SaaS",
        "comparisons": []
        # Missing overall_position and summary
    }
    
    mock_service = MagicMock()
    mock_service.invoke = MagicMock(return_value=json.dumps(incomplete_response))
    
    with patch('benchmark_agent.get_service', return_value=mock_service):
        with pytest.raises(ValueError, match="Missing required key"):
            await benchmark(sample_score_report)


@pytest.mark.asyncio
async def test_benchmark_empty_comparisons_raises_error(sample_score_report):
    """Test that empty comparisons list raises error"""
    response_empty_comparisons = {
        "industry": "SaaS",
        "comparisons": [],
        "overall_position": "Average",
        "summary": "Test"
    }
    
    mock_service = MagicMock()
    mock_service.invoke = MagicMock(return_value=json.dumps(response_empty_comparisons))
    
    with patch('benchmark_agent.get_service', return_value=mock_service):
        with pytest.raises(ValueError, match="comparisons list cannot be empty"):
            await benchmark(sample_score_report)


@pytest.mark.asyncio
async def test_benchmark_invalid_overall_position_defaults(sample_score_report):
    """Test that invalid overall_position defaults to Average"""
    response_invalid_position = {
        "industry": "SaaS",
        "comparisons": [
            {
                "metric": "funding",
                "startup_value": "$5M",
                "sector_avg": "$3M",
                "percentile": 65,
                "insight": "Test"
            }
        ],
        "overall_position": "Invalid Position",
        "summary": "Test summary"
    }
    
    mock_service = MagicMock()
    mock_service.invoke = MagicMock(return_value=json.dumps(response_invalid_position))
    
    with patch('benchmark_agent.get_service', return_value=mock_service):
        result = await benchmark(sample_score_report)
    
    assert result["overall_position"] == "Average"


@pytest.mark.asyncio
async def test_log_to_database_success(sample_score_report, valid_benchmark_response):
    """Test successful database logging"""
    mock_conn = MagicMock()
    mock_conn.execute = MagicMock()
    
    async def mock_close():
        pass
    mock_conn.close = mock_close
    
    with patch('benchmark_agent.asyncpg') as mock_asyncpg:
        async def mock_connect(url):
            return mock_conn
        mock_asyncpg.connect = mock_connect
        
        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"
        
        result = await log_to_database("startup123", valid_benchmark_response)
        
        assert result is True
        # Should execute CREATE TABLE + INSERT for each comparison
        assert mock_conn.execute.call_count >= len(valid_benchmark_response["comparisons"]) + 1


@pytest.mark.asyncio
async def test_log_to_database_no_config(valid_benchmark_response):
    """Test that logging gracefully handles missing database config"""
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]
    if "POSTGRES_URL" in os.environ:
        del os.environ["POSTGRES_URL"]
    
    result = await log_to_database("startup123", valid_benchmark_response)
    
    assert result is False


@pytest.mark.asyncio
async def test_benchmark_with_logging(sample_score_report, valid_benchmark_response):
    """Test benchmark_with_logging combines analysis and database logging"""
    mock_service = MagicMock()
    mock_service.invoke = MagicMock(return_value=json.dumps(valid_benchmark_response))
    
    with patch('benchmark_agent.get_service', return_value=mock_service):
        with patch('benchmark_agent.log_to_database', return_value=True) as mock_log:
            result = await benchmark_with_logging(
                sample_score_report,
                startup_id="test123"
            )
            
            # Verify benchmark result
            assert "comparisons" in result
            assert len(result["comparisons"]) > 0
            
            # Verify database logging was called
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][0] == "test123"
            assert call_args[0][1] == result


@pytest.mark.asyncio
async def test_benchmark_invalid_json_raises_error(sample_score_report):
    """Test that invalid JSON raises an error"""
    mock_service = MagicMock()
    mock_service.invoke = MagicMock(return_value="Invalid JSON content")
    
    with patch('benchmark_agent.get_service', return_value=mock_service):
        with pytest.raises(Exception, match="Failed to parse JSON"):
            await benchmark(sample_score_report)


@pytest.mark.asyncio
async def test_benchmark_comparison_missing_key_raises_error(sample_score_report):
    """Test that comparison missing required key raises error"""
    response_missing_key = {
        "industry": "SaaS",
        "comparisons": [
            {
                "metric": "funding",
                "startup_value": "$5M"
                # Missing sector_avg, percentile, insight
            }
        ],
        "overall_position": "Above Average",
        "summary": "Test summary"
    }
    
    mock_service = MagicMock()
    mock_service.invoke = MagicMock(return_value=json.dumps(response_missing_key))
    
    with patch('benchmark_agent.get_service', return_value=mock_service):
        with pytest.raises(ValueError, match="Missing required key in comparison"):
            await benchmark(sample_score_report)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

