"""
Pytest tests for AI Critique Agent
Tests severity parsing, red flag identification, and database logging
"""
import pytest
import os
import sys
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# Add agents directory to path
agents_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, agents_dir)

from critique_agent import (
    analyze_critique,
    normalize_critique_response,
    generate_fallback_critique,
    save_critique_to_db,
    SeverityLevel,
    RiskLabel
)


@pytest.fixture
def sample_score_report():
    """Sample scoring report for testing"""
    return {
        "overall_score": 6.5,
        "breakdown": {
            "qualitative_assessment": {
                "idea": {
                    "score": 7,
                    "assessment": "Strong idea",
                    "strengths": ["Innovative approach"],
                    "concerns": ["Market validation needed"]
                },
                "team": {
                    "score": 5,
                    "assessment": "Decent team",
                    "strengths": ["Technical expertise"],
                    "concerns": ["Lack of business experience"]
                },
                "traction": {
                    "score": 4,
                    "assessment": "Limited traction",
                    "strengths": [],
                    "concerns": ["Low user growth", "No revenue"]
                },
                "market": {
                    "score": 8,
                    "assessment": "Large market",
                    "strengths": ["TAM is significant"],
                    "concerns": []
                }
            }
        },
        "recommendation": "Moderate investment potential"
    }


@pytest.fixture
def sample_pitchdeck_summary():
    """Sample pitch deck summary for testing"""
    return {
        "total_slides": 12,
        "missing_slides_report": "Potentially missing key slides: Financial Projections",
        "overall_summary": "Complete pitch deck with minor gaps"
    }


@pytest.fixture
def sample_low_score_report():
    """Low scoring report for testing critical flags"""
    return {
        "overall_score": 3.2,
        "breakdown": {
            "qualitative_assessment": {
                "idea": {"score": 2, "concerns": ["Vague concept"]},
                "team": {"score": 3, "concerns": ["Incomplete team"]},
                "traction": {"score": 2, "concerns": ["No users"]},
                "market": {"score": 5, "concerns": []}
            }
        }
    }


def test_normalize_critique_response_valid():
    """Test normalizing valid critique response"""
    valid_response = {
        "red_flags": [
            {
                "flag": "Low traction score",
                "severity": "high",
                "explanation": "Only 4/10 in traction indicates weak product-market fit",
                "category": "traction"
            },
            {
                "flag": "Missing financial projections",
                "severity": "medium",
                "explanation": "Pitch deck lacks financial projections",
                "category": "financial"
            }
        ],
        "overall_risk_label": "moderate_risk",
        "summary": "Several areas of concern identified"
    }
    
    result = normalize_critique_response(valid_response)
    
    assert "red_flags" in result
    assert len(result["red_flags"]) == 2
    assert result["red_flags"][0]["severity"] == "high"
    assert result["red_flags"][0]["category"] == "traction"
    assert result["overall_risk_label"] == "moderate_risk"
    assert "analysis_timestamp" in result


def test_normalize_critique_response_invalid_severity():
    """Test normalizing response with invalid severity"""
    invalid_response = {
        "red_flags": [
            {
                "flag": "Test flag",
                "severity": "invalid_severity",
                "explanation": "Test",
                "category": "other"
            }
        ],
        "overall_risk_label": "invalid_risk"
    }
    
    result = normalize_critique_response(invalid_response)
    
    assert result["red_flags"][0]["severity"] == "medium"  # Should default to medium
    assert result["overall_risk_label"] in ["low_risk", "moderate_risk", "high_risk", "very_high_risk"]


def test_normalize_critique_response_more_than_5_flags():
    """Test that more than 5 flags are limited to top 5"""
    many_flags = {
        "red_flags": [
            {"flag": f"Flag {i}", "severity": "low", "explanation": "", "category": "other"}
            for i in range(10)
        ],
        "overall_risk_label": "high_risk"
    }
    
    result = normalize_critique_response(many_flags)
    
    assert len(result["red_flags"]) <= 5


def test_normalize_critique_response_infers_risk_from_severity():
    """Test that risk label is inferred from flag severities"""
    critical_flags = {
        "red_flags": [
            {"flag": "Critical issue", "severity": "critical", "explanation": "", "category": "other"}
        ],
        "overall_risk_label": "invalid"
    }
    
    result = normalize_critique_response(critical_flags)
    
    assert result["overall_risk_label"] == "very_high_risk"
    
    high_flags = {
        "red_flags": [
            {"flag": "High issue", "severity": "high", "explanation": "", "category": "other"}
        ],
        "overall_risk_label": "invalid"
    }
    
    result = normalize_critique_response(high_flags)
    assert result["overall_risk_label"] == "high_risk"


