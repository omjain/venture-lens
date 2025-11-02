import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Sparkles } from "lucide-react";
import { apiService, ScoreRequest, ScoreResponse } from "@/services/api";
import ScoringBreakdown from "./ScoringBreakdown";

const ScoringForm = () => {
  const [formData, setFormData] = useState<ScoreRequest>({
    idea: "",
    team: "",
    traction: "",
    market: "",
    startup_name: "",
  });
  const [scoreData, setScoreData] = useState<ScoreResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      // Ensure all required fields meet minimum length
      if (formData.idea.trim().length < 10) {
        setError("Idea must be at least 10 characters long");
        setIsLoading(false);
        return;
      }
      if (formData.team.trim().length < 10) {
        setError("Team description must be at least 10 characters long");
        setIsLoading(false);
        return;
      }
      if (formData.traction.trim().length < 10) {
        setError("Traction description must be at least 10 characters long");
        setIsLoading(false);
        return;
      }
      if (formData.market.trim().length < 10) {
        setError("Market description must be at least 10 characters long");
        setIsLoading(false);
        return;
      }

      // Prepare request data - only include startup_name if it's not empty
      const requestData: ScoreRequest = {
        idea: formData.idea.trim(),
        team: formData.team.trim(),
        traction: formData.traction.trim(),
        market: formData.market.trim(),
        ...(formData.startup_name?.trim() && { startup_name: formData.startup_name.trim() }),
      };

      console.log("Submitting scoring request:", requestData);
      const result = await apiService.scoreStartup(requestData);
      setScoreData(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to score startup";
      setError(errorMessage);
      console.error("Scoring error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setFormData({
      idea: "",
      team: "",
      traction: "",
      market: "",
      startup_name: "",
    });
    setScoreData(null);
    setError(null);
  };

  if (scoreData) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-foreground">Scoring Results</h2>
          <Button variant="outline" onClick={handleReset}>
            Score Another Startup
          </Button>
        </div>
        <ScoringBreakdown scoreData={scoreData} />
      </div>
    );
  }

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <div className="p-6">
        <div className="flex items-center space-x-2 mb-6">
          <Sparkles className="w-6 h-6 text-primary" />
          <div>
            <h3 className="text-xl font-semibold text-foreground">Venture Lens Scoring</h3>
            <p className="text-sm text-muted-foreground">
              Get weighted scores across Idea, Team, Traction, and Market
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <Label htmlFor="startup_name">Startup Name (Optional)</Label>
            <Input
              id="startup_name"
              value={formData.startup_name}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, startup_name: e.target.value }))
              }
              placeholder="Enter startup name"
              className="mt-1"
            />
          </div>

          <div>
            <Label htmlFor="idea">
              Idea / Concept <span className="text-danger">*</span>
            </Label>
            <Textarea
              id="idea"
              value={formData.idea}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, idea: e.target.value }))
              }
              placeholder="Describe the business idea, innovation, value proposition, problem it solves..."
              className="mt-1 min-h-[120px]"
              required
            />
            <p className="text-xs text-muted-foreground mt-1">
              Minimum 10 characters required
            </p>
          </div>

          <div>
            <Label htmlFor="team">
              Team <span className="text-danger">*</span>
            </Label>
            <Textarea
              id="team"
              value={formData.team}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, team: e.target.value }))
              }
              placeholder="Describe the team composition, experience, skills, track record, execution capability..."
              className="mt-1 min-h-[120px]"
              required
            />
            <p className="text-xs text-muted-foreground mt-1">
              Minimum 10 characters required
            </p>
          </div>

          <div>
            <Label htmlFor="traction">
              Traction <span className="text-danger">*</span>
            </Label>
            <Textarea
              id="traction"
              value={formData.traction}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, traction: e.target.value }))
              }
              placeholder="Describe current traction, metrics, users, revenue, growth, milestones, validation..."
              className="mt-1 min-h-[120px]"
              required
            />
            <p className="text-xs text-muted-foreground mt-1">
              Minimum 10 characters required
            </p>
          </div>

          <div>
            <Label htmlFor="market">
              Market <span className="text-danger">*</span>
            </Label>
            <Textarea
              id="market"
              value={formData.market}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, market: e.target.value }))
              }
              placeholder="Describe market size, opportunity, competition, TAM/SAM/SOM, market trends, defensibility..."
              className="mt-1 min-h-[120px]"
              required
            />
            <p className="text-xs text-muted-foreground mt-1">
              Minimum 10 characters required
            </p>
          </div>

          {error && (
            <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
              <p className="text-sm text-destructive">{error}</p>
            </div>
          )}

          <div className="flex space-x-3 pt-4">
            <Button
              type="submit"
              disabled={
                isLoading ||
                !formData.idea.trim() ||
                !formData.team.trim() ||
                !formData.traction.trim() ||
                !formData.market.trim()
              }
              className="flex-1"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Scoring...
                </>
              ) : (
                "Get Venture Lens Score"
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
      </div>
    </Card>
  );
};

export default ScoringForm;

