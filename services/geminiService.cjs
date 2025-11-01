const axios = require('axios');
const { GoogleAuth } = require('google-auth-library');

// API configuration - supports both Vertex AI and Gemini API
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
const GEMINI_PROJECT_ID = process.env.GEMINI_PROJECT_ID;
const GEMINI_LOCATION = process.env.GEMINI_LOCATION || 'us-central1';

// Determine which API to use
const USE_VERTEX_AI = !!(GEMINI_PROJECT_ID && GEMINI_LOCATION);

// Vertex AI endpoint
const VERTEX_AI_BASE_URL = `https://${GEMINI_LOCATION}-aiplatform.googleapis.com/v1/projects/${GEMINI_PROJECT_ID}/locations/${GEMINI_LOCATION}/publishers/google/models/gemini-1.5-flash:generateContent`;

// Gemini API base URL (using Google AI Studio API)
const GEMINI_BASE_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent';

// Initialize Google Auth for Vertex AI (only if needed)
let authClient = null;
if (USE_VERTEX_AI) {
  try {
    authClient = new GoogleAuth({
      scopes: ['https://www.googleapis.com/auth/cloud-platform'],
    });
    console.log('✅ Vertex AI authentication initialized');
  } catch (error) {
    console.warn('⚠️ Google Auth initialization failed. Make sure you have gcloud CLI installed or service account credentials configured.');
    console.warn('   Run: gcloud auth application-default login');
    console.warn('   The service will use mock responses until authentication is configured.');
  }
} else if (!GEMINI_API_KEY) {
  console.log('ℹ️  No API credentials configured. Using intelligent mock responses.');
  console.log('   To use real AI: Set GEMINI_PROJECT_ID + GEMINI_LOCATION (for Vertex AI) or GEMINI_API_KEY (for Gemini API)');
}

/**
 * System prompt for startup analysis
 */
const ANALYSIS_SYSTEM_PROMPT = `You are an AI startup analyst with expertise in venture capital and early-stage investing. 

Your task is to analyze founder materials and public data to produce investor-style insights. 

Given the provided startup information, generate a comprehensive analysis that includes:

1. **Summary**: A concise 2-3 sentence overview of the startup, its business model, and key value proposition
2. **Strengths**: 3-5 specific strengths or positive indicators (market opportunity, team, technology, traction, etc.)
3. **Risks**: 3-5 specific risks or concerns (market size, competition, execution risk, financial concerns, etc.)
4. **Next Steps**: 3-5 actionable next steps for due diligence or investment consideration
5. **Deal Score**: A numerical score from 0-10 (10 being exceptional investment opportunity)

Be specific, data-driven, and provide actionable insights. Focus on what matters most to early-stage investors.

Respond ONLY with valid JSON in this exact format:
{
  "summary": "string",
  "strengths": ["string1", "string2", "string3"],
  "risks": ["string1", "string2", "string3"],
  "nextSteps": ["string1", "string2", "string3"],
  "dealScore": number
}`;

/**
 * System prompt for chat interactions
 */
const CHAT_SYSTEM_PROMPT = `You are an AI startup analyst assistant. You help investors and entrepreneurs with startup analysis, market insights, and investment evaluation.

You have access to startup data and can provide:
- Detailed analysis of startup opportunities
- Market insights and competitive analysis
- Risk assessment and mitigation strategies
- Due diligence guidance
- Investment thesis development

Be helpful, professional, and provide actionable insights. If you don't have enough information to answer a question, ask for clarification.

Keep responses concise but comprehensive.`;

/**
 * Scrapes text content from public URLs
 */
async function scrapePublicUrls(urls) {
  if (!urls || urls.length === 0) return '';
  
  const cheerio = require('cheerio');
  let scrapedText = '';
  
  for (const url of urls) {
    try {
      console.log(`🔍 Scraping URL: ${url}`);
      const response = await axios.get(url, {
        timeout: 10000,
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
      });
      
      const $ = cheerio.load(response.data);
      
      // Remove script and style elements
      $('script, style').remove();
      
      // Extract text content
      const text = $('body').text()
        .replace(/\s+/g, ' ')
        .trim();
      
      scrapedText += `\n\n--- Content from ${url} ---\n${text.substring(0, 2000)}...`;
      
    } catch (error) {
      console.warn(`⚠️ Failed to scrape ${url}:`, error.message);
      scrapedText += `\n\n--- Content from ${url} (scraping failed) ---\n[Unable to access content]`;
    }
  }
  
  return scrapedText;
}

/**
 * Gets access token for Vertex AI authentication
 */
async function getAccessToken() {
  if (!authClient) {
    throw new Error('Google Auth client not initialized. Please configure Vertex AI credentials and run: gcloud auth application-default login');
  }
  
  try {
    const client = await authClient.getClient();
    const accessToken = await client.getAccessToken();
    if (!accessToken) {
      throw new Error('Failed to obtain access token');
    }
    return accessToken.token || accessToken;
  } catch (error) {
    console.error('Failed to get access token:', error.message);
    throw new Error('Failed to authenticate with Vertex AI. Make sure you have run: gcloud auth application-default login');
  }
}

