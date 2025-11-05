import { useEffect } from 'react';
import { EnvironmentPanel } from './components/hvac/EnvironmentPanel';
import { ExecutionProgress } from './components/hvac/ExecutionProgress';
import { TemperatureTimeline } from './components/hvac/TemperatureTimeline';
import { AgentPlanVisualization } from './components/hvac/AgentPlanVisualization';
import { FeedbackDetail } from './components/hvac/FeedbackDetail';
import { useHVACFlow } from './hooks/use-hvac-flow';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { useHVACStore } from './stores/hvac-store';

export default function App() {
  const { loadPolicies } = useHVACFlow();
  const { policies } = useHVACStore();
  
  useEffect(() => {
    loadPolicies();
  }, [loadPolicies]);
  
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border px-6 py-4">
        <h1 className="text-2xl font-bold">HVAC Agent Demo</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Autonomous HVAC control with learned policies
        </p>
      </header>
      
      <main className="grid grid-cols-12 gap-4 p-6 h-[calc(100vh-100px)]">
        {/* Left Panel: Execution Progress + Timeline */}
        <div className="col-span-3 space-y-4 overflow-y-auto">
          <ExecutionProgress />
          <TemperatureTimeline />
        </div>
        
        {/* Center Panel: Agent Plan + Feedback (MAIN FOCUS) */}
        <div className="col-span-6 space-y-4 overflow-y-auto">
          <AgentPlanVisualization />
          <FeedbackDetail />
        </div>
        
        {/* Right Panel: Environment + Policies */}
        <div className="col-span-3 space-y-4 overflow-y-auto">
          <EnvironmentPanel />
          {policies.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Learned Policies ({policies.length})</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {policies.slice(0, 5).map((policy, i) => (
                    <div key={i} className="text-xs text-foreground p-2 bg-muted rounded">
                      {policy}
                    </div>
                  ))}
                  {policies.length > 5 && (
                    <div className="text-xs text-muted-foreground text-center pt-2">
                      ... and {policies.length - 5} more policies
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
}
