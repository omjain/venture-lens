# Venture Lens - AI Startup Analysis Platform

A comprehensive full-stack AI-powered startup analysis platform that provides intelligent investment insights, risk assessment, and peer benchmarking. Built with React/TypeScript frontend and Node.js/Express backend, featuring sophisticated AI analysis engines that respond dynamically to startup data.

## 🚀 Features

### 🤖 AI-Powered Analysis
- **Dynamic Startup Analysis**: Intelligent analysis that adapts to your actual startup data
- **Risk MRI Analysis**: 5-category risk assessment (Team, Market, Product, Traction, Moat)
- **Peer Benchmark Analysis**: Industry-specific performance comparison
- **Smart Data Extraction**: Automatically extracts revenue, user count, team size, and growth metrics
- **Industry Detection**: Context-aware analysis for different sectors (fintech, SaaS, healthcare, etc.)

### 💬 Conversational AI
- **Intelligent Chat Interface**: Context-aware responses to investment questions
- **Investment Guidance**: Professional AI analyst persona with domain expertise
- **Due Diligence Support**: Answers questions about risks, strengths, and next steps

### 📊 Advanced Analytics
- **Deal Scoring**: Multi-factor scoring system (1-10 scale)
- **Real-time Metrics**: Dynamic calculation based on input data
- **Visual Dashboards**: Interactive charts and heatmaps
- **Export Capabilities**: Download analysis reports

### 🔧 Technical Features
- **Web Scraping**: Automatic content extraction from public URLs
- **Rate Limiting**: Built-in protection against abuse
- **CORS Support**: Seamless frontend-backend integration
- **Error Handling**: Comprehensive error handling and validation
- **Hot Reload**: Development-friendly with live updates

## 📋 Prerequisites

- **Node.js** (v18 or higher)
- **npm** or **yarn** package manager
- **Google Cloud Project** with Vertex AI enabled (optional - works with mock data)
- **Modern web browser** (Chrome, Firefox, Safari, Edge)

## 🛠️ Installation

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd venture-lens-dash
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```

4. **Configure your `.env` file:**
   ```env
   # Server Configuration
   PORT=3001
   NODE_ENV=development

   # Google Vertex AI Configuration (Optional)
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_PROJECT_ID=your_project_id_here
   GEMINI_LOCATION=us-central1

   # CORS Configuration
   FRONTEND_URL=http://localhost:8080

   # Rate Limiting
   RATE_LIMIT_WINDOW_MS=900000
   RATE_LIMIT_MAX_REQUESTS=100
   ```

5. **Start the application:**
   ```bash
   # Start backend (Terminal 1)
   npm run dev

   # Start frontend (Terminal 2)
   npm run dev:frontend
   ```

6. **Open your browser:**
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:3001

## 🚀 Running the Application

### Development Mode (Recommended)
```bash
# Terminal 1 - Backend
npm run dev

# Terminal 2 - Frontend  
npm run dev:frontend
```

### Production Mode
```bash
# Build frontend
npm run build

# Start production server
npm start
```

### Available Scripts
- `npm run dev` - Start backend with nodemon
- `npm run dev:frontend` - Start Vite frontend dev server
- `npm run build` - Build frontend for production
- `npm run preview` - Preview production build
- `npm start` - Start production backend
- `npm test` - Run backend tests

## 🎯 How to Use

### 1. Upload Startup Data
- Enter startup name
- Paste pitch deck content
- Add founder interview transcript (optional)
- Include public URLs for additional data (optional)

### 2. View AI Analysis
- **Summary**: AI-generated overview based on your data
- **Strengths**: Dynamic strengths based on actual metrics
- **Risks**: Contextual risks tailored to your industry and data
- **Next Steps**: Actionable due diligence recommendations
- **Deal Score**: 1-10 score based on multiple factors

### 3. Risk MRI Analysis
- **Team Risk**: Based on team size and interview data
- **Market Risk**: Industry-specific market assessment
- **Product Risk**: Product-market fit validation
- **Traction Risk**: Revenue and user growth analysis
- **Moat Risk**: Competitive advantage assessment

### 4. Peer Benchmark Analysis
- **Revenue Growth**: Compared to industry peers
- **Gross Margin**: Industry-specific margin analysis
- **CAC Payback**: Customer acquisition cost efficiency
- **Net Retention**: Customer retention performance

### 5. AI Chat
- Ask questions about the analysis
- Get investment guidance
- Request clarification on specific metrics
- Discuss due diligence strategies

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
  "deckText": "We are a SaaS platform with $2M ARR and 10,000 users...",
  "transcriptText": "Our team of 25 has 10 years experience...",
  "publicUrls": ["https://example.com/news", "https://crunchbase.com/company/techcorp"]
}
```

