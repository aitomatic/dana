import { useEffect, useState } from 'react';
import { EnvironmentPanel } from './components/hvac/EnvironmentPanel';
import { ExecutionProgress } from './components/hvac/ExecutionProgress';
import { AgentPlanVisualization } from './components/hvac/AgentPlanVisualization';
import { FeedbackDetail } from './components/hvac/FeedbackDetail';
import { useHVACFlow } from './hooks/use-hvac-flow';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Trash2 } from 'lucide-react';
import { useHVACStore } from './stores/hvac-store';
import { hvacApi } from './lib/hvac-api';

export default function App() {
  const { loadPolicies } = useHVACFlow();
  const { policies, newlyLearnedPolicies } = useHVACStore();
  const [deletingPolicy, setDeletingPolicy] = useState<string | null>(null);

  useEffect(() => {
    loadPolicies();
  }, [loadPolicies]);

  const handleDeletePolicy = async (policy: string) => {
    if (!confirm(`Are you sure you want to delete this policy?\n\n"${policy}"`)) {
      return;
    }

    setDeletingPolicy(policy);
    try {
      await hvacApi.deletePolicies([policy]);
      // Reload policies after deletion
      await loadPolicies();
    } catch (error) {
      console.error('Failed to delete policy:', error);
      alert('Failed to delete policy. Please try again.');
    } finally {
      setDeletingPolicy(null);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border px-6 py-4">
        <h1 className="text-2xl font-bold">HVAC Agent Demo</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Autonomous HVAC control with learned policies
        </p>
      </header>

      <main className="grid grid-cols-12 gap-4 p-6 h-[calc(100vh-100px)]">
        {/* Left Panel: Environment + Execution Progress */}
        <div className="col-span-3 space-y-4 overflow-y-auto">
          <EnvironmentPanel />
          <ExecutionProgress />
        </div>

        {/* Center Panel: Agent Plan + Feedback (MAIN FOCUS) */}
        <div className="col-span-6 space-y-4 overflow-y-auto">
          <AgentPlanVisualization />
          <FeedbackDetail />
        </div>

        {/* Right Panel: Policies */}
        <div className="col-span-3 space-y-4 overflow-y-auto">
          {policies.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Learned Policies ({policies.length})</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {(() => {
                    // Sort policies: newly learned ones first, then others
                    const sortedPolicies = [...policies].sort((a, b) => {
                      const aIsNew = newlyLearnedPolicies.includes(a);
                      const bIsNew = newlyLearnedPolicies.includes(b);
                      if (aIsNew && !bIsNew) return -1;
                      if (!aIsNew && bIsNew) return 1;
                      return 0;
                    });

                    return sortedPolicies.map((policy, i) => {
                      const isNew = newlyLearnedPolicies.includes(policy);
                      const isDeleting = deletingPolicy === policy;
                      return (
                        <div
                          key={i}
                          className={`text-sm p-2 rounded flex items-start justify-between gap-2 ${
                            isNew
                              ? 'text-success-700 dark:text-success-400 bg-success-50 dark:bg-success-500/20 border border-success-200 dark:border-success-500/30'
                              : 'text-foreground bg-muted'
                          }`}
                        >
                          <span className="flex-1">{policy}</span>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0 flex-shrink-0 hover:bg-destructive/10 hover:text-destructive"
                            onClick={() => handleDeletePolicy(policy)}
                            disabled={isDeleting}
                            title="Delete policy"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      );
                    });
                  })()}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
}
