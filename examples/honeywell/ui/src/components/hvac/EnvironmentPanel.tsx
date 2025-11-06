import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { useHVACFlow } from '@/hooks/use-hvac-flow';
import { Thermometer, Clock, Calendar, AlertCircle, Building } from 'lucide-react';

export function EnvironmentPanel() {
  const { environment, runFlow, reset, isLoading, error } = useHVACFlow();

  return (
    <div className="space-y-4">
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Environment</CardTitle>
        </CardHeader>
        <CardContent>
          {environment ? (
            <div className="space-y-3">
              <div className="flex items-center gap-2 mb-3 pb-2 border-b">
                <Building className="w-5 h-5 text-muted-foreground" />
                <span className="text-base font-semibold">{environment.room_name}</span>
              </div>

              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm text-foreground">{environment.current_time}</span>
              </div>

              <div className="flex items-center gap-2">
                <Badge
                  variant="outline"
                  className="border-purple-500 text-purple-700 dark:text-purple-400 bg-purple-50 dark:bg-purple-500/10"
                >
                  <Thermometer className="w-4 h-4 mr-1" />
                  Indoor: {environment.indoor_temp.toFixed(1)}°F
                </Badge>
              </div>

              <div className="flex items-center gap-2">
                <Badge
                  variant="outline"
                  className="border-blue-500 text-blue-700 dark:text-blue-400 bg-blue-50 dark:bg-blue-500/10"
                >
                  <Thermometer className="w-4 h-4 mr-1" />
                  Outdoor: {environment.outdoor_temp.toFixed(1)}°F
                </Badge>
              </div>

              <Separator />

              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Calendar className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm font-medium">
                    {environment.meeting_plan.length} Meeting(s)
                  </span>
                </div>
                {environment.meeting_plan.map(
                  (meeting: { start_time: string; end_time: string }, i: number) => (
                    <div key={i} className="text-sm font-semibold ml-6">
                      {meeting.start_time} - {meeting.end_time}
                    </div>
                  ),
                )}
              </div>
            </div>
          ) : (
            <div className="text-sm text-muted-foreground text-center py-8">
              No environment loaded
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex gap-2">
        <Button onClick={runFlow} disabled={isLoading} className="flex-1">
          {isLoading ? 'Running...' : 'Run Agent'}
        </Button>
        <Button onClick={reset} variant="outline">
          Reset
        </Button>
      </div>
    </div>
  );
}
