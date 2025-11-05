import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useHVACStore } from '@/stores/hvac-store';
import { CheckCircle, Circle, Loader2 } from 'lucide-react';

export function TimelinePanel() {
  const { executionStep, environment, agentPlan, feedback } = useHVACStore();
  
  const steps = [
    { id: 'environment', label: 'Get Environment' },
    { id: 'planning', label: 'Agent Creates Plan' },
    { id: 'validation', label: 'Validate Plan' },
  ];
  
  const getStepStatus = (stepId: string) => {
    const stepIndex = steps.findIndex(s => s.id === stepId);
    const currentIndex = steps.findIndex(s => s.id === executionStep);
    
    if (executionStep === stepId) {
      return 'active';
    }
    if (executionStep === 'complete' || currentIndex > stepIndex) {
      return 'complete';
    }
    return 'pending';
  };
  
  return (
    <div className="space-y-4">
      {/* Progress Indicator */}
      <Card>
        <CardHeader>
          <CardTitle>Execution Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            {steps.map((step, i) => {
              const status = getStepStatus(step.id);
              return (
                <div key={step.id} className="flex items-center gap-2">
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
      
      {/* Temperature Graph placeholder */}
      <Card>
        <CardHeader>
          <CardTitle>Temperature Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center text-muted-foreground text-sm">
            {environment && agentPlan && feedback ? (
              <div className="text-center space-y-2">
                <p>Graph visualization will appear here</p>
                <p className="text-xs text-muted-foreground">
                  Showing temperature changes over time with HVAC actions
                </p>
              </div>
            ) : (
              <div className="text-center text-muted-foreground">
                Run the flow to see temperature timeline
              </div>
            )}
          </div>
        </CardContent>
      </Card>
      
      {/* Timeline Bar placeholder */}
      {(environment || agentPlan) && (
        <Card>
          <CardHeader>
            <CardTitle>Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {environment?.meeting_plan.map((meeting, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  <div className="w-24 text-muted-foreground">{meeting.start_time}</div>
                  <div className="flex-1 h-6 bg-purple-100 dark:bg-purple-500/20 rounded border border-purple-300 dark:border-purple-500/40 flex items-center px-2">
                    <span className="text-xs text-purple-900 dark:text-purple-100">Meeting</span>
                  </div>
                  <div className="w-24 text-muted-foreground text-right">{meeting.end_time}</div>
                </div>
              ))}
              {agentPlan?.plan.map((action, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  <div className="w-24 text-muted-foreground">{action.time_on}</div>
                  <div 
                    className={`flex-1 h-6 rounded border flex items-center px-2 ${
                      agentPlan.mode === 'cool' 
                        ? 'bg-blue-100 dark:bg-blue-500/20 border-blue-300 dark:border-blue-500/40' 
                        : 'bg-red-100 dark:bg-red-500/20 border-red-300 dark:border-red-500/40'
                    }`}
                    style={{ opacity: action.use_turbo ? 1 : 0.6 }}
                  >
                    <span className={`text-xs ${
                      agentPlan.mode === 'cool' 
                        ? 'text-blue-900 dark:text-blue-100' 
                        : 'text-red-900 dark:text-red-100'
                    }`}>
                      {agentPlan.mode === 'cool' ? 'Cooling' : 'Heating'}
                      {action.use_turbo && ' (Turbo)'}
                    </span>
                  </div>
                  <div className="w-24 text-muted-foreground text-right">{action.time_off}</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

