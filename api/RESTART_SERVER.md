# How to Restart FastAPI Server

## Method 1: If Server is Running in Terminal

### Windows (PowerShell/CMD):
1. **Stop the server:**
   - Find the terminal where FastAPI is running
   - Press `Ctrl+C` to stop the server

2. **Start it again:**
   ```bash
   cd api
   python -m uvicorn main:app --reload --port 8000
   ```
   
   OR if you have a start script:
   ```bash
   cd api
   .\start.bat
   ```

### Alternative: Use the start script
```bash
cd api
.\start.bat
```

## Method 2: If Server is Running in Background

### Find and Kill the Process:

**Windows PowerShell:**
```powershell
# Find process on port 8000
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

**Or use netstat:**
```bash
netstat -ano | findstr ":8000"
taskkill /PID <PID> /F
```

Then restart:
```bash
cd api
python -m uvicorn main:app --reload --port 8000
```

## Method 3: Simple Restart (Recommended)

1. **Open a new terminal/command prompt**
2. **Navigate to project:**
   ```bash
   cd C:\Users\oswal\OneDrive\Desktop\venture-lens-dash\api
   ```
3. **Stop any existing server** (if running):
   - Press `Ctrl+C` in the terminal where it's running
   - OR kill the process (see Method 2)
4. **Start the server:**
   ```bash
   python -m uvicorn main:app --reload --port 8000
   ```

## Verification

After restarting, check:

1. **Server should show:**
   ```
   INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
   INFO:     Started reloader process
   INFO:     Started server process
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   ```

2. **Test health endpoint:**
   - Open browser: http://localhost:8000/health
   - Should show: `{"status": "OK", ...}`

3. **Check for errors:**
   - Look for import errors
   - Check if all dependencies are installed

## Quick Commands

**Stop server:** `Ctrl+C` (in the terminal running it)

**Start server:**
```bash
cd api
python -m uvicorn main:app --reload --port 8000
```

**Check if port 8000 is in use:**
```bash
netstat -ano | findstr ":8000"
```

**Install/Update dependencies first:**
```bash
cd api
pip install -r requirements.txt
```