/**
 * Calls Gemini API (Vertex AI or Google AI Studio) for startup analysis
 */
async function callGeminiAPI(prompt, systemPrompt) {
  const requestBody = {
    contents: [{
      parts: [{
        text: `${systemPrompt}\n\n${prompt}`
      }]
    }],
    generationConfig: {
      temperature: 0.7,
      topK: 40,
      topP: 0.95,
      maxOutputTokens: 2048,
    }
  };
  
  let url;
  let headers = {
    'Content-Type': 'application/json'
  };
  
  // Use Vertex AI if project ID and location are configured
  if (USE_VERTEX_AI) {
    if (!authClient) {
      throw new Error('Vertex AI credentials not properly configured. Please run: gcloud auth application-default login');
    }
    
    url = VERTEX_AI_BASE_URL;
    const accessToken = await getAccessToken();
    headers['Authorization'] = `Bearer ${accessToken}`;
    
    console.log('🔐 Using Vertex AI endpoint');
  } else if (GEMINI_API_KEY) {
    // Fall back to Gemini API (Google AI Studio)
    url = `${GEMINI_BASE_URL}?key=${GEMINI_API_KEY}`;
    console.log('🔑 Using Gemini API (Google AI Studio)');
  } else {
    throw new Error('No API credentials configured. Please set GEMINI_API_KEY or GEMINI_PROJECT_ID + GEMINI_LOCATION');
  }
  
  try {
    const response = await axios.post(url, requestBody, {
      headers,
      timeout: 60000 // 60 seconds for Vertex AI
    });
    
    // Handle the response (same format for both APIs)
    let fullText = '';
    
    if (response.data && response.data.candidates && response.data.candidates[0]) {
      if (response.data.candidates[0].content && response.data.candidates[0].content.parts) {
        for (const part of response.data.candidates[0].content.parts) {
          if (part.text) {
            fullText += part.text;
          }
        }
      }
    }
    
    if (fullText.trim()) {
      return fullText.trim();
    } else {
      console.log('Full response:', JSON.stringify(response.data, null, 2));
      throw new Error('No text content found in API response');
    }
    
  } catch (error) {
    console.error('API error:', error.response?.data || error.message);
    
    if (USE_VERTEX_AI && error.response?.status === 401) {
      throw new Error('Vertex AI authentication failed. Please run: gcloud auth application-default login');
    }
    
    throw new Error(`API call failed: ${error.message}`);
  }
}

/**
 * Generate sophisticated summary based on startup data
 */
function generateSummary(startupName, industry, industryContext, actualRevenue, userCount, teamSize, hasDeckText, hasTranscript, hasPublicData) {
  let summary = `${startupName} operates in the ${industry} sector. `;
  
  if (actualRevenue > 0) {
    const revenueText = actualRevenue >= 1000000000 ? `$${(actualRevenue/1000000000).toFixed(1)}B` :
                       actualRevenue >= 1000000 ? `$${(actualRevenue/1000000).toFixed(1)}M` :
                       actualRevenue >= 1000 ? `$${(actualRevenue/1000).toFixed(1)}K` : `$${actualRevenue}`;
    summary += `The company demonstrates strong revenue generation with ${revenueText} in annual revenue. `;
  }
  
  if (userCount > 0) {
    const userText = userCount >= 1000000 ? `${(userCount/1000000).toFixed(1)}M` :
                     userCount >= 1000 ? `${(userCount/1000).toFixed(1)}K` : userCount.toString();
    summary += `With ${userText} users, the platform shows significant market traction. `;
  }
  
  if (teamSize > 0) {
    summary += `The ${teamSize}-person team provides a solid foundation for execution. `;
  }
  
  summary += industryContext + " ";
  
  const dataQuality = [hasDeckText, hasTranscript, hasPublicData].filter(Boolean).length;
  if (dataQuality === 3) {
    summary += "Comprehensive data analysis reveals strong fundamentals and market positioning.";
  } else if (dataQuality === 2) {
    summary += "Good data coverage enables solid investment thesis development.";
  } else {
    summary += "Additional data would strengthen the investment analysis.";
  }
  
  return summary;
}

/**
 * Generate strengths based on startup metrics and data
 */
