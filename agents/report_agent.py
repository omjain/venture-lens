"""
Gemini-powered Report Generator for Venture Lens
Generates professional PDF reports using Jinja2 + pdfkit with AI-generated commentary
"""
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
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
logger = logging.getLogger("report_agent")

# Jinja2 template for report
REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Venture Lens Evaluation Report - {{ startup_name }}</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px;
            background: #fff;
        }
        .header {
            border-bottom: 3px solid #2563eb;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #2563eb;
            margin: 0;
            font-size: 28px;
        }
        .header .subtitle {
            color: #666;
            margin-top: 5px;
        }
        .section {
            margin: 30px 0;
            page-break-inside: avoid;
        }
        .section h2 {
            color: #1e40af;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 10px;
            margin-bottom: 15px;
            font-size: 20px;
        }
        .score-box {
            background: #f0f9ff;
            border-left: 4px solid #2563eb;
            padding: 15px;
            margin: 15px 0;
        }
        .score-value {
            font-size: 32px;
            font-weight: bold;
            color: #2563eb;
        }
        .breakdown {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin: 20px 0;
        }
        .breakdown-item {
            background: #f9fafb;
            padding: 15px;
            border-radius: 5px;
        }
        .breakdown-item .metric {
            font-weight: bold;
            color: #1e40af;
        }
        .breakdown-item .value {
            font-size: 18px;
            color: #2563eb;
        }
        .red-flag {
            background: #fef2f2;
            border-left: 4px solid #dc2626;
            padding: 12px;
            margin: 10px 0;
        }
        .red-flag .severity {
            font-weight: bold;
            color: #dc2626;
        }
        .comparison-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        .comparison-table th, .comparison-table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }
        .comparison-table th {
            background: #f3f4f6;
            font-weight: bold;
            color: #1e40af;
        }
        .narrative-box {
            background: #f0fdf4;
            border-left: 4px solid #16a34a;
            padding: 15px;
            margin: 15px 0;
        }
        .highlight {
            background: #fef3c7;
            padding: 2px 5px;
            border-radius: 3px;
        }
        .footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            text-align: center;
            color: #666;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Venture Lens Evaluation Report</h1>
        <div class="subtitle">{{ startup_name }}</div>
        <div class="subtitle">Generated: {{ generated_date }}</div>
    </div>

    <div class="section">
        <h2>Executive Summary</h2>
        <div class="score-box">
            <div>Venture Lens Score</div>
            <div class="score-value">{{ venture_lens_score }}/10</div>
            <div style="margin-top: 10px;">Overall Position: <span class="highlight">{{ overall_position }}</span></div>
        </div>
        <p>{{ executive_summary }}</p>
    </div>

    <div class="section">
        <h2>Investment Thesis</h2>
        <p>{{ investment_thesis }}</p>
    </div>

    <div class="section">
        <h2>Scoring Breakdown</h2>
        <div class="breakdown">
            <div class="breakdown-item">
                <div class="metric">Market</div>
                <div class="value">{{ market_score }}/20</div>
                <div style="font-size: 12px; color: #666; margin-top: 5px;">{{ market_reasoning }}</div>
            </div>
            <div class="breakdown-item">
                <div class="metric">Product</div>
                <div class="value">{{ product_score }}/20</div>
                <div style="font-size: 12px; color: #666; margin-top: 5px;">{{ product_reasoning }}</div>
            </div>
            <div class="breakdown-item">
                <div class="metric">Team</div>
                <div class="value">{{ team_score }}/20</div>
                <div style="font-size: 12px; color: #666; margin-top: 5px;">{{ team_reasoning }}</div>
            </div>
            <div class="breakdown-item">
                <div class="metric">Traction</div>
                <div class="value">{{ traction_score }}/20</div>
                <div style="font-size: 12px; color: #666; margin-top: 5px;">{{ traction_reasoning }}</div>
            </div>
            <div class="breakdown-item">
                <div class="metric">Risk</div>
                <div class="value">{{ risk_score }}/20</div>
                <div style="font-size: 12px; color: #666; margin-top: 5px;">{{ risk_reasoning }}</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Startup Narrative</h2>
        <div class="narrative-box">
            <p><strong>Vision:</strong> {{ vision }}</p>
            <p><strong>Differentiation:</strong> {{ differentiation }}</p>
            <p><strong>Timing:</strong> {{ timing }}</p>
            <p style="margin-top: 15px; font-style: italic;"><strong>Tagline:</strong> "{{ tagline }}"</p>
        </div>
    </div>

    {% if red_flags %}
    <div class="section">
        <h2>Risk Analysis & Red Flags</h2>
        <p><strong>Overall Risk Level:</strong> <span class="highlight">{{ risk_level }}</span></p>
        <p>{{ risk_summary }}</p>
        {% for flag in red_flags %}
        <div class="red-flag">
            <div class="severity">{{ flag.severity }} Severity</div>
            <div><strong>{{ flag.issue }}</strong></div>
            <div style="margin-top: 5px; font-size: 14px;">{{ flag.reason }}</div>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    {% if comparisons %}
    <div class="section">
        <h2>Benchmark Analysis</h2>
        <p><strong>Industry:</strong> {{ industry }}</p>
        <p><strong>Overall Position:</strong> <span class="highlight">{{ overall_position }}</span></p>
        <table class="comparison-table">
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Startup Value</th>
                    <th>Sector Average</th>
                    <th>Percentile</th>
                    <th>Insight</th>
                </tr>
            </thead>
            <tbody>
                {% for comp in comparisons %}
                <tr>
                    <td><strong>{{ comp.metric }}</strong></td>
                    <td>{{ comp.startup_value }}</td>
                    <td>{{ comp.sector_avg }}</td>
                    <td>{{ comp.percentile }}%</td>
                    <td>{{ comp.insight }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% endif %}

    <div class="section">
        <h2>Final Recommendation</h2>
        <p><strong>{{ recommendation }}</strong></p>
    </div>

    <div class="section">
        <h2>Key Highlights</h2>
        <ul>
            {% for highlight in key_highlights %}
            <li>{{ highlight }}</li>
            {% endfor %}
        </ul>
    </div>

    <div class="footer">
        <p>This report was generated by Venture Lens AI Evaluation System</p>
        <p>Report ID: {{ report_id }} | Generated: {{ generated_date }}</p>
    </div>