def test_generate_fallback_critique_low_score(sample_low_score_report, sample_pitchdeck_summary):
    """Test fallback critique generation for low scores"""
    result = generate_fallback_critique(sample_low_score_report, sample_pitchdeck_summary)
    
    assert "red_flags" in result
    assert len(result["red_flags"]) > 0
    assert any("low" in f["flag"].lower() or "score" in f["flag"].lower() for f in result["red_flags"])
    assert "overall_risk_label" in result
    assert result["overall_risk_label"] in ["low_risk", "moderate_risk", "high_risk", "very_high_risk"]


def test_generate_fallback_critique_missing_slides(sample_score_report):
    """Test fallback critique for missing pitch deck slides"""
    pitchdeck_with_missing = {
        "missing_slides_report": "Potentially missing key slides: Financial Projections, Team"
    }
    
    result = generate_fallback_critique(sample_score_report, pitchdeck_with_missing)
    
    assert any("incomplete" in f["flag"].lower() or "missing" in f["flag"].lower() 
               for f in result["red_flags"])


@pytest.mark.asyncio
async def test_analyze_critique_with_mock_llm(sample_score_report, sample_pitchdeck_summary):
    """Test critique analysis with mocked LLM"""
    mock_response = {
        "red_flags": [
            {
                "flag": "Low traction",
                "severity": "high",
                "explanation": "Limited user growth",
                "category": "traction"
            }
        ],
        "overall_risk_label": "moderate_risk",
        "summary": "Several concerns identified"
    }
    
    with patch('critique_agent.llm_service') as mock_llm:
        mock_llm.invoke = AsyncMock(return_value=json.dumps(mock_response))
        
        result = await analyze_critique(sample_score_report, sample_pitchdeck_summary)
        
        assert "red_flags" in result
        assert len(result["red_flags"]) >= 1
        assert result["red_flags"][0]["severity"] in ["low", "medium", "high", "critical"]
        assert "overall_risk_label" in result


@pytest.mark.asyncio
async def test_analyze_critique_fallback_on_error(sample_score_report, sample_pitchdeck_summary):
    """Test that fallback critique is used when LLM fails"""
    with patch('critique_agent.llm_service') as mock_llm:
        mock_llm.invoke = AsyncMock(side_effect=Exception("LLM error"))
        
        result = await analyze_critique(sample_score_report, sample_pitchdeck_summary)
        
        # Should still return a valid critique structure
        assert "red_flags" in result
        assert "overall_risk_label" in result
        assert isinstance(result["red_flags"], list)


@pytest.mark.asyncio
async def test_save_critique_to_db_asyncpg():
    """Test saving critique to database with asyncpg"""
    mock_connection = AsyncMock()
    mock_connection.execute = AsyncMock()
    
    critique_result = {
        "red_flags": [
            {
                "flag": "Test flag",
                "severity": "high",
                "explanation": "Test explanation",
                "category": "other"
            }
        ],
        "overall_risk_label": "high_risk",
        "summary": "Test summary"
    }
    
    result = await save_critique_to_db("Test Startup", critique_result, mock_connection)
    
    assert result is True
    # Verify execute was called (at least for CREATE TABLE + INSERT)
    assert mock_connection.execute.call_count >= 2


@pytest.mark.asyncio
async def test_save_critique_to_db_psycopg2():
    """Test saving critique to database with psycopg2"""
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value = mock_cursor
    
    critique_result = {
        "red_flags": [
            {
                "flag": "Test flag",
                "severity": "medium",
                "explanation": "Test",
                "category": "other"
            }
        ],
        "overall_risk_label": "moderate_risk",
        "summary": "Test"
    }
    
    result = await save_critique_to_db("Test Startup", critique_result, mock_connection)
    
    # Should work with psycopg2 connection
    assert mock_connection.cursor.called
    assert mock_cursor.execute.called
    assert mock_connection.commit.called or result is False  # May fail gracefully


def test_severity_level_enum():
    """Test SeverityLevel enum values"""
    assert SeverityLevel.LOW.value == "low"
    assert SeverityLevel.MEDIUM.value == "medium"
    assert SeverityLevel.HIGH.value == "high"
    assert SeverityLevel.CRITICAL.value == "critical"


def test_risk_label_enum():
    """Test RiskLabel enum values"""
    assert RiskLabel.LOW_RISK.value == "low_risk"
    assert RiskLabel.MODERATE_RISK.value == "moderate_risk"
    assert RiskLabel.HIGH_RISK.value == "high_risk"
    assert RiskLabel.VERY_HIGH_RISK.value == "very_high_risk"


@pytest.mark.asyncio
async def test_critique_with_empty_inputs():
    """Test critique with empty or minimal inputs"""
    empty_score = {}
    empty_summary = {}
    
    result = await analyze_critique(empty_score, empty_summary)
    
    # Should still return valid structure
    assert "red_flags" in result
    assert "overall_risk_label" in result
    assert isinstance(result["red_flags"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

