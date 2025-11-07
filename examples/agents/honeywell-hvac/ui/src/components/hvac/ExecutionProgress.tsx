import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useHVACStore } from '@/stores/hvac-store';
import { CheckCircle, Circle, Loader2 } from 'lucide-react';

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

  const steps = [
    { id: 'environment', label: 'Get Environment' },
    { id: 'planning', label: 'Agent Creates Plan' },
    { id: 'validation', label: 'Validate Plan' },
    { id: 'learning', label: 'Agent Learns from Execution' },
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
      <CardHeader>
        <CardTitle>Execution Progress</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {steps.map((step) => {
            const status = getStepStatus(step.id);
            return (
              <div key={step.id} className="flex items-center gap-3">
                {status === 'active' ? (
                  <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                ) : status === 'complete' ? (
                  <CheckCircle className="w-5 h-5 text-success-500" />
                ) : (
                  <Circle className="w-5 h-5 text-muted-foreground" />
                )}
                <span className="text-sm">{step.label}</span>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
