import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useStartup } from "@/contexts/StartupContext";
import { Loader2 } from "lucide-react";

const BenchmarkChart = () => {
  const { analysis, isLoading } = useStartup();
  
  if (!analysis || !analysis.peerBenchmark) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-32">
          {isLoading ? (
            <div className="flex items-center space-x-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-muted-foreground">Analyzing benchmarks...</span>
            </div>
          ) : (
            <p className="text-muted-foreground">No benchmark analysis available</p>
          )}
        </div>
      </Card>
    );
  }

  const metrics = analysis.peerBenchmark.metrics;
  const peerCompanies = analysis.peerBenchmark.peerCompanies;
  const outperformingCount = analysis.peerBenchmark.outperformingCount;
  const percentileRank = analysis.peerBenchmark.percentileRank;

  const getPerformanceColor = (companyValue: number, peerAverage: number, higherIsBetter: boolean) => {
    const isPerforming = higherIsBetter ? companyValue > peerAverage : companyValue < peerAverage;
    return isPerforming ? "text-success" : "text-danger";
  };

  return (
    <Card className="p-6">
      <div className="mb-6">
        <h3 className="text-lg font-bold text-foreground mb-2">Peer Benchmark Analysis</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Performance comparison against sector leaders
        </p>
        
        <div className="flex flex-wrap gap-2">
          <Badge variant="default">Your Company</Badge>
          {peerCompanies.map((peer, index) => (
            <Badge key={index} variant="outline">{peer}</Badge>
          ))}
        </div>
      </div>

      <div className="space-y-6">
        {metrics.map((metric, index) => {
          const peerAverage = metric.peers.reduce((a, b) => a + b, 0) / metric.peers.length;
          const maxValue = Math.max(metric.company, ...metric.peers);
          
          return (
            <div key={index} className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="font-medium text-foreground">{metric.name}</h4>
                <div className={`font-bold ${getPerformanceColor(metric.company, peerAverage, metric.higher)}`}>
                  {metric.company}{metric.unit}
                </div>
              </div>
              
              <div className="space-y-2">
                {/* Company Bar */}
                <div className="flex items-center space-x-3">
                  <div className="w-20 text-xs text-muted-foreground">Your Company</div>
                  <div className="flex-1 bg-secondary rounded-full h-6 relative overflow-hidden">
                    <div 
                      className="bg-primary h-full rounded-full transition-all duration-500"
                      style={{ width: `${(metric.company / maxValue) * 100}%` }}
                    >
                      <div className="absolute right-2 top-0 h-full flex items-center">
                        <span className="text-xs text-primary-foreground font-medium">
                          {metric.company}{metric.unit}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Peer Bars */}
                {metric.peers.map((peerValue, peerIndex) => (
                  <div key={peerIndex} className="flex items-center space-x-3">
                    <div className="w-20 text-xs text-muted-foreground">
                      Peer {String.fromCharCode(65 + peerIndex)}
                    </div>
                    <div className="flex-1 bg-secondary rounded-full h-4 relative overflow-hidden">
                      <div 
                        className="bg-muted-foreground/30 h-full rounded-full transition-all duration-500"
                        style={{ width: `${(peerValue / maxValue) * 100}%` }}
                      >
                        <div className="absolute right-2 top-0 h-full flex items-center">
                          <span className="text-xs text-foreground font-medium">
                            {peerValue}{metric.unit}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-6 pt-6 border-t border-border">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="font-semibold text-success">Outperforming</div>
            <div className="text-muted-foreground">{outperformingCount} of {metrics.length} metrics</div>
          </div>
          <div className="text-right">
            <div className="font-semibold text-foreground">Percentile Rank</div>
            <div className="text-lg font-bold text-primary">{percentileRank}th</div>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default BenchmarkChart;