**Enhanced Response:**
```json
{
  "summary": "TechCorp operates in the SaaS sector. The company demonstrates strong revenue generation with $2.0M in annual revenue. With 10,000 users, the platform shows significant market traction...",
  "strengths": [
    "Strong revenue generation with $2.0M+ annual revenue",
    "Experienced team of 25 professionals with execution capability",
    "Modern technology stack leveraging AI",
    "Comprehensive pitch deck with clear business model"
  ],
  "risks": [
    "Limited public validation - market presence unclear",
    "No founder interview - team assessment incomplete",
    "Market competition and differentiation challenges"
  ],
  "nextSteps": [
    "Conduct founder interviews to assess team and vision",
    "Gather public data and market validation metrics",
    "Conduct detailed financial analysis and growth projections"
  ],
  "dealScore": 8,
  "riskMRI": {
    "categories": [
      {
        "name": "Team",
        "score": 3,
        "description": "Solid team size for execution"
      },
      {
        "name": "Market", 
        "score": 4,
        "description": "SaaS market with moderate user base"
      }
    ],
    "overallScore": 4.2
  },
  "peerBenchmark": {
    "metrics": [
      {
        "name": "Revenue Growth",
        "company": 60,
        "peers": [45, 52, 38],
        "unit": "%",
        "higher": true
      }
    ],
    "peerCompanies": ["CloudSoft", "DataFlow", "AppTech"],
    "outperformingCount": 3,
    "percentileRank": 75
  }
}
```

### AI Chat
```http
POST /api/chat
Content-Type: application/json

{
  "conversationHistory": [
    {"role": "user", "content": "What are the key risks?"},
    {"role": "assistant", "content": "Based on the startup analysis, I'd recommend focusing on the key metrics that matter most..."}
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
  "answer": "To mitigate these risks, I recommend focusing on the key metrics that matter most: revenue growth, user acquisition costs, and market size. The deal score and risk assessment provide a good starting point, but you'll want to dive deeper into the unit economics and competitive positioning before making an investment decision."
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PORT` | Backend server port | `3001` | No |
| `NODE_ENV` | Environment mode | `development` | No |
| `GEMINI_API_KEY` | Google Vertex AI API key | - | No* |
| `GEMINI_PROJECT_ID` | Google Cloud project ID | - | No* |
| `GEMINI_LOCATION` | Vertex AI location | `us-central1` | No |
| `FRONTEND_URL` | Frontend URL for CORS | `http://localhost:8080` | No |
| `RATE_LIMIT_WINDOW_MS` | Rate limit window (ms) | `900000` (15 min) | No |
| `RATE_LIMIT_MAX_REQUESTS` | Max requests per window | `100` | No |

*Note: Gemini API is optional. The system works with sophisticated mock AI responses if no API key is provided.

### AI Analysis Features

The platform includes multiple AI analysis engines:

#### 1. **Data Extraction AI**
- Extracts revenue figures ($2M → $2,000,000)
- Identifies user metrics (10,000 users)
- Detects team size (25 employees)
- Recognizes growth rates (20% MoM)
- Identifies technology keywords (AI, SaaS, blockchain)

#### 2. **Industry Detection AI**
- Automatically detects industry from content
- Supports: fintech, SaaS, healthcare, e-commerce, food delivery
- Provides industry-specific context and benchmarks

#### 3. **Risk Assessment AI**
- **Team Risk**: Based on team size and interview data
- **Market Risk**: Industry-specific market analysis
- **Product Risk**: Product-market fit validation
- **Traction Risk**: Revenue and user growth assessment
- **Moat Risk**: Competitive advantage evaluation

