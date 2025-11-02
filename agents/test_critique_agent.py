"""
Pytest tests for Gemini-native Critique Agent
Tests valid JSON parsing, 3-5 red flags validation, and Pydantic schema
"""
import pytest
import os
import sys
import json
from unittest.mock import patch, MagicMock

# Add agents directory to path
agents_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, agents_dir)

from critique_agent import (
    analyze_critique,
    critique_with_logging,
    log_to_database,
    CritiqueResponse,
    RedFlag,
    Severity,
    RiskLevel
)


@pytest.fixture
def sample_score_report():
    """Sample scoring report from scoring_agent"""
    return {
        "startup_name": "Test Startup",
        "venture_lens_score": 7.5,
        "breakdown": {
            "market": {
                "score": 15.5,
                "reasoning": "Large market opportunity"
            },
            "product": {
                "score": 14.0,
                "reasoning": "Innovative solution"
            },
            "team": {
                "score": 12.0,
                "reasoning": "Experienced team but missing key roles"
            },
            "traction": {
                "score": 10.0,
                "reasoning": "Early traction but revenue still low"
            },
            "risk": {
                "score": 13.0,
                "reasoning": "Moderate risk factors"
            }
        }
    }


@pytest.fixture
def sample_pitchdeck_summary():
    """Sample pitch deck summary text"""
    return "This is a fintech startup focused on payment solutions. The pitch deck covers problem, solution, and market opportunity, but lacks detailed financial projections and competitive analysis."


@pytest.fixture
def valid_critique_response():
    """Valid critique response JSON"""
    return {
        "red_flags": [
            {
                "issue": "Low traction score (10.0/20) indicates weak product-market fit",
                "severity": "Medium",
                "reason": "Early traction is limited with low revenue, suggesting market validation is incomplete"
            },
            {
                "issue": "Team missing key business roles",
                "severity": "Low",
                "reason": "Technical team is strong but lacks business development expertise"
            },
            {
                "issue": "Pitch deck lacks financial projections",
                "severity": "Medium",
                "reason": "Missing financial forecasts makes it difficult to assess business model viability"
            },
            {
                "issue": "Competitive analysis incomplete",
                "severity": "Low",
                "reason": "Limited understanding of competitive landscape could indicate market research gaps"
            }
        ],
        "overall_risk_level": "Moderate",
        "summary": "The startup shows promise in market opportunity and product innovation, but faces challenges in traction and team completeness. The moderate risk level reflects both strengths and areas requiring attention before investment consideration."
    }


def test_red_flag_model():
    """Test RedFlag Pydantic model"""
    flag = RedFlag(
        issue="Test issue",
        severity=Severity.HIGH,
        reason="Test reason"
    )
    
    assert flag.issue == "Test issue"
    assert flag.severity == Severity.HIGH
    assert flag.reason == "Test reason"


def test_critique_response_model_valid():
    """Test CritiqueResponse with valid 3-5 red flags"""
    response = CritiqueResponse(
        red_flags=[
            RedFlag(issue="Issue 1", severity=Severity.LOW, reason="Reason 1"),
            RedFlag(issue="Issue 2", severity=Severity.MEDIUM, reason="Reason 2"),
            RedFlag(issue="Issue 3", severity=Severity.HIGH, reason="Reason 3")
        ],
        overall_risk_level=RiskLevel.MODERATE,
        summary="Test summary"
    )
    
    assert len(response.red_flags) == 3
    assert response.overall_risk_level == RiskLevel.MODERATE


def test_critique_response_model_too_few():
    """Test CritiqueResponse validation fails with < 3 red flags"""
    with pytest.raises(ValueError, match="Must have 3-5 red flags"):
        CritiqueResponse(
            red_flags=[
                RedFlag(issue="Issue 1", severity=Severity.LOW, reason="Reason 1"),
                RedFlag(issue="Issue 2", severity=Severity.MEDIUM, reason="Reason 2")
            ],
            overall_risk_level=RiskLevel.LOW,
            summary="Test"
        )


def test_critique_response_model_too_many():
    """Test CritiqueResponse validation fails with > 5 red flags"""
    with pytest.raises(ValueError, match="Must have 3-5 red flags"):
        CritiqueResponse(
            red_flags=[
                RedFlag(issue=f"Issue {i}", severity=Severity.LOW, reason=f"Reason {i}")
                for i in range(6)
            ],
            overall_risk_level=RiskLevel.HIGH,
            summary="Test"
        )


def test_severity_enum():
    """Test Severity enum values"""
    assert Severity.LOW.value == "Low"
    assert Severity.MEDIUM.value == "Medium"
    assert Severity.HIGH.value == "High"


def test_risk_level_enum():
    """Test RiskLevel enum values"""
    assert RiskLevel.LOW.value == "Low"
    assert RiskLevel.MODERATE.value == "Moderate"
    assert RiskLevel.HIGH.value == "High"


