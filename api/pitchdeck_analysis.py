"""
Pitch Deck Analysis Module
Uses LangChain's UnstructuredPDFLoader to analyze pitch deck PDFs
"""
from typing import Dict, List, Any
import os
import json
import httpx

# Standard pitch deck slide types
STANDARD_SLIDE_TYPES = [
    "Title",
    "Problem",
    "Solution",
    "Market Opportunity",
    "Product/Service",
    "Business Model",
    "Traction",
    "Team",
    "Competition",
    "Financial Projections",
    "Funding Ask",
    "Roadmap",
    "Contact"
]


def segment_slides(content: str) -> List[Dict[str, Any]]:
    """
    Segment PDF content into individual slides
    Uses page breaks and formatting cues to identify slide boundaries
    """
    slides = []
    
    # Split by common slide separators (page breaks, large gaps, etc.)
    # For PDFs loaded with LangChain, content may be structured by pages
    pages = content.split('\n\n\n')  # Triple newline often indicates page break
    
    if len(pages) == 1:
        # Try other separators
        pages = content.split('\f')  # Form feed character (page break)
    
    if len(pages) == 1:
        # Fallback: split by double newlines and chunk by length
        paragraphs = content.split('\n\n')
        current_slide = []
        current_length = 0
        
        for para in paragraphs:
            para_length = len(para)
            # If adding this paragraph exceeds threshold, start new slide
            if current_length > 0 and current_length + para_length > 1000:
                slides.append({
                    "content": '\n\n'.join(current_slide),
                    "page_number": len(slides) + 1
                })
                current_slide = [para]
                current_length = para_length
            else:
                current_slide.append(para)
                current_length += para_length
        
        if current_slide:
            slides.append({
                "content": '\n\n'.join(current_slide),
                "page_number": len(slides) + 1
            })
    else:
        # Content already segmented by pages
        for idx, page in enumerate(pages, 1):
            if page.strip():
                slides.append({
                    "content": page.strip(),
                    "page_number": idx
                })
    
    return slides


async def classify_slide(content: str, llm_available: bool = True) -> Dict[str, Any]:
    """
    Classify a slide using LLM to determine its type
    Returns classification with confidence
    """
    try:
        if llm_available:
            # Try to use LLM for classification
            classification_prompt = f"""Analyze this pitch deck slide content and classify it.

Content:
{content[:500]}...

Classify this slide as one of these types:
- Title
- Problem
- Solution
- Market Opportunity
- Product/Service
- Business Model
- Traction
- Team
- Competition
- Financial Projections
- Funding Ask
- Roadmap
- Contact
- Other

Respond with JSON format:
{{
    "slide_type": "Type name",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation"
}}"""

            # Call LLM (reuse Vertex AI infrastructure)
            try:
                from google.auth import default
                from google.auth.transport.requests import Request
                
                credentials, project = default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
                credentials.refresh(Request())
                
                project_id = os.getenv("GEMINI_PROJECT_ID", project)
                location = os.getenv("GEMINI_LOCATION", "us-central1")
                model_name = "gemini-2.0-flash-exp"
                
                endpoint = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model_name}:generateContent"
                
                payload = {
                    "contents": [{
                        "parts": [{"text": classification_prompt}]
                    }],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 200
                    }
                }
                
                headers = {
                    "Authorization": f"Bearer {credentials.token}",
                    "Content-Type": "application/json"
                }
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(endpoint, json=payload, headers=headers)
                    response.raise_for_status()
                    result = response.json()
                    
                    if "candidates" in result and len(result["candidates"]) > 0:
                        text_content = ""
                        for part in result["candidates"][0].get("content", {}).get("parts", []):
                            text_content += part.get("text", "")
                        
                        # Parse JSON response
                        if "```json" in text_content:
                            json_start = text_content.find("```json") + 7
                            json_end = text_content.find("```", json_start)
                            text_content = text_content[json_start:json_end].strip()
                        elif "```" in text_content:
                            json_start = text_content.find("```") + 3
                            json_end = text_content.find("```", json_start)
                            text_content = text_content[json_start:json_end].strip()
                        
                        classification = json.loads(text_content)
                        return {
                            "slide_type": classification.get("slide_type", "Other"),
                            "confidence": float(classification.get("confidence", 0.5)),
                            "reasoning": classification.get("reasoning", "")
                        }
            except Exception as e:
                print(f"⚠️ LLM classification failed, using rule-based: {e}")
        
        # Fallback: Rule-based classification
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["problem", "pain point", "challenge", "issue"]):
            slide_type = "Problem"
        elif any(word in content_lower for word in ["solution", "product", "service", "platform"]):
            slide_type = "Product/Service"
        elif any(word in content_lower for word in ["market", "opportunity", "tam", "sam", "addressable"]):
            slide_type = "Market Opportunity"
        elif any(word in content_lower for word in ["traction", "revenue", "users", "customers", "growth"]):
            slide_type = "Traction"
        elif any(word in content_lower for word in ["team", "founder", "executive", "advisory"]):
            slide_type = "Team"
        elif any(word in content_lower for word in ["competition", "competitor", "vs", "comparison"]):
            slide_type = "Competition"
        elif any(word in content_lower for word in ["financial", "revenue", "projection", "forecast", "$"]):
            slide_type = "Financial Projections"
        elif any(word in content_lower for word in ["funding", "investment", "ask", "raise", "seeking"]):
            slide_type = "Funding Ask"
        elif any(word in content_lower for word in ["roadmap", "timeline", "milestone", "future"]):
            slide_type = "Roadmap"
        elif any(word in content_lower for word in ["contact", "email", "website", "reach"]):
            slide_type = "Contact"
        elif len(content) < 200 and ("title" in content_lower or "pitch" in content_lower):
            slide_type = "Title"
        else:
            slide_type = "Other"
        
        return {
            "slide_type": slide_type,
            "confidence": 0.6,
            "reasoning": "Rule-based classification"
        }
        
    except Exception as e:
        print(f"Error classifying slide: {e}")
        return {
            "slide_type": "Other",
            "confidence": 0.3,
            "reasoning": f"Classification failed: {str(e)}"
        }


