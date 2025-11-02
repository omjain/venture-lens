# Quick Fix: Still Seeing Static Data

## The Problem
Your `.env` file is missing or not configured, so the backend is falling back to mock data.

## Immediate Steps

### Step 1: Create .env File

If `.env` doesn't exist, create it in the project root (same folder as `package.json`).

### Step 2: Add Your Credentials

Add these lines to `.env`:

```env
PORT=3001
NODE_ENV=development

# Vertex AI Configuration
GEMINI_PROJECT_ID=YOUR_PROJECT_ID_HERE
GEMINI_LOCATION=us-central1

# Service Account JSON File Path (EASIEST METHOD)
GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\your\service-account.json

FRONTEND_URL=http://localhost:8080
```

**Replace:**
- `YOUR_PROJECT_ID_HERE` with your actual project ID (from JSON file)
- `C:\path\to\your\service-account.json` with the actual path to your JSON file

### Step 3: Verify File Path

Make sure:
1. The JSON file exists at that path
2. The path uses backslashes for Windows: `C:\path\to\file.json`
3. Or use forward slashes: `C:/path/to/file.json`

### Step 4: Restart Backend

**IMPORTANT:** After editing `.env`:
1. Stop backend: Press `Ctrl+C` in backend terminal
2. Start again: `npm run dev`
3. Look for this message on startup:
   ```
   ✅ Vertex AI authentication initialized from file: C:\path\to\file.json
   ```

### Step 5: Test

1. **Check health endpoint:**
   - Visit: http://localhost:3001/api/analyze/health
   - Should show: `"usingVertexAI": true`

2. **Submit analysis:**
   - Submit a startup analysis
   - Check backend terminal for:
     ```
     🤖 Calling Gemini API for analysis of: [name]
        Using Vertex AI: YES
     🔐 Using Vertex AI endpoint - Authentication successful
     ✅ Successfully received AI analysis from Gemini API
     ```

## Still Not Working?

Share these details:

1. **Backend terminal logs** when you start the server
   - Copy the authentication messages
   
2. **Health endpoint response:**
   - Visit: http://localhost:3001/api/analyze/health
   - Share the JSON response

3. **Backend logs when submitting analysis:**
   - Copy the entire log output

4. **Your .env file (hide sensitive parts):**
   - Show the variable names (not values)
   - Or confirm it exists

## Common Mistakes

❌ **File path wrong:**
```
GOOGLE_APPLICATION_CREDENTIALS=C:\wrong\path\file.json
```
✅ **Check file actually exists at that path**

❌ **Project ID wrong:**
```
GEMINI_PROJECT_ID=wrong-project-id
```
✅ **Get project_id from your JSON file**

❌ **Not restarting backend:**
- Changes to `.env` only take effect after restart

✅ **Always restart backend after editing .env**

❌ **Using JSON in env var incorrectly:**
- If using `GOOGLE_APPLICATION_CREDENTIALS_JSON`, JSON must be on one line
- Better to use file path method instead

