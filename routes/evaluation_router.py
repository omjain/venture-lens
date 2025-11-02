"""
Unified Evaluation Router for Venture Lens
Orchestrates all agents for comprehensive startup evaluation
"""
import os
import sys
import tempfile
import shutil
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import logging

# Add agents directory to path
agents_path = os.path.join(os.path.dirname(__file__), '..', 'agents')
if os.path.exists(agents_path):
    sys.path.insert(0, agents_path)

# Import agents
try:
    from ingestion_agent import ingest
    INGESTION_AGENT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Ingestion agent not available: {e}")
    INGESTION_AGENT_AVAILABLE = False

try:
    from scoring_agent import score
    SCORING_AGENT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Scoring agent not available: {e}")
    SCORING_AGENT_AVAILABLE = False

try:
    from critique_agent import analyze_critique
    CRITIQUE_AGENT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Critique agent not available: {e}")
    CRITIQUE_AGENT_AVAILABLE = False

try:
    from narrative_agent import generate_narrative
    NARRATIVE_AGENT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Narrative agent not available: {e}")
    NARRATIVE_AGENT_AVAILABLE = False

try:
    from benchmark_agent import benchmark
    BENCHMARK_AGENT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Benchmark agent not available: {e}")
    BENCHMARK_AGENT_AVAILABLE = False

try:
    from report_agent import generate as generate_report
    REPORT_AGENT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Report agent not available: {e}")
    REPORT_AGENT_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("evaluation_router")

# Create router
router = APIRouter(prefix="/evaluate", tags=["evaluation"])


class EvaluationResponse(BaseModel):
    """Response model for evaluation endpoint"""
    startup: str = Field(..., description="Startup name")
    scores: Dict[str, Any] = Field(..., description="Scoring results")
    critique: Dict[str, Any] = Field(..., description="Critique analysis")
    narrative: Dict[str, Any] = Field(..., description="Narrative generation")
    benchmarks: Dict[str, Any] = Field(..., description="Benchmark analysis")
    report_url: str = Field(..., description="URL to generated report")


