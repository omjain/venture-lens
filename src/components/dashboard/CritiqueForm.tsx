import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, AlertTriangle, CheckCircle2, XCircle, Info } from "lucide-react";
import { apiService, ScoreResponse, CritiqueResponse } from "@/services/api";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";

const CritiqueForm = () => {
  const [startupName, setStartupName] = useState("");
  const [scoreReportJson, setScoreReportJson] = useState("");
  const [pitchdeckSummaryJson, setPitchdeckSummaryJson] = useState("");
  const [critiqueResult, setCritiqueResult] = useState<CritiqueResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      // Parse JSON inputs
      let scoreReport: ScoreResponse | Record<string, any>;
      let pitchdeckSummary: Record<string, any>;

      try {
        scoreReport = scoreReportJson.trim() 
          ? JSON.parse(scoreReportJson) 
          : { overall_score: 0, breakdown: {} };
      } catch (err) {
        throw new Error("Invalid JSON in Score Report field");
      }

      try {
        pitchdeckSummary = pitchdeckSummaryJson.trim()
          ? JSON.parse(pitchdeckSummaryJson)
          : { missing_slides_report: "No pitch deck data provided" };
      } catch (err) {
        throw new Error("Invalid JSON in Pitch Deck Summary field");
      }

      const result = await apiService.critiqueStartup(
        scoreReport,
        pitchdeckSummary,
        startupName || undefined
      );
      
      setCritiqueResult(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to run critique analysis";
      setError(errorMessage);
      console.error("Critique error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setStartupName("");
    setScoreReportJson("");
    setPitchdeckSummaryJson("");
    setCritiqueResult(null);
    setError(null);
  };

  const loadSampleData = () => {
    setScoreReportJson(`{
  "overall_score": 6.5,
  "breakdown": {
    "qualitative_assessment": {
      "idea": {
        "score": 7,
        "concerns": ["Market validation needed"]
      },
      "team": {
        "score": 5,
        "concerns": ["Lack of business experience"]
      },
      "traction": {
        "score": 4,
        "concerns": ["Low user growth", "No revenue"]
      },
      "market": {
        "score": 8,
        "concerns": []
      }
    }
  }
}`);
    setPitchdeckSummaryJson(`{
  "missing_slides_report": "Potentially missing key slides: Financial Projections",
  "overall_summary": "Complete pitch deck with minor gaps"
}`);
    setStartupName("Sample Startup");
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "bg-red-600 text-white";
      case "high":
        return "bg-orange-600 text-white";
      case "medium":
        return "bg-yellow-600 text-white";
      case "low":
        return "bg-blue-600 text-white";
      default:
        return "bg-gray-600 text-white";
    }
  };

  const getRiskLabelColor = (label: string) => {
    switch (label) {
      case "very_high_risk":
        return "bg-red-600 text-white";
      case "high_risk":
        return "bg-orange-600 text-white";
      case "moderate_risk":
        return "bg-yellow-600 text-white";
      case "low_risk":
        return "bg-green-600 text-white";
      default:
        return "bg-gray-600 text-white";
    }
  };

  if (critiqueResult) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl">VC Critique Analysis</CardTitle>
              <CardDescription>
                Critical analysis from AI VC perspective
              </CardDescription>
            </div>
            <Button variant="outline" onClick={handleReset} size="sm">
              New Critique
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Overall Risk */}
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription className="flex items-center justify-between">
              <span className="font-semibold">Overall Risk:</span>
              <Badge className={getRiskLabelColor(critiqueResult.overall_risk_label)}>
                {critiqueResult.overall_risk_label.replace(/_/g, " ").toUpperCase()}
              </Badge>
            </AlertDescription>
          </Alert>

          {/* Summary */}
          <div>
            <h3 className="text-lg font-semibold mb-2">Summary</h3>
            <p className="text-sm text-muted-foreground">{critiqueResult.summary}</p>
          </div>

          {/* Red Flags */}
          <div>
            <h3 className="text-lg font-semibold mb-4">
              Red Flags ({critiqueResult.red_flags.length})
            </h3>
            <div className="space-y-4">
              {critiqueResult.red_flags.map((flag, index) => (
                <Card key={index} className="border-l-4 border-l-orange-500">
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="h-5 w-5 text-orange-500" />
                        <span className="font-semibold">{flag.flag}</span>
                      </div>
                      <Badge className={getSeverityColor(flag.severity)}>
                        {flag.severity.toUpperCase()}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">{flag.explanation}</p>
                    <Badge variant="outline" className="text-xs">
                      {flag.category}
                    </Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {critiqueResult.analysis_timestamp && (
            <div className="text-xs text-muted-foreground text-right">
              Analyzed: {new Date(critiqueResult.analysis_timestamp).toLocaleString()}
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle className="text-2xl">VC Critique Agent</CardTitle>
        <CardDescription>
          Analyze startup critically from a VC perspective. Identifies red flags and risk levels.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Startup Name */}
          <div>
            <Label htmlFor="startupName">Startup Name (Optional)</Label>
            <Input
              id="startupName"
              value={startupName}
              onChange={(e) => setStartupName(e.target.value)}
              placeholder="e.g., TechVenture"
            />
          </div>

          {/* Score Report JSON */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <Label htmlFor="scoreReport">Score Report (JSON)</Label>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={loadSampleData}
                className="text-xs"
              >
                Load Sample Data
              </Button>
            </div>
            <Textarea
              id="scoreReport"
              value={scoreReportJson}
              onChange={(e) => setScoreReportJson(e.target.value)}
              placeholder='{"overall_score": 6.5, "breakdown": {...}}'
              className="font-mono text-sm"
              rows={8}
            />
            <p className="text-xs text-muted-foreground mt-1">
              Paste the JSON output from the Scoring endpoint, or leave empty for minimal test
            </p>
          </div>

          {/* Pitch Deck Summary JSON */}
          <div>
            <Label htmlFor="pitchdeckSummary">Pitch Deck Summary (JSON)</Label>
            <Textarea
              id="pitchdeckSummary"
              value={pitchdeckSummaryJson}
              onChange={(e) => setPitchdeckSummaryJson(e.target.value)}
              placeholder='{"missing_slides_report": "...", "overall_summary": "..."}'
              className="font-mono text-sm"
              rows={6}
            />
            <p className="text-xs text-muted-foreground mt-1">
              Paste the JSON output from Pitch Deck Analysis, or leave empty for minimal test
            </p>
          </div>

          {error && (
            <Alert variant="destructive">
              <XCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="flex items-center gap-2">
            <Info className="h-4 w-4 text-muted-foreground" />
            <p className="text-xs text-muted-foreground">
              Tip: You can copy results from the Scoring tab or Pitch Deck Analysis to use here
            </p>
          </div>

          <div className="flex space-x-3 pt-4">
            <Button
              type="submit"
              disabled={isLoading}
              className="flex-1"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <AlertTriangle className="w-4 h-4 mr-2" />
                  Run VC Critique
                </>
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={handleReset}
              disabled={isLoading}
            >
              Clear
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

export default CritiqueForm;