#### 4. **Benchmark Analysis AI**
- Generates industry-specific peer comparisons
- Calculates realistic performance metrics
- Provides percentile rankings
- Creates dynamic peer company names

### Rate Limiting

The API includes intelligent rate limiting:
- 100 requests per 15 minutes per IP address
- Configurable via environment variables
- Graceful degradation for high traffic

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

### Test Analysis with Real Data
```bash
# Test with revenue and user data
curl -X POST http://localhost:3001/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "startupName": "TechCorp",
    "deckText": "We are a SaaS platform with $2M ARR and 10,000 users. Our team of 25 has 10 years experience in AI.",
    "transcriptText": "Our founder has previously built two successful startups...",
    "publicUrls": ["https://techcorp.com", "https://crunchbase.com/company/techcorp"]
  }'
```

### Test Chat Interface
```bash
curl -X POST http://localhost:3001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "conversationHistory": [],
    "userQuestion": "What are the main investment risks for this startup?",
    "contextData": {}
  }'
```

### Frontend Testing
1. Open http://localhost:8080
2. Enter startup data with specific metrics
3. Verify AI analysis updates dynamically
4. Test Risk MRI and Peer Benchmark charts
5. Try the AI chat interface

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
venture-lens-dash/
├── 📁 Backend (Node.js/Express)
│   ├── index.cjs                    # Main server file
│   ├── package.json                 # Dependencies and scripts
│   ├── .env.example                 # Environment variables template
│   ├── routes/
│   │   ├── analyze.cjs              # Analysis endpoints
│   │   └── chat.cjs                 # Chat endpoints
│   ├── services/
│   │   └── geminiService.cjs        # AI analysis engine
│   ├── middleware/
│   │   └── validation.cjs           # Request validation
│   └── test-backend.cjs             # Backend tests
│
├── 📁 Frontend (React/TypeScript)
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/                  # Reusable UI components
│   │   │   └── dashboard/           # Dashboard components
│   │   │       ├── UploadZone.tsx   # File upload interface
│   │   │       ├── StartupSummary.tsx # Company overview
│   │   │       ├── DealMemo.tsx     # Investment memo
│   │   │       ├── RiskHeatmap.tsx  # Risk MRI analysis
│   │   │       ├── BenchmarkChart.tsx # Peer benchmarking
│   │   │       └── AIChat.tsx       # Chat interface
│   │   ├── contexts/
│   │   │   └── StartupContext.tsx   # State management
│   │   ├── pages/
│   │   │   └── Index.tsx            # Main dashboard page
│   │   └── main.tsx                 # App entry point
│   ├── vite.config.ts               # Vite configuration
│   ├── tailwind.config.ts           # Tailwind CSS config
│   └── tsconfig.json                # TypeScript config
│
├── 📁 Configuration
│   ├── .env                         # Environment variables
│   ├── .gitignore                   # Git ignore rules
│   └── README.md                    # This file
```

### Key Files Explained

#### Backend Files
- **`index.cjs`**: Main Express server with CORS, rate limiting, and routing
- **`services/geminiService.cjs`**: Core AI analysis engine with multiple AI agents
- **`routes/analyze.cjs`**: Startup analysis API endpoint
- **`routes/chat.cjs`**: AI chat API endpoint

#### Frontend Files
- **`src/pages/Index.tsx`**: Main dashboard layout
- **`src/contexts/StartupContext.tsx`**: React context for state management
- **`src/components/dashboard/`**: Dashboard components with AI integration
- **`vite.config.ts`**: Vite build configuration

#### AI Analysis Engine
The `geminiService.cjs` contains multiple AI agents:
- **Data Extraction AI**: Extracts metrics from text
- **Industry Detection AI**: Identifies business sector
- **Risk Assessment AI**: Calculates risk scores
- **Benchmark Analysis AI**: Generates peer comparisons
- **Chat AI**: Provides conversational responses

## 🎨 Frontend Integration

The React frontend is fully integrated with the backend API. The frontend automatically handles:

### State Management
```typescript
// React Context for startup data
const { analysis, isLoading, analyzeStartup } = useStartup();

