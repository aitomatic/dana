import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useHVACFlow } from '@/hooks/use-hvac-flow';
import { useHVACStore } from '@/stores/hvac-store';
import { Clock, Calendar, AlertCircle, Building, Brain } from 'lucide-react';

export function EnvironmentPanel() {
  const { environment, error } = useHVACFlow();
  const { acquisitiveLearnings } = useHVACStore();

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
              <div className="flex items-center gap-2">
                <Building className="w-5 h-5 text-muted-foreground" />
                <span className="text-base font-semibold">{environment.room_name}</span>
              </div>
              
              <div className="flex gap-4">
                {/* Left Block */}
                <div className="flex-1 space-y-3">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm text-foreground">{environment.current_time}</span>
                  </div>

                  <div className="flex gap-3">
                    {/* Indoor Temperature Block */}
                    <div className="flex flex-col items-center justify-center p-4 rounded-lg border border-purple-500 bg-purple-50 dark:bg-purple-500/10 min-w-[100px] aspect-square">
                      <span className="text-xs text-purple-700 dark:text-purple-400 mb-1">Indoor</span>
                      <span className="text-2xl font-bold text-purple-700 dark:text-purple-400">
                        {environment.indoor_temp.toFixed(1)}
                      </span>
                      <span className="text-xs text-purple-700 dark:text-purple-400">°F</span>
                    </div>

                    {/* Outdoor Temperature Block */}
                    <div className="flex flex-col items-center justify-center p-4 rounded-lg border border-blue-500 bg-blue-50 dark:bg-blue-500/10 min-w-[100px] aspect-square">
                      <span className="text-xs text-blue-700 dark:text-blue-400 mb-1">Outdoor</span>
                      <span className="text-2xl font-bold text-blue-700 dark:text-blue-400">
                        {environment.outdoor_temp.toFixed(1)}
                      </span>
                      <span className="text-xs text-blue-700 dark:text-blue-400">°F</span>
                    </div>
                  </div>
                </div>

                {/* Separator */}
                <Separator orientation="vertical" />

                {/* Right Block - Meetings */}
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm font-medium">
                      {environment.meeting_plan.length} Meeting(s):
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {environment.meeting_plan.map(
                      (meeting: { start_time: string; end_time: string }, i: number) => (
                        <Badge
                          key={i}
                          variant="outline"
                          className="border-orange-500 text-orange-700 dark:text-orange-400 bg-orange-50 dark:bg-orange-500/10"
                        >
                          {meeting.start_time} - {meeting.end_time}
                        </Badge>
                      ),
                    )}
                  </div>
                </div>
              </div>

              {/* Learning Indicators */}
              {acquisitiveLearnings.length > 0 && (
                <>
                
                  <div className="pt-2">
                    <Badge
                      variant="outline"
                      className="border-green-500 text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-500/10 w-full justify-start"
                    >
                      <Brain className="w-4 h-4 mr-1" />
                      {acquisitiveLearnings.length} previous learning{acquisitiveLearnings.length !== 1 ? 's' : ''} inform this plan
                    </Badge>
                  </div>
                </>
              )}
            </div>
          ) : (
            <div className="text-sm text-muted-foreground text-center py-8">
             Run Agent to get environment data
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
