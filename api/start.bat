@echo off
REM Startup script for Venture Lens Scoring API (Windows)

echo 🚀 Starting Venture Lens Scoring API...

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Check if .env exists
if not exist ".env" (
    echo ⚠️  Warning: .env file not found. Make sure to set GEMINI_PROJECT_ID and GEMINI_LOCATION
)

REM Run the API
uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause

