const express = require('express');
const router = express.Router();
const { analyzeStartup } = require('../services/geminiService.cjs');
const { validateAnalyzeRequest } = require('../middleware/validation.cjs');

/**
 * POST /api/analyze
 * Analyzes startup data using AI and returns structured insights
 */
router.post('/', validateAnalyzeRequest, async (req, res) => {
  try {
    const { startupName, deckText, transcriptText, publicUrls } = req.body;
    
    console.log(`🔍 Analyzing startup: ${startupName}`);
    
    // Prepare the analysis data
    const analysisData = {
      startupName,
      deckText: deckText || '',
      transcriptText: transcriptText || '',
      publicUrls: publicUrls || []
    };
    
    // Call Gemini AI service
    const analysisResult = await analyzeStartup(analysisData);
    
    console.log(`✅ Analysis completed for: ${startupName}`);
    
    res.json(analysisResult);
    
  } catch (error) {
    console.error('❌ Analysis error:', error);
    
    // Return structured error response
    res.status(500).json({
      error: 'Failed to analyze startup data',
      details: process.env.NODE_ENV === 'development' ? error.message : 'Internal server error'
    });
  }
});

/**
 * GET /api/analyze/health
 * Health check for analysis service
 */
router.get('/health', (req, res) => {
  const hasProjectId = !!process.env.GEMINI_PROJECT_ID;
  const hasLocation = !!process.env.GEMINI_LOCATION;
  const hasApiKey = !!process.env.GEMINI_API_KEY;
  const hasServiceAccountJson = !!process.env.GOOGLE_APPLICATION_CREDENTIALS_JSON;
  const hasServiceAccountPath = !!process.env.GOOGLE_APPLICATION_CREDENTIALS;
  
  // Vertex AI is configured if we have project + location + (service account OR api key)
  const isVertexAIConfigured = hasProjectId && hasLocation && (hasServiceAccountJson || hasServiceAccountPath);
  const isGeminiAPIConfigured = hasApiKey && !hasProjectId;
  const isConfigured = isVertexAIConfigured || isGeminiAPIConfigured;
  
  res.json({
    status: 'OK',
    service: 'analyze',
    timestamp: new Date().toISOString(),
    geminiConfigured: isConfigured,
    usingVertexAI: isVertexAIConfigured,
    usingGeminiAPI: isGeminiAPIConfigured,
    configuration: {
      hasProjectId,
      hasLocation,
      hasApiKey,
      hasServiceAccountJson,
      hasServiceAccountPath,
      projectId: hasProjectId ? process.env.GEMINI_PROJECT_ID.substring(0, 10) + '...' : 'NOT SET',
      location: hasLocation ? process.env.GEMINI_LOCATION : 'NOT SET',
      apiKeyStatus: hasApiKey ? 'SET (hidden)' : 'NOT SET',
      serviceAccountStatus: hasServiceAccountJson ? 'SET (JSON env var)' : 
                           hasServiceAccountPath ? `SET (file: ${process.env.GOOGLE_APPLICATION_CREDENTIALS})` : 'NOT SET'
    },
    warning: !isConfigured ? '⚠️ No API credentials configured. Analysis will use mock data.' : null,
    recommendation: !isConfigured ? 'Configure GEMINI_PROJECT_ID + GEMINI_LOCATION + GOOGLE_APPLICATION_CREDENTIALS_JSON (or GOOGLE_APPLICATION_CREDENTIALS) for Vertex AI, or GEMINI_API_KEY for Gemini API.' : null
  });
});

module.exports = router;