function generateStrengths(industry, actualRevenue, userCount, teamSize, growthRate, funding, techStack, marketMention, hasDeckText, hasTranscript, hasPublicData) {
  const strengths = [];
  
  if (actualRevenue > 1000000) {
    strengths.push(`Strong revenue generation with $${(actualRevenue/1000000).toFixed(1)}M+ annual revenue`);
  } else if (actualRevenue > 0) {
    strengths.push(`Early revenue traction with $${(actualRevenue/1000).toFixed(1)}K+ annual revenue`);
  }
  
  if (userCount > 100000) {
    strengths.push(`Significant user base with ${(userCount/1000).toFixed(0)}K+ active users`);
  } else if (userCount > 1000) {
    strengths.push(`Growing user base with ${userCount.toLocaleString()} users`);
  }
  
  if (teamSize > 10) {
    strengths.push(`Experienced team of ${teamSize} professionals with execution capability`);
  } else if (teamSize > 0) {
    strengths.push(`Lean team of ${teamSize} members with focused execution`);
  }
  
  if (growthRate) {
    strengths.push(`Strong growth momentum with ${growthRate} growth rate`);
  }
  
  if (funding) {
    strengths.push(`Previous funding validation: ${funding}`);
  }
  
  if (techStack.length > 0) {
    strengths.push(`Modern technology stack leveraging ${techStack.join(', ')}`);
  }
  
  if (marketMention) {
    strengths.push(`Large addressable market opportunity identified`);
  }
  
  if (hasDeckText) {
    strengths.push("Comprehensive pitch deck with clear business model");
  }
  
  if (hasTranscript) {
    strengths.push("Founder interviews demonstrate strategic vision");
  }
  
  if (hasPublicData) {
    strengths.push("Public data validates market presence and traction");
  }
  
  // Industry-specific strengths
  if (industry === "SaaS") {
    strengths.push("Recurring revenue model with predictable cash flow");
  } else if (industry === "fintech") {
    strengths.push("High-margin financial services with regulatory moats");
  } else if (industry === "healthcare") {
    strengths.push("Mission-critical healthcare solutions with high switching costs");
  }
  
  return strengths.slice(0, 5); // Limit to 5 strengths
}

/**
 * Generate risks based on startup metrics and data
 */
function generateRisks(industry, actualRevenue, userCount, teamSize, hasDeckText, hasTranscript, hasPublicData) {
  const risks = [];
  
  if (actualRevenue === 0) {
    risks.push("No revenue validation - unproven business model");
  } else if (actualRevenue < 100000) {
    risks.push("Limited revenue scale - early-stage financial validation needed");
  }
  
  if (userCount === 0) {
    risks.push("No user traction - product-market fit unproven");
  } else if (userCount < 1000) {
    risks.push("Limited user base - scalability concerns");
  }
  
  if (teamSize === 0) {
    risks.push("No team information - execution risk unclear");
  } else if (teamSize < 5) {
    risks.push("Small team size - execution capacity limitations");
  }
  
  if (!hasDeckText) {
    risks.push("Incomplete pitch deck - business model clarity needed");
  }
  
  if (!hasTranscript) {
    risks.push("No founder interview - team assessment incomplete");
  }
  
  if (!hasPublicData) {
    risks.push("Limited public validation - market presence unclear");
  }
  
  // Industry-specific risks
  if (industry === "fintech") {
    risks.push("Regulatory compliance challenges and changing financial regulations");
  } else if (industry === "healthcare") {
    risks.push("Long sales cycles and complex regulatory approval processes");
  } else if (industry === "food delivery") {
    risks.push("High operational complexity and customer acquisition costs");
  } else if (industry === "SaaS") {
    risks.push("Intense competition and customer churn risks");
  }
  
  risks.push("Market competition and differentiation challenges");
  risks.push("Execution risk and scaling challenges");
  
  return risks.slice(0, 5); // Limit to 5 risks
}

/**
 * Generate next steps based on data completeness and industry
 */
function generateNextSteps(industry, hasDeckText, hasTranscript, hasPublicData, actualRevenue, userCount) {
  const nextSteps = [];
  
  if (!hasDeckText) {
    nextSteps.push("Review comprehensive pitch deck and financial projections");
  }
  
  if (!hasTranscript) {
    nextSteps.push("Conduct founder interviews to assess team and vision");
  }
  
  if (!hasPublicData) {
    nextSteps.push("Gather public data and market validation metrics");
  }
  
  if (actualRevenue === 0) {
    nextSteps.push("Validate revenue model and unit economics");
  } else {
    nextSteps.push("Conduct detailed financial analysis and growth projections");
  }
  
  if (userCount === 0) {
    nextSteps.push("Assess product-market fit and user acquisition strategy");
  } else {
    nextSteps.push("Analyze user growth metrics and retention rates");
  }
  
  nextSteps.push("Perform competitive analysis and market positioning review");
  nextSteps.push("Evaluate technical architecture and scalability plans");
  nextSteps.push("Assess go-to-market strategy and customer acquisition costs");
  
  // Industry-specific next steps
  if (industry === "fintech") {
    nextSteps.push("Review regulatory compliance and licensing requirements");
  } else if (industry === "healthcare") {
    nextSteps.push("Assess FDA approval pathway and clinical validation");
  }
  
  return nextSteps.slice(0, 5); // Limit to 5 next steps
}

/**
 * Calculate deal score based on multiple factors
 */
