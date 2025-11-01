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
  const isConfigured = !!(process.env.GEMINI_API_KEY || 
                          (process.env.GEMINI_PROJECT_ID && process.env.GEMINI_LOCATION));
  res.json({
    status: 'OK',
    service: 'analyze',
    timestamp: new Date().toISOString(),
    geminiConfigured: isConfigured,
    usingVertexAI: !!(process.env.GEMINI_PROJECT_ID && process.env.GEMINI_LOCATION),
    usingGeminiAPI: !!process.env.GEMINI_API_KEY && !process.env.GEMINI_PROJECT_ID
  });
});

module.exports = router;