// Analyze startup with AI
await analyzeStartup({
  startupName: "TechCorp",
  deckText: "We have $2M ARR and 10,000 users...",
  transcriptText: "Our team of 25 has 10 years experience...",
  publicUrls: ["https://techcorp.com"]
});
```

### AI-Powered Components
- **`StartupSummary`**: Displays AI-generated summary and deal score
- **`DealMemo`**: Shows strengths, risks, and next steps
- **`RiskHeatmap`**: Interactive risk MRI analysis
- **`BenchmarkChart`**: Peer benchmark comparison
- **`AIChat`**: Conversational AI interface

### Real-time Updates
All components automatically update when new analysis data is received, providing a seamless user experience.

## 🚀 Deployment

### Development
```bash
# Start both frontend and backend
npm run dev          # Backend on :3001
npm run dev:frontend # Frontend on :8080
```

### Production
```bash
# Build frontend
npm run build

# Start production server
npm start
```

### Docker (Optional)
```dockerfile
# Backend Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3001
CMD ["npm", "start"]
```

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**: 
   ```bash
   # Kill process on port 3001
   npx kill-port 3001
   # Or find and kill manually
   netstat -ano | findstr :3001
   taskkill /PID <PID> /F
   ```

2. **CORS errors**: 
   - Verify `FRONTEND_URL` in `.env` matches your frontend URL
   - Check that both frontend and backend are running

3. **AI analysis not working**:
   - The system works with mock AI responses by default
   - For real Gemini API, ensure `GEMINI_API_KEY` is set
   - Check console logs for specific error messages

4. **Frontend not loading**:
   - Ensure Vite dev server is running on port 8080
   - Check for TypeScript compilation errors
   - Verify all dependencies are installed

5. **Data extraction issues**:
   - Use specific metrics in your input (e.g., "$2M revenue", "10,000 users")
   - Include industry keywords for better detection
   - Check that pitch deck content is substantial

### Debug Mode

Set `NODE_ENV=development` for detailed error messages and logging.

### Performance Tips

- Use specific metrics in startup data for better AI analysis
- Include industry context for more accurate benchmarks
- Provide substantial pitch deck content for comprehensive analysis

## 📊 Example Use Cases

### 1. Early Stage Startup Analysis
```json
{
  "startupName": "HealthTech Startup",
  "deckText": "We are a healthcare AI platform with $50K ARR and 500 users. Our team of 5 has 15 years combined experience in healthcare technology.",
  "transcriptText": "Our founder previously worked at Mayo Clinic and has deep healthcare domain expertise...",
  "publicUrls": ["https://healthtech.com", "https://crunchbase.com/company/healthtech"]
}
```

### 2. Mature Company Analysis
```json
{
  "startupName": "FinTech Unicorn",
  "deckText": "We are a fintech platform with $100M ARR and 1M+ users. Our team of 500 includes former executives from Goldman Sachs and JP Morgan.",
  "transcriptText": "We've raised $200M in Series C funding and are expanding globally...",
  "publicUrls": ["https://fintech.com", "https://techcrunch.com/fintech-unicorn"]
}
```

## 🎯 Key Features Summary

✅ **AI-Powered Analysis**: Dynamic analysis that responds to your actual data  
✅ **Risk MRI Analysis**: 5-category risk assessment with visual heatmap  
✅ **Peer Benchmarking**: Industry-specific performance comparison  
✅ **Smart Data Extraction**: Automatically extracts revenue, users, team size  
✅ **Conversational AI**: Chat interface for investment guidance  
✅ **Real-time Updates**: All components update dynamically  
✅ **No API Key Required**: Works with sophisticated mock responses  
✅ **Full-stack Integration**: Seamless frontend-backend communication  

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly with different startup data
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section above
- Review console logs for specific error messages
- Ensure all environment variables are set correctly
- Test with the provided example data

## 🚀 Future Enhancements

- Real-time collaboration features
- Advanced financial modeling
- Integration with external data sources
- Machine learning model improvements
- Mobile app development
- Advanced reporting and export features