async def summarize_slide(content: str, slide_type: str, llm_available: bool = True) -> Dict[str, Any]:
    """
    Summarize a slide and extract key points
    """
    try:
        if llm_available:
            summary_prompt = f"""Summarize this {slide_type} slide from a pitch deck.

Content:
{content[:1000]}

Provide:
1. A 2-3 sentence summary
2. 3-5 key points (as a list)

Respond in JSON:
{{
    "summary": "summary text",
    "key_points": ["point1", "point2", "point3"]
}}"""

            try:
                from google.auth import default
                from google.auth.transport.requests import Request
                
                credentials, project = default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
                credentials.refresh(Request())
                
                project_id = os.getenv("GEMINI_PROJECT_ID", project)
                location = os.getenv("GEMINI_LOCATION", "us-central1")
                model_name = "gemini-2.0-flash-exp"
                
                endpoint = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model_name}:generateContent"
                
                payload = {
                    "contents": [{
                        "parts": [{"text": summary_prompt}]
                    }],
                    "generationConfig": {
                        "temperature": 0.5,
                        "maxOutputTokens": 300
                    }
                }
                
                headers = {
                    "Authorization": f"Bearer {credentials.token}",
                    "Content-Type": "application/json"
                }
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(endpoint, json=payload, headers=headers)
                    response.raise_for_status()
                    result = response.json()
                    
                    if "candidates" in result and len(result["candidates"]) > 0:
                        text_content = ""
                        for part in result["candidates"][0].get("content", {}).get("parts", []):
                            text_content += part.get("text", "")
                        
                        # Parse JSON
                        if "```json" in text_content:
                            json_start = text_content.find("```json") + 7
                            json_end = text_content.find("```", json_start)
                            text_content = text_content[json_start:json_end].strip()
                        elif "```" in text_content:
                            json_start = text_content.find("```") + 3
                            json_end = text_content.find("```", json_start)
                            text_content = text_content[json_start:json_end].strip()
                        
                        summary_data = json.loads(text_content)
                        return {
                            "summary": summary_data.get("summary", content[:200] + "..."),
                            "key_points": summary_data.get("key_points", [])
                        }
            except Exception as e:
                print(f"⚠️ LLM summarization failed, using extractive: {e}")
        
        # Fallback: Extractive summarization
        sentences = content.split('. ')
        summary = '. '.join(sentences[:3]) + '.' if len(sentences) > 3 else content[:200]
        
        # Extract key points (sentences with numbers, dates, or key phrases)
        key_points = []
        for sent in sentences[:10]:
            if any(keyword in sent.lower() for keyword in ["$", "%", "million", "billion", "users", "customers", "revenue", "growth"]):
                key_points.append(sent.strip())
            if len(key_points) >= 5:
                break
        
        if not key_points:
            key_points = [sent.strip() for sent in sentences[:3] if len(sent) > 20]
        
        return {
            "summary": summary,
            "key_points": key_points[:5]
        }
        
    except Exception as e:
        print(f"Error summarizing slide: {e}")
        return {
            "summary": content[:200] + "...",
            "key_points": []
        }


