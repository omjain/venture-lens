import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { TrendingUp, Users, Target, Briefcase, AlertCircle, CheckCircle } from "lucide-react";
import { ScoreResponse } from "@/services/api";

interface ScoringBreakdownProps {
  scoreData: ScoreResponse;
}

const ScoringBreakdown = ({ scoreData }: ScoringBreakdownProps) => {
  const { overall_score, breakdown, weights, recommendation, confidence } = scoreData;

  const categories = [
    {
      key: "idea" as const,
      label: "Idea",
      icon: Target,
      color: "text-blue-600",
      bgColor: "bg-blue-50",
      score: breakdown.idea_score,
      assessment: breakdown.qualitative_assessment.idea,
      weight: weights.idea,
    },
    {
      key: "team" as const,
      label: "Team",
      icon: Users,
      color: "text-purple-600",
      bgColor: "bg-purple-50",
      score: breakdown.team_score,
      assessment: breakdown.qualitative_assessment.team,
      weight: weights.team,
    },
    {
      key: "traction" as const,
      label: "Traction",
      icon: TrendingUp,
      color: "text-green-600",
      bgColor: "bg-green-50",
      score: breakdown.traction_score,
      assessment: breakdown.qualitative_assessment.traction,
      weight: weights.traction,
    },
    {
      key: "market" as const,
      label: "Market",
      icon: Briefcase,
      color: "text-orange-600",
      bgColor: "bg-orange-50",
      score: breakdown.market_score,
      assessment: breakdown.qualitative_assessment.market,
      weight: weights.market,
    },
  ];

  const getScoreColor = (score: number) => {
    if (score >= 8) return "text-success";
    if (score >= 6.5) return "text-green-600";
    if (score >= 5) return "text-yellow-600";
    if (score >= 3.5) return "text-orange-600";
    return "text-danger";
  };

  const getRecommendationColor = (score: number) => {
    if (score >= 8) return "bg-success/10 text-success border-success/20";
    if (score >= 6.5) return "bg-green-50 text-green-700 border-green-200";
    if (score >= 5) return "bg-yellow-50 text-yellow-700 border-yellow-200";
    if (score >= 3.5) return "bg-orange-50 text-orange-700 border-orange-200";
    return "bg-danger/10 text-danger border-danger/20";
  };

  return (
    <Card className="p-6">
      <div className="mb-6">
        <h3 className="text-lg font-bold text-foreground mb-2">Venture Lens Score</h3>
        <p className="text-sm text-muted-foreground">
          Weighted scoring across four key dimensions
        </p>
      </div>

      {/* Overall Score */}
      <div className="mb-8 p-6 bg-primary-soft rounded-lg border-2 border-primary/20">
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-sm text-muted-foreground mb-1">Overall Venture Lens Score</p>
            <div className="flex items-baseline space-x-2">
              <span className={`text-5xl font-bold ${getScoreColor(overall_score)}`}>
                {overall_score.toFixed(1)}
              </span>
              <span className="text-2xl text-muted-foreground">/10</span>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm text-muted-foreground mb-1">Confidence</p>
            <p className="text-lg font-semibold text-foreground">
              {(confidence * 100).toFixed(0)}%
            </p>
          </div>
        </div>
        <Progress value={overall_score * 10} className="h-3" />
      </div>

      {/* Recommendation */}
      <div className={`mb-6 p-4 rounded-lg border ${getRecommendationColor(overall_score)}`}>
        <div className="flex items-start space-x-2">
          {overall_score >= 6.5 ? (
            <CheckCircle className="w-5 h-5 mt-0.5" />
          ) : (
            <AlertCircle className="w-5 h-5 mt-0.5" />
          )}
          <div>
            <p className="font-semibold mb-1">Investment Recommendation</p>
            <p className="text-sm">{recommendation}</p>
          </div>
        </div>
      </div>

      {/* Category Breakdown */}
      <div className="space-y-6">
        {categories.map((category) => {
          const Icon = category.icon;
          return (
            <div key={category.key} className="border border-border rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-lg ${category.bgColor}`}>
                    <Icon className={`w-5 h-5 ${category.color}`} />
                  </div>
                  <div>
                    <h4 className="font-semibold text-foreground">{category.label}</h4>
                    <p className="text-xs text-muted-foreground">
                      Weight: {(category.weight * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-3xl font-bold ${getScoreColor(category.score)}`}>
                    {category.score.toFixed(1)}
                  </div>
                  <p className="text-xs text-muted-foreground">/10</p>
                </div>
              </div>

              <Progress 
                value={category.score * 10} 
                className="h-2 mb-4"
              />

              {/* Assessment */}
              <div className="mb-4">
                <p className="text-sm text-foreground leading-relaxed">
                  {category.assessment.assessment}
                </p>
              </div>

              {/* Strengths */}
              {category.assessment.strengths.length > 0 && (
                <div className="mb-3">
                  <p className="text-xs font-semibold text-success mb-2">Strengths</p>
                  <div className="flex flex-wrap gap-2">
                    {category.assessment.strengths.map((strength, idx) => (
                      <Badge
                        key={idx}
                        variant="secondary"
                        className="bg-success-soft text-success text-xs"
                      >
                        {strength}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Concerns */}
              {category.assessment.concerns.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-danger mb-2">Concerns</p>
                  <div className="flex flex-wrap gap-2">
                    {category.assessment.concerns.map((concern, idx) => (
                      <Badge
                        key={idx}
                        variant="secondary"
                        className="bg-danger-soft text-danger text-xs"
                      >
                        {concern}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
};

export default ScoringBreakdown;