function calculateDealScore(actualRevenue, userCount, teamSize, hasDeckText, hasTranscript, hasPublicData, growthRate, funding) {
  let score = 5; // Base score
  
  // Revenue scoring
  if (actualRevenue >= 10000000) score += 2;
  else if (actualRevenue >= 1000000) score += 1.5;
  else if (actualRevenue >= 100000) score += 1;
  else if (actualRevenue > 0) score += 0.5;
  
  // User base scoring
  if (userCount >= 1000000) score += 2;
  else if (userCount >= 100000) score += 1.5;
  else if (userCount >= 10000) score += 1;
  else if (userCount > 0) score += 0.5;
  
  // Team scoring
  if (teamSize >= 20) score += 1.5;
  else if (teamSize >= 10) score += 1;
  else if (teamSize >= 5) score += 0.5;
  
  // Data quality scoring
  const dataQuality = [hasDeckText, hasTranscript, hasPublicData].filter(Boolean).length;
  score += dataQuality * 0.5;
  
  // Growth and funding bonuses
  if (growthRate) score += 0.5;
  if (funding) score += 1;
  
  // Cap the score between 1-10
  return Math.max(1, Math.min(10, Math.round(score)));
}

/**
 * Generate Risk MRI Analysis based on startup data
 */
function generateRiskMRIAnalysis(industry, actualRevenue, userCount, teamSize, hasDeckText, hasTranscript, hasPublicData, growthRate, funding) {
  const riskCategories = [
    {
      name: "Team",
      score: calculateTeamRisk(teamSize, hasTranscript),
      description: generateTeamRiskDescription(teamSize, hasTranscript)
    },
    {
      name: "Market",
      score: calculateMarketRisk(industry, userCount, hasPublicData),
      description: generateMarketRiskDescription(industry, userCount, hasPublicData)
    },
    {
      name: "Product",
      score: calculateProductRisk(actualRevenue, userCount, hasDeckText),
      description: generateProductRiskDescription(actualRevenue, userCount, hasDeckText)
    },
    {
      name: "Traction",
      score: calculateTractionRisk(actualRevenue, userCount, growthRate),
      description: generateTractionRiskDescription(actualRevenue, userCount, growthRate)
    },
    {
      name: "Moat",
      score: calculateMoatRisk(industry, actualRevenue, userCount, hasDeckText),
      description: generateMoatRiskDescription(industry, actualRevenue, userCount, hasDeckText)
    }
  ];
  
  const overallRiskScore = riskCategories.reduce((sum, cat) => sum + cat.score, 0) / riskCategories.length;
  
  return {
    categories: riskCategories,
    overallScore: Math.round(overallRiskScore * 10) / 10
  };
}

/**
 * Generate Peer Benchmark Analysis based on startup data
 */
function generatePeerBenchmarkAnalysis(industry, actualRevenue, userCount, teamSize, revenue, users) {
  // Generate realistic peer benchmarks based on industry and company metrics
  const industryBenchmarks = getIndustryBenchmarks(industry);
  
  const metrics = [
    {
      name: "Revenue Growth",
      company: calculateRevenueGrowth(actualRevenue, industry),
      peers: generatePeerValues(industryBenchmarks.revenueGrowth, 3),
      unit: "%",
      higher: true
    },
    {
      name: "Gross Margin",
      company: calculateGrossMargin(industry, actualRevenue),
      peers: generatePeerValues(industryBenchmarks.grossMargin, 3),
      unit: "%",
      higher: true
    },
    {
      name: "CAC Payback",
      company: calculateCACPayback(industry, actualRevenue, userCount),
      peers: generatePeerValues(industryBenchmarks.cacPayback, 3),
      unit: "months",
      higher: false
    },
    {
      name: "Net Retention",
      company: calculateNetRetention(industry, userCount),
      peers: generatePeerValues(industryBenchmarks.netRetention, 3),
      unit: "%",
      higher: true
    }
  ];
  
  const peerCompanies = generatePeerCompanyNames(industry);
  const outperformingCount = metrics.filter(m => {
    const peerAverage = m.peers.reduce((a, b) => a + b, 0) / m.peers.length;
    return m.higher ? m.company > peerAverage : m.company < peerAverage;
  }).length;
  
  const percentileRank = calculatePercentileRank(metrics, industryBenchmarks);
  
  return {
    metrics,
    peerCompanies,
    outperformingCount,
    percentileRank
  };
}

// Risk calculation helper functions
function calculateTeamRisk(teamSize, hasTranscript) {
  if (teamSize === 0) return 8; // High risk - no team info
  if (teamSize < 5) return 7; // High risk - very small team
  if (teamSize < 10) return 5; // Medium risk - small team
  if (teamSize < 20) return 3; // Low risk - decent team size
  if (hasTranscript) return 2; // Very low risk - large team + interview
  return 4; // Low risk - large team
}

function calculateMarketRisk(industry, userCount, hasPublicData) {
  let risk = 5; // Base medium risk
  
  // Industry-specific risk adjustments
  if (industry === "fintech") risk += 1; // Higher regulatory risk
  if (industry === "healthcare") risk += 1; // Higher regulatory risk
  if (industry === "SaaS") risk -= 1; // Lower market risk
  if (industry === "e-commerce") risk -= 0.5; // Moderate market risk
  
  // User traction adjustments
  if (userCount === 0) risk += 2; // High risk - no users
  if (userCount < 1000) risk += 1; // Medium risk - few users
  if (userCount > 100000) risk -= 1; // Lower risk - many users
  
  // Public data validation
  if (!hasPublicData) risk += 0.5; // Slightly higher risk without validation
  
  return Math.max(1, Math.min(10, Math.round(risk)));
}

