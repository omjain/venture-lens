# AI Analyst for Startup Evaluation - Backend

A Node.js/Express backend API that powers an AI-driven startup analysis platform. This backend integrates with Google Vertex AI (Gemini) to provide intelligent startup evaluation and chat-based insights.

## 🚀 Features

- **Startup Analysis**: AI-powered analysis of pitch decks, transcripts, and public data
- **Chat Interface**: Conversational AI for startup insights and Q&A
- **Web Scraping**: Automatic extraction of content from public URLs
- **Rate Limiting**: Built-in protection against abuse
- **Error Handling**: Comprehensive error handling and validation
- **CORS Support**: Ready for frontend integration

## 📋 Prerequisites

- Node.js (v16 or higher)
- Google Cloud Project with Vertex AI enabled
- Gemini API access

## 🛠️ Installation

1. **Clone and install dependencies:**
   ```bash
   npm install
   ```

2. **Set up environment variables:**
   ```bash
   cp env.example .env
   ```

3. **Configure your `.env` file:**
   ```env
   PORT=3001
   NODE_ENV=development
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_PROJECT_ID=your_project_id_here
   GEMINI_LOCATION=us-central1
   FRONTEND_URL=http://localhost:5173
   ```

4. **Get Gemini API credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Enable Vertex AI API
   - Create a service account with Vertex AI permissions
   - Generate and download the API key

## 🚀 Running the Application

### Development Mode
```bash
npm run dev
```

### Production Mode
```bash
npm start
```

The server will start on `http://localhost:3001` (or your configured PORT).

## 📡 API Endpoints

### Health Check
```http
GET /health
```

### Startup Analysis
```http
POST /api/analyze
Content-Type: application/json

{
  "startupName": "TechCorp Inc",
  "deckText": "Pitch deck content...",
  "transcriptText": "Founder interview transcript...",
  "publicUrls": ["https://example.com/news", "https://crunchbase.com/company/techcorp"]
}
```

**Response:**
```json
{
  "summary": "TechCorp is a B2B SaaS platform...",
  "strengths": ["Strong team", "Large market opportunity", "Proven traction"],
  "risks": ["High competition", "Customer concentration", "Regulatory concerns"],
  "nextSteps": ["Technical due diligence", "Customer reference calls", "Market analysis"],
  "dealScore": 7.5
}
```

### AI Chat
```http
POST /api/chat
Content-Type: application/json

{
  "conversationHistory": [
    {"role": "user", "content": "What are the key risks?"},
    {"role": "assistant", "content": "Based on the analysis..."}
  ],
  "userQuestion": "How can we mitigate these risks?",
  "contextData": {
    "startupName": "TechCorp Inc",
    "industry": "SaaS"
  }
}
```

**Response:**
```json
{
  "answer": "To mitigate these risks, I recommend..."
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | `3001` |
| `NODE_ENV` | Environment | `development` |
| `GEMINI_API_KEY` | Google Vertex AI API key | Required |
| `GEMINI_PROJECT_ID` | Google Cloud project ID | Required |
| `GEMINI_LOCATION` | Vertex AI location | `us-central1` |
| `FRONTEND_URL` | Frontend URL for CORS | `http://localhost:5173` |
| `RATE_LIMIT_WINDOW_MS` | Rate limit window | `900000` (15 min) |
| `RATE_LIMIT_MAX_REQUESTS` | Max requests per window | `100` |

### Rate Limiting

The API includes rate limiting to prevent abuse:
- 100 requests per 15 minutes per IP address
- Configurable via environment variables

## 🧪 Testing

### Health Checks
```bash
# Server health
curl http://localhost:3001/health

# Analysis service health
curl http://localhost:3001/api/analyze/health

# Chat service health
curl http://localhost:3001/api/chat/health
```

### Test Analysis
```bash
curl -X POST http://localhost:3001/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "startupName": "Test Startup",
    "deckText": "We are building the next generation of AI-powered analytics...",
    "transcriptText": "Our team has 10 years of experience in machine learning...",
    "publicUrls": ["https://example.com"]
  }'
```

## 🚨 Error Handling

The API returns structured error responses:

```json
{
  "error": "Error message",
  "details": "Additional details (development only)"
}
```

Common error codes:
- `400` - Bad Request (validation errors)
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error

## 🔒 Security Features

- **Helmet.js**: Security headers
- **CORS**: Configurable cross-origin requests
- **Rate Limiting**: Request throttling
- **Input Validation**: Request sanitization
- **Error Handling**: No sensitive data leakage

## 📁 Project Structure

```
├── index.js                 # Main server file
├── package.json            # Dependencies and scripts
├── env.example             # Environment variables template
├── routes/
│   ├── analyze.js          # Analysis endpoints
│   └── chat.js             # Chat endpoints
├── services/
│   └── geminiService.js    # Gemini AI integration
├── middleware/
│   └── validation.js       # Request validation
└── README.md               # This file
```

## 🤝 Frontend Integration

This backend is designed to work with the React frontend. Update your frontend API calls to point to:

```javascript
// Analysis endpoint
const response = await fetch('http://localhost:3001/api/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    startupName: 'Your Startup',
    deckText: 'Pitch deck content...',
    transcriptText: 'Interview transcript...',
    publicUrls: ['https://example.com']
  })
});

// Chat endpoint
const chatResponse = await fetch('http://localhost:3001/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    conversationHistory: [],
    userQuestion: 'Your question...',
    contextData: {}
  })
});
```

## 🐛 Troubleshooting

### Common Issues

1. **Gemini API errors**: Check your API key and project ID
2. **CORS errors**: Verify FRONTEND_URL matches your frontend
3. **Rate limiting**: Reduce request frequency or increase limits
4. **Web scraping failures**: Some sites block automated requests

### Debug Mode

Set `NODE_ENV=development` for detailed error messages and logging.

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section
- Review error logs
- Ensure all environment variables are set correctly