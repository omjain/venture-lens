"""
Test script for /score endpoint
"""
import requests
import json
import sys
import io

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

API_URL = "http://localhost:8000"

def test_score_endpoint():
    """Test the /score endpoint with sample data"""
    
    test_data = {
        "idea": """
        AI-powered platform for healthcare data analysis that helps hospitals reduce costs 
        by 30% through predictive analytics. Uses machine learning to identify patterns in 
        patient data and optimize resource allocation. Unique approach combines real-time 
        monitoring with historical data analysis.
        """,
        "team": """
        Founding team includes 2 ex-Google engineers with 10+ years ML experience, 
        1 healthcare veteran who previously built a successful healthtech startup, 
        and 1 data scientist with PhD in biostatistics. Combined experience of 35+ years 
        in healthcare and technology. Strong technical and domain expertise.
        """,
        "traction": """
        Currently have 50 paying customers (hospitals), generating $50K MRR. 
        Growing at 20% month-over-month. Signed 3 enterprise contracts in last quarter. 
        Product is proven to reduce costs by average of 28%. Customer retention rate of 95%.
        """,
        "market": """
        Healthcare analytics market is $50B+ globally and growing at 15% CAGR. 
        Large addressable market with 6,000+ hospitals in US alone. Market is fragmented 
        with no clear dominant player. Growing demand for cost reduction in healthcare 
        driven by regulatory pressures.
        """,
        "startup_name": "HealthTech AI"
    }
    
    print("[TEST] Testing /score endpoint...")
    print(f"[SEND] Sending request to {API_URL}/score\n")
    
    try:
        response = requests.post(
            f"{API_URL}/score",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        response.raise_for_status()
        
        result = response.json()
        
        print("[SUCCESS] Success! Response received:\n")
        print(json.dumps(result, indent=2))
        
        print("\n[SUMMARY]")
        print(f"   Overall Score: {result['overall_score']}/10")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Recommendation: {result['recommendation']}")
        print(f"\n   Breakdown:")
        print(f"   - Idea: {result['breakdown']['idea_score']}/10")
        print(f"   - Team: {result['breakdown']['team_score']}/10")
        print(f"   - Traction: {result['breakdown']['traction_score']}/10")
        print(f"   - Market: {result['breakdown']['market_score']}/10")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return False


def test_health():
    """Test the /health endpoint"""
    try:
        response = requests.get(f"{API_URL}/health")
        response.raise_for_status()
        print("[SUCCESS] Health check passed:")
        print(json.dumps(response.json(), indent=2))
        return True
    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] Health check failed: Cannot connect to API server.")
        print(f"        Make sure the API server is running on {API_URL}")
        print(f"        Start it with: cd api && uvicorn main:app --reload --port 8000")
        print(f"        Or run: cd api && python -m uvicorn main:app --reload --port 8000")
        return False
    except Exception as e:
        print(f"[ERROR] Health check failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Venture Lens Scoring API Test")
    print("=" * 60)
    print()
    
    # Test health first
    print("1. Testing health endpoint...")
    test_health()
    print()
    
    # Test score endpoint
    print("2. Testing /score endpoint...")
    test_score_endpoint()