@router.post("", response_model=EvaluationResponse)
async def evaluate(
    # Text input fields (all optional to support backward compatibility)
    startup_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    market: Optional[str] = Form(None),
    team: Optional[str] = Form(None),
    traction: Optional[str] = Form(None),
    # File upload (optional)
    file: Optional[UploadFile] = File(None),
    # Legacy support: URL and JSON data
    url: Optional[str] = Form(None),
    json_data: Optional[str] = Form(None)
):
    """
    Unified Evaluation Endpoint
    
    Orchestrates the complete evaluation pipeline:
    1. Ingestion (PDF or text input) → structured JSON
    2. Scoring → score report
    3. Critique → red flags and risk assessment
    4. Narrative → 3-part narrative
    5. Benchmark → peer comparison
    6. Report Generation → comprehensive report
    
    Accepts multipart/form-data with:
    - Text fields (optional): startup_name, description, market, team, traction
    - PDF file (optional): 'file' field
    - Legacy support: 'url' or 'json_data' fields
    
    If PDF is attached, it will be analyzed through Gemini.
    If no PDF, will mark "No PDF attached" and use text inputs only.
    
    Returns comprehensive evaluation with all agent outputs (format unchanged).
    """
    logger.info("🚀 Starting unified evaluation pipeline")
    
    # Phase 1: Ingestion
    logger.info("📥 Phase 1: Data Ingestion")
    if not INGESTION_AGENT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Ingestion agent not available"
        )
    
    try:
        startup_data = None
        pdf_attached = False
        
        # Handle PDF upload (optional)
        pdf_bytes = None
        pdf_filename = None
        if file:
            if not file.filename or not file.filename.lower().endswith('.pdf'):
                raise HTTPException(status_code=400, detail="File must be a PDF")
            
            logger.info(f"   Processing PDF: {file.filename}")
            pdf_bytes = await file.read()
            pdf_filename = file.filename
            pdf_attached = True
            logger.info(f"   ✓ PDF attached ({len(pdf_bytes)} bytes)")
        else:
            logger.info("   No PDF attached")
        
        # Build description from form fields if provided
        text_description = description or ""
        if market:
            text_description += f"\n\nMarket: {market}"
        if team:
            text_description += f"\n\nTeam: {team}"
        if traction:
            text_description += f"\n\nTraction: {traction}"
        
        # Determine startup name
        startup_name_value = startup_name or "Unnamed Startup"
        
        # Handle different input modes
        if pdf_bytes or text_description.strip():
            # Use ingestion agent with text + optional PDF
            from ingestion_agent import ingest_endpoint
            
            logger.info(f"   Using ingestion agent (PDF: {'Yes' if pdf_bytes else 'No'}, Text: {'Yes' if text_description.strip() else 'No'})")
            
            # Call ingest_endpoint with proper parameters
            startup_data = await ingest_endpoint(
                startup_name=startup_name_value,
                description=text_description or "Startup description not provided",
                file=pdf_bytes,
                filename=pdf_filename,
                urls=None
            )
            logger.info("   ✓ Ingestion complete")
        
        # Legacy support: Handle URL
        elif url:
            if not url.startswith(('http://', 'https://')):
                raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
            
            logger.info(f"   Processing URL: {url}")
            from ingestion_agent import ingest_endpoint
            startup_data = await ingest_endpoint(
                startup_name="Unknown Startup",
                description=f"Information from URL: {url}",
                file=None,
                filename=None,
                urls=[url]
            )
            logger.info("   ✓ URL ingestion complete")
        
        # Legacy support: Handle JSON data
        elif json_data:
            import json as json_lib
            logger.info("   Using provided JSON data")
            startup_data = json_lib.loads(json_data)
            logger.info("   ✓ JSON data loaded")
        
        else:
            raise HTTPException(
                status_code=400,
                detail="Either provide text fields (startup_name, description, etc.) with optional PDF, or provide 'url' or 'json_data'"
            )
        
        # Mark PDF status in startup_data (for logging/debugging, not changing output format)
        if startup_data:
            # Add metadata without changing response structure
            if not pdf_attached:
                logger.info("   📄 Status: No PDF attached - using text input only")
        
        if not startup_data:
            raise HTTPException(status_code=500, detail="Failed to extract startup data")
        
        startup_name_final = startup_data.get("startup_name") or startup_data.get("name") or startup_name_value or "Unnamed Startup"
        logger.info(f"   Startup: {startup_name_final}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"   ✗ Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
    
    # Phase 2: Scoring
    logger.info("📊 Phase 2: Startup Scoring")
    if not SCORING_AGENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Scoring agent not available")
    
    try:
        scores = await score(startup_data)
        logger.info(f"   ✓ Scoring complete: {scores.get('overall_score', 'N/A')}/10")
    except Exception as e:
        logger.error(f"   ✗ Scoring failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}")
    
    # Phase 3: Critique
    logger.info("🔍 Phase 3: VC Critique Analysis")
    if not CRITIQUE_AGENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Critique agent not available")
    
    try:
        # Create pitchdeck_summary from startup_data for critique
        pitchdeck_summary = {
            "startup_name": startup_name,
            "description": startup_data.get("description", ""),
            "problem": startup_data.get("problem", ""),
            "solution": startup_data.get("solution", ""),
            "missing_slides_report": "Analysis based on provided data"
        }
        
        critique = await analyze_critique(
            score_report=scores,
            pitchdeck_summary=pitchdeck_summary
        )
        logger.info(f"   ✓ Critique complete: {critique.get('overall_risk_label', 'N/A')}")
    except Exception as e:
        logger.error(f"   ✗ Critique failed: {e}")
        raise HTTPException(status_code=500, detail=f"Critique failed: {str(e)}")
    
    # Phase 4: Narrative
    logger.info("📖 Phase 4: Narrative Generation")
    if not NARRATIVE_AGENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Narrative agent not available")
    
    try:
        narrative = await generate_narrative(
            startup_data=startup_data,
            startup_id=None
        )
        logger.info("   ✓ Narrative generation complete")
    except Exception as e:
        logger.error(f"   ✗ Narrative failed: {e}")
        raise HTTPException(status_code=500, detail=f"Narrative generation failed: {str(e)}")
    
    # Phase 5: Benchmark
    logger.info("📈 Phase 5: Benchmark Analysis")
    if not BENCHMARK_AGENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Benchmark agent not available")
    
    try:
        # Prepare score_report with industry, stage, and metrics from startup_data
        benchmark_input = {
            "industry": startup_data.get("sector") or startup_data.get("industry") or "Technology",
            "stage": startup_data.get("stage") or "Seed",
            "metrics": {
                # Extract metrics from startup_data if available
                "funding": startup_data.get("funding", ""),
                "ARR": startup_data.get("revenue") or startup_data.get("ARR", ""),
                "users": startup_data.get("users") or "",
                "CAC": startup_data.get("CAC", ""),
                "LTV": startup_data.get("LTV", ""),
                "churn": startup_data.get("churn", "")
            },
            **scores  # Include scoring breakdown
        }
        
        benchmarks = await benchmark(benchmark_input)
        logger.info("   ✓ Benchmark analysis complete")
    except Exception as e:
        logger.error(f"   ✗ Benchmark failed: {e}")
        raise HTTPException(status_code=500, detail=f"Benchmark analysis failed: {str(e)}")
    
    # Phase 6: Report Generation
    logger.info("📄 Phase 6: Report Generation")
    if not REPORT_AGENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Report agent not available")
    
    try:
        # Generate startup_id from startup name
        startup_id_for_report = f"{startup_name.lower().replace(' ', '-').replace('/', '-')}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        report = await generate_report(
            startup_data=startup_data,
            scores=scores,
            critique=critique,
            narrative=narrative,
            benchmarks=benchmarks,
            startup_id=startup_id_for_report
        )
        logger.info(f"   ✓ Report generated: {report.get('report_url', 'N/A')}")
    except Exception as e:
        logger.error(f"   ✗ Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
    
    # Aggregate and return results
    logger.info("✅ Evaluation pipeline complete")
    
    return EvaluationResponse(
        startup=startup_name_final,
        scores=scores,
        critique=critique,
        narrative=narrative,
        benchmarks=benchmarks,
        report_url=report.get("report_url", "/reports/placeholder")
    )


@router.get("/reports/{report_id}")
async def download_report(report_id: str):
    """
    Download generated PDF report
    
    Args:
        report_id: Report identifier (startup_id)
        
    Returns:
        PDF file download
    """
    from pathlib import Path
    
    reports_dir = Path("reports")
    pdf_path = reports_dir / f"{report_id}.pdf"
    
    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Report not found for report_id: {report_id}"
        )
    
    return FileResponse(
        path=str(pdf_path),
        filename=f"{report_id}.pdf",
        media_type="application/pdf"
    )


@router.get("/health")
async def health_check():
    """Health check for evaluation router"""
    agent_status = {
        "ingestion": INGESTION_AGENT_AVAILABLE,
        "scoring": SCORING_AGENT_AVAILABLE,
        "critique": CRITIQUE_AGENT_AVAILABLE,
        "narrative": NARRATIVE_AGENT_AVAILABLE,
        "benchmark": BENCHMARK_AGENT_AVAILABLE,
        "report": REPORT_AGENT_AVAILABLE
    }
    
    all_available = all(agent_status.values())
    
    return {
        "status": "healthy" if all_available else "degraded",
        "agents": agent_status,
        "message": "All agents available" if all_available else "Some agents unavailable"
    }

