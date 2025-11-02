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

// FastAPI Scoring Service Types
export interface ScoreRequest {
  idea: string;
  team: string;
  traction: string;
  market: string;
  startup_name?: string;
}

export interface CategoryAssessment {
  score: number;
  assessment: string;
  strengths: string[];
  concerns: string[];
}

export interface ScoreBreakdown {
  idea_score: number;
  team_score: number;
  traction_score: number;
  market_score: number;
  qualitative_assessment: {
    idea: CategoryAssessment;
    team: CategoryAssessment;
    traction: CategoryAssessment;
    market: CategoryAssessment;
  };
}

export interface ScoreResponse {
  overall_score: number;
  breakdown: ScoreBreakdown;
  weights: {
    idea: number;
    team: number;
    traction: number;
    market: number;
  };
  recommendation: string;
  confidence: number;
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

  /**
   * Score startup using FastAPI scoring service
   * Note: This calls the FastAPI service on port 8000
   */
  async scoreStartup(data: ScoreRequest): Promise<ScoreResponse> {
    const FASTAPI_URL = import.meta.env.VITE_FASTAPI_URL || 'http://localhost:8000';
    
    try {
      const response = await fetch(`${FASTAPI_URL}/score`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        
        // Handle FastAPI validation errors
        let errorMessage = `HTTP error! status: ${response.status}`;
        
        if (errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            // Pydantic validation errors
            const errors = errorData.detail.map((err: any) => {
              const field = err.loc ? err.loc.join('.') : 'unknown';
              return `${field}: ${err.msg}`;
            }).join(', ');
            errorMessage = `Validation error: ${errors}`;
          } else if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else {
            errorMessage = JSON.stringify(errorData.detail);
          }
        }
        
        throw new Error(errorMessage);
      }

      return await response.json();
    } catch (error) {
      console.error('FastAPI scoring request failed:', error);
      throw error;
    }
  }

  /**
   * Critique startup using FastAPI critique agent
   * Note: This calls the FastAPI service on port 8000
   */
  async critiqueStartup(
    scoreReport: ScoreResponse | Record<string, any>,
    pitchdeckSummary: Record<string, any>,
    startupName?: string
  ): Promise<CritiqueResponse> {
    const FASTAPI_URL = import.meta.env.VITE_FASTAPI_URL || 'http://localhost:8000';
    
    try {
      const response = await fetch(`${FASTAPI_URL}/critique`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          score_report: scoreReport,
          pitchdeck_summary: pitchdeckSummary,
          startup_name: startupName,
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        
        // Handle FastAPI validation errors
        let errorMessage = `HTTP error! status: ${response.status}`;
        
        if (errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            const errors = errorData.detail.map((err: any) => {
              const field = err.loc ? err.loc.join('.') : 'unknown';
              return `${field}: ${err.msg}`;
            }).join(', ');
            errorMessage = `Validation error: ${errors}`;
          } else if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else {
            errorMessage = JSON.stringify(errorData.detail);
          }
        }
        
        throw new Error(errorMessage);
      }

      return await response.json();
    } catch (error) {
      console.error('FastAPI critique request failed:', error);
      throw error;
    }
  }

  /**
   * Unified evaluation endpoint - runs full pipeline
   * Calls FastAPI /evaluate endpoint which orchestrates all agents
   */
  async evaluateStartup(
    options: {
      file?: File;
      url?: string;
      jsonData?: Record<string, any>;
      // Text input fields (for form-based submission)
      startupName?: string;
      description?: string;
      market?: string;
      team?: string;
      traction?: string;
    }
  ): Promise<EvaluationResponse> {
    const FASTAPI_URL = import.meta.env.VITE_FASTAPI_URL || 'http://localhost:8000';
    
    try {
      const formData = new FormData();
      
      // Add text fields if provided
      if (options.startupName) {
        formData.append('startup_name', options.startupName);
      }
      if (options.description) {
        formData.append('description', options.description);
      }
      if (options.market) {
        formData.append('market', options.market);
      }
      if (options.team) {
        formData.append('team', options.team);
      }
      if (options.traction) {
        formData.append('traction', options.traction);
      }
      
      // Add PDF file (optional)
      if (options.file) {
        formData.append('file', options.file);
      }
      
      // Legacy support: URL or JSON data
      if (options.url) {
        formData.append('url', options.url);
      } else if (options.jsonData) {
        formData.append('json_data', JSON.stringify(options.jsonData));
      }
      
      // Validate at least one input method is provided
      if (!options.file && !options.url && !options.jsonData && 
          !options.description && !options.startupName) {
        throw new Error('Either file, url, jsonData, or text fields (startupName/description) must be provided');
      }

      const response = await fetch(`${FASTAPI_URL}/evaluate`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        
        let errorMessage = `HTTP error! status: ${response.status}`;
        
        if (errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            const errors = errorData.detail.map((err: any) => {
              const field = err.loc ? err.loc.join('.') : 'unknown';
              return `${field}: ${err.msg}`;
            }).join(', ');
            errorMessage = `Validation error: ${errors}`;
          } else if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else {
            errorMessage = JSON.stringify(errorData.detail);
          }
        }
        
        throw new Error(errorMessage);
      }

      return await response.json();
    } catch (error) {
      console.error('FastAPI evaluation request failed:', error);
      throw error;
    }
  }

  /**
   * Download generated PDF report
   */
  async downloadReport(reportId: string): Promise<Blob> {
    const FASTAPI_URL = import.meta.env.VITE_FASTAPI_URL || 'http://localhost:8000';
    
    try {
      const response = await fetch(`${FASTAPI_URL}/evaluate/reports/${reportId}`, {
        method: 'GET',
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to download report: ${response.status}`);
      }

      return await response.blob();
    } catch (error) {
      console.error('Report download failed:', error);
      throw error;
    }
  }
}

export interface CritiqueResponse {
  red_flags: Array<{
    flag: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    explanation: string;
    category: string;
  }>;
  overall_risk_label: 'low_risk' | 'moderate_risk' | 'high_risk' | 'very_high_risk';
  summary: string;
  analysis_timestamp?: string;
}

// Unified Evaluation Response
export interface EvaluationResponse {
  startup: string;
  scores: ScoreResponse;
  critique: CritiqueResponse;
  narrative: {
    vision: string;
    differentiation: string;
    timing: string;
    tagline: string;
  };
  benchmarks: {
    industry: string;
    comparisons: Array<{
      metric: string;
      startup_value: string | number;
      sector_avg: string | number;
      percentile: number;
      insight: string;
    }>;
    overall_position: string;
    summary: string;
  };
  report_url: string;
}

export const apiService = new ApiService();
export default apiService;