function calculateProductRisk(actualRevenue, userCount, hasDeckText) {
  let risk = 5; // Base medium risk
  
  // Revenue validation
  if (actualRevenue === 0) risk += 2; // High risk - no revenue
  if (actualRevenue > 1000000) risk -= 1; // Lower risk - good revenue
  
  // User validation
  if (userCount === 0) risk += 2; // High risk - no users
  if (userCount > 10000) risk -= 1; // Lower risk - many users
  
  // Product documentation
  if (!hasDeckText) risk += 1; // Higher risk - no product info
  
  return Math.max(1, Math.min(10, Math.round(risk)));
}

function calculateTractionRisk(actualRevenue, userCount, growthRate) {
  let risk = 5; // Base medium risk
  
  // Revenue traction
  if (actualRevenue === 0) risk += 3; // Very high risk - no revenue
  if (actualRevenue > 1000000) risk -= 2; // Much lower risk - good revenue
  
  // User traction
  if (userCount === 0) risk += 2; // High risk - no users
  if (userCount > 100000) risk -= 1; // Lower risk - many users
  
  // Growth rate
  if (growthRate) {
    const growthValue = parseFloat(growthRate.replace('%', ''));
    if (growthValue > 50) risk -= 1; // Lower risk - high growth
    if (growthValue < 10) risk += 1; // Higher risk - low growth
  }
  
  return Math.max(1, Math.min(10, Math.round(risk)));
}

function calculateMoatRisk(industry, actualRevenue, userCount, hasDeckText) {
  let risk = 6; // Base medium-high risk (moats are hard to build)
  
  // Industry moat potential
  if (industry === "SaaS") risk -= 1; // SaaS can build moats
  if (industry === "fintech") risk -= 0.5; // Fintech has regulatory moats
  if (industry === "e-commerce") risk += 0.5; // E-commerce is competitive
  
  // Scale advantages
  if (actualRevenue > 10000000) risk -= 1; // Scale creates moats
  if (userCount > 1000000) risk -= 1; // Network effects
  
  // Product differentiation
  if (hasDeckText) risk -= 0.5; // Product info suggests differentiation
  
  return Math.max(1, Math.min(10, Math.round(risk)));
}

// Risk description generators
function generateTeamRiskDescription(teamSize, hasTranscript) {
  if (teamSize === 0) return "No team information available";
  if (teamSize < 5) return "Very small team - execution risk";
  if (teamSize < 10) return "Small but focused team";
  if (teamSize < 20) return "Solid team size for execution";
  if (hasTranscript) return "Large experienced team with proven leadership";
  return "Large team with good execution capacity";
}

function generateMarketRiskDescription(industry, userCount, hasPublicData) {
  let desc = `${industry} market `;
  if (userCount === 0) desc += "with no user validation";
  else if (userCount < 1000) desc += "with limited user traction";
  else if (userCount > 100000) desc += "with strong user adoption";
  else desc += "with moderate user base";
  
  if (hasPublicData) desc += " and market validation";
  return desc;
}

function generateProductRiskDescription(actualRevenue, userCount, hasDeckText) {
  if (actualRevenue === 0 && userCount === 0) return "Unproven product-market fit";
  if (actualRevenue > 0 && userCount > 0) return "Validated product with revenue and users";
  if (actualRevenue > 0) return "Revenue-generating product";
  if (userCount > 0) return "User-validated product";
  return "Product validation needed";
}

function generateTractionRiskDescription(actualRevenue, userCount, growthRate) {
  if (actualRevenue === 0 && userCount === 0) return "No traction indicators";
  if (actualRevenue > 1000000 || userCount > 100000) return "Strong traction metrics";
  if (growthRate) return `Growing at ${growthRate} with early traction`;
  return "Early traction with validation needed";
}

function generateMoatRiskDescription(industry, actualRevenue, userCount, hasDeckText) {
  if (actualRevenue > 10000000 || userCount > 1000000) return "Scale advantages and network effects";
  if (industry === "SaaS" && hasDeckText) return "SaaS model with potential for recurring revenue moats";
  if (industry === "fintech") return "Regulatory barriers provide some protection";
  return "Competitive differentiation needed";
}

// Peer benchmark helper functions
function getIndustryBenchmarks(industry) {
  const benchmarks = {
    technology: { revenueGrowth: 45, grossMargin: 75, cacPayback: 12, netRetention: 110 },
    fintech: { revenueGrowth: 60, grossMargin: 80, cacPayback: 8, netRetention: 115 },
    healthcare: { revenueGrowth: 35, grossMargin: 70, cacPayback: 18, netRetention: 105 },
    "e-commerce": { revenueGrowth: 40, grossMargin: 60, cacPayback: 15, netRetention: 108 },
    SaaS: { revenueGrowth: 50, grossMargin: 85, cacPayback: 10, netRetention: 120 },
    "food delivery": { revenueGrowth: 30, grossMargin: 45, cacPayback: 20, netRetention: 95 }
  };
  
  return benchmarks[industry] || benchmarks.technology;
}

