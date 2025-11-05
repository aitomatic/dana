import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useHVACStore } from '@/stores/hvac-store';
import { CheckCircle, XCircle, Clock, Thermometer, Zap } from 'lucide-react';

export function FeedbackDetail() {
  const { feedback } = useHVACStore();
  
  if (!feedback) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Feedback</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-muted-foreground py-8">
            No feedback available yet
          </div>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Feedback</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Status Summary */}
        <div className="flex items-center gap-2">
          {feedback.plan_success === 'success' ? (
            <>
              <CheckCircle className="w-5 h-5 text-success-500" />
              <Badge variant="default" className="bg-success-500 text-white">Success</Badge>
            </>
          ) : (
            <>
              <XCircle className="w-5 h-5 text-error-500" />
              <Badge variant="destructive">Failed</Badge>
            </>
          )}
        </div>
        
        {/* Summary Metrics */}
        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 rounded-lg bg-muted">
            <div className="text-xs text-muted-foreground mb-1">Total Cost</div>
            <div className="text-lg font-semibold">{feedback.total_cost_kwh.toFixed(3)} kWh</div>
          </div>
          <div className="p-3 rounded-lg bg-muted">
            <div className="text-xs text-muted-foreground mb-1">Final Temperature</div>
            <div className="text-lg font-semibold">{feedback.final_temp_f.toFixed(1)}°F</div>
          </div>
        </div>
        
        <Separator />
        
        {/* Action Results */}
        <div>
          <h4 className="text-sm font-medium mb-3">Action Results</h4>
          <div className="space-y-3">
            {feedback.action_results.map((action, i) => (
              <div 
                key={i}
                className={`p-3 rounded-lg border ${
                  action.schedule_success === 'success' 
                    ? 'bg-success-50 dark:bg-success-500/10 border-success-200 dark:border-success-500/30' 
                    : 'bg-error-50 dark:bg-error-500/10 border-error-200 dark:border-error-500/30'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm font-medium">
                      {action.time_on} → {action.time_off}
                    </span>
                    {action.use_turbo && (
                      <Badge variant="outline" className="text-xs border-yellow-500 text-yellow-700 dark:text-yellow-400">
                        <Zap className="w-3 h-3 mr-1" />
                        Turbo
                      </Badge>
                    )}
                  </div>
                  {action.schedule_success === 'success' ? (
                    <Badge variant="default" className="bg-success-500 text-white text-xs">Success</Badge>
                  ) : (
                    <Badge variant="destructive" className="text-xs">Failed</Badge>
                  )}
                </div>
                
                <div className="grid grid-cols-2 gap-2 text-xs mt-2">
                  {action.time_needed_minutes !== null && (
                    <div className="text-muted-foreground">
                      <span className="font-medium">Time needed:</span> {action.time_needed_minutes} min
                      {action.time_available_minutes !== null && (
                        <> / Available: {action.time_available_minutes} min</>
                      )}
                    </div>
                  )}
                  {action.reached_time && (
                    <div className="text-muted-foreground">
                      <span className="font-medium">Reached target:</span> {action.reached_time}
                    </div>
                  )}
                  {action.cost_kwh && (
                    <div className="text-muted-foreground">
                      <span className="font-medium">Cost:</span> {action.cost_kwh.toFixed(3)} kWh
                    </div>
                  )}
                  <div className="text-muted-foreground">
                    <span className="font-medium">Target:</span> {action.target_temp_f}°F
                  </div>
                </div>
                
                {action.error && (
                  <div className="mt-2 text-xs text-error-500 bg-error-100 dark:bg-error-500/20 p-2 rounded">
                    {action.error}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
        
        {/* Failed Actions Summary */}
        {feedback.failed_actions && feedback.failed_actions.length > 0 && (
          <>
            <Separator />
            <div>
              <h4 className="text-sm font-medium mb-2 text-error-500">
                Failed Actions ({feedback.failed_actions.length})
              </h4>
              <div className="text-xs text-muted-foreground">
                {feedback.failed_actions.map((failed, i) => (
                  <div key={i} className="p-2 bg-error-50 dark:bg-error-500/10 rounded mb-1">
                    Action {failed.action_index + 1}: {failed.error || 'Unknown error'}
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

