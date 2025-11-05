import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useHVACStore } from '@/stores/hvac-store';
import { Clock, Thermometer, Zap, Calendar } from 'lucide-react';
import { Meeting, HVACAction } from '@/types/hvac';

interface TimelineItem {
  type: 'meeting' | 'action';
  startTime: string;
  endTime: string;
  meeting?: Meeting;
  action?: HVACAction;
  actionIndex?: number;
  targetTemp?: number;
}

export function UnifiedTimeline() {
  const { environment, agentPlan } = useHVACStore();
  
  if (!environment || !agentPlan) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-muted-foreground py-8">
            Run the flow to see timeline
          </div>
        </CardContent>
      </Card>
    );
  }

  // Helper function to convert time string to minutes for sorting
  const timeToMinutes = (timeStr: string): number => {
    const [hours, minutes] = timeStr.split(':').map(Number);
    return hours * 60 + minutes;
  };

  // Combine meetings and actions into a single timeline
  const timelineItems: TimelineItem[] = [];

  // Add meetings
  environment.meeting_plan.forEach((meeting) => {
    timelineItems.push({
      type: 'meeting',
      startTime: meeting.start_time,
      endTime: meeting.end_time,
      meeting,
    });
  });

  // Add actions
  const targetTemps = Array.isArray(agentPlan.target_temps) 
    ? agentPlan.target_temps 
    : [agentPlan.target_temps];

  agentPlan.plan.forEach((action, index) => {
    timelineItems.push({
      type: 'action',
      startTime: action.time_on,
      endTime: action.time_off,
      action,
      actionIndex: index,
      targetTemp: targetTemps[index] || targetTemps[0],
    });
  });

  // Sort by start time
  timelineItems.sort((a, b) => timeToMinutes(a.startTime) - timeToMinutes(b.startTime));

  // Calculate duration for actions
  const calculateDuration = (startTime: string, endTime: string): { hours: number; minutes: number } => {
    const start = timeToMinutes(startTime);
    const end = timeToMinutes(endTime);
    const totalMinutes = end - start;
    return {
      hours: Math.floor(totalMinutes / 60),
      minutes: totalMinutes % 60,
    };
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Timeline</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {timelineItems.map((item, index) => {
            if (item.type === 'meeting') {
              const meeting = item.meeting!;
              return (
                <div 
                  key={`meeting-${index}`}
                  className="flex items-center gap-3 p-3 rounded-lg bg-purple-50 dark:bg-purple-500/10 border border-purple-200 dark:border-purple-500/30"
                >
                  <div className="w-24 text-sm text-muted-foreground font-medium">
                    {meeting.start_time}
                  </div>
                  <div className="flex-1 flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                    <Badge 
                      variant="outline" 
                      className="border-purple-300 dark:border-purple-500 text-purple-700 dark:text-purple-300 bg-purple-100 dark:bg-purple-500/20"
                    >
                      Meeting
                    </Badge>
                    <span className="text-sm text-muted-foreground ml-auto">
                      {meeting.end_time}
                    </span>
                  </div>
                </div>
              );
            } else {
              const action = item.action!;
              const duration = calculateDuration(action.time_on, action.time_off);
              const targetTemp = item.targetTemp!;
              
              return (
                <div 
                  key={`action-${item.actionIndex}`}
                  className={`p-3 rounded-lg border-2 ${
                    action.use_turbo
                      ? agentPlan.mode === 'cool'
                        ? 'bg-blue-50 dark:bg-blue-500/15 border-yellow-400 dark:border-yellow-500 shadow-md'
                        : 'bg-red-50 dark:bg-red-500/15 border-yellow-400 dark:border-yellow-500 shadow-md'
                      : agentPlan.mode === 'cool' 
                        ? 'bg-blue-50 dark:bg-blue-500/10 border-blue-200 dark:border-blue-500/30' 
                        : 'bg-red-50 dark:bg-red-500/10 border-red-200 dark:border-red-500/30'
                  } ${action.use_turbo ? 'ring-2 ring-yellow-300 dark:ring-yellow-500/50' : ''}`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-muted-foreground" />
                      <span className="text-sm font-medium">
                        {action.time_on} → {action.time_off}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Thermometer className="w-4 h-4 text-muted-foreground" />
                      <span className="text-sm font-medium">{targetTemp}°F</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge 
                        variant={agentPlan.mode === 'cool' ? 'default' : 'destructive'}
                        className={
                          agentPlan.mode === 'cool'
                            ? 'bg-blue-500 text-white'
                            : 'bg-red-500 text-white'
                        }
                      >
                        {agentPlan.mode === 'cool' ? 'Cooling' : 'Heating'}
                      </Badge>
                      {action.use_turbo ? (
                        <Badge 
                          variant="default" 
                          className="text-xs bg-yellow-500 text-yellow-900 dark:text-yellow-100 border-yellow-600 dark:border-yellow-400 shadow-sm"
                        >
                          <Zap className="w-3 h-3 mr-1 fill-current" />
                          Use Turbo
                        </Badge>
                      ) : (
                        <Badge 
                          variant="outline" 
                          className="text-xs border-muted-foreground/30 text-muted-foreground bg-muted/50"
                        >
                          No Turbo
                        </Badge>
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Duration: {duration.hours > 0 && `${duration.hours}h `}{duration.minutes}m
                    </div>
                  </div>
                  
                  {action.use_turbo && (
                    <div className="mt-2 text-xs text-yellow-700 dark:text-yellow-400 font-medium flex items-center gap-1">
                      <Zap className="w-3 h-3" />
                      High Power Mode
                    </div>
                  )}
                </div>
              );
            }
          })}
        </div>
      </CardContent>
    </Card>
  );
}