@pytest.mark.asyncio
async def test_analyze_critique_valid_json(sample_score_report, sample_pitchdeck_summary, valid_critique_response):
    """Test that analyze_critique returns valid JSON with 3-5 red flags"""
    
    # Mock the LLM service
    mock_service = MagicMock()
    mock_service.invoke = MagicMock(return_value=json.dumps(valid_critique_response))
    
    with patch('critique_agent.get_service', return_value=mock_service):
        result = await analyze_critique(sample_score_report, sample_pitchdeck_summary)
    
    # Verify structure
    assert "red_flags" in result
    assert isinstance(result["red_flags"], list)
    assert 3 <= len(result["red_flags"]) <= 5
    
    # Verify each red flag has required fields
    for flag in result["red_flags"]:
        assert "issue" in flag
        assert "severity" in flag
        assert "reason" in flag
        assert flag["severity"] in ["Low", "Medium", "High"]
    
    # Verify overall risk level
    assert "overall_risk_level" in result
    assert result["overall_risk_level"] in ["Low", "Moderate", "High"]
    
    # Verify summary
    assert "summary" in result
    assert isinstance(result["summary"], str)
    assert len(result["summary"]) > 0


@pytest.mark.asyncio
async def test_analyze_critique_exactly_3_flags(sample_score_report, sample_pitchdeck_summary):
    """Test that exactly 3 red flags are valid"""
    response_3_flags = {
        "red_flags": [
            {"issue": "Issue 1", "severity": "Low", "reason": "Reason 1"},
            {"issue": "Issue 2", "severity": "Medium", "reason": "Reason 2"},
            {"issue": "Issue 3", "severity": "High", "reason": "Reason 3"}
        ],
        "overall_risk_level": "Moderate",
        "summary": "Test summary"
    }
    
    mock_service = MagicMock()
    mock_service.invoke = MagicMock(return_value=json.dumps(response_3_flags))
    
    with patch('critique_agent.get_service', return_value=mock_service):
        result = await analyze_critique(sample_score_report, sample_pitchdeck_summary)
    
    assert len(result["red_flags"]) == 3


@pytest.mark.asyncio
async def test_analyze_critique_exactly_5_flags(sample_score_report, sample_pitchdeck_summary):
    """Test that exactly 5 red flags are valid"""
    response_5_flags = {
        "red_flags": [
            {"issue": f"Issue {i}", "severity": "Low", "reason": f"Reason {i}"}
            for i in range(5)
        ],
        "overall_risk_level": "High",
        "summary": "Test summary"
    }
    
    mock_service = MagicMock()
    mock_service.invoke = MagicMock(return_value=json.dumps(response_5_flags))
    
    with patch('critique_agent.get_service', return_value=mock_service):
        result = await analyze_critique(sample_score_report, sample_pitchdeck_summary)
    
    assert len(result["red_flags"]) == 5


@pytest.mark.asyncio
async def test_analyze_critique_invalid_json_raises_error(sample_score_report, sample_pitchdeck_summary):
    """Test that invalid JSON raises an error"""
    mock_service = MagicMock()
    mock_service.invoke = MagicMock(return_value="Invalid JSON content")
    
    with patch('critique_agent.get_service', return_value=mock_service):
        with pytest.raises(Exception, match="Failed to parse JSON"):
            await analyze_critique(sample_score_report, sample_pitchdeck_summary)


@pytest.mark.asyncio
async def test_analyze_critique_invalid_schema_raises_error(sample_score_report, sample_pitchdeck_summary):
    """Test that invalid schema (missing fields) raises validation error"""
    invalid_response = {
        "red_flags": [
            {"issue": "Issue 1"}  # Missing severity and reason
        ],
        "overall_risk_level": "Moderate"
        # Missing summary
    }
    
    mock_service = MagicMock()
    mock_service.invoke = MagicMock(return_value=json.dumps(invalid_response))
    
    with patch('critique_agent.get_service', return_value=mock_service):
        with pytest.raises(Exception, match="Response validation failed"):
            await analyze_critique(sample_score_report, sample_pitchdeck_summary)


@pytest.mark.asyncio
async def test_log_to_database_success():
    """Test successful database logging"""
    mock_conn = MagicMock()
    mock_conn.execute = MagicMock()
    
    # Mock async close method
    async def mock_close():
        pass
    mock_conn.close = mock_close
    
    with patch('critique_agent.asyncpg') as mock_asyncpg:
        # Mock asyncpg.connect to return a connection
        async def mock_connect(url):
            return mock_conn
        mock_asyncpg.connect = mock_connect
        
        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"
        
        result = await log_to_database("startup123", "Moderate", ["Issue 1", "Issue 2"])
        
        assert result is True
        assert mock_conn.execute.call_count >= 2  # CREATE TABLE + INSERT


@pytest.mark.asyncio
async def test_log_to_database_no_config():
    """Test that logging gracefully handles missing database config"""
    # Remove database URL if present
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]
    if "POSTGRES_URL" in os.environ:
        del os.environ["POSTGRES_URL"]
    
    result = await log_to_database("startup123", "Moderate", ["Issue 1"])
    
    assert result is False


@pytest.mark.asyncio
async def test_critique_with_logging(sample_score_report, sample_pitchdeck_summary, valid_critique_response):
    """Test critique_with_logging combines analysis and database logging"""
    mock_service = MagicMock()
    mock_service.invoke = MagicMock(return_value=json.dumps(valid_critique_response))
    
    with patch('critique_agent.get_service', return_value=mock_service):
        with patch('critique_agent.log_to_database', return_value=True) as mock_log:
            result = await critique_with_logging(
                sample_score_report,
                sample_pitchdeck_summary,
                startup_id="test123"
            )
            
            # Verify critique result
            assert "red_flags" in result
            assert len(result["red_flags"]) >= 3
            
            # Verify database logging was called
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][0] == "test123"
            assert call_args[0][1] in ["Low", "Moderate", "High"]
            assert isinstance(call_args[0][2], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
