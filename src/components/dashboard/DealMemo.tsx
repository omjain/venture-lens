import { Star, AlertTriangle, CheckCircle, Loader2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useStartup } from "@/contexts/StartupContext";

const DealMemo = () => {
  const { analysis, isLoading } = useStartup();

  if (!analysis) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-32">
          {isLoading ? (
            <div className="flex items-center space-x-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-muted-foreground">Analyzing...</span>
            </div>
          ) : (
            <p className="text-muted-foreground">No analysis available</p>
          )}
        </div>
      </Card>
    );
  }

  const strengths = analysis.strengths || [];
  const risks = analysis.risks || [];
  const nextSteps = analysis.nextSteps || [];

  return (
    <Card className="p-6">
      <div className="mb-6">
        <h3 className="text-lg font-bold text-foreground mb-2">Deal Memo</h3>
        <p className="text-sm text-muted-foreground">
          AI-generated investment analysis summary
        </p>
      </div>

      {/* Top Strengths */}
      <div className="mb-6">
        <div className="flex items-center space-x-2 mb-3">
          <Star className="w-4 h-4 text-success" />
          <h4 className="font-semibold text-foreground">Top 5 Strengths</h4>
        </div>
        <div className="space-y-2">
          {strengths.map((strength, index) => (
            <Badge
              key={index}
              variant="secondary"
              className="block w-full justify-start text-left bg-success-soft text-success text-xs py-2 px-3"
            >
              {strength}
            </Badge>
          ))}
        </div>
      </div>

      {/* Top Risks */}
      <div className="mb-6">
        <div className="flex items-center space-x-2 mb-3">
          <AlertTriangle className="w-4 h-4 text-danger" />
          <h4 className="font-semibold text-foreground">Top 5 Risks</h4>
        </div>
        <div className="space-y-2">
          {risks.map((risk, index) => (
            <Badge
              key={index}
              variant="secondary"
              className="block w-full justify-start text-left bg-danger-soft text-danger text-xs py-2 px-3"
            >
              {risk}
            </Badge>
          ))}
        </div>
      </div>

      {/* Next Steps */}
      <div>
        <div className="flex items-center space-x-2 mb-3">
          <CheckCircle className="w-4 h-4 text-primary" />
          <h4 className="font-semibold text-foreground">Recommended Next Steps</h4>
        </div>
        <div className="space-y-2">
          {nextSteps.map((step, index) => (
            <div key={index} className="flex items-center space-x-3 text-sm">
              <div className="w-4 h-4 border-2 border-border rounded bg-background"></div>
              <span className="text-foreground">{step}</span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};

export default DealMemo;