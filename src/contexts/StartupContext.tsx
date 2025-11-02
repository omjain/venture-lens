import React, { createContext, useContext, useState, useCallback } from 'react';
import { apiService, AnalysisRequest, AnalysisResponse, StartupData, EvaluationResponse } from '../services/api';

interface EvaluationData {
  evaluation: EvaluationResponse | null;
  reportId: string | null;
  hasPdf?: boolean; // Track if PDF was uploaded
}

interface StartupContextType {
  startupData: StartupData | null;
  analysis: AnalysisResponse | null;
  evaluation: EvaluationData | null;
  isLoading: boolean;
  error: string | null;
  evaluateStartup: (params: { 
    file?: File; 
    url?: string; 
    jsonData?: Record<string, any>;
    startupName?: string;
    description?: string;
    market?: string;
    team?: string;
    traction?: string;
  }) => Promise<void>;
  analyzeStartup: (data: AnalysisRequest) => Promise<void>;
  downloadReport: (reportId: string) => Promise<void>;
  clearData: () => void;
  setStartupData: (data: Partial<StartupData>) => void;
}

const StartupContext = createContext<StartupContextType | undefined>(undefined);

export const useStartup = () => {
  const context = useContext(StartupContext);
  if (context === undefined) {
    throw new Error('useStartup must be used within a StartupProvider');
  }
  return context;
};

interface StartupProviderProps {
  children: React.ReactNode;
}

export const StartupProvider: React.FC<StartupProviderProps> = ({ children }) => {
  const [startupData, setStartupDataState] = useState<StartupData | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [evaluation, setEvaluation] = useState<EvaluationData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const evaluateStartup = useCallback(async (params: { 
    file?: File; 
    url?: string; 
    jsonData?: Record<string, any>;
    startupName?: string;
    description?: string;
    market?: string;
    team?: string;
    traction?: string;
  }) => {
    setIsLoading(true);
    setError(null);
    
    try {
      console.log('🚀 Starting full evaluation pipeline...');
      const result = await apiService.evaluateStartup(params);
      console.log('✅ Evaluation completed:', result);
      
      // Extract report ID from report_url
      const reportUrl = result.report_url;
      const reportId = reportUrl.includes('/') 
        ? reportUrl.split('/').pop()?.replace('.pdf', '') || null
        : null;
      
      // Track if PDF was uploaded
      const hadPdf = !!params.file;
      
      setEvaluation({
        evaluation: result,
        reportId,
        hasPdf: hadPdf,
      });
      
      // Update startup data
      setStartupDataState(prev => ({
        ...prev,
        name: result.startup,
        tagline: result.narrative.tagline,
        logo: prev?.logo || '🚀',
        sector: result.benchmarks.industry || 'Technology',
        stage: prev?.stage || 'Early Stage',
        foundedYear: prev?.foundedYear || new Date().getFullYear(),
        teamSize: prev?.teamSize || 10,
        website: prev?.website || 'example.com',
        metrics: prev?.metrics || {
          mrr: '$0K',
          growth: '+0%',
          customers: '0+',
        }
      }));
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Evaluation failed';
      console.error('❌ Evaluation error:', errorMessage);
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const analyzeStartup = useCallback(async (data: AnalysisRequest) => {
    setIsLoading(true);
    setError(null);
    
    try {
      console.log('🔍 Starting analysis for:', data.startupName);
      const result = await apiService.analyzeStartup(data);
      console.log('✅ Analysis completed:', result);
      
      setAnalysis(result);
      
      // Update startup data with analysis
      setStartupDataState(prev => ({
        ...prev,
        name: data.startupName,
        analysis: result,
        // Set default values if not provided
        tagline: prev?.tagline || 'AI-powered startup',
        logo: prev?.logo || '🚀',
        sector: prev?.sector || 'Technology',
        stage: prev?.stage || 'Early Stage',
        foundedYear: prev?.foundedYear || new Date().getFullYear(),
        teamSize: prev?.teamSize || 10,
        website: prev?.website || 'example.com',
        metrics: prev?.metrics || {
          mrr: '$0K',
          growth: '+0%',
          customers: '0+',
        }
      }));
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Analysis failed';
      console.error('❌ Analysis error:', errorMessage);
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const downloadReport = useCallback(async (reportId: string) => {
    try {
      console.log('📥 Downloading report:', reportId);
      const blob = await apiService.downloadReport(reportId);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${reportId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      console.log('✅ Report downloaded');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Download failed';
      console.error('❌ Download error:', errorMessage);
      setError(errorMessage);
    }
  }, []);

  const clearData = useCallback(() => {
    setStartupDataState(null);
    setAnalysis(null);
    setEvaluation(null);
    setError(null);
  }, []);

  const setStartupData = useCallback((data: Partial<StartupData>) => {
    setStartupDataState(prev => ({
      ...prev,
      ...data,
    } as StartupData));
  }, []);

  const value: StartupContextType = {
    startupData,
    analysis,
    evaluation,
    isLoading,
    error,
    evaluateStartup,
    analyzeStartup,
    downloadReport,
    clearData,
    setStartupData,
  };

  return (
    <StartupContext.Provider value={value}>
      {children}
    </StartupContext.Provider>
  );
};
