"""
Gemini-only LLM Service for Venture Lens
Uses google-generativeai library directly with PDF support
"""
import os
import time
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("core.llm_service")

# Try importing google-generativeai
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-generativeai not installed. Install with: pip install google-generativeai")


class GeminiLLMService:
    """Gemini-only LLM service using google-generativeai library"""
    
    def __init__(self):
        """Initialize the service with API key from environment"""
        if not GENAI_AVAILABLE:
            raise ImportError(
                "google-generativeai is not installed. "
                "Please install it with: pip install google-generativeai"
            )
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is not set. "
                "Please set it in your .env file or environment."
            )
        
        # Configure the API key
        genai.configure(api_key=api_key)
        logger.info("✅ Gemini LLM service initialized")
    
    def invoke(
        self,
        model: str,
        prompt: str,
        pdf_bytes: Optional[bytes] = None
    ) -> str:
        """
        Invoke Gemini model with prompt and optionally PDF
        
        Args:
            model: Gemini model name (e.g., "gemini-1.5-pro", "gemini-2.0-flash")
                   Note: v1beta API maps older model names to "gemini-2.0-flash-exp"
            prompt: Text prompt for the model
            pdf_bytes: Optional PDF file bytes to include in the request
            
        Returns:
            Response text from the model
            
        Raises:
            Exception: If API call fails after retries
        """
        start_time = time.time()
        
        try:
            # Normalize model name - handle common variations
            # Note: v1beta API supports gemini-2.0-flash-exp, but not gemini-1.5-pro
            normalized_model = model
            model_mapping = {
                "gemini-1.5-pro": "gemini-2.0-flash-exp",  # Fallback to working model
                "gemini-1.5-flash": "gemini-2.0-flash-exp",
                "gemini-2.0-flash": "gemini-2.0-flash-exp",
                "gemini-pro": "gemini-2.0-flash-exp",
            }
            
            if normalized_model in model_mapping:
                normalized_model = model_mapping[normalized_model]
                logger.info(f"🔄 Mapped model '{model}' to '{normalized_model}' (v1beta API compatibility)")
            
            # Create the generative model
            generative_model = genai.GenerativeModel(normalized_model)
            
            # Prepare content: text prompt + optional PDF
            if pdf_bytes:
                logger.info(f"🤖 Calling Gemini API (model={normalized_model}, with PDF, size={len(pdf_bytes)} bytes)")
                content = [
                    prompt,
                    {
                        "mime_type": "application/pdf",
                        "data": pdf_bytes
                    }
                ]
            else:
                logger.info(f"🤖 Calling Gemini API (model={normalized_model}, text only)")
                content = prompt
            
            # Retry logic for quota and timeout errors
            max_retries = 3
            retry_delay = 2  # seconds
            
            for attempt in range(max_retries):
                try:
                    # Generate content
                    response = generative_model.generate_content(content)
                    
                    # Extract text from response
                    if hasattr(response, 'text') and response.text:
                        text = response.text
                    elif hasattr(response, 'candidates') and len(response.candidates) > 0:
                        # Fallback: extract from candidates
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content'):
                            parts = candidate.content.parts
                            if parts and len(parts) > 0:
                                text = parts[0].text
                            else:
                                text = str(response)
                        else:
                            text = str(response)
                    else:
                        text = str(response)
                    
                    # Log success
                    duration = time.time() - start_time
                    logger.info(f"✅ Gemini API call successful (duration={duration:.2f}s, model={normalized_model})")
                    return text
                    
                except Exception as e:
                    error_type = type(e).__name__
                    error_msg = str(e)
                    
                    # Check for quota or timeout errors
                    is_quota_error = (
                        "quota" in error_msg.lower() or
                        "QuotaExceeded" in error_type or
                        "ResourceExhausted" in error_type or
                        "429" in error_msg
                    )
                    
                    is_timeout_error = (
                        "timeout" in error_msg.lower() or
                        "Timeout" in error_type or
                        "504" in error_msg or
                        "408" in error_msg
                    )
                    
                    # Handle retryable errors
                    if (is_quota_error or is_timeout_error) and attempt < max_retries - 1:
                        retry_num = attempt + 1
                        logger.warning(
                            f"⚠️ Gemini API error ({error_type}): {error_msg}. "
                            f"Retrying ({retry_num}/{max_retries}) after {retry_delay}s..."
                        )
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        # Non-retryable error or max retries reached
                        duration = time.time() - start_time
                        logger.error(
                            f"❌ Gemini API call failed after {attempt + 1} attempts "
                            f"(duration={duration:.2f}s, error={error_type}): {error_msg}"
                        )
                        raise Exception(f"Gemini API call failed: {error_type}: {error_msg}")
        
        except Exception as e:
            # Catch any unexpected errors
            duration = time.time() - start_time
            logger.error(f"❌ Unexpected error in Gemini API call (duration={duration:.2f}s): {str(e)}")
            raise
    
    async def invoke_async(
        self,
        model: str,
        prompt: str,
        pdf_bytes: Optional[bytes] = None
    ) -> str:
        """
        Async version of invoke (for compatibility with async code)
        
        Args:
            model: Gemini model name
            prompt: Text prompt for the model
            pdf_bytes: Optional PDF file bytes
            
        Returns:
            Response text from the model
        """
        # For now, run sync invoke in executor if needed
        # google-generativeai is synchronous, but we can wrap it
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.invoke, model, prompt, pdf_bytes)


# Global service instance (lazy initialization)
_service_instance: Optional[GeminiLLMService] = None


def get_service() -> GeminiLLMService:
    """Get or create global service instance"""
    global _service_instance
    if _service_instance is None:
        _service_instance = GeminiLLMService()
    return _service_instance


def invoke(model: str, prompt: str, pdf_bytes: Optional[bytes] = None) -> str:
    """
    Convenience function for invoking Gemini model
    
    Args:
        model: Gemini model name
        prompt: Text prompt
        pdf_bytes: Optional PDF bytes
        
    Returns:
        Response text
    """
    service = get_service()
    return service.invoke(model, prompt, pdf_bytes)


async def invoke_async(model: str, prompt: str, pdf_bytes: Optional[bytes] = None) -> str:
    """
    Async convenience function for invoking Gemini model
    
    Args:
        model: Gemini model name
        prompt: Text prompt
        pdf_bytes: Optional PDF bytes
        
    Returns:
        Response text
    """
    service = get_service()
    return await service.invoke_async(model, prompt, pdf_bytes)

