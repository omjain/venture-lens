import { FileText, CheckCircle2, AlertCircle } from "lucide-react";
import { Card } from "@/components/ui/card";
import { useStartup } from "@/contexts/StartupContext";
import { Badge } from "@/components/ui/badge";

const PdfEvaluator = () => {
  const { evaluation, isLoading } = useStartup();

  // Check if PDF was part of the evaluation
  const hasPdf = evaluation?.hasPdf ?? false;
  const evalData = evaluation?.evaluation;

  if (!evalData) {
    return (
      <Card className="p-6">
        <div className="flex items-center space-x-3 mb-4">
          <div className="flex items-center justify-center w-10 h-10 bg-primary/10 rounded-lg">
            <FileText className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-foreground">PDF Evaluation</h3>
            <p className="text-sm text-muted-foreground">
              AI-based evaluation of uploaded PDF document
            </p>
          </div>
        </div>
        <div className="p-4 bg-muted rounded-lg text-center">
          <p className="text-sm text-muted-foreground">No PDF is attached for evaluation</p>
        </div>
      </Card>
    );
  }

  if (!hasPdf) {
    return (
      <Card className="p-6">
        <div className="flex items-center space-x-3 mb-4">
          <div className="flex items-center justify-center w-10 h-10 bg-primary/10 rounded-lg">
            <FileText className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-foreground">PDF Evaluation</h3>
            <p className="text-sm text-muted-foreground">
              AI-based evaluation of uploaded PDF document
            </p>
          </div>
        </div>
        <div className="p-4 bg-muted rounded-lg text-center">
          <AlertCircle className="w-5 h-5 mx-auto mb-2 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">No PDF is attached for evaluation</p>
        </div>
      </Card>
    );
  }

  // Display PDF evaluation results
  return (
    <Card className="p-6">
      <div className="flex items-center space-x-3 mb-4">
        <div className="flex items-center justify-center w-10 h-10 bg-primary/10 rounded-lg">
          <FileText className="w-5 h-5 text-primary" />
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-foreground">PDF Evaluation</h3>
          <p className="text-sm text-muted-foreground">
            AI-based evaluation of uploaded PDF document
          </p>
        </div>
        <Badge variant="outline" className="flex items-center space-x-1">
          <CheckCircle2 className="w-3 h-3" />
          <span>PDF Analyzed</span>
        </Badge>
      </div>

      <div className="space-y-4">
        {/* Scores Summary */}
        {evalData.scores && (
          <div className="p-4 bg-primary/5 rounded-lg border border-primary/20">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-foreground">Venture Lens Score</span>
              <span className="text-2xl font-bold text-primary">
                {evalData.scores.venture_lens_score?.toFixed(1) || 'N/A'}/10
              </span>
            </div>
            {evalData.scores.reasoning && (
              <p className="text-xs text-muted-foreground mt-2 line-clamp-2">
                {evalData.scores.reasoning}
              </p>
            )}
          </div>
        )}

        {/* Narrative Summary */}
        {evalData.narrative && (
          <div className="p-4 bg-secondary/50 rounded-lg">
            <h4 className="text-sm font-semibold text-foreground mb-2">Narrative</h4>
            {evalData.narrative.tagline && (
              <p className="text-sm text-foreground italic mb-2">
                "{evalData.narrative.tagline}"
              </p>
            )}
            {evalData.narrative.vision && (
              <p className="text-xs text-muted-foreground line-clamp-2">
                {evalData.narrative.vision}
              </p>
            )}
          </div>
        )}

        {/* Risk Summary */}
        {evalData.critique && (
          <div className="p-4 bg-secondary/50 rounded-lg">
            <h4 className="text-sm font-semibold text-foreground mb-2">Risk Assessment</h4>
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-xs text-muted-foreground">Overall Risk:</span>
              <Badge 
                variant={
                  evalData.critique.overall_risk_label?.toLowerCase() === 'low' ? 'default' :
                  evalData.critique.overall_risk_label?.toLowerCase() === 'medium' ? 'secondary' :
                  'destructive'
                }
              >
                {evalData.critique.overall_risk_label || 'N/A'}
              </Badge>
            </div>
            {evalData.critique.red_flags && evalData.critique.red_flags.length > 0 && (
              <p className="text-xs text-muted-foreground">
                {evalData.critique.red_flags.length} red flag(s) identified
              </p>
            )}
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="p-4 bg-muted rounded-lg text-center">
            <p className="text-sm text-muted-foreground">Evaluating PDF...</p>
          </div>
        )}
      </div>
    </Card>
  );
};

export default PdfEvaluator;
