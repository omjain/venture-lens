import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Sparkles, Target, Clock, Quote } from "lucide-react";
import { Loader2 } from "lucide-react";

interface NarrativeData {
  vision: string;
  differentiation: string;
  timing: string;
  tagline: string;
}

interface NarrativeDisplayProps {
  narrative: NarrativeData | null;
  isLoading?: boolean;
}

const NarrativeDisplay = ({ narrative, isLoading }: NarrativeDisplayProps) => {
  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-32">
          <div className="flex items-center space-x-2">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-muted-foreground">Generating narrative...</span>
          </div>
        </div>
      </Card>
    );
  }

  if (!narrative) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-32">
          <p className="text-muted-foreground">No narrative data available</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <CardHeader>
        <CardTitle className="text-2xl flex items-center space-x-2">
          <Sparkles className="w-6 h-6 text-primary" />
          <span>Investment Narrative</span>
        </CardTitle>
        <CardDescription>
          AI-generated compelling story for investors
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Tagline - Prominent */}
        <div className="bg-primary-soft rounded-lg p-4 border-l-4 border-primary">
          <div className="flex items-start space-x-3">
            <Quote className="w-5 h-5 text-primary mt-1 flex-shrink-0" />
            <div>
              <div className="text-xs font-semibold text-primary mb-1">TAGLINE</div>
              <p className="text-lg font-medium text-foreground italic">
                "{narrative.tagline}"
              </p>
            </div>
          </div>
        </div>

        {/* Vision */}
        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            <Target className="w-5 h-5 text-primary" />
            <h3 className="text-lg font-semibold text-foreground">Vision</h3>
          </div>
          <p className="text-muted-foreground leading-relaxed pl-7">
            {narrative.vision}
          </p>
        </div>

        {/* Differentiation */}
        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-5 h-5 text-primary" />
            <h3 className="text-lg font-semibold text-foreground">Differentiation</h3>
          </div>
          <p className="text-muted-foreground leading-relaxed pl-7">
            {narrative.differentiation}
          </p>
        </div>

        {/* Timing */}
        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            <Clock className="w-5 h-5 text-primary" />
            <h3 className="text-lg font-semibold text-foreground">Why Now?</h3>
          </div>
          <p className="text-muted-foreground leading-relaxed pl-7">
            {narrative.timing}
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default NarrativeDisplay;

