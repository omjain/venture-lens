import { Star, AlertTriangle, CheckCircle } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const DealMemo = () => {
  const strengths = [
    "Strong product-market fit with 95% NPS",
    "Experienced team from Google & Meta",
    "Proprietary AI technology advantage",
    "Rapid customer acquisition growth",
    "Clear path to profitability"
  ];

  const risks = [
    "High customer concentration risk",
    "Competitive market landscape", 
    "Regulatory uncertainty in AI",
    "Dependency on cloud infrastructure",
    "Limited international presence"
  ];

  const nextSteps = [
    "Technical due diligence review",
    "Reference calls with top customers",
    "Market size validation study",
    "Legal and IP assessment",
    "Financial model deep-dive"
  ];

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