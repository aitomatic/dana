import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useHVACFlow } from '@/hooks/use-hvac-flow';
import { useHVACStore } from '@/stores/hvac-store';
import { Clock, Calendar, AlertCircle, Building, RefreshCw, Thermometer } from 'lucide-react';
import { useState } from 'react';

export function EnvironmentPanel() {
  const { environment, error, fetchEnvironment } = useHVACFlow();
  const { agentPlan, feedback, comparisonResults } = useHVACStore();
  const [isFetching, setIsFetching] = useState(false);
  
  // Show button only after first execution (when there's a plan, feedback, or comparison results)
  const hasRunAgent = !!(agentPlan || feedback || comparisonResults);

  const handleFetchEnvironment = async () => {
    setIsFetching(true);
    try {
      await fetchEnvironment();
    } finally {
      setIsFetching(false);
    }
  };

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
          <div className="flex items-center justify-between">
            <CardTitle className="flex border-b border-white/10 w-full items-center gap-2 pb-4">
              {' '}
              <Building className="w-5 h-5 text-muted-foreground" />
              {environment?.room_name || 'Environment'}
              {environment && (
                <div className="flex text-white/60 items-center gap-2">
                  |<Clock className="w-4 h-4 text-white/60" />
                  <span className="text-sm text-white/60">
                    <b>{environment.current_time}</b>
                  </span>
                </div>
              )}
            </CardTitle>
            {hasRunAgent && (
              <Button
                onClick={handleFetchEnvironment}
                disabled={isFetching}
                variant="outline"
                size="sm"
                className="ml-auto !bg-transparent border !border-white/20"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
                {isFetching ? 'Refreshing...' : 'Refresh'}
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent className="pb-4 px-4">
          {environment ? (
            <div className="space-y-3">
              <div className="flex gap-4 items-start">
                {/* Column 1: Conference Room */}
                <div className="flex-1">
                  {/* Column 2: Current Time and Temperature */}
                  <div className="flex-1 space-y-3">
                  <div className="flex items-center text-white/70 mb-4 gap-2">
                    <Thermometer className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm font-medium">
                     Temperature:
                    </span>
                  </div>
                    <div className="flex gap-3">
                      {/* Indoor Temperature Block */}
                      <div className="flex gap-2 items-center px-3 py-1 justify-center rounded-md bg-purple-600  ">
                        <span className="text-sm text-white ">
                          Inside
                        </span>
                        <span className="text-xl font-bold text-white">
                          {environment.indoor_temp.toFixed(1)}°F
                        </span>
                      </div>

                      {/* Outdoor Temperature Block */}
                      <div className="flex gap-2 items-center px-2 justify-center rounded-md bg-cyan-600 ">
                        <span className="text-sm text-white ">Outside</span>
                        <span className="text-xl font-bold text-white">
                          {environment.outdoor_temp.toFixed(1)}°F
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Column 3: Meetings */}
                <div className="flex-1 space-y-2">
                  <div className="flex items-center mb-4 gap-2">
                    <Calendar className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm text-white/70 font-medium">
                      {environment.meeting_plan.length} Meeting(s):
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {environment.meeting_plan.map(
                      (meeting: { start_time: string; end_time: string }, i: number) => (
                        <Badge
                          key={i}
                     
                          className=" text-md text-white-700 dark:text-white-400 bg-green-700 "
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
