# Debugging: Why Am I Still Seeing Static Data?

## Quick Diagnostic Steps

### Step 1: Check Backend Terminal Logs

When you submit an analysis, look for these messages in your backend terminal:

**✅ If working correctly, you'll see:**
```
🔍 Starting analysis for: [StartupName]
🤖 Calling Gemini API for analysis of: [StartupName]
   Using Vertex AI: YES
   Project ID: your_project...
   Location: us-central1
   API Key: NOT SET
🔐 Using Vertex AI endpoint - Authentication successful
✅ Successfully received AI analysis from Gemini API
✅ Analysis completed successfully for: [StartupName]
```

**❌ If falling back to mock, you'll see:**
```
🔍 Starting analysis for: [StartupName]
🤖 Calling Gemini API for analysis of: [StartupName]
   Using Vertex AI: NO  ← PROBLEM: Not detecting Vertex AI config
   Project ID: NOT SET
   Location: NOT SET
⚠️  Gemini API call failed, falling back to intelligent analysis
✅ Fallback analysis completed for: [StartupName] (using intelligent mock analysis)
```

### Step 2: Check Health Endpoint

Visit: http://localhost:3001/api/analyze/health

**What to look for:**
- `"geminiConfigured": false` → Credentials not set
- `"usingVertexAI": false` → Vertex AI not configured
- `"serviceAccountStatus": "NOT SET"` → Service account not found

### Step 3: Verify .env File

**Check these in your `.env` file:**

1. **File exists?** Should be in project root (same folder as `package.json`)

2. **Has required variables?**
   ```env
   GEMINI_PROJECT_ID=your_actual_project_id
   GEMINI_LOCATION=us-central1
   GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\file.json
   # OR
   GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account",...}
   ```

3. **No typos?**
   - `GEMINI_PROJECT_ID` (not `GEMINI_PROJECT`)
   - `GOOGLE_APPLICATION_CREDENTIALS` (not `GOOGLE_APPLICATION_CREDENTIAL`)
   - Exact spelling matters!

4. **Values are correct?**
   - Project ID matches your JSON file's `project_id`
   - File path is correct and file exists (if using file path method)
   - JSON is valid (if using JSON env var)

### Step 4: Restart Backend After Changes

**Important:** After editing `.env`:
1. Stop backend (Ctrl+C)
2. Start again: `npm run dev`
3. Check startup logs for authentication message

### Step 5: Check Authentication on Startup

When backend starts, you should see one of these:

**✅ Good:**
```
✅ Vertex AI authentication initialized from GOOGLE_APPLICATION_CREDENTIALS_JSON
```
OR
```
✅ Vertex AI authentication initialized from file: C:\path\to\file.json
```

**❌ Problem:**
```
⚠️ Google Auth initialization failed: [error message]
```
OR
```
ℹ️  No API credentials configured. Using intelligent mock responses.
```

## Common Issues and Fixes

### Issue 1: "Using Vertex AI: NO" in logs
**Cause:** `.env` not loaded or variables not set correctly
**Fix:**
- Verify `.env` file is in project root
- Check variable names are exact (no typos)
- Restart backend after changes

### Issue 2: "Google Auth initialization failed"
**Cause:** Invalid JSON or file path
**Fix:**
- If using file path: Verify file exists at that path
- If using JSON env var: Check JSON is valid and on one line
- Check file permissions

### Issue 3: "Failed to get access token"
**Cause:** Service account doesn't have correct permissions
**Fix:**
- Ensure service account has "Vertex AI User" role
- Verify project has Vertex AI API enabled
- Check JSON file is not corrupted

### Issue 4: Health endpoint shows "NOT SET"
**Cause:** Environment variables not loaded
**Fix:**
- Make sure `.env` is in correct location
- Verify `dotenv` package is installed (it should be)
- Restart backend

## Quick Test Script

Run this to check your configuration:
```bash
# In backend terminal (while server is running):
curl http://localhost:3001/api/analyze/health
```

Or visit in browser: http://localhost:3001/api/analyze/health

Look for:
- `"geminiConfigured": true` ← Must be true
- `"usingVertexAI": true` ← Must be true  
- `"serviceAccountStatus": "SET (...)"` ← Must be SET

## Still Not Working?

1. **Share your backend terminal logs** when you submit analysis
2. **Check the health endpoint response** - share what it shows
3. **Verify .env file location** - should be next to `package.json`
4. **Check file permissions** - make sure backend can read the JSON file

