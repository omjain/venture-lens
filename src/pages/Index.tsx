import { useState, useEffect } from "react";
import { Upload, FileText, MessageCircle, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import UploadZone from "@/components/dashboard/UploadZone";
import StartupSummary from "@/components/dashboard/StartupSummary";
import DealMemo from "@/components/dashboard/DealMemo";
import RiskHeatmap from "@/components/dashboard/RiskHeatmap";
import BenchmarkChart from "@/components/dashboard/BenchmarkChart";
import AIChat from "@/components/dashboard/AIChat";
import ScoringForm from "@/components/dashboard/ScoringForm";
import CritiqueForm from "@/components/dashboard/CritiqueForm";
import NarrativeDisplay from "@/components/dashboard/NarrativeDisplay";
import ScoringBreakdown from "@/components/dashboard/ScoringBreakdown";
import PdfEvaluator from "@/components/dashboard/PdfEvaluator";
import { useStartup } from "@/contexts/StartupContext";

const Index = () => {
  const [hasData, setHasData] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const { evaluation, downloadReport, isLoading } = useStartup();

  // Auto-show results when evaluation exists (e.g., from PDF evaluator)
  useEffect(() => {
    if (evaluation?.evaluation) {
      setHasData(true);
    }
  }, [evaluation]);

  return (
    <div className="min-h-screen bg-dashboard-bg">
      {/* Header */}
      <header className="border-b border-border bg-background px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 bg-primary rounded-lg">
              <FileText className="w-6 h-6 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-foreground">AI Startup Analyst</h1>
              <p className="text-sm text-muted-foreground">Professional Investment Intelligence</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsChatOpen(!isChatOpen)}
              className="flex items-center space-x-2"
            >
              <MessageCircle className="w-4 h-4" />
              <span>AI Analyst</span>
            </Button>
            {hasData && (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setHasData(false)}
                  className="flex items-center space-x-2"
                >
                  <Upload className="w-4 h-4" />
                  <span>New Analysis</span>
                </Button>
                {evaluation?.reportId && (
                  <Button 
                    size="sm" 
                    className="flex items-center space-x-2"
                    onClick={() => evaluation.reportId && downloadReport(evaluation.reportId)}
                    disabled={isLoading}
                  >
                    <Download className="w-4 h-4" />
                    <span>Export Report</span>
                  </Button>
                )}
              </>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8 max-w-7xl">
        <Tabs defaultValue="analysis" className="w-full">
          <TabsList className="grid w-full max-w-xl grid-cols-3 mb-6">
            <TabsTrigger value="analysis">Full Analysis</TabsTrigger>
            <TabsTrigger value="scoring">Quick Scoring</TabsTrigger>
            <TabsTrigger value="critique">VC Critique</TabsTrigger>
          </TabsList>

          <TabsContent value="analysis">
            {!hasData ? (
              <div className="flex items-center justify-center min-h-[60vh]">
                <UploadZone onUpload={() => setHasData(true)} />
              </div>
            ) : (
              <div className="space-y-6">
                {/* Narrative Display - Full Width */}
                {evaluation?.evaluation?.narrative && (
                  <NarrativeDisplay 
                    narrative={evaluation.evaluation.narrative}
                    isLoading={isLoading}
                  />
                )}

                {/* Main Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Left Column - Startup Overview */}
                  <div className="lg:col-span-1 space-y-6">
                    <PdfEvaluator />
                    <StartupSummary />
                    <DealMemo />
                  </div>

                  {/* Right Column - Analytics */}
                  <div className="lg:col-span-2 space-y-6">
                    {/* Scoring Breakdown */}
                    {evaluation?.evaluation?.scores && (
                      <ScoringBreakdown scoreData={evaluation.evaluation.scores} />
                    )}
                    
                    {/* Risk/Critique */}
                    {evaluation?.evaluation?.critique && (
                      <RiskHeatmap critique={evaluation.evaluation.critique} />
                    )}
                    
                    {/* Benchmark Analysis */}
                    {evaluation?.evaluation?.benchmarks && (
                      <BenchmarkChart 
                        benchmarks={evaluation.evaluation.benchmarks}
                        isLoading={isLoading}
                      />
                    )}
                  </div>
                </div>
              </div>
            )}
          </TabsContent>

          <TabsContent value="scoring">
            <div className="flex items-center justify-center min-h-[60vh]">
              <ScoringForm />
            </div>
          </TabsContent>

          <TabsContent value="critique">
            <div className="flex items-center justify-center min-h-[60vh]">
              <CritiqueForm />
            </div>
          </TabsContent>
        </Tabs>
      </main>

      {/* AI Chat Panel */}
      <AIChat isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </div>
  );
};

export default Index;