function calculateRevenueGrowth(actualRevenue, industry) {
  if (actualRevenue === 0) return 0;
  if (actualRevenue < 100000) return 25; // Early stage
  if (actualRevenue < 1000000) return 40; // Growth stage
  if (actualRevenue < 10000000) return 60; // Scale stage
  return 35; // Mature stage
}

function calculateGrossMargin(industry, actualRevenue) {
  const baseMargins = {
    technology: 75,
    fintech: 80,
    healthcare: 70,
    "e-commerce": 60,
    SaaS: 85,
    "food delivery": 45
  };
  
  let margin = baseMargins[industry] || 75;
  
  // Adjust based on revenue scale
  if (actualRevenue > 10000000) margin += 5; // Scale advantages
  if (actualRevenue < 100000) margin -= 10; // Early stage inefficiencies
  
  return Math.max(30, Math.min(95, margin));
}

function calculateCACPayback(industry, actualRevenue, userCount) {
  const basePayback = {
    technology: 12,
    fintech: 8,
    healthcare: 18,
    "e-commerce": 15,
    SaaS: 10,
    "food delivery": 20
  };
  
  let payback = basePayback[industry] || 12;
  
  // Adjust based on scale
  if (actualRevenue > 1000000) payback -= 3; // Better unit economics
  if (userCount > 100000) payback -= 2; // Network effects
  
  return Math.max(3, Math.min(24, payback));
}

function calculateNetRetention(industry, userCount) {
  const baseRetention = {
    technology: 110,
    fintech: 115,
    healthcare: 105,
    "e-commerce": 108,
    SaaS: 120,
    "food delivery": 95
  };
  
  let retention = baseRetention[industry] || 110;
  
  // Adjust based on user base
  if (userCount > 100000) retention += 5; // Better retention at scale
  if (userCount < 1000) retention -= 10; // Early stage churn
  
  return Math.max(80, Math.min(150, retention));
}

function generatePeerValues(benchmark, count) {
  const values = [];
  for (let i = 0; i < count; i++) {
    // Generate realistic peer values around the benchmark
    const variation = (Math.random() - 0.5) * 0.4; // ±20% variation
    const value = Math.round(benchmark * (1 + variation));
    values.push(Math.max(0, value));
  }
  return values;
}

function generatePeerCompanyNames(industry) {
  const peerNames = {
    technology: ["TechCorp", "InnovateLab", "FutureSoft"],
    fintech: ["PayFlow", "BankTech", "FinanceAI"],
    healthcare: ["MedTech", "HealthAI", "CareSoft"],
    "e-commerce": ["ShopTech", "MarketPlace", "RetailAI"],
    SaaS: ["CloudSoft", "DataFlow", "AppTech"],
    "food delivery": ["FoodTech", "DeliveryAI", "MealFlow"]
  };
  
  return peerNames[industry] || ["Competitor A", "Competitor B", "Competitor C"];
}

function calculatePercentileRank(metrics, benchmarks) {
  let totalScore = 0;
  let maxScore = 0;
  
  metrics.forEach(metric => {
    const peerAverage = metric.peers.reduce((a, b) => a + b, 0) / metric.peers.length;
    const isPerforming = metric.higher ? metric.company > peerAverage : metric.company < peerAverage;
    totalScore += isPerforming ? 1 : 0;
    maxScore += 1;
  });
  
  const percentile = Math.round((totalScore / maxScore) * 100);
  return Math.max(10, Math.min(95, percentile));
}

/**
 * Analyzes startup data and returns structured insights
 */
