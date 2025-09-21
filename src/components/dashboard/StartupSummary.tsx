import { Building2, Globe, TrendingUp, Users, Loader2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useStartup } from "@/contexts/StartupContext";

const StartupSummary = () => {
  const { startupData, analysis, isLoading } = useStartup();

  if (!startupData) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-32">
          <p className="text-muted-foreground">No startup data available</p>
        </div>
      </Card>
    );
  }

  const startup = startupData;

  return (
    <Card className="p-6">
      <div className="flex items-start space-x-4 mb-6">
        <div className="w-16 h-16 bg-primary-soft rounded-lg flex items-center justify-center text-2xl">
          {startup.logo}
        </div>
        <div className="flex-1">
          <h2 className="text-xl font-bold text-foreground mb-1">{startup.name}</h2>
          <p className="text-sm text-muted-foreground mb-3">{startup.tagline}</p>
          <div className="flex space-x-2">
            <Badge variant="secondary">{startup.sector}</Badge>
            <Badge variant="outline">{startup.stage}</Badge>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <div className="flex items-center space-x-2 text-sm">
          <Globe className="w-4 h-4 text-muted-foreground" />
          <span className="text-muted-foreground">{startup.website}</span>
        </div>
        
        <div className="flex items-center space-x-2 text-sm">
          <Building2 className="w-4 h-4 text-muted-foreground" />
          <span className="text-muted-foreground">Founded {startup.foundedYear}</span>
        </div>
        
        <div className="flex items-center space-x-2 text-sm">
          <Users className="w-4 h-4 text-muted-foreground" />
          <span className="text-muted-foreground">{startup.teamSize} team members</span>
        </div>
      </div>

      {analysis && (
        <div className="mt-6 pt-6 border-t border-border">
          <h3 className="text-sm font-semibold text-foreground mb-4">AI Analysis Summary</h3>
          <div className="space-y-3">
            <div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {analysis.summary}
              </p>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Deal Score</span>
              <div className="flex items-center space-x-2">
                <div className="text-2xl font-bold text-foreground">
                  {analysis.dealScore}/10
                </div>
                <div className={`w-3 h-3 rounded-full ${
                  analysis.dealScore >= 8 ? 'bg-green-500' :
                  analysis.dealScore >= 6 ? 'bg-yellow-500' : 'bg-red-500'
                }`} />
              </div>
            </div>
          </div>
        </div>
      )}

      {isLoading && (
        <div className="mt-6 pt-6 border-t border-border">
          <div className="flex items-center justify-center space-x-2">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-sm text-muted-foreground">Analyzing startup...</span>
          </div>
        </div>
      )}
    </Card>
  );
};

export default StartupSummary;