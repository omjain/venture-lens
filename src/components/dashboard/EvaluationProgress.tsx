import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { CheckCircle2, Loader2, Circle } from "lucide-react";

interface Phase {
  name: string;
  status: 'pending' | 'running' | 'completed' | 'error';
}

interface EvaluationProgressProps {
  phases: Phase[];
  currentPhase?: number;
}

const EvaluationProgress = ({ phases, currentPhase = 0 }: EvaluationProgressProps) => {
  const completedPhases = phases.filter(p => p.status === 'completed').length;
  const progress = phases.length > 0 ? (completedPhases / phases.length) * 100 : 0;

  const getPhaseIcon = (phase: Phase, index: number) => {
    if (phase.status === 'completed') {
      return <CheckCircle2 className="w-5 h-5 text-success" />;
    }
    if (phase.status === 'running' || (phase.status === 'pending' && index === currentPhase)) {
      return <Loader2 className="w-5 h-5 text-primary animate-spin" />;
    }
    return <Circle className="w-5 h-5 text-muted-foreground" />;
  };

  const getPhaseColor = (phase: Phase, index: number) => {
    if (phase.status === 'completed') return 'text-success';
    if (phase.status === 'running' || (phase.status === 'pending' && index === currentPhase)) {
      return 'text-primary font-semibold';
    }
    if (phase.status === 'error') return 'text-destructive';
    return 'text-muted-foreground';
  };

  return (
    <Card className="p-6">
      <div className="mb-4">
        <h3 className="text-lg font-bold text-foreground mb-2">Evaluation Progress</h3>
        <Progress value={progress} className="h-2" />
        <p className="text-sm text-muted-foreground mt-2">
          {completedPhases} of {phases.length} phases completed
        </p>
      </div>

      <div className="space-y-3">
        {phases.map((phase, index) => (
          <div key={index} className="flex items-center space-x-3">
            {getPhaseIcon(phase, index)}
            <span className={`text-sm ${getPhaseColor(phase, index)}`}>
              {phase.name}
            </span>
          </div>
        ))}
      </div>
    </Card>
  );
};

export default EvaluationProgress;