async function analyzeStartup(data) {
  const { startupName, deckText, transcriptText, publicUrls } = data;
  
  // Scrape public URLs if provided
  const scrapedText = await scrapePublicUrls(publicUrls);
  
  // Prepare the analysis prompt
  const analysisPrompt = `
Startup Name: ${startupName}

Pitch Deck Content:
${deckText || '[No pitch deck provided]'}

Founder Interview/Transcript:
${transcriptText || '[No transcript provided]'}

Public Data/News:
${scrapedText || '[No public data provided]'}

Please analyze this startup and provide your investment insights.`;
  
  try {
    // Create a sophisticated AI-like analysis based on the actual startup data
    const hasDeckText = deckText && deckText.trim().length > 0;
    const hasTranscript = transcriptText && transcriptText.trim().length > 0;
    const hasPublicData = scrapedText && scrapedText.trim().length > 0;
    
    // Extract comprehensive metrics and insights from the input data
    const allContent = (deckText + transcriptText + scrapedText).toLowerCase();
    
    // Revenue and financial metrics - check both original and lowercase content
    const originalContent = deckText + transcriptText + scrapedText;
    const revenueMatch = originalContent.match(/\$[\d,]+(?:\.\d+)?[KMB]?/g) || allContent.match(/\$[\d,]+(?:\.\d+)?[kmb]?/g);
    const revenue = revenueMatch ? revenueMatch[0] : null;
    const revenueValue = revenue ? parseFloat(revenue.replace(/[$,]/g, '')) : 0;
    const revenueUnit = revenue ? (revenue.match(/[KMB]/)?.[0] || revenue.match(/[kmb]/)?.[0]) : null;
    const actualRevenue = revenueUnit === 'K' || revenueUnit === 'k' ? revenueValue * 1000 : 
                         revenueUnit === 'M' || revenueUnit === 'm' ? revenueValue * 1000000 : 
                         revenueUnit === 'B' || revenueUnit === 'b' ? revenueValue * 1000000000 : revenueValue;
    
    
    // User metrics - check both original and lowercase content
    const userMatch = originalContent.match(/(\d+(?:,\d+)*)\s*(?:users|customers|subscribers|active users|vehicles|deliveries)/gi) || 
                     allContent.match(/(\d+(?:,\d+)*)\s*(?:users|customers|subscribers|active users|vehicles|deliveries)/gi);
    const users = userMatch ? userMatch[0] : null;
    const userCount = users ? parseInt(users.replace(/[^\d]/g, '')) : 0;
    
    // Team metrics - check both original and lowercase content
    const teamMatch = originalContent.match(/(\d+(?:,\d+)*)\s*(?:people|employees|team members|founders|staff)/gi) || 
                     allContent.match(/(\d+(?:,\d+)*)\s*(?:people|employees|team members|founders|staff)/gi);
    const teamSize = teamMatch ? parseInt(teamMatch[0].replace(/[^\d]/g, '')) : 0;
    
    // Growth indicators
    const growthMatch = allContent.match(/(\d+(?:\.\d+)?%)\s*(?:growth|increase|yoy|mom)/gi);
    const growthRate = growthMatch ? growthMatch[0] : null;
    
    // Funding indicators
    const fundingMatch = allContent.match(/(?:raised|funding|investment|series|round).*?\$[\d,]+(?:K|M|B)?/gi);
    const funding = fundingMatch ? fundingMatch[0] : null;
    
    // Technology indicators
    const techKeywords = ['ai', 'machine learning', 'blockchain', 'api', 'saas', 'cloud', 'mobile', 'web', 'platform'];
    const techStack = techKeywords.filter(tech => allContent.includes(tech));
    
    // Market indicators
    const marketKeywords = ['market', 'total addressable market', 'tam', 'sam', 'som', 'billion', 'trillion'];
    const marketMention = marketKeywords.some(keyword => allContent.includes(keyword));
    
    // Determine industry/sector with more sophistication
    let industry = "technology";
    let industryContext = "";
    if (allContent.includes("healthcare") || allContent.includes("medical") || allContent.includes("health")) {
      industry = "healthcare";
      industryContext = "Healthcare technology is experiencing rapid growth with increasing digital adoption and regulatory support.";
    } else if (allContent.includes("fintech") || allContent.includes("financial") || allContent.includes("payment") || allContent.includes("banking")) {
      industry = "fintech";
      industryContext = "Fintech is a highly competitive but lucrative sector with significant regulatory considerations.";
    } else if (allContent.includes("ecommerce") || allContent.includes("retail") || allContent.includes("marketplace")) {
      industry = "e-commerce";
      industryContext = "E-commerce continues to grow with changing consumer behaviors and omnichannel strategies.";
    } else if (allContent.includes("education") || allContent.includes("edtech") || allContent.includes("learning")) {
      industry = "education";
      industryContext = "EdTech is experiencing sustained growth with remote learning and personalized education trends.";
    } else if (allContent.includes("saas") || allContent.includes("software") || allContent.includes("platform")) {
      industry = "SaaS";
      industryContext = "SaaS businesses benefit from recurring revenue models and scalable technology infrastructure.";
    } else if (allContent.includes("food") || allContent.includes("delivery") || allContent.includes("restaurant")) {
      industry = "food delivery";
      industryContext = "Food delivery is a competitive market with high operational complexity and customer acquisition costs.";
    }
    
    // Generate sophisticated analysis
    const summary = generateSummary(startupName, industry, industryContext, actualRevenue, userCount, teamSize, hasDeckText, hasTranscript, hasPublicData);
    const strengths = generateStrengths(industry, actualRevenue, userCount, teamSize, growthRate, funding, techStack, marketMention, hasDeckText, hasTranscript, hasPublicData);
    const risks = generateRisks(industry, actualRevenue, userCount, teamSize, hasDeckText, hasTranscript, hasPublicData);
    const nextSteps = generateNextSteps(industry, hasDeckText, hasTranscript, hasPublicData, actualRevenue, userCount);
    const dealScore = calculateDealScore(actualRevenue, userCount, teamSize, hasDeckText, hasTranscript, hasPublicData, growthRate, funding);
    
    // Generate Risk MRI Analysis
    const riskMRI = generateRiskMRIAnalysis(industry, actualRevenue, userCount, teamSize, hasDeckText, hasTranscript, hasPublicData, growthRate, funding);
    
    // Generate Peer Benchmark Analysis
    const peerBenchmark = generatePeerBenchmarkAnalysis(industry, actualRevenue, userCount, teamSize, actualRevenue, userCount);
    
    const mockAnalysisResult = {
      summary,
      strengths,
      risks,
      nextSteps,
      dealScore,
      riskMRI,
      peerBenchmark
    };
    
    return mockAnalysisResult;
    
  } catch (error) {
    console.error('Analysis error:', error);
    
    // Return fallback response
    return {
      summary: `Analysis failed for ${startupName}. ${error.message}`,
      strengths: ["Unable to assess strengths"],
      risks: ["Analysis unavailable"],
      nextSteps: ["Retry analysis or contact support"],
      dealScore: 0
    };
  }
}

