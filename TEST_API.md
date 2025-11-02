# Testing API Integration

## Step 1: Configure Your .env File

Create or edit `.env` in the project root:

### For Vertex AI (Service Account JSON):
```env
PORT=3001
NODE_ENV=development

GEMINI_PROJECT_ID=your_project_id
GEMINI_LOCATION=us-central1

# Option A: JSON in environment variable
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account","project_id":"...","private_key_id":"...","private_key":"...","client_email":"...",...}

# OR Option B: Path to JSON file
# GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service-account-key.json

FRONTEND_URL=http://localhost:8080
```

### For Gemini API (Alternative):
```env
PORT=3001
NODE_ENV=development

GEMINI_API_KEY=your_api_key_here

FRONTEND_URL=http://localhost:8080
```

## Step 2: Restart Backend

```bash
# Stop current server (Ctrl+C)
npm run dev
```

## Step 3: Check Health Endpoint

Open: http://localhost:3001/api/analyze/health

**Expected response:**
```json
{
  "status": "OK",
  "service": "analyze",
  "geminiConfigured": true,
  "usingVertexAI": true,
  "configuration": {
    "hasProjectId": true,
    "hasLocation": true,
    "hasServiceAccountJson": true,
    "serviceAccountStatus": "SET (JSON env var)"
  }
}
```

## Step 4: Check Backend Terminal on Startup

Look for these messages:

### ✅ Success (Vertex AI):
```
✅ Vertex AI authentication initialized from GOOGLE_APPLICATION_CREDENTIALS_JSON
```

### ❌ Error (Authentication failed):
```
⚠️ Google Auth initialization failed: [error]
```

## Step 5: Test Analysis

1. Submit a startup analysis through the frontend
2. Check backend terminal logs:

**Expected logs (Vertex AI):**
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

**If you see:**
```
⚠️ Gemini API call failed, falling back to intelligent analysis
```
→ Authentication issue. Check your service account JSON.

## Troubleshooting

### Issue: "Vertex AI credentials not properly configured"
- **Solution**: Make sure `GOOGLE_APPLICATION_CREDENTIALS_JSON` is set and valid JSON
- **OR**: Set `GOOGLE_APPLICATION_CREDENTIALS` to path of JSON file

### Issue: "Failed to parse GOOGLE_APPLICATION_CREDENTIALS_JSON"
- **Solution**: Make sure the JSON is valid and on a single line (no line breaks)
- Escape quotes properly if needed

### Issue: Still seeing mock data
- **Solution**: 
  1. Verify health endpoint shows `"geminiConfigured": true`
  2. Check backend terminal for authentication errors
  3. Make sure you restarted backend after changing .env

### Issue: "Failed to get access token"
- **Solution**: 
  1. Verify service account has "Vertex AI User" role
  2. Check that project has Vertex AI API enabled
  3. Verify JSON file is valid and not corrupted

