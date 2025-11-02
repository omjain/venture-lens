const axios = require("axios");
const cheerio = require("cheerio");

// Config
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
const GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent";

// Scraper
async function scrapeUrls(urls = []) {
  let text = "";
  for (const url of urls) {
    try {
      const res = await axios.get(url, { headers: { "User-Agent": "Mozilla/5.0" } });
      const $ = cheerio.load(res.data);
      $("script, style, noscript").remove();
      text += `\n\n--- ${url} ---\n${$("body").text().replace(/\s+/g, " ").slice(0, 2000)}...`;
    } catch (err) {
      console.error(`Scraping failed for ${url}:`, err.message);
      text += `\n\n--- ${url} --- [Scraping failed]`;
    }
  }
  return text;
}

// Default structured response
function getDefaultResponse() {
  return {
    summary: "No summary available.",
    strengths: [],
    risks: [],
    nextSteps: [],
    dealScore: 0,
    riskMRI: {
      categories: [
        { name: "Team", score: 0, description: "Not analyzed" },
        { name: "Market", score: 0, description: "Not analyzed" },
        { name: "Product", score: 0, description: "Not analyzed" },
        { name: "Traction", score: 0, description: "Not analyzed" },
        { name: "Moat", score: 0, description: "Not analyzed" }
      ],
      overallScore: 0
    },
    peerBenchmark: {
      metrics: [],
      peerCompanies: [],
      outperformingCount: 0,
      percentileRank: 0
    }
  };
}

// Main
async function analyzeStartup(data) {
  const { startupName, deckText = "", transcriptText = "", publicUrls = [] } = data;

  const scrapedText = await scrapeUrls(publicUrls);

  const prompt = `
You are a venture capital startup analyst. Analyze the startup using deck, transcript, and public data.

Return ONLY valid JSON (no markdown, no commentary) matching EXACTLY this structure:

{
  "summary": "short text summary",
  "strengths": ["..."],
  "risks": ["..."],
  "nextSteps": ["..."],
  "dealScore": number (0-10),
  "riskMRI": {
    "categories": [
      {"name": "Team", "score": number, "description": "..."},
      {"name": "Market", "score": number, "description": "..."},
      {"name": "Product", "score": number, "description": "..."},
      {"name": "Traction", "score": number, "description": "..."},
      {"name": "Moat", "score": number, "description": "..."}
    ],
    "overallScore": number
  },
  "peerBenchmark": {
    "metrics": [
      {"name": "Revenue Growth", "company": number, "peers": [numbers], "unit": "%", "higher": true},
      {"name": "Gross Margin", "company": number, "peers": [numbers], "unit": "%", "higher": true},
      {"name": "CAC Payback", "company": number, "peers": [numbers], "unit": "months", "higher": false},
      {"name": "Net Retention", "company": number, "peers": [numbers], "unit": "%", "higher": true}
    ],
    "peerCompanies": ["..."],
    "outperformingCount": number,
    "percentileRank": number
  }
}

Context:
Startup Name: ${startupName}
Pitch Deck: ${deckText}
Transcript: ${transcriptText}
Public Data: ${scrapedText}
`;

  try {
    const response = await axios.post(
      `${GEMINI_API_URL}?key=${GEMINI_API_KEY}`,
      {
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: { temperature: 0.7, maxOutputTokens: 1024 }
      },
      { headers: { "Content-Type": "application/json" } }
    );

    let output = response?.data?.candidates?.[0]?.content?.parts?.[0]?.text || "{}";
    output = output.replace(/```json|```/g, "").trim();

    let parsed;
    try {
      parsed = JSON.parse(output);
    } catch (err) {
      console.warn("Non-JSON output:", output);
      parsed = {};
    }

    // Merge defaults + parsed (so FE always gets all keys)
    const finalOutput = {
      ...getDefaultResponse(),
      ...parsed,
      riskMRI: { ...getDefaultResponse().riskMRI, ...parsed.riskMRI },
      peerBenchmark: { ...getDefaultResponse().peerBenchmark, ...parsed.peerBenchmark }
    };

    return finalOutput;
  } catch (err) {
    console.error("Gemini API Error:", err.response?.data || err.message);
    return { error: "Analysis failed", details: err.response?.data || err.message };
  }
} 

module.exports = { analyzeStartup };
