import React, { createContext, useContext, useState, useCallback } from 'react';
import { apiService, AnalysisRequest, AnalysisResponse, StartupData } from '../services/api';

interface StartupContextType {
  startupData: StartupData | null;
  analysis: AnalysisResponse | null;
  isLoading: boolean;
  error: string | null;
  analyzeStartup: (data: AnalysisRequest) => Promise<void>;
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
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  const clearData = useCallback(() => {
    setStartupDataState(null);
    setAnalysis(null);
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
    isLoading,
    error,
    analyzeStartup,
    clearData,
    setStartupData,
  };

  return (
    <StartupContext.Provider value={value}>
      {children}
    </StartupContext.Provider>
  );
};
