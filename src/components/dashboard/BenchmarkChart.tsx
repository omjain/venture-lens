import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";

interface BenchmarkData {
  industry: string;
  comparisons: Array<{
    metric: string;
    startup_value: string | number;
    sector_avg: string | number;
    percentile: number;
    insight: string;
  }>;
  overall_position: string;
  summary: string;
}

interface BenchmarkChartProps {
  benchmarks: BenchmarkData | null;
  isLoading?: boolean;
}

const BenchmarkChart = ({ benchmarks, isLoading }: BenchmarkChartProps) => {
  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-32">
          <div className="flex items-center space-x-2">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-muted-foreground">Analyzing benchmarks...</span>
          </div>
        </div>
      </Card>
    );
  }

  if (!benchmarks || !benchmarks.comparisons || benchmarks.comparisons.length === 0) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-32">
          <p className="text-muted-foreground">No benchmark analysis available</p>
        </div>
      </Card>
    );
  }

  const comparisons = benchmarks.comparisons;
  const outperformingCount = comparisons.filter(c => c.percentile >= 50).length;

  const getPerformanceColor = (percentile: number) => {
    if (percentile >= 75) return "text-success";
    if (percentile >= 50) return "text-yellow-600";
    return "text-danger";
  };

  const getPercentileBadge = (percentile: number) => {
    if (percentile >= 75) return <Badge className="bg-success">Top 25%</Badge>;
    if (percentile >= 50) return <Badge className="bg-yellow-500">Top 50%</Badge>;
    return <Badge variant="destructive">Bottom 50%</Badge>;
  };

  const parseValue = (value: string | number): number => {
    if (typeof value === 'number') return value;
    const numStr = String(value).replace(/[^0-9.-]/g, '');
    return parseFloat(numStr) || 0;
  };

  return (
    <Card className="p-6">
      <div className="mb-6">
        <h3 className="text-lg font-bold text-foreground mb-2">Benchmark Analysis</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Performance comparison against {benchmarks.industry} sector averages
        </p>
        
        <div className="flex flex-wrap gap-2 mb-2">
          <Badge variant="default">{benchmarks.overall_position}</Badge>
          <Badge variant="outline">Industry: {benchmarks.industry}</Badge>
        </div>
      </div>

      <div className="space-y-6">
        {comparisons.map((comparison, index) => {
          const startupVal = parseValue(comparison.startup_value);
          const sectorAvg = parseValue(comparison.sector_avg);
          const maxValue = Math.max(startupVal, sectorAvg);
          
          return (
            <div key={index} className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-foreground">{comparison.metric}</h4>
                  <p className="text-xs text-muted-foreground mt-1">{comparison.insight}</p>
                </div>
                <div className="text-right">
                  <div className={`font-bold ${getPerformanceColor(comparison.percentile)}`}>
                    {comparison.startup_value}
                  </div>
                  {getPercentileBadge(comparison.percentile)}
                </div>
              </div>
              
              <div className="space-y-2">
                {/* Startup Value Bar */}
                <div className="flex items-center space-x-3">
                  <div className="w-24 text-xs text-muted-foreground">Startup</div>
                  <div className="flex-1 bg-secondary rounded-full h-6 relative overflow-hidden">
                    <div 
                      className="bg-primary h-full rounded-full transition-all duration-500"
                      style={{ width: `${maxValue > 0 ? (startupVal / maxValue) * 100 : 0}%` }}
                    >
                      <div className="absolute right-2 top-0 h-full flex items-center">
                        <span className="text-xs text-primary-foreground font-medium">
                          {comparison.startup_value}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Sector Average Bar */}
                <div className="flex items-center space-x-3">
                  <div className="w-24 text-xs text-muted-foreground">Sector Avg</div>
                  <div className="flex-1 bg-secondary rounded-full h-4 relative overflow-hidden">
                    <div 
                      className="bg-muted-foreground/30 h-full rounded-full transition-all duration-500"
                      style={{ width: `${maxValue > 0 ? (sectorAvg / maxValue) * 100 : 0}%` }}
                    >
                      <div className="absolute right-2 top-0 h-full flex items-center">
                        <span className="text-xs text-foreground font-medium">
                          {comparison.sector_avg}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-6 pt-6 border-t border-border">
        <div className="space-y-3">
          <div className="text-sm">
            <div className="font-semibold text-foreground mb-1">Summary</div>
            <p className="text-muted-foreground">{benchmarks.summary}</p>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="font-semibold text-success">Outperforming</div>
              <div className="text-muted-foreground">{outperformingCount} of {comparisons.length} metrics</div>
            </div>
            <div className="text-right">
              <div className="font-semibold text-foreground">Overall Position</div>
              <div className="text-lg font-bold text-primary">{benchmarks.overall_position}</div>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default BenchmarkChart;