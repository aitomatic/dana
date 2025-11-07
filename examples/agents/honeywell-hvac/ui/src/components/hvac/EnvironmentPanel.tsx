import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useHVACFlow } from '@/hooks/use-hvac-flow';
import { Clock, Calendar, AlertCircle, Building } from 'lucide-react';

export function EnvironmentPanel() {
  const { environment, error } = useHVACFlow();

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
        <CardContent className="pb-1">
          {environment ? (
            <div className="space-y-3">
              <div className="flex gap-4 items-start">
                {/* Column 1: Conference Room */}
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Building className="w-5 h-5 text-muted-foreground" />
                    <span className="text-base font-semibold">{environment.room_name}</span>
                  </div>
                  <div className="flex pt-2 items-center gap-2">
                    <Clock className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm text-foreground">Current Time: <b>{environment.current_time}</b></span>
                  </div>
                </div>

                {/* Separator */}
                <Separator orientation="vertical" />

                {/* Column 2: Current Time and Temperature */}
                <div className="flex-1 space-y-3">
                 

                  <div className="flex gap-3">
                    {/* Indoor Temperature Block */}
                    <div className="flex flex-col p-2 justify-center rounded-md border border-purple-500 bg-purple-100 dark:bg-purple-500/10 ">
                      <span className="text-xs text-purple-700 dark:text-purple-400 mb-1">Indoor</span>
                      <span className="text-xl font-bold text-purple-700 dark:text-purple-400">
                        {environment.indoor_temp.toFixed(1)}°F
                      </span>
                    </div>

                    {/* Outdoor Temperature Block */}
                    <div className="flex flex-col p-2 justify-center rounded-md border border-blue-500 bg-blue-100 dark:bg-blue-500/10 ">
                      <span className="text-xs text-blue-700 dark:text-blue-400 mb-1">Outdoor</span>
                      <span className="text-xl font-bold text-blue-700 dark:text-blue-400">
                        {environment.outdoor_temp.toFixed(1)}°F
                      </span>
                    </div>
                  </div>
                </div>

                {/* Separator */}
                <Separator orientation="vertical" />

                {/* Column 3: Meetings */}
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
                          className="border-white-500 text-md text-white-700 dark:text-white-400 bg-white/50 dark:bg-white/10"
                        >
                          {meeting.start_time} - {meeting.end_time}
                        </Badge>
                      ),
                    )}
                  </div>
                </div>
              </div>
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
