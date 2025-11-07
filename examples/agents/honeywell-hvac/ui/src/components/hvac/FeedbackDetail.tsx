import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useHVACStore } from '@/stores/hvac-store';
import { Clock, Zap } from 'lucide-react';
import { useState } from 'react';
import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
  ComposedChart,
} from 'recharts';
import { calculateTemperaturePoints, parseTimeToMinutes } from '@/lib/temperature-calculator';

export function FeedbackDetail() {
  const { feedback, environment, agentPlan } = useHVACStore();
  const [hoveredReachedTarget, setHoveredReachedTarget] = useState<number | null>(null);

  if (!feedback) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Feedback</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-muted-foreground py-8">No feedback available yet</div>
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


       
        {/* Temperature Timeline */}
        {environment && agentPlan && feedback && (
          <>
            <Separator />
            <div>
              <h4 className="text-sm font-medium mb-3">Temperature Timeline</h4>
              {(() => {
                const dataPoints = calculateTemperaturePoints(environment, agentPlan, feedback);
                const targetTemps = Array.isArray(agentPlan.target_temps)
                  ? agentPlan.target_temps
                  : [agentPlan.target_temps];
                const uniqueTargetTemps = [...new Set(targetTemps)];
                const chartData = dataPoints.map((point) => ({
                  time: point.time,
                  minutes: point.minutes,
                  indoor: point.indoorTemp,
                  outdoor: point.outdoorTemp,
                  target: point.targetTemp || null,
                }));

                // Prepare reached target data for custom rendering
                const reachedTargets = feedback.action_results
                  .map((action, i) => {
                    if (!action.reached_time) return null;
                    const reachedMinutes = parseTimeToMinutes(action.reached_time);
                    const closestPointIndex = chartData.findIndex(
                      (point) => Math.abs(point.minutes - reachedMinutes) < 30
                    );
                    if (closestPointIndex === -1) return null;
                    return { action, index: i, closestPointIndex, targetTemp: action.target_temp_f };
                  })
                  .filter((item): item is NonNullable<typeof item> => item !== null);

                return (
                  <div className="h-64 relative">
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart
                        data={chartData}
                        margin={{ top: 40, right: 20, bottom: 5, left: 40 }}
                      >
                        <CartesianGrid
                          strokeDasharray="3 3"
                          stroke="hsl(var(--muted-foreground))"
                          opacity={0.2}
                        />
                        <XAxis
                          dataKey="time"
                          stroke="hsl(var(--muted-foreground))"
                          tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                        />
                        <YAxis
                          stroke="hsl(var(--muted-foreground))"
                          tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                          label={{
                            value: 'Temperature (°F)',
                            angle: -90,
                            position: 'left',
                            offset: 10,
                          }}
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: 'hsl(var(--card))',
                            border: '1px solid hsl(var(--border))',
                            borderRadius: '8px',
                          }}
                          formatter={(value: number, name: string) => [
                            `${value.toFixed(1)}°F`,
                            name === 'indoor'
                              ? 'Indoor'
                              : name === 'outdoor'
                                ? 'Outdoor'
                                : 'Target',
                          ]}
                        />
                        <Legend />

                        {/* Reference lines for target temperatures */}
                        {uniqueTargetTemps.map((target, i) => (
                          <ReferenceLine
                            key={`target-${i}`}
                            y={target}
                            stroke="hsl(var(--success-500))"
                            strokeDasharray="5 5"
                          />
                        ))}

                        {/* Reference lines for meeting start times */}
                        {environment.meeting_plan.map((meeting, i) => {
                          // Find the data point closest to meeting start time
                          const meetingStartMinutes = parseTimeToMinutes(meeting.start_time);
                          const closestPoint = chartData.find(
                            (point) => Math.abs(point.minutes - meetingStartMinutes) < 30
                          );
                          
                          if (!closestPoint) return null;
                          
                          return (
                            <ReferenceLine
                              key={`meeting-${i}`}
                              x={closestPoint.time}
                              stroke="hsl(270, 70%, 50%)"
                              strokeDasharray="3 3"
                              strokeWidth={2}
                              label={{
                                value: `Meeting ${meeting.start_time}`,
                                position: 'top',
                                fill: 'hsl(270, 70%, 50%)',
                                fontSize: 11,
                                fontWeight: 'bold',
                                offset: 5,
                              }}
                            />
                          );
                        })}

                        {/* Reference lines for target reached times */}
                        {reachedTargets.map(({ index: i, closestPointIndex, targetTemp }) => {
                          const closestPoint = chartData[closestPointIndex];
                          
                          return (
                            <ReferenceLine
                              key={`reached-${i}`}
                              x={closestPoint.time}
                              y={targetTemp}
                              stroke="hsl(25, 95%, 53%)"
                              strokeWidth={2}
                              strokeDasharray="0"
                            />
                          );
                        })}

                        {/* Outdoor temperature line (dashed) */}
                        <Line
                          type="monotone"
                          dataKey="outdoor"
                          stroke="hsl(210, 100%, 50%)"
                          strokeDasharray="5 5"
                          strokeWidth={2}
                          dot={false}
                          name="Outdoor"
                        />

                        {/* Indoor temperature line */}
                        <Line
                          type="monotone"
                          dataKey="indoor"
                          stroke="hsl(270, 70%, 50%)"
                          strokeWidth={2}
                          dot={{ r: 4 }}
                          name="Indoor"
                        />
                      </ComposedChart>
                    </ResponsiveContainer>
                    
                    {/* Triangular indicators for reached targets */}
                    {reachedTargets.map(({ action, index: i, closestPointIndex, targetTemp }) => {
                      // Calculate positions relative to chart container
                      const chartAreaHeight = 256 - 45; // h-64 = 256px, minus margins (top: 40, bottom: 5)
                      const dataLength = chartData.length;
                      
                      // Calculate x position based on data point index (matching Recharts categorical spacing)
                      // Recharts spaces categorical data evenly, so we use index-based calculation
                      // Account for left margin (40px) and right margin (20px)
                      // The chart area width is container width - 60px (40 + 20)
                      // Position within chart area: index / (length - 1) for even spacing
                      const positionInChart = dataLength > 1 ? closestPointIndex / (dataLength - 1) : 0.5;
                      
                      // Calculate percentage: left margin + position in chart area
                      // Using calc() approach: left margin is ~5% (40px of ~800px), chart area is ~92.5%
                      const leftMarginPercent = 5;
                      const chartAreaWidthPercent = 92.5;
                      const xPercent = leftMarginPercent + (positionInChart * chartAreaWidthPercent);
                      
                      // Calculate y position for target temperature
                      const allTemps = chartData.flatMap((p) =>
                        [p.indoor, p.outdoor, p.target].filter(Boolean),
                      );
                      const minTemp = Math.min(...(allTemps as number[]));
                      const maxTemp = Math.max(...(allTemps as number[]));
                      const tempRange = maxTemp - minTemp || 1;
                      const normalizedY = ((targetTemp - minTemp) / tempRange) * chartAreaHeight;
                      const targetYPercent = ((40 + chartAreaHeight - normalizedY) / 256) * 100;
                      
                      return (
                        <div
                          key={`triangle-${i}`}
                          className="absolute pointer-events-none"
                          style={{
                            left: `${xPercent}%`,
                            top: `${targetYPercent}%`,
                            transform: 'translate(-50%, -100%)',
                          }}
                        >
                          <div
                            className="relative"
                            onMouseEnter={() => setHoveredReachedTarget(i)}
                            onMouseLeave={() => setHoveredReachedTarget(null)}
                            style={{ cursor: 'pointer', pointerEvents: 'auto' }}
                          >
                            {/* Triangle */}
                            <div
                              className="w-0 h-0 border-l-[6px] border-r-[6px] border-b-[8px] border-l-transparent border-r-transparent"
                              style={{ borderBottomColor: 'hsl(25, 95%, 53%)' }}
                            />
                            {/* Tooltip */}
                            {hoveredReachedTarget === i && (
                              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 whitespace-nowrap">
                                <div className="inline-flex items-center rounded-md bg-orange-500/90 text-white text-xs font-medium px-2 py-1 shadow-sm">
                                  Reached target at {action.reached_time}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                );
              })()}
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
          </>
        )}

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
                      <Badge
                        variant="outline"
                        className="text-xs border-yellow-500 text-yellow-700 dark:text-yellow-400"
                      >
                        <Zap className="w-3 h-3 mr-1" />
                        Turbo
                      </Badge>
                    )}
                  </div>
                  {action.schedule_success === 'success' ? (
                    <Badge variant="default" className="bg-success-500 text-white text-xs">
                      Success
                    </Badge>
                  ) : (
                    <Badge variant="destructive" className="bg-error-500 text-white">
                      Failed
                    </Badge>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs mt-2">
                  {action.time_needed_minutes !== null && (
                    <div className="text-muted-foreground">
                      <span className="font-medium">Time needed:</span> {action.time_needed_minutes}{' '}
                      min
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
                  <div className="mt-2 text-sm font-medium dark:bg-error-500/20 rounded">
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

            <div className='hidden'>
              <h4 className="text-sm font-medium mb-2 text-error-500">
                Failed Actions ({feedback.failed_actions.length})
              </h4>
              <div className="text-xs text-muted-foreground">
                {feedback.failed_actions.map((failed, i) => (
                  <div key={i} className="p-2  dark:bg-error-500/10 rounded mb-1">
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
