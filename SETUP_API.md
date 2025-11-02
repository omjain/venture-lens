# Setting Up Gemini API for Real Analysis

If you have a **Vertex AI service account key** (JSON file), you can use it without installing `gcloud` CLI.

## Option 1: Using Vertex AI with Service Account JSON (Recommended for Vertex AI)

If you have a service account JSON key file from Vertex AI:

### Step 1: Get Your Service Account JSON Key

If you already have a service account JSON key file from Google Cloud Console:
- Keep it secure and note the file path

If you need to create one:
1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
2. Select your project (or create a new one)
3. Click "Create Service Account"
4. Give it a name (e.g., "venture-lens-api")
5. Grant it the role: "Vertex AI User" or "AI Platform Developer"
6. Click "Done"
7. Click on the created service account
8. Go to "Keys" tab → "Add Key" → "Create new key" → Choose "JSON"
9. Download the JSON file and save it securely

### Step 2: Configure Your Backend

**Method A: Using Service Account JSON as Environment Variable (Recommended)**

1. Open your service account JSON file
2. Copy the entire JSON content
3. Create or edit `.env` file in the project root:

```env
# Server Configuration
PORT=3001
NODE_ENV=development

# Vertex AI Configuration
GEMINI_PROJECT_ID=your_project_id_here
GEMINI_LOCATION=us-central1

# Service Account JSON (paste the entire JSON content here, on one line)
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account","project_id":"...","private_key_id":"...","private_key":"...","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}

# CORS Configuration
FRONTEND_URL=http://localhost:8080
```

**Method B: Using Service Account JSON File Path**

1. Place your service account JSON file in a secure location
2. Create or edit `.env` file:

```env
# Server Configuration
PORT=3001
NODE_ENV=development

# Vertex AI Configuration
GEMINI_PROJECT_ID=your_project_id_here
GEMINI_LOCATION=us-central1

# Service Account JSON File Path (full path to your JSON file)
GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\your\service-account-key.json

# CORS Configuration
FRONTEND_URL=http://localhost:8080
```

**Important:** 
- Replace `your_project_id_here` with your actual Google Cloud Project ID
- The Project ID is usually found in your service account JSON file as `"project_id"`

### Step 3: Restart Backend Server

```bash
# Stop the current server (Ctrl+C)
# Then restart:
npm run dev
```

### Step 4: Verify It's Working

1. Check health endpoint: http://localhost:3001/api/analyze/health
   - Should show: `"usingVertexAI": true`
   - Should show: `"geminiConfigured": true`

2. Submit a new analysis and check backend terminal:
   - Look for: `✅ Vertex AI authentication initialized`
   - Look for: `🔐 Using Vertex AI endpoint - Authentication successful`
   - Look for: `✅ Successfully received AI analysis from Gemini API`

## Option 2: Using Gemini API Key (Google AI Studio - Alternative)

If you prefer to use Google AI Studio API key instead:

1. **Get Your API Key:**
   - Go to: https://aistudio.google.com/apikey
   - Sign in and create an API key
   - Copy the key

2. **Configure `.env`:**
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```
   (Do NOT set GEMINI_PROJECT_ID and GEMINI_LOCATION when using API key)

3. Restart backend server

## Troubleshooting

### Still seeing mock data?

1. **Check your `.env` file:**
   - Make sure it's in the project root (same folder as `package.json`)
   - Make sure the API key is correct (no extra spaces)
   - Make sure you restarted the backend after adding it

2. **Check backend terminal logs:**
   - Look for error messages about API credentials
   - Check if it says "Using Gemini API" or "Using Vertex AI"

3. **Test the health endpoint:**
   - Visit: http://localhost:3001/api/analyze/health
   - Should show configuration status

4. **Check browser console:**
   - Open DevTools (F12)
   - Check for API errors in the Network tab

### Common Issues

- **"No API credentials configured"**: Your `.env` file is missing or API key not set
- **"API call failed"**: API key is invalid or quota exceeded
- **Still showing mock data**: Backend not restarted after adding credentials

## Quick Test

After setup, analyze a startup and check your **backend terminal**. You should see:
```
🔍 Starting analysis for: [StartupName]
🤖 Calling Gemini API for analysis of: [StartupName]
   Using Vertex AI: NO
   API Key: SET (hidden)
🔑 Using Gemini API (Google AI Studio)
✅ Successfully received AI analysis from Gemini API
```

If you see `⚠️ Gemini API call failed`, check your API key and try again.