def generate_missing_slide_report(found_slide_types: List[str]) -> Dict[str, Any]:
    """
    Analyze which standard slides are missing and generate a report
    """
    found_set = set([s.lower() for s in found_slide_types])
    missing = []
    
    for slide_type in STANDARD_SLIDE_TYPES:
        # Check variations
        type_lower = slide_type.lower()
        found = False
        
        # Check if this type or a variation exists
        for found_type in found_set:
            if type_lower in found_type or found_type in type_lower:
                found = True
                break
        
        if not found and slide_type not in ["Title", "Contact"]:  # These are optional
            missing.append(slide_type)
    
    # Calculate completeness score
    essential_slides = ["Problem", "Solution", "Market Opportunity", "Product/Service", "Business Model", "Team"]
    essential_found = sum(1 for slide in essential_slides if any(slide.lower() in ft for ft in found_set))
    completeness_score = essential_found / len(essential_slides) if essential_slides else 0
    
    # Generate recommendations
    recommended = []
    if "Financial Projections" in missing:
        recommended.append("Add financial projections to demonstrate revenue potential")
    if "Traction" in missing:
        recommended.append("Include traction metrics to show validation")
    if "Competition" in missing:
        recommended.append("Add competitive analysis to show differentiation")
    if "Team" in missing:
        recommended.append("Include team slide to showcase founding team experience")
    if "Market Opportunity" in missing:
        recommended.append("Add market opportunity slide to quantify the addressable market")
    
    analysis = f"Found {len(found_slide_types)} unique slide types. "
    if missing:
        analysis += f"Missing {len(missing)} standard slides: {', '.join(missing[:5])}"
        if len(missing) > 5:
            analysis += f" and {len(missing) - 5} more."
    else:
        analysis += "All standard slides present."
    
    return {
        "missing_types": missing,
        "recommended_slides": recommended,
        "completeness_score": round(completeness_score, 2),
        "analysis": analysis
    }


async def analyze_pitchdeck(pdf_path: str) -> Dict[str, Any]:
    """
    Analyze a pitch deck PDF using LangChain's UnstructuredPDFLoader
    Segments slides, classifies each, summarizes, and returns missing-slide report
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary with analysis results including slides, classifications, summaries, and missing slide report
    """
    try:
        # Check if LangChain is available
        try:
            from langchain_community.document_loaders import UnstructuredPDFLoader
            langchain_available = True
            print("✅ Using LangChain UnstructuredPDFLoader")
        except ImportError:
            print("⚠️ LangChain not available, using fallback PDF extraction")
            langchain_available = False
        
        # Load PDF content
        content = ""
        if langchain_available:
            try:
                loader = UnstructuredPDFLoader(pdf_path)
                documents = loader.load()
                content = "\n\n".join([doc.page_content for doc in documents])
                print(f"   Loaded {len(documents)} document pages using LangChain")
            except Exception as e:
                print(f"⚠️ UnstructuredPDFLoader failed: {e}, using fallback")
                langchain_available = False
        
        if not content or not langchain_available:
            # Fallback: Use PyPDF2
            try:
                import pypdf
                content = ""
                with open(pdf_path, 'rb') as file:
                    pdf_reader = pypdf.PdfReader(file)
                    for page in pdf_reader.pages:
                        content += page.extract_text() + "\n\n"
                print(f"   Loaded PDF using PyPDF2 fallback")
            except ImportError:
                raise Exception("PyPDF2 not installed. Please install: pip install pypdf")
            except Exception as e:
                raise Exception(f"Failed to extract PDF content: {str(e)}")
        
        if not content or len(content.strip()) < 50:
            raise Exception("PDF appears to be empty or unreadable")
        
        # Step 1: Segment slides
        print(f"📄 Analyzing PDF: {pdf_path}")
        slides_data = segment_slides(content)
        print(f"   Found {len(slides_data)} slides/pages")
        
        # Step 2: Classify and summarize each slide
        slides_analysis = []
        found_slide_types = []
        
        # Check if LLM is available
        llm_available = bool(os.getenv("GEMINI_PROJECT_ID") or os.getenv("GEMINI_API_KEY"))
        
        for slide_data in slides_data:
            slide_content = slide_data["content"]
            slide_num = slide_data["page_number"]
            
            # Classify slide
            classification = await classify_slide(slide_content, llm_available)
            slide_type = classification["slide_type"]
            
            if slide_type not in found_slide_types:
                found_slide_types.append(slide_type)
            
            # Summarize slide
            summary_data = await summarize_slide(slide_content, slide_type, llm_available)
            
            slides_analysis.append({
                "slide_number": slide_num,
                "slide_type": slide_type,
                "content": slide_content[:500] + "..." if len(slide_content) > 500 else slide_content,
                "summary": summary_data["summary"],
                "key_points": summary_data["key_points"],
                "confidence": classification["confidence"]
            })
        
        # Step 3: Generate missing slide report
        missing_report = generate_missing_slide_report(found_slide_types)
        
        # Step 4: Generate overall summary
        overall_summary = f"Analyzed pitch deck with {len(slides_analysis)} slides. "
        overall_summary += f"Identified sections: {', '.join(found_slide_types[:5])}. "
        overall_summary += f"Completeness score: {missing_report['completeness_score'] * 100}%."
        
        print(f"✅ Pitch deck analysis complete: {len(slides_analysis)} slides, {len(found_slide_types)} types")
        
        return {
            "total_slides": len(slides_analysis),
            "slides": slides_analysis,
            "missing_slide_report": missing_report,
            "overall_summary": overall_summary,
            "identified_sections": found_slide_types
        }
        
    except Exception as e:
        raise Exception(f"Pitch deck analysis failed: {str(e)}")



