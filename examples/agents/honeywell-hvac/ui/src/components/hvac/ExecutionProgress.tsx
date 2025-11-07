import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useHVACStore } from '@/stores/hvac-store';
import { useHVACFlow } from '@/hooks/use-hvac-flow';
import { Check, Loader2, Play } from 'lucide-react';

interface ExecutionProgressProps {
  showPlanComplete?: boolean;
  showValidationComplete?: boolean;
  showLearningComplete?: boolean;
}

export function ExecutionProgress({
  showPlanComplete = false,
  showValidationComplete = false,
  showLearningComplete = false,
}: ExecutionProgressProps) {
  const { executionStep } = useHVACStore();
  const { runFlow, reset, isLoading } = useHVACFlow();

  const steps = [
    { id: 'environment', label: 'Read environment data' },
    { id: 'planning', label: 'Create control plan' },
    { id: 'validation', label: 'Execute plan & Get feedback' },
    { id: 'learning', label: 'Learn new insights' },
  ];

  const getStepStatus = (stepId: string) => {
    const stepIndex = steps.findIndex((s) => s.id === stepId);
    const currentIndex = steps.findIndex((s) => s.id === executionStep);

    // Check completion status based on visibility props to align with card appearances
    if (stepId === 'planning') {
      if (showPlanComplete) {
        return 'complete';
      }
      if (executionStep === 'planning') {
        return 'active';
      }
    }

    if (stepId === 'validation') {
      if (showValidationComplete) {
        return 'complete';
      }
      if (executionStep === 'validation') {
        return 'active';
      }
      // If planning is complete, validation can be pending
      if (showPlanComplete) {
        return 'pending';
      }
    }

    if (stepId === 'learning') {
      if (showLearningComplete) {
        return 'complete';
      }
      if (executionStep === 'learning') {
        return 'active';
      }
      // If validation is complete, learning can be pending
      if (showValidationComplete) {
        return 'pending';
      }
    }

    // Default logic for other steps
    if (executionStep === stepId) {
      return 'active';
    }
    if (executionStep === 'complete' || currentIndex > stepIndex) {
      return 'complete';
    }
    return 'pending';
  };

  return (
    <Card>
      <CardContent className="py-3">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-4 flex-1">
            {steps.map((step, index) => {
              const status = getStepStatus(step.id);
              const stepNumber = index + 1;

              return (
                <div key={step.id} className="flex items-center gap-4 flex-1">
                  <div className="flex items-center gap-2">
                    <div
                      className={`flex items-center justify-center w-6 h-6 rounded-full border-2 transition-colors ${
                        status === 'active'
                          ? 'border-blue-500 bg-blue-500/10'
                          : status === 'complete'
                            ? 'border-success-500 bg-success-500/10'
                            : 'border-muted-foreground bg-muted'
                      }`}
                    >
                      {status === 'active' ? (
                        <Loader2 className="w-3 h-3 text-blue-500 animate-spin" />
                      ) : status === 'complete' ? (
                        <Check className="w-3 h-3 text-success-500" />
                      ) : (
                        <span
                          className={`text-xs font-medium ${
                            status === 'pending' ? 'text-muted-foreground' : 'text-foreground'
                          }`}
                        >
                          {stepNumber}
                        </span>
                      )}
                    </div>
                    <span
                      className={`text-sm ${
                        status === 'active'
                          ? 'text-blue-500 font-medium'
                          : status === 'complete'
                            ? 'text-success-500'
                            : 'text-muted-foreground'
                      }`}
                    >
                      {step.label}
                    </span>
                  </div>
                  {index < steps.length - 1 && (
                    <div
                      className={`flex-1 h-px ${
                        status === 'complete' ? 'bg-success-500' : 'bg-border'
                      }`}
                    />
                  )}
                </div>
              );
            })}
          </div>
          <div className="flex items-center gap-2 ml-4">
            <Button onClick={runFlow} disabled={isLoading} className="bg-blue-600 text-white">
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Run Agent
                </>
              )}
            </Button>
            <Button onClick={reset} className="bg-transparent border-white/10 border-2">
              Reset
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
