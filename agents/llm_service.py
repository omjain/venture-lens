"""
LLM Service for Venture Lens
Provides unified interface to call Gemini/Vertex AI models
"""
import os
from typing import Optional, Dict, Any
import httpx
import json
from dotenv import load_dotenv

# Load environment variables (look in parent directory for .env file)
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)
# Also try loading from current directory
load_dotenv()


class LLMService:
    """Service for invoking LLM models (Gemini/Vertex AI)"""
    
    def __init__(self):
        self.project_id = os.getenv("GEMINI_PROJECT_ID")
        self.location = os.getenv("GEMINI_LOCATION", "us-central1")
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.use_vertex_ai = bool(self.project_id and self.location)
    
    async def invoke(
        self,
        prompt: str,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Invoke LLM model with given prompt
        
        Args:
            prompt: The user prompt
            model: Model name (default: gemini-1.5-pro)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum output tokens
            system_prompt: Optional system prompt
            
        Returns:
            LLM response text
        """
        try:
            # Check if we have credentials for Vertex AI (need service account too)
            has_vertex_creds = (
                self.use_vertex_ai and 
                (os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON"))
            )
            
            # Check if API key is valid Gemini format (starts with AIza...)
            is_valid_gemini_key = self.api_key and self.api_key.startswith("AIza")
            
            # Prefer API key if available and valid format (simpler authentication)
            if is_valid_gemini_key:
                print("✅ Using Gemini API Key (Google AI Studio)")
                return await self._invoke_gemini_api(prompt, model, temperature, max_tokens, system_prompt)
            elif has_vertex_creds:
                print("✅ Using Vertex AI")
                return await self._invoke_vertex_ai(prompt, model, temperature, max_tokens, system_prompt)
            elif self.api_key:
                # Invalid API key format - try Vertex AI if credentials available
                print(f"⚠️ API key format invalid (starts with {self.api_key[:5]}...). Expected Gemini API key (starts with AIza...)")
                print("   Attempting Vertex AI if credentials available...")
                if self.use_vertex_ai:
                    try:
                        return await self._invoke_vertex_ai(prompt, model, temperature, max_tokens, system_prompt)
                    except Exception as ve:
                        print(f"⚠️ Vertex AI also failed: {ve}")
                print("⚠️ Using mock response - Please set valid GEMINI_API_KEY (starts with AIza...) or configure Vertex AI")
                return self._mock_response(prompt)
            else:
                # Fallback: return mock response
                print("⚠️ NO CREDENTIALS - Using mock response")
                return self._mock_response(prompt)
        except Exception as e:
            print(f"⚠️ LLM invocation failed: {e}, using fallback")
            return self._mock_response(prompt)
    
    async def _invoke_vertex_ai(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str]
    ) -> str:
        """Invoke Vertex AI Gemini model"""
        try:
            from google.auth import default
            from google.auth.transport.requests import Request
            
            credentials, project = default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
            credentials.refresh(Request())
            
            project_id = self.project_id or project
            location = self.location
            
            endpoint = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model}:generateContent"
            
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            
            payload = {
                "contents": [{
                    "parts": [{"text": full_prompt}]
                }],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                    "topK": 40,
                    "topP": 0.95,
                }
            }
            
            headers = {
                "Authorization": f"Bearer {credentials.token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                
                if "candidates" in result and len(result["candidates"]) > 0:
                    text_content = ""
                    for part in result["candidates"][0].get("content", {}).get("parts", []):
                        text_content += part.get("text", "")
                    return text_content.strip()
                
                raise Exception("No text content in response")
                
        except Exception as e:
            raise Exception(f"Vertex AI invocation failed: {str(e)}")
    
    async def _invoke_gemini_api(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str]
    ) -> str:
        """Invoke Gemini API (Google AI Studio)"""
        try:
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            
            # Use gemini-2.0-flash model
            api_model = "gemini-2.0-flash-exp"
            
            # Use v1 endpoint
            url = f"https://generativelanguage.googleapis.com/v1/models/{api_model}:generateContent?key={self.api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{"text": full_prompt}]
                }],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                    "topK": 40,
                    "topP": 0.95,
                }
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload)
                
                response.raise_for_status()
                result = response.json()
                
                if "candidates" in result and len(result["candidates"]) > 0:
                    text_content = ""
                    for part in result["candidates"][0].get("content", {}).get("parts", []):
                        text_content += part.get("text", "")
                    return text_content.strip()
                
                raise Exception("No text content in response")
                
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_body = e.response.json()
                error_detail = error_body.get("error", {}).get("message", str(e))
            except:
                error_detail = str(e)
            
            # Provide helpful error message
            if "403" in str(e) or "PERMISSION_DENIED" in error_detail:
                raise Exception(
                    f"Gemini API authentication failed (403). "
                    f"Please check: 1) API key is valid, 2) API key has Gemini API enabled, "
                    f"3) Model '{model}' is available for your API key tier. "
                    f"Error: {error_detail}"
                )
            else:
                raise Exception(f"Gemini API invocation failed: {error_detail}")
        except Exception as e:
            raise Exception(f"Gemini API invocation failed: {str(e)}")
    
    def _mock_response(self, prompt: str) -> str:
        """Fallback mock response"""
        return f"Mock LLM response for: {prompt[:50]}..."


# Global LLM service instance
llm_service = LLMService()

