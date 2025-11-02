# How to Configure .env with Service Account JSON

## Step-by-Step Guide

### Option 1: Using JSON as Environment Variable (Recommended)

1. **Open your service account JSON file** in a text editor
2. **Copy the entire JSON content** - it should look like:
   ```json
   {
     "type": "service_account",
     "project_id": "your-project-id",
     "private_key_id": "...",
     "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
     "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
     "client_id": "...",
     "auth_uri": "https://accounts.google.com/o/oauth2/auth",
     "token_uri": "https://oauth2.googleapis.com/token",
     ...
   }
   ```

3. **Convert it to a single line** for the `.env` file:
   - Remove all line breaks
   - Keep all quotes and escape them properly
   - Or use an online JSON minifier tool

4. **Create or edit `.env` file** in project root:
   ```env
   PORT=3001
   NODE_ENV=development

   # Vertex AI Configuration
   GEMINI_PROJECT_ID=your_project_id_here
   GEMINI_LOCATION=us-central1

   # Service Account JSON (paste the minified JSON here)
   GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account","project_id":"your-project-id","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n","client_email":"...","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token",...}

   FRONTEND_URL=http://localhost:8080
   ```

**Important Notes:**
- Replace `your_project_id_here` with the `project_id` from your JSON file
- The JSON must be on a single line (no line breaks)
- Escape backslashes in the private key: `\n` becomes `\\n`
- Escape quotes if needed

### Option 2: Using JSON File Path (Easier)

1. **Place your JSON file** in a secure location (e.g., `C:\credentials\service-account.json`)
2. **Create or edit `.env` file**:
   ```env
   PORT=3001
   NODE_ENV=development

   # Vertex AI Configuration
   GEMINI_PROJECT_ID=your_project_id_here
   GEMINI_LOCATION=us-central1

   # Path to your service account JSON file
   GOOGLE_APPLICATION_CREDENTIALS=C:\credentials\service-account.json

   FRONTEND_URL=http://localhost:8080
   ```

**This is easier** - no need to convert to single line!

### Getting Your Project ID

Your `GEMINI_PROJECT_ID` should match the `"project_id"` field in your JSON file.

To find it:
1. Open your JSON file
2. Look for: `"project_id": "your-project-id-here"`
3. Use that value for `GEMINI_PROJECT_ID` in `.env`

### After Configuration

1. **Save the `.env` file**
2. **Restart your backend server:**
   ```bash
   # Stop current server (Ctrl+C if running)
   npm run dev
   ```

3. **Check the logs** - you should see:
   ```
   ✅ Vertex AI authentication initialized from GOOGLE_APPLICATION_CREDENTIALS_JSON
   ```
   OR
   ```
   ✅ Vertex AI authentication initialized from file: C:\path\to\file.json
   ```

4. **Test the health endpoint:**
   - Visit: http://localhost:3001/api/analyze/health
   - Should show: `"usingVertexAI": true`

### Troubleshooting

**Issue: "Failed to parse GOOGLE_APPLICATION_CREDENTIALS_JSON"**
- Make sure JSON is on one line
- Escape backslashes: `\n` → `\\n`
- Use file path method instead (Option 2)

**Issue: "Vertex AI credentials not properly configured"**
- Check that `GEMINI_PROJECT_ID` and `GEMINI_LOCATION` are set
- Verify JSON file path is correct (if using Option 2)
- Check that JSON content is valid

**Issue: Still showing mock data**
- Verify health endpoint shows `"geminiConfigured": true`
- Check backend terminal for authentication errors
- Make sure you restarted backend after changing `.env`

