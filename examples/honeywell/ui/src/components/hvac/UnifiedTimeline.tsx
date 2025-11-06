import { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { useHVACStore } from '@/stores/hvac-store';
import { Clock, Zap, Calendar, ChevronUp } from 'lucide-react';
import type { Meeting, HVACAction } from '@/types/hvac';

interface TimelineItem {
  type: 'meeting' | 'action';
  startTime: string;
  endTime: string;
  meeting?: Meeting;
  action?: HVACAction;
  actionIndex?: number;
  targetTemp?: number;
}

interface TimelineSpan {
  start: number;
  end: number;
  total: number;
}

// Helper function to convert time string to minutes
const timeToMinutes = (timeStr: string): number => {
  const [hours, minutes] = timeStr.split(':').map(Number);
  return hours * 60 + minutes;
};

// Helper function to convert minutes to time string
const minutesToTime = (minutes: number): string => {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
};

// Calculate timeline span with 30-minute padding
const getTimelineSpan = (items: TimelineItem[]): TimelineSpan => {
  if (items.length === 0) {
    return { start: 0, end: 1440, total: 1440 }; // Default to full day
  }

  const allTimes = items.flatMap((item) => [
    timeToMinutes(item.startTime),
    timeToMinutes(item.endTime),
  ]);

  const earliest = Math.min(...allTimes);
  const latest = Math.max(...allTimes);

  // Add 30 minutes padding
  const start = Math.max(0, earliest - 30);
  const end = Math.min(1440, latest + 30);
  const total = end - start;

  return { start, end, total };
};

// Calculate item position as percentage
const getItemPosition = (itemStart: string, dayStart: number, total: number): number => {
  const itemStartMinutes = timeToMinutes(itemStart);
  const offset = itemStartMinutes - dayStart;
  return (offset / total) * 100;
};

// Calculate item width as percentage
const getItemWidth = (itemStart: string, itemEnd: string, total: number): number => {
  const startMinutes = timeToMinutes(itemStart);
  const endMinutes = timeToMinutes(itemEnd);
  const duration = endMinutes - startMinutes;
  return (duration / total) * 100;
};

// Calculate vertical stacking for overlapping bars
const calculateBarStacks = (
  items: TimelineItem[],
): Array<{ item: TimelineItem; index: number; top: number; zIndex: number }> => {
  const stacks: Array<Array<{ item: TimelineItem; index: number; start: number; end: number }>> =
    [];
  const barHeight = 2.5; // rem (h-10)
  const spacing = 0.25; // rem (top padding)

  // Group overlapping items
  items.forEach((item, index) => {
    const start = timeToMinutes(item.startTime);
    const end = timeToMinutes(item.endTime);

    // Find a stack that doesn't overlap
    let placed = false;
    for (const stack of stacks) {
      const overlaps = stack.some(
        (existing) =>
          (start >= existing.start && start < existing.end) ||
          (end > existing.start && end <= existing.end) ||
          (start <= existing.start && end >= existing.end),
      );

      if (!overlaps) {
        stack.push({ item, index, start, end });
        placed = true;
        break;
      }
    }

    // If no stack found, create new one
    if (!placed) {
      stacks.push([{ item, index, start, end }]);
    }
  });

  // Calculate top positions for each item
  const result: Array<{ item: TimelineItem; index: number; top: number; zIndex: number }> = [];

  stacks.forEach((stack, stackIndex) => {
    stack.forEach(({ item, index }) => {
      result.push({
        item,
        index,
        top: spacing + stackIndex * (barHeight + spacing),
        zIndex: stacks.length - stackIndex, // Higher items have higher z-index
      });
    });
  });

  return result;
};

export function UnifiedTimeline() {
  const { environment, agentPlan, feedback } = useHVACStore();
  const [expandedItemId, setExpandedItemId] = useState<string | null>(null);

  if (!environment || !agentPlan) {
    return (
      <div className="text-center text-muted-foreground py-8">Run the flow to see timeline</div>
    );
  }

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

  // Calculate timeline span
  const timelineSpan = getTimelineSpan(timelineItems);

  // Calculate duration helper
  const calculateDuration = (
    startTime: string,
    endTime: string,
  ): { hours: number; minutes: number } => {
    const start = timeToMinutes(startTime);
    const end = timeToMinutes(endTime);
    const totalMinutes = end - start;
    return {
      hours: Math.floor(totalMinutes / 60),
      minutes: totalMinutes % 60,
    };
  };

  // Click handler
  const handleItemClick = (itemId: string) => {
    setExpandedItemId((prev) => (prev === itemId ? null : itemId));
  };

  // Get action result for energy metrics
  const getActionResult = (actionIndex: number) => {
    return feedback?.action_results.find((result) => result.action_index === actionIndex);
  };

  // Calculate bar stacks for vertical positioning
  const barStacks = calculateBarStacks(timelineItems);
  const maxStackHeight = Math.max(...barStacks.map((b) => b.top), 0) + 2.5; // Add bar height

  // Helper to render expanded card
  const renderExpandedCard = (item: TimelineItem, itemId: string) => {
    const isExpanded = expandedItemId === itemId;

    if (!isExpanded) return null;

    if (item.type === 'meeting') {
      const meeting = item.meeting!;
      return (
        <div
          key={`expanded-${itemId}`}
          className="animate-in fade-in-0 slide-in-from-top-2 duration-200 border border-purple-200 bg-purple-50 dark:bg-purple-500/10 dark:border-purple-500/30 rounded-lg p-4 z-10"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-purple-600 dark:text-purple-400" />
              <span className="font-semibold">Meeting</span>
            </div>
            <button
              onClick={() => handleItemClick(itemId)}
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              <ChevronUp className="w-4 h-4" />
            </button>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-xs text-muted-foreground mb-1">Time</div>
              <div className="text-sm font-medium">
                {meeting.start_time} - {meeting.end_time}
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Duration</div>
              <div className="text-sm font-medium">
                {(() => {
                  const duration = calculateDuration(meeting.start_time, meeting.end_time);
                  return `${duration.hours > 0 ? `${duration.hours}h ` : ''}${duration.minutes}m`;
                })()}
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Target Temperature</div>
              <div className="text-sm font-medium">{environment.indoor_temp.toFixed(1)}°F</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Status</div>
              <Badge variant="outline" className="border-purple-300 dark:border-purple-500">
                Ready
              </Badge>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-purple-200 dark:border-purple-500/30">
            <p className="text-xs text-muted-foreground">
              Temperature will be maintained at comfortable levels during this meeting period.
            </p>
          </div>
        </div>
      );
    } else {
      const action = item.action!;
      const targetTemp = item.targetTemp!;
      const actionResult = getActionResult(item.actionIndex!);
      const duration = calculateDuration(action.time_on, action.time_off);
      const isCool = agentPlan.mode === 'cool';

      return (
        <div
          key={`expanded-${itemId}`}
          className={`animate-in fade-in-0 slide-in-from-top-2 duration-200 border rounded-lg p-4 z-10 ${
            isCool
              ? 'border-gray-200 bg-gray-100 dark:bg-blue-500/10 dark:border-blue-500/30'
              : 'border-gray-200 bg-gray-100 dark:bg-red-500/10 dark:border-red-500/30'
          }`}
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="font-semibold">HVAC Action</span>
            </div>
            <button
              onClick={() => handleItemClick(itemId)}
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              <ChevronUp className="w-4 h-4" />
            </button>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-xs text-muted-foreground mb-1">Time Range</div>
              <div className="text-sm font-medium">
                {action.time_on} → {action.time_off}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                Duration: {duration.hours > 0 && `${duration.hours}h `}
                {duration.minutes}m
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Target Temperature</div>
              <div className="text-sm font-medium">
                {actionResult
                  ? `${actionResult.start_temp_f.toFixed(1)}°F → ${targetTemp}°F`
                  : `${targetTemp}°F`}
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Mode</div>
              <div className="flex items-center gap-2">
                <Badge
                  variant={isCool ? 'default' : 'destructive'}
                  className={isCool ? 'bg-blue-500 text-white' : 'bg-red-500 text-white'}
                >
                  {isCool ? 'Cooling' : 'Heating'}
                </Badge>
                {action.use_turbo ? (
                  <Badge className="text-xs bg-yellow-500 text-yellow-900 dark:text-yellow-100">
                    <Zap className="w-3 h-3 mr-1 fill-current" />
                    Turbo
                  </Badge>
                ) : (
                  <Badge variant="outline" className="text-xs">
                    No Turbo
                  </Badge>
                )}
              </div>
            </div>
            {actionResult && (
              <div>
                <div className="text-xs text-muted-foreground mb-1">Energy</div>
                <div className="text-sm font-medium">{actionResult.cost_kwh.toFixed(3)} kWh</div>
                {actionResult.reached_time && (
                  <div className="text-xs text-muted-foreground mt-1">
                    Reached: {actionResult.reached_time}
                  </div>
                )}
              </div>
            )}
          </div>
          {action.use_turbo && (
            <div className="mt-4 pt-4 border-t border-border">
              <div className="flex items-center gap-1 text-xs text-yellow-700 dark:text-yellow-400 font-medium">
                <Zap className="w-3 h-3" />
                High Power Mode
              </div>
            </div>
          )}
        </div>
      );
    }
  };

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-semibold">Actions Timeline</h3>

      {/* Timeline Axis */}
      <div
        className="relative bg-muted/30 rounded-lg border border-border overflow-visible"
        style={{ minHeight: `${maxStackHeight + 0.5}rem` }}
      >
        {/* Time Labels */}
        <div className="absolute left-0 top-0 text-xs text-muted-foreground -mt-5">
          {minutesToTime(timelineSpan.start)}
        </div>
        <div className="absolute left-1/2 top-0 -translate-x-1/2 text-xs text-muted-foreground -mt-5">
          {minutesToTime(timelineSpan.start + timelineSpan.total / 2)}
        </div>
        <div className="absolute right-0 top-0 text-xs text-muted-foreground -mt-5">
          {minutesToTime(timelineSpan.end)}
        </div>

        {/* Timeline Bars Container */}
        <div className="relative w-full" style={{ minHeight: `${maxStackHeight + 0.5}rem` }}>
          {barStacks.map(({ item, index, top, zIndex }) => {
            const itemId =
              item.type === 'meeting' ? `meeting-${index}` : `action-${item.actionIndex}`;
            const position = getItemPosition(
              item.startTime,
              timelineSpan.start,
              timelineSpan.total,
            );
            const width = getItemWidth(item.startTime, item.endTime, timelineSpan.total);

            if (item.type === 'meeting') {
              return (
                <div
                  key={itemId}
                  onClick={() => handleItemClick(itemId)}
                  className="absolute cursor-pointer transition-all duration-200 flex items-center justify-center h-10 rounded-md bg-gradient-to-r from-purple-400 to-purple-500 hover:shadow-lg hover:from-purple-500 hover:to-purple-600 text-white text-xs font-semibold shadow-md"
                  style={{
                    left: `${position}%`,
                    width: `${width}%`,
                    top: `${top}rem`,
                    zIndex: zIndex,
                  }}
                >
                  <Calendar className="w-3 h-3 mr-1" />
                  Meeting
                </div>
              );
            } else {
              const action = item.action!;
              const isCool = agentPlan.mode === 'cool';
              const gradientFrom = isCool ? 'from-blue-400' : 'from-red-400';
              const gradientTo = isCool ? 'to-blue-500' : 'to-red-500';
              const hoverFrom = isCool ? 'hover:from-blue-500' : 'hover:from-red-500';
              const hoverTo = isCool ? 'hover:to-blue-600' : 'hover:to-red-600';

              return (
                <div
                  key={itemId}
                  onClick={() => handleItemClick(itemId)}
                  className={`absolute cursor-pointer transition-all duration-200 flex items-center justify-center h-10 rounded-md bg-gradient-to-r ${gradientFrom} ${gradientTo} ${hoverFrom} ${hoverTo} hover:shadow-lg text-white text-xs font-semibold shadow-md ${
                    action.use_turbo ? 'ring-2 ring-yellow-400' : ''
                  }`}
                  style={{
                    left: `${position}%`,
                    width: `${width}%`,
                    top: `${top}rem`,
                    zIndex: zIndex,
                  }}
                >
                  <Clock className="w-3 h-3 mr-1" />
                  {isCool ? 'Cooling' : 'Heating'}
                  {action.use_turbo && (
                    <span className="bg-orange-500 px-1 rounded text-[10px] ml-1">TURBO</span>
                  )}
                </div>
              );
            }
          })}
        </div>
      </div>

      {/* Expanded Cards Container - Separate from timeline bars */}
      <div className="space-y-2">
        {timelineItems.map((item, index) => {
          const itemId =
            item.type === 'meeting' ? `meeting-${index}` : `action-${item.actionIndex}`;
          return renderExpandedCard(item, itemId);
        })}
      </div>
    </div>
  );
}
