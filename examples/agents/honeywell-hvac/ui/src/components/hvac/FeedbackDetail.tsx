import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useHVACStore } from '@/stores/hvac-store';
import { Clock, Zap } from 'lucide-react';
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
import { calculateTemperaturePoints, parseTimeToMinutes, minutesToTime } from '@/lib/temperature-calculator';

export function FeedbackDetail() {
  const { feedback, environment, agentPlan } = useHVACStore();

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
                  target: point.targetTemp || null,
                }));

                // Calculate Y-axis domain and ticks based on actual data range
                const allTemps = chartData.flatMap((p) => [p.indoor, p.target].filter(Boolean)) as number[];
                const minTemp = Math.min(...allTemps);
                const maxTemp = Math.max(...allTemps);
                const yAxisMin = Math.floor(minTemp / 10) * 10;
                const yAxisMax = Math.ceil(maxTemp / 10) * 10;
                const domainRange = yAxisMax - yAxisMin;
                
                // Use 5°F intervals if range < 30°F to ensure at least 4 ticks, otherwise use 10°F intervals
                const tickInterval = domainRange < 30 ? 5 : 10;
                const yAxisTicks: number[] = [];
                for (let i = yAxisMin; i <= yAxisMax; i += tickInterval) {
                  yAxisTicks.push(i);
                }
                
                // Ensure at least 4 ticks
                if (yAxisTicks.length < 4) {
                  // Expand domain if needed to get at least 4 ticks
                  const neededRange = (4 - 1) * tickInterval;
                  const center = (yAxisMin + yAxisMax) / 2;
                  const expandedMin = Math.floor((center - neededRange / 2) / tickInterval) * tickInterval;
                  const expandedMax = Math.ceil((center + neededRange / 2) / tickInterval) * tickInterval;
                  yAxisTicks.length = 0;
                  for (let i = expandedMin; i <= expandedMax; i += tickInterval) {
                    yAxisTicks.push(i);
                  }
                }

                // Calculate X-axis ticks at 30-minute intervals
                const minMinutes = Math.min(...chartData.map(p => p.minutes));
                const maxMinutes = Math.max(...chartData.map(p => p.minutes));
                const xAxisTicks: string[] = [];
                // Round down to nearest 30-minute interval
                const startMinutes = Math.floor(minMinutes / 30) * 30;
                // Round up to nearest 30-minute interval
                const endMinutes = Math.ceil(maxMinutes / 30) * 30;
                for (let minutes = startMinutes; minutes <= endMinutes; minutes += 30) {
                  xAxisTicks.push(minutesToTime(minutes));
                }

                // Prepare reached target data for custom rendering
                const reachedTargets = feedback.action_results
                  .map((action, i) => {
                    if (!action.reached_time) return null;
                    const reachedMinutes = parseTimeToMinutes(action.reached_time);
                    const closestPointWithIndex = chartData.reduce((closest, point, index) => {
                      const currentDiff = Math.abs(point.minutes - reachedMinutes);
                      const closestDiff = closest ? Math.abs(chartData[closest.index].minutes - reachedMinutes) : Infinity;
                      return currentDiff < closestDiff ? { point, index } : closest;
                    }, null as { point: typeof chartData[0]; index: number } | null);
                    
                    if (!closestPointWithIndex || Math.abs(closestPointWithIndex.point.minutes - reachedMinutes) >= 30) {
                      return null;
                    }
                    const closestPointIndex = closestPointWithIndex.index;
                    return { action, index: i, closestPointIndex, targetTemp: action.target_temp_f, reachedMinutes };
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
                          stroke="rgba(255, 255, 255, 0.8)"
                          opacity={0.2}
                        />
                        <XAxis
                          dataKey="time"
                          stroke="rgba(255, 255, 255, 0.8)"
                          tick={{ fill: 'rgba(255, 255, 255, 0.8)', fontSize: 12 }}
                          label={{ fill: 'rgba(255, 255, 255, 0.8)', fontSize: 12 }}
                          ticks={xAxisTicks}
                          interval={0}
                        />
                        <YAxis
                          stroke="rgba(255, 255, 255, 0.8)"
                          tick={{ fill: 'rgba(255, 255, 255, 0.8)', fontSize: 12 }}
                          label={{
                            value: 'Temperature (°F)',
                            angle: -90,
                            position: 'left',
                            offset: 10,
                            fontSize: 12,
                            fill: 'rgba(255, 255, 255, 0.8)',
                          }}
                          domain={[yAxisTicks[0], yAxisTicks[yAxisTicks.length - 1]]}
                          ticks={yAxisTicks}
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
                          const closestPoint = chartData.reduce((closest, point) => {
                            const currentDiff = Math.abs(point.minutes - meetingStartMinutes);
                            const closestDiff = closest ? Math.abs(closest.minutes - meetingStartMinutes) : Infinity;
                            return currentDiff < closestDiff ? point : closest;
                          }, null as typeof chartData[0] | null);
                          
                          // Only render if within reasonable distance (e.g., 30 minutes)
                          if (!closestPoint || Math.abs(closestPoint.minutes - meetingStartMinutes) >= 30) {
                            return null;
                          }
                          
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

                        {/* Reference lines for target reached times with triangular indicators */}
                        {reachedTargets.map(({ index: i, closestPointIndex, targetTemp }) => {
                          const closestPoint = chartData[closestPointIndex];
                          if (!closestPoint) return null;
                          
                          // Custom label renderer for triangle - receives Recharts label props
                          const TriangleLabel = (props: any) => {
                            // Recharts passes x, y, and viewBox to label functions
                            const x = props.x ?? props.viewBox?.x ?? 0;
                            const y = props.y ?? props.viewBox?.y ?? 0;
                            
                            return (
                              <g>
                                {/* Triangle pointing down at intersection */}
                                <polygon
                                  points={`${x},${y} ${x - 6},${y + 8} ${x + 6},${y + 8}`}
                                  fill="hsl(25, 95%, 53%)"
                                />
                              </g>
                            );
                          };
                          
                          return (
                            <ReferenceLine
                              key={`reached-${i}`}
                              x={closestPoint.time}
                              y={targetTemp}
                              stroke="hsl(25, 95%, 53%)"
                              strokeWidth={2}
                              strokeDasharray="0"
                              label={TriangleLabel}
                            />
                          );
                        })}

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
                      Satisfied
                    </Badge>
                  ) : (
                    <Badge variant="destructive" className="bg-error-500 text-white">
                      Dissatisfied
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
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-muted-foreground">Reached target:</span>
                      <Badge variant="outline" className="bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/30">
                        {action.reached_time}
                      </Badge>
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
                  <div className="mt-2 text-sm font-medium  rounded">
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
