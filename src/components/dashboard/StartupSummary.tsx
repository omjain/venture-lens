import { Building2, Globe, TrendingUp, Users } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const StartupSummary = () => {
  const startup = {
    name: "NeuralFlow AI",
    tagline: "AI-powered customer service automation platform",
    logo: "🤖",
    sector: "B2B SaaS",
    stage: "Series A",
    foundedYear: 2022,
    teamSize: 15,
    website: "neuralflow.ai",
    metrics: {
      mrr: "$180K",
      growth: "+85%",
      customers: "120+",
    }
  };

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

      <div className="mt-6 pt-6 border-t border-border">
        <h3 className="text-sm font-semibold text-foreground mb-4">Key Metrics</h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-lg font-bold text-foreground">{startup.metrics.mrr}</div>
            <div className="text-xs text-muted-foreground">MRR</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-success flex items-center justify-center">
              <TrendingUp className="w-4 h-4 mr-1" />
              {startup.metrics.growth}
            </div>
            <div className="text-xs text-muted-foreground">Growth</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-foreground">{startup.metrics.customers}</div>
            <div className="text-xs text-muted-foreground">Customers</div>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default StartupSummary;