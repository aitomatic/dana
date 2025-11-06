import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useHVACStore } from '@/stores/hvac-store';
import { CheckCircle, XCircle, Clock, Zap } from 'lucide-react';
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
  LabelList,
} from 'recharts';
import { calculateTemperaturePoints } from '@/lib/temperature-calculator';

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
        <div className="flex items-center gap-2">
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
              <Badge variant="destructive" className="bg-error-500 text-white">
                Failed
              </Badge>
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

                return (
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart
                        data={chartData}
                        margin={{ top: 5, right: 20, bottom: 5, left: 40 }}
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
                        >
                          <LabelList
                            dataKey="target"
                            content={({ x, y, value, index }: any) => {
                              if (
                                value === null ||
                                value === undefined ||
                                x === undefined ||
                                y === undefined
                              )
                                return null;

                              // Only show badge for the first occurrence of each target temperature
                              const currentTarget = value;
                              const isFirstOccurrence =
                                index ===
                                chartData.findIndex(
                                  (point) =>
                                    point.target !== null &&
                                    Math.abs(point.target - currentTarget) < 0.1,
                                );

                              if (!isFirstOccurrence) return null;

                              // Calculate y position for target temperature line
                              // Recharts uses SVG coordinates where y increases downward
                              // We need to find the y position corresponding to the target temperature
                              // Since we don't have direct access to the scale, we'll approximate
                              // based on the temperature range and chart dimensions
                              const chartAreaHeight = 256 - 10; // h-64 = 256px, minus margins (top: 5, bottom: 5)
                              const allTemps = chartData.flatMap((p) =>
                                [p.indoor, p.outdoor, p.target].filter(Boolean),
                              );
                              const minTemp = Math.min(...(allTemps as number[]));
                              const maxTemp = Math.max(...(allTemps as number[]));
                              const tempRange = maxTemp - minTemp || 1; // Avoid division by zero

                              // Calculate y position: top margin (5) + normalized position
                              // SVG y increases downward, so we invert: chartHeight - normalizedY
                              const normalizedY =
                                ((currentTarget - minTemp) / tempRange) * chartAreaHeight;
                              const targetY = 5 + chartAreaHeight - normalizedY;

                              return (
                                <foreignObject
                                  x={x - 35}
                                  y={targetY + 15}
                                  width={70}
                                  height={24}
                                  className="pointer-events-none"
                                >
                                  <div className="inline-flex items-center rounded-md bg-success-500/90 text-white text-xs font-medium px-2 py-1 shadow-sm">
                                    Target {currentTarget}°F
                                  </div>
                                </foreignObject>
                              );
                            }}
                          />
                        </Line>
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                );
              })()}
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
            <Separator />
            <div>
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
