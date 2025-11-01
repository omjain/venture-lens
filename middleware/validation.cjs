/**
 * Validates analyze request body
 */
function validateAnalyzeRequest(req, res, next) {
  const { startupName, deckText, transcriptText, publicUrls } = req.body;
  
  // Check required fields
  if (!startupName || typeof startupName !== 'string' || startupName.trim().length === 0) {
    return res.status(400).json({
      error: 'startupName is required and must be a non-empty string'
    });
  }
  
  // Validate optional fields
  if (deckText && typeof deckText !== 'string') {
    return res.status(400).json({
      error: 'deckText must be a string'
    });
  }
  
  if (transcriptText && typeof transcriptText !== 'string') {
    return res.status(400).json({
      error: 'transcriptText must be a string'
    });
  }
  
  if (publicUrls && !Array.isArray(publicUrls)) {
    return res.status(400).json({
      error: 'publicUrls must be an array'
    });
  }
  
  // Validate URLs if provided
  if (publicUrls && publicUrls.length > 0) {
    const urlRegex = /^https?:\/\/.+/;
    for (const url of publicUrls) {
      if (typeof url !== 'string' || !urlRegex.test(url)) {
        return res.status(400).json({
          error: 'All publicUrls must be valid HTTP/HTTPS URLs'
        });
      }
    }
  }
  
  // Note: Data sources are optional - the AI can analyze with just a startup name
  // If no data is provided, the analysis will be more limited but still possible
  
  // Sanitize and trim inputs
  req.body.startupName = startupName.trim();
  req.body.deckText = deckText ? deckText.trim() : '';
  req.body.transcriptText = transcriptText ? transcriptText.trim() : '';
  req.body.publicUrls = publicUrls || [];
  
  next();
}

/**
 * Validates chat request body
 */
function validateChatRequest(req, res, next) {
  const { conversationHistory, userQuestion, contextData } = req.body;
  
  // Check required fields
  if (!userQuestion || typeof userQuestion !== 'string' || userQuestion.trim().length === 0) {
    return res.status(400).json({
      error: 'userQuestion is required and must be a non-empty string'
    });
  }
  
  // Validate conversation history
  if (conversationHistory && !Array.isArray(conversationHistory)) {
    return res.status(400).json({
      error: 'conversationHistory must be an array'
    });
  }
  
  // Validate conversation history format
  if (conversationHistory && conversationHistory.length > 0) {
    for (const msg of conversationHistory) {
      if (!msg.role || !msg.content || 
          typeof msg.role !== 'string' || 
          typeof msg.content !== 'string') {
        return res.status(400).json({
          error: 'Each message in conversationHistory must have role and content strings'
        });
      }
    }
  }
  
  // Validate context data
  if (contextData && typeof contextData !== 'object') {
    return res.status(400).json({
      error: 'contextData must be an object'
    });
  }
  
  // Sanitize inputs
  req.body.userQuestion = userQuestion.trim();
  req.body.conversationHistory = conversationHistory || [];
  req.body.contextData = contextData || {};
  
  next();
}

module.exports = {
  validateAnalyzeRequest,
  validateChatRequest
};
