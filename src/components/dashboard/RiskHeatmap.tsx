import { Card } from "@/components/ui/card";
import { useStartup } from "@/contexts/StartupContext";
import { Loader2 } from "lucide-react";

const RiskHeatmap = () => {
  const { analysis, isLoading } = useStartup();
  
  if (!analysis || !analysis.riskMRI) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-32">
          {isLoading ? (
            <div className="flex items-center space-x-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-muted-foreground">Analyzing risks...</span>
            </div>
          ) : (
            <p className="text-muted-foreground">No risk analysis available</p>
          )}
        </div>
      </Card>
    );
  }

  const riskCategories = analysis.riskMRI.categories;
  const overallScore = analysis.riskMRI.overallScore;

  const getRiskColor = (score: number) => {
    if (score <= 3) return "bg-success text-success-foreground";
    if (score <= 6) return "bg-yellow-500 text-white";
    return "bg-danger text-danger-foreground";
  };

  const getRiskLevel = (score: number) => {
    if (score <= 3) return "Low Risk";
    if (score <= 6) return "Medium Risk";
    return "High Risk";
  };

  return (
    <Card className="p-6">
      <div className="mb-6">
        <h3 className="text-lg font-bold text-foreground mb-2">Risk MRI Analysis</h3>
        <p className="text-sm text-muted-foreground">
          Comprehensive risk assessment across key investment areas
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {riskCategories.map((category) => (
          <div key={category.name} className="space-y-3">
            <div className="text-center">
              <h4 className="font-semibold text-foreground text-sm mb-2">
                {category.name}
              </h4>
              
              <div className="relative w-20 h-20 mx-auto">
                <div className="w-full h-full rounded-full border-4 border-muted flex items-center justify-center">
                  <div
                    className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-sm ${getRiskColor(category.score)}`}
                  >
                    {category.score}
                  </div>
                </div>
              </div>
              
              <div className="mt-2">
                <div className={`text-xs font-medium ${
                  category.score <= 3 ? "text-success" :
                  category.score <= 6 ? "text-yellow-600" : "text-danger"
                }`}>
                  {getRiskLevel(category.score)}
                </div>
              </div>
            </div>
            
            <p className="text-xs text-muted-foreground text-center">
              {category.description}
            </p>
          </div>
        ))}
      </div>

      <div className="mt-6 pt-6 border-t border-border">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-success rounded-full"></div>
              <span className="text-muted-foreground">Low (1-3)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
              <span className="text-muted-foreground">Medium (4-6)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-danger rounded-full"></div>
              <span className="text-muted-foreground">High (7-10)</span>
            </div>
          </div>
          
          <div className="text-right">
            <div className="font-semibold text-foreground">Overall Risk Score</div>
            <div className={`text-lg font-bold ${
              overallScore <= 3 ? "text-success" :
              overallScore <= 6 ? "text-yellow-600" : "text-danger"
            }`}>
              {overallScore}/10
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default RiskHeatmap;