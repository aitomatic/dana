import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useHVACStore } from '@/stores/hvac-store';
import { CheckCircle, XCircle } from 'lucide-react';

function JsonDisplay({ data }: { data: any }) {
  return (
    <pre className="overflow-auto p-4 text-xs font-mono bg-muted rounded-md max-h-64 text-foreground">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

export function ResultsPanel() {
  const { agentPlan, feedback, policies } = useHVACStore();

  return (
    <div className="space-y-4 overflow-y-auto max-h-[calc(100vh-200px)]">
      {/* Agent Plan */}
      {agentPlan && (
        <Card>
          <CardHeader>
            <CardTitle>Agent Plan</CardTitle>
          </CardHeader>
          <CardContent>
            <JsonDisplay data={agentPlan} />
          </CardContent>
        </Card>
      )}

      {/* Feedback Summary */}
      {feedback && (
        <Card>
          <CardHeader>
            <CardTitle>Feedback</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2 mb-4">
              {feedback.plan_success === 'success' ? (
                <>
                  <CheckCircle className="w-5 h-5 text-success-500" />
                  <Badge variant="default" className="bg-success-500 text-white">
                    Success
                  </Badge>
                </>
              ) : (
                <>
                  <XCircle className="w-5 h-5 text-error-500" />
                  <Badge variant="destructive">Failed</Badge>
                </>
              )}
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total Cost:</span>
                <span className="font-medium">{feedback.total_cost_kwh.toFixed(3)} kWh</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Final Temp:</span>
                <span className="font-medium">{feedback.final_temp_f.toFixed(1)}°F</span>
              </div>
            </div>

            <Separator className="my-4" />

            <div className="space-y-2">
              <h4 className="text-sm font-medium">Actions</h4>
              {feedback.action_results.map((action, i) => (
                <div key={i} className="text-xs space-y-1 p-2 bg-muted rounded">
                  <div className="flex items-center justify-between">
                    <span className="text-foreground">
                      {action.time_on} → {action.time_off}
                    </span>
                    {action.schedule_success === 'success' ? (
                      <Badge variant="default" className="bg-success-500 text-white text-xs">
                        Success
                      </Badge>
                    ) : (
                      <Badge variant="destructive" className="text-xs">
                        Failed
                      </Badge>
                    )}
                  </div>
                  {action.time_needed_minutes !== null && (
                    <div className="text-muted-foreground">
                      Time needed: {action.time_needed_minutes} min
                      {action.time_available_minutes !== null && (
                        <> / Available: {action.time_available_minutes} min</>
                      )}
                    </div>
                  )}
                  {action.reached_time && (
                    <div className="text-muted-foreground">
                      Reached target at: {action.reached_time}
                    </div>
                  )}
                  {action.cost_kwh && (
                    <div className="text-muted-foreground">
                      Cost: {action.cost_kwh.toFixed(3)} kWh
                    </div>
                  )}
                  {action.error && <div className="text-error-500">{action.error}</div>}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Policies */}
      {policies.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Learned Policies ({policies.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {policies.slice(0, 12).map((policy, i) => (
                <div key={i} className="text-xs text-foreground p-2 bg-muted rounded">
                  {policy}
                </div>
              ))}
              {policies.length > 12 && (
                <div className="text-xs text-muted-foreground text-center pt-2">
                  ... and {policies.length - 12} more policies
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