</body>
</html>
"""


def ensure_reports_directory():
    """Ensure /reports directory exists"""
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    return reports_dir


async def generate_ai_commentary(
    startup_data: Dict[str, Any],
    scores: Dict[str, Any],
    critique: Dict[str, Any],
    narrative: Dict[str, Any],
    benchmarks: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate AI-powered commentary sections using Gemini
    
    Args:
        startup_data: Structured startup data
        scores: Scoring report
        critique: Critique analysis
        narrative: Narrative
        benchmarks: Benchmark analysis
        
    Returns:
        Dictionary with executive_summary, investment_thesis, risk_summary, recommendation, key_highlights
    """
    if not CORE_LLM_AVAILABLE:
        raise ImportError(
            "Core LLM service not available. "
            "Please ensure core/llm_service.py exists and google-generativeai is installed."
        )
    
    startup_name = startup_data.get("startup_name") or startup_data.get("name") or "Unnamed Startup"
    
    # Prepare comprehensive context
    context = {
        "startup": startup_name,
        "venture_lens_score": scores.get("venture_lens_score", "N/A"),
        "overall_position": benchmarks.get("overall_position", "N/A"),
        "risk_level": critique.get("overall_risk_level", "N/A"),
        "red_flags_count": len(critique.get("red_flags", [])),
        "scores_breakdown": scores.get("breakdown", {}),
        "narrative": narrative,
        "benchmarks": benchmarks.get("comparisons", [])[:3]  # Top 3 for summary
    }
    
    prompt = f"""You are an investment analyst generating a comprehensive evaluation report for a startup.

EVALUATION SUMMARY:
Startup: {startup_name}
Venture Lens Score: {scores.get("venture_lens_score", "N/A")}/10
Overall Position: {benchmarks.get("overall_position", "N/A")}
Risk Level: {critique.get("overall_risk_level", "N/A")}
Red Flags: {len(critique.get("red_flags", []))}

Generate a comprehensive executive summary report (2-3 paragraphs) that synthesizes:
1. Overall investment thesis
2. Key strengths and opportunities
3. Primary risks and concerns
4. Benchmark positioning
5. Final recommendation

Keep it concise, investor-focused, and actionable.

Respond ONLY with valid JSON in this exact format:
{{
  "executive_summary": "Comprehensive 2-3 paragraph summary of the evaluation...",
  "key_highlights": [
    "Highlight 1",
    "Highlight 2"
  ],
  "investment_thesis": "Why this could be a good/bad investment...",
  "risk_summary": "Summary of main risks...",
  "recommendation": "Final recommendation with next steps"
}}"""

    try:
        logger.info("🤖 Calling Gemini 1.5 Pro for AI commentary generation")
        
        llm_service = get_service()
        
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
        json_text = response_text.strip()
        
        if "```json" in json_text:
            json_start = json_text.find("```json") + 7
            json_end = json_text.find("```", json_start)
            json_text = json_text[json_start:json_end].strip()
        elif "```" in json_text:
            json_start = json_text.find("```") + 3
            json_end = json_text.find("```", json_start)
            json_text = json_text[json_start:json_end].strip()
        
        commentary = json.loads(json_text)
        
        logger.info("✅ Successfully parsed AI commentary")
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Failed to parse JSON response: {e}")
        raise Exception(f"Failed to parse JSON response: {str(e)}")
    
    return commentary


