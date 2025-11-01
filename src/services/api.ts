// API service for communicating with the backend
// Use VITE_API_URL if set, otherwise default to localhost for development
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001';

export interface AnalysisRequest {
  startupName: string;
  deckText?: string;
  transcriptText?: string;
  publicUrls?: string[];
}

export interface RiskMRI {
  categories: Array<{
    name: string;
    score: number;
    description: string;
  }>;
  overallScore: number;
}

export interface PeerBenchmark {
  metrics: Array<{
    name: string;
    company: number;
    peers: number[];
    unit: string;
    higher: boolean;
  }>;
  peerCompanies: string[];
  outperformingCount: number;
  percentileRank: number;
}

export interface AnalysisResponse {
  summary: string;
  strengths: string[];
  risks: string[];
  nextSteps: string[];
  dealScore: number;
  riskMRI?: RiskMRI;
  peerBenchmark?: PeerBenchmark;
}

export interface ChatRequest {
  conversationHistory: Array<{
    role: 'user' | 'assistant';
    content: string;
  }>;
  userQuestion: string;
  contextData?: Record<string, any>;
}

export interface ChatResponse {
  answer: string;
}

export interface StartupData {
  name: string;
  tagline: string;
  logo: string;
  sector: string;
  stage: string;
  foundedYear: number;
  teamSize: number;
  website: string;
  metrics: {
    mrr: string;
    growth: string;
    customers: string;
  };
  analysis?: AnalysisResponse;
}

class ApiService {
  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, defaultOptions);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  async analyzeStartup(data: AnalysisRequest): Promise<AnalysisResponse> {
    return this.makeRequest<AnalysisResponse>('/api/analyze', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async chatWithAI(data: ChatRequest): Promise<ChatResponse> {
    return this.makeRequest<ChatResponse>('/api/chat', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async checkHealth(): Promise<{ status: string; timestamp: string }> {
    return this.makeRequest<{ status: string; timestamp: string }>('/health');
  }

  async checkAnalyzeHealth(): Promise<{ status: string; service: string; geminiConfigured: boolean }> {
    return this.makeRequest<{ status: string; service: string; geminiConfigured: boolean }>('/api/analyze/health');
  }

  async checkChatHealth(): Promise<{ status: string; service: string; geminiConfigured: boolean }> {
    return this.makeRequest<{ status: string; service: string; geminiConfigured: boolean }>('/api/chat/health');
  }
}

export const apiService = new ApiService();
export default apiService;
