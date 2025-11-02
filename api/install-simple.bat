@echo off
REM Simple installation script for Windows - installs packages without version pins
echo Installing FastAPI Scoring Service dependencies...
echo.

pip install --upgrade pip
echo.

echo Installing FastAPI and Uvicorn...
pip install fastapi uvicorn[standard]
echo.

echo Installing Pydantic (this may take a minute)...
pip install pydantic
echo.

echo Installing Google Auth libraries...
pip install google-auth google-auth-oauthlib google-auth-httplib2
echo.

echo Installing remaining dependencies...
pip install python-dotenv httpx requests
echo.

echo.
echo Installation complete!
echo.
echo To run the service:
echo   cd api
echo   uvicorn main:app --reload --port 8000
echo.
pause