def generate_pdf_from_html(
    html_content: str,
    output_path: str
) -> str:
    """
    Generate PDF from HTML using pdfkit
    
    Args:
        html_content: HTML content string
        output_path: Path where PDF should be saved
        
    Returns:
        Path to generated PDF
    """
    try:
        import pdfkit
        
        # Configure pdfkit options
        options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None
        }
        
        # Generate PDF
        pdfkit.from_string(html_content, output_path, options=options)
        
        logger.info(f"✅ PDF generated successfully: {output_path}")
        return output_path
        
    except ImportError:
        raise ImportError(
            "pdfkit is not installed. Please install with: pip install pdfkit\n"
            "Also install wkhtmltopdf binary:\n"
            "  - Windows: Download from https://wkhtmltopdf.org/downloads.html\n"
            "  - macOS: brew install wkhtmltopdf\n"
            "  - Linux: sudo apt-get install wkhtmltopdf"
        )
    except Exception as e:
        logger.error(f"❌ PDF generation failed: {e}")
        raise Exception(f"Failed to generate PDF: {str(e)}")


def create_signed_url(file_path: str, base_url: str = "http://localhost:8000") -> str:
    """
    Create a download URL for the PDF
    
    Args:
        file_path: Path to PDF file
        base_url: Base URL for the API server
        
    Returns:
        Download URL (signed URLs would be added in production)
    """
    # Extract report_id from file path (e.g., "reports/startup-123.pdf" -> "startup-123")
    filename = os.path.basename(file_path)
    report_id = os.path.splitext(filename)[0]  # Remove .pdf extension
    
    # For local development, return direct download endpoint
    # In production, you would:
    # 1. Use cloud storage (S3, GCS) with signed URLs
    # 2. Add authentication/signing for security
    download_url = f"{base_url}/reports/{report_id}"
    
    return download_url


async def generate(
    startup_data: Dict[str, Any],
    scores: Dict[str, Any],
    critique: Dict[str, Any],
    narrative: Dict[str, Any],
    benchmarks: Dict[str, Any],
    startup_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate comprehensive PDF report with AI-generated commentary
    
    Args:
        startup_data: Structured startup data from ingestion agent
        scores: Scoring report from scoring_agent
        critique: Critique analysis from critique_agent
        narrative: Narrative from narrative_agent
        benchmarks: Benchmark analysis from benchmark_agent
        startup_id: Optional startup identifier for file naming
        
    Returns:
        Report metadata with report_url (signed download URL)
    """
    logger.info("📄 Generating comprehensive PDF report")
    
    startup_name = startup_data.get("startup_name") or startup_data.get("name") or "Unnamed Startup"
    
    # Generate startup_id if not provided
    if not startup_id:
        startup_id = f"{startup_name.lower().replace(' ', '-').replace('/', '-')}-{datetime.now().strftime('%Y%m%d')}"
    
    # Step 1: Generate AI commentary
    try:
        commentary = await generate_ai_commentary(
            startup_data,
            scores,
            critique,
            narrative,
            benchmarks
        )
    except Exception as e:
        logger.error(f"❌ AI commentary generation failed: {e}")
        # Use fallback commentary
        commentary = {
            "executive_summary": f"Evaluation report for {startup_name}. Comprehensive analysis across multiple dimensions.",
            "key_highlights": [
                f"Venture Lens Score: {scores.get('venture_lens_score', 'N/A')}/10",
                f"Risk Level: {critique.get('overall_risk_level', 'N/A')}"
            ],
            "investment_thesis": "Detailed investment thesis requires LLM analysis.",
            "risk_summary": f"Identified {len(critique.get('red_flags', []))} red flags requiring attention.",
            "recommendation": "Further analysis recommended."
        }
    
    # Step 2: Prepare template context
    try:
        from jinja2 import Template
        
        # Extract scores breakdown
        breakdown = scores.get("breakdown", {})
        market_data = breakdown.get("market", {})
        product_data = breakdown.get("product", {})
        team_data = breakdown.get("team", {})
        traction_data = breakdown.get("traction", {})
        risk_data = breakdown.get("risk", {})
        
        template_context = {
            "startup_name": startup_name,
            "generated_date": datetime.now().strftime("%B %d, %Y"),
            "venture_lens_score": scores.get("venture_lens_score", "N/A"),
            "overall_position": benchmarks.get("overall_position", "N/A"),
            "executive_summary": commentary.get("executive_summary", ""),
            "investment_thesis": commentary.get("investment_thesis", ""),
            "risk_summary": commentary.get("risk_summary", ""),
            "recommendation": commentary.get("recommendation", ""),
            "key_highlights": commentary.get("key_highlights", []),
            "market_score": market_data.get("score", "N/A"),
            "market_reasoning": market_data.get("reasoning", ""),
            "product_score": product_data.get("score", "N/A"),
            "product_reasoning": product_data.get("reasoning", ""),
            "team_score": team_data.get("score", "N/A"),
            "team_reasoning": team_data.get("reasoning", ""),
            "traction_score": traction_data.get("score", "N/A"),
            "traction_reasoning": traction_data.get("reasoning", ""),
            "risk_score": risk_data.get("score", "N/A"),
            "risk_reasoning": risk_data.get("reasoning", ""),
            "vision": narrative.get("vision", ""),
            "differentiation": narrative.get("differentiation", ""),
            "timing": narrative.get("timing", ""),
            "tagline": narrative.get("tagline", ""),
            "red_flags": critique.get("red_flags", []),
            "risk_level": critique.get("overall_risk_level", "N/A"),
            "industry": benchmarks.get("industry", "N/A"),
            "comparisons": benchmarks.get("comparisons", []),
            "report_id": startup_id
        }
        
        logger.info("✅ Template context prepared")
        
    except ImportError:
        raise ImportError(
            "jinja2 is not installed. Please install with: pip install jinja2"
        )
    except Exception as e:
        logger.error(f"❌ Template context preparation failed: {e}")
        raise
    
    # Step 3: Render HTML template
    try:
        template = Template(REPORT_TEMPLATE)
        html_content = template.render(**template_context)
        
        logger.info("✅ HTML template rendered")
        
    except Exception as e:
        logger.error(f"❌ HTML template rendering failed: {e}")
        raise Exception(f"Failed to render HTML template: {str(e)}")
    
    # Step 4: Generate PDF
    try:
        # Ensure reports directory exists
        reports_dir = ensure_reports_directory()
        
        # Generate PDF path
        pdf_filename = f"{startup_id}.pdf"
        pdf_path = reports_dir / pdf_filename
        
        # Generate PDF
        generate_pdf_from_html(html_content, str(pdf_path))
        
        logger.info(f"✅ PDF generated: {pdf_path}")
        
    except Exception as e:
        logger.error(f"❌ PDF generation failed: {e}")
        raise Exception(f"Failed to generate PDF: {str(e)}")
    
    # Step 5: Create signed download URL
    try:
        download_url = create_signed_url(str(pdf_path))
        
        logger.info(f"✅ Download URL created: {download_url}")
        
    except Exception as e:
        logger.error(f"❌ URL creation failed: {e}")
        # Still return the path even if URL creation fails
        download_url = f"/reports/{pdf_filename}"
    
    # Return report metadata
    result = {
        "report_id": startup_id,
        "report_url": download_url,
        "pdf_path": str(pdf_path),
        "generated_at": datetime.utcnow().isoformat(),
        "executive_summary": commentary.get("executive_summary", ""),
        "key_highlights": commentary.get("key_highlights", []),
        "investment_thesis": commentary.get("investment_thesis", ""),
        "risk_summary": commentary.get("risk_summary", ""),
        "recommendation": commentary.get("recommendation", ""),
        "_metadata": {
            "source": "core_llm_service",
            "model": "gemini-1.5-pro"
        }
    }
    
    logger.info(f"✅ Report generation complete: {download_url}")
    return result
