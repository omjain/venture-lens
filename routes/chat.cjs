const express = require('express');
const router = express.Router();
const { chatWithAI } = require('../services/geminiService.cjs');
const { validateChatRequest } = require('../middleware/validation.cjs');

/**
 * POST /api/chat
 * Handles chat interactions with AI analyst
 */
router.post('/', validateChatRequest, async (req, res) => {
  try {
    const { conversationHistory, userQuestion, contextData } = req.body;
    
    console.log(`💬 Chat request: ${userQuestion.substring(0, 100)}...`);
    
    // Prepare chat data
    const chatData = {
      conversationHistory: conversationHistory || [],
      userQuestion,
      contextData: contextData || {}
    };
    
    // Call Gemini AI service for chat
    const chatResponse = await chatWithAI(chatData);
    
    console.log(`✅ Chat response generated`);
    
    res.json(chatResponse);
    
  } catch (error) {
    console.error('❌ Chat error:', error);
    
    // Return structured error response
    res.status(500).json({
      error: 'Failed to process chat request',
      details: process.env.NODE_ENV === 'development' ? error.message : 'Internal server error'
    });
  }
});

/**
 * GET /api/chat/health
 * Health check for chat service
 */
router.get('/health', (req, res) => {
  const isConfigured = !!(process.env.GEMINI_API_KEY || 
                          (process.env.GEMINI_PROJECT_ID && process.env.GEMINI_LOCATION));
  res.json({
    status: 'OK',
    service: 'chat',
    timestamp: new Date().toISOString(),
    geminiConfigured: isConfigured,
    usingVertexAI: !!(process.env.GEMINI_PROJECT_ID && process.env.GEMINI_LOCATION),
    usingGeminiAPI: !!process.env.GEMINI_API_KEY && !process.env.GEMINI_PROJECT_ID
  });
});

module.exports = router;
