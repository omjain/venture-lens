import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, AlertTriangle } from "lucide-react";
import { CritiqueResponse } from "@/services/api";

interface RiskHeatmapProps {
  critique?: CritiqueResponse;
  isLoading?: boolean;
}

const RiskHeatmap = ({ critique, isLoading }: RiskHeatmapProps) => {
  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-32">
          <div className="flex items-center space-x-2">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-muted-foreground">Analyzing risks...</span>
          </div>
        </div>
      </Card>
    );
  }

  if (!critique || !critique.red_flags || critique.red_flags.length === 0) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-32">
          <p className="text-muted-foreground">No risk analysis available</p>
        </div>
      </Card>
    );
  }

  const redFlags = critique.red_flags;
  
  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'high':
      case 'critical':
        return 'bg-danger text-danger-foreground';
      case 'medium':
        return 'bg-yellow-500 text-white';
      case 'low':
        return 'bg-success text-success-foreground';
      default:
        return 'bg-muted text-muted-foreground';
    }
  };

  const getRiskLevelColor = (level: string) => {
    if (level.includes('high') || level.includes('very_high')) {
      return 'text-danger';
    }
    if (level.includes('moderate')) {
      return 'text-yellow-600';
    }
    return 'text-success';
  };

  return (
    <Card className="p-6">
      <div className="mb-6">
        <h3 className="text-lg font-bold text-foreground mb-2 flex items-center space-x-2">
          <AlertTriangle className="w-5 h-5 text-danger" />
          <span>VC Risk Analysis</span>
        </h3>
        <p className="text-sm text-muted-foreground">
          Critical red flags and risk assessment from VC perspective
        </p>
      </div>

      <div className="space-y-4 mb-6">
        {redFlags.map((flag, index) => (
          <div key={index} className="p-4 border border-border rounded-lg space-y-2">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-1">
                  <Badge className={getSeverityColor(flag.severity)}>
                    {flag.severity.toUpperCase()}
                  </Badge>
                  {flag.category && (
                    <Badge variant="outline">{flag.category}</Badge>
                  )}
                </div>
                <h4 className="font-semibold text-foreground">{flag.flag}</h4>
                <p className="text-sm text-muted-foreground mt-1">{flag.explanation}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {critique.summary && (
        <div className="mb-6 p-4 bg-secondary rounded-lg">
          <h4 className="font-semibold text-foreground mb-2">Summary</h4>
          <p className="text-sm text-muted-foreground">{critique.summary}</p>
        </div>
      )}

      <div className="pt-6 border-t border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-sm text-muted-foreground">Overall Risk Level:</span>
            <Badge className={getSeverityColor(critique.overall_risk_label)}>
              {critique.overall_risk_label.replace('_', ' ').toUpperCase()}
            </Badge>
          </div>
          <div className={`text-lg font-bold ${getRiskLevelColor(critique.overall_risk_label)}`}>
            {critique.red_flags.length} Red Flag{critique.red_flags.length !== 1 ? 's' : ''}
          </div>
        </div>
      </div>
    </Card>
  );
};

export default RiskHeatmap;