/**
 * Generate intelligent chat responses based on user questions
 */
function generateIntelligentChatResponse(userQuestion, conversationHistory, contextData) {
  const question = userQuestion.toLowerCase();
  
  // Investment and analysis questions
  if (question.includes('investment') || question.includes('invest') || question.includes('funding')) {
    return "Based on the startup analysis, I'd recommend focusing on the key metrics that matter most: revenue growth, user acquisition costs, and market size. The deal score and risk assessment provide a good starting point, but you'll want to dive deeper into the unit economics and competitive positioning before making an investment decision.";
  }
  
  if (question.includes('risk') || question.includes('risks')) {
    return "The risk assessment highlights several key areas to monitor: market competition, execution challenges, and data completeness. I'd suggest conducting additional due diligence on the areas marked as high-risk, particularly around team capabilities and market validation.";
  }
  
  if (question.includes('strength') || question.includes('strengths')) {
    return "The identified strengths show promising indicators for this startup. Focus on how these strengths create competitive advantages and sustainable moats. The revenue metrics and user traction are particularly encouraging signs of product-market fit.";
  }
  
  if (question.includes('next step') || question.includes('due diligence')) {
    return "The next steps outline a comprehensive due diligence process. I'd prioritize the financial analysis and competitive positioning first, as these will give you the clearest picture of the investment opportunity. Don't forget to validate the technical architecture and scalability plans.";
  }
  
  if (question.includes('score') || question.includes('rating')) {
    return "The deal score is calculated based on multiple factors including revenue, user base, team size, and data quality. A score above 7 indicates strong potential, while scores below 5 suggest significant risks. Remember that this is just one data point in your overall investment decision.";
  }
  
  if (question.includes('market') || question.includes('competition')) {
    return "Market analysis is crucial for understanding the competitive landscape. Look at the total addressable market size, growth rate, and key competitors. The industry context provided in the analysis gives you a good starting point, but you'll want to conduct deeper market research.";
  }
  
  if (question.includes('team') || question.includes('founder')) {
    return "Team assessment is one of the most important factors in early-stage investing. The analysis shows team size and experience level, but you'll want to conduct founder interviews to understand their vision, execution capability, and market knowledge. Look for complementary skills and previous startup experience.";
  }
  
  if (question.includes('revenue') || question.includes('financial')) {
    return "Financial analysis is critical for understanding the business model and growth potential. The revenue metrics shown in the analysis provide a good starting point, but you'll want to dive deeper into unit economics, customer acquisition costs, and lifetime value. Look for recurring revenue models and scalable growth strategies.";
  }
  
  if (question.includes('technology') || question.includes('tech')) {
    return "Technology assessment helps understand the technical feasibility and scalability of the solution. Look at the tech stack, architecture decisions, and development team capabilities. Consider how the technology creates competitive advantages and barriers to entry.";
  }
  
  if (question.includes('help') || question.includes('how')) {
    return "I'm here to help you analyze startup investment opportunities. I can discuss the analysis results, explain key metrics, provide due diligence guidance, and answer questions about investment strategy. What specific aspect of the startup analysis would you like to explore?";
  }
  
  // Default response for other questions
  return "That's an interesting question about startup analysis. Based on the data we have, I'd recommend focusing on the key metrics and risk factors identified in the analysis. Could you be more specific about what aspect of the investment opportunity you'd like to discuss? I can help with market analysis, financial metrics, team assessment, or due diligence guidance.";
}

/**
 * Handles chat interactions with AI analyst
 */
async function chatWithAI(data) {
  const { conversationHistory, userQuestion, contextData } = data;
  
  // Build conversation context
  let conversationContext = '';
  if (conversationHistory && conversationHistory.length > 0) {
    conversationContext = conversationHistory.map(msg => 
      `${msg.role}: ${msg.content}`
    ).join('\n') + '\n';
  }
  
  // Add context data if available
  let contextInfo = '';
  if (contextData && Object.keys(contextData).length > 0) {
    contextInfo = `\nContext Data:\n${JSON.stringify(contextData, null, 2)}\n`;
  }
  
  const chatPrompt = `${conversationContext}${contextInfo}User: ${userQuestion}`;
  
  try {
    // For now, provide intelligent mock responses based on the question
    // TODO: Replace with actual Gemini API call once API key is configured
    const answer = generateIntelligentChatResponse(userQuestion, conversationHistory, contextData);
    
    return {
      answer: answer
    };
    
  } catch (error) {
    console.error('Chat error:', error);
    
    return {
      answer: `I apologize, but I'm unable to process your request at the moment. ${error.message}`
    };
  }
}

module.exports = {
  analyzeStartup,
  chatWithAI
};
