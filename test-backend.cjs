/**
 * Test script for AI Analyst Backend
 * Run with: node test-backend.js
 */

const axios = require('axios');

const BASE_URL = 'http://localhost:3001';

// Test data
const testStartupData = {
  startupName: "TechFlow Solutions",
  deckText: `
    TechFlow Solutions - AI-Powered Supply Chain Optimization
    
    Problem: Supply chains lose $1.2T annually due to inefficiencies
    Solution: AI platform that optimizes logistics in real-time
    Market: $15B TAM, growing 12% annually
    Traction: $2M ARR, 150+ enterprise customers
    Team: Ex-Amazon, Google, McKinsey founders
    Funding: Seeking $5M Series A
  `,
  transcriptText: `
    Interviewer: Tell us about your biggest customer win.
    Founder: We helped Walmart reduce logistics costs by 23% in Q3. 
    They're now our largest customer at $500K ARR.
    Interviewer: What's your competitive moat?
    Founder: Our proprietary ML algorithms have 3 years of training data
    and we're 40% more accurate than competitors.
  `,
  publicUrls: [
    "https://techcrunch.com/2024/01/15/techflow-raises-series-a",
    "https://crunchbase.com/organization/techflow-solutions"
  ]
};

const testChatData = {
  conversationHistory: [
    {
      role: "user",
      content: "What are the main risks for this startup?"
    },
    {
      role: "assistant", 
      content: "Based on the analysis, the main risks include market competition and customer concentration."
    }
  ],
  userQuestion: "How can we mitigate the customer concentration risk?",
  contextData: {
    startupName: "TechFlow Solutions",
    industry: "Supply Chain Tech"
  }
};

async function testHealthEndpoints() {
  console.log('🏥 Testing health endpoints...');
  
  try {
    const healthResponse = await axios.get(`${BASE_URL}/health`);
    console.log('✅ Main health check:', healthResponse.data);
    
    const analyzeHealthResponse = await axios.get(`${BASE_URL}/api/analyze/health`);
    console.log('✅ Analysis health check:', analyzeHealthResponse.data);
    
    const chatHealthResponse = await axios.get(`${BASE_URL}/api/chat/health`);
    console.log('✅ Chat health check:', chatHealthResponse.data);
    
  } catch (error) {
    console.error('❌ Health check failed:', error.message);
  }
}

async function testAnalyzeEndpoint() {
  console.log('\n🔍 Testing analyze endpoint...');
  
  try {
    const response = await axios.post(`${BASE_URL}/api/analyze`, testStartupData, {
      headers: { 'Content-Type': 'application/json' },
      timeout: 60000 // 60 second timeout for AI processing
    });
    
    console.log('✅ Analysis successful!');
    console.log('📊 Response:', JSON.stringify(response.data, null, 2));
    
    // Validate response structure
    const { summary, strengths, risks, nextSteps, dealScore } = response.data;
    
    if (!summary || !Array.isArray(strengths) || !Array.isArray(risks) || 
        !Array.isArray(nextSteps) || typeof dealScore !== 'number') {
      console.warn('⚠️ Response structure validation failed');
    } else {
      console.log('✅ Response structure validation passed');
    }
    
  } catch (error) {
    console.error('❌ Analysis test failed:', error.response?.data || error.message);
  }
}

async function testChatEndpoint() {
  console.log('\n💬 Testing chat endpoint...');
  
  try {
    const response = await axios.post(`${BASE_URL}/api/chat`, testChatData, {
      headers: { 'Content-Type': 'application/json' },
      timeout: 30000
    });
    
    console.log('✅ Chat successful!');
    console.log('🤖 Response:', JSON.stringify(response.data, null, 2));
    
    // Validate response structure
    if (!response.data.answer || typeof response.data.answer !== 'string') {
      console.warn('⚠️ Chat response structure validation failed');
    } else {
      console.log('✅ Chat response structure validation passed');
    }
    
  } catch (error) {
    console.error('❌ Chat test failed:', error.response?.data || error.message);
  }
}

async function testErrorHandling() {
  console.log('\n🚨 Testing error handling...');
  
  // Test invalid analyze request
  try {
    await axios.post(`${BASE_URL}/api/analyze`, {
      // Missing required startupName
      deckText: "Some content"
    });
    console.warn('⚠️ Should have failed validation');
  } catch (error) {
    if (error.response?.status === 400) {
      console.log('✅ Validation error handling works');
    } else {
      console.error('❌ Unexpected error:', error.message);
    }
  }
  
  // Test invalid chat request
  try {
    await axios.post(`${BASE_URL}/api/chat`, {
      // Missing required userQuestion
      conversationHistory: []
    });
    console.warn('⚠️ Should have failed validation');
  } catch (error) {
    if (error.response?.status === 400) {
      console.log('✅ Chat validation error handling works');
    } else {
      console.error('❌ Unexpected error:', error.message);
    }
  }
}

async function runAllTests() {
  console.log('🚀 Starting AI Analyst Backend Tests\n');
  console.log('Make sure the backend is running on http://localhost:3001\n');
  
  await testHealthEndpoints();
  await testAnalyzeEndpoint();
  await testChatEndpoint();
  await testErrorHandling();
  
  console.log('\n✨ Test suite completed!');
  console.log('\n📝 Next steps:');
  console.log('1. Set up your .env file with Gemini API credentials');
  console.log('2. Test with real data from your frontend');
  console.log('3. Deploy to your preferred hosting platform');
}

// Run tests if this file is executed directly
if (require.main === module) {
  runAllTests().catch(console.error);
}

module.exports = {
  testHealthEndpoints,
  testAnalyzeEndpoint,
  testChatEndpoint,
  testErrorHandling,
  runAllTests
};
