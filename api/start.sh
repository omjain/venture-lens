#!/bin/bash
# Startup script for Venture Lens Scoring API

echo "🚀 Starting Venture Lens Scoring API..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Make sure to set GEMINI_PROJECT_ID and GEMINI_LOCATION"
fi

# Run the API
uvicorn main:app --reload --host 0.0.0.0 --port 8000

