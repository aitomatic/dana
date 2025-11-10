import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useHVACStore } from '@/stores/hvac-store';
import { 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ReferenceLine,
  ResponsiveContainer,
  ComposedChart
} from 'recharts';
import { calculateTemperaturePoints, parseTimeToMinutes, minutesToTime } from '@/lib/temperature-calculator';

export function TemperatureTimeline() {
  const { environment, agentPlan, feedback } = useHVACStore();
  
  if (!environment || !agentPlan || !feedback) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Temperature Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center text-muted-foreground text-sm">
            Run the flow to see temperature timeline
          </div>
        </CardContent>
      </Card>
    );
  }
  
  const dataPoints = calculateTemperaturePoints(environment, agentPlan, feedback);
  
  // Get target temps for reference lines
  const targetTemps = Array.isArray(agentPlan.target_temps) 
    ? agentPlan.target_temps 
    : [agentPlan.target_temps];
  const uniqueTargetTemps = [...new Set(targetTemps)];
  
  // Prepare chart data with periods
  const chartData = dataPoints.map(point => ({
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
  
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Temperature Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--muted-foreground))" opacity={0.2} />
              <XAxis 
                dataKey="time" 
                stroke="hsl(var(--muted-foreground))"
                tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                ticks={xAxisTicks}
                interval={0}
              />
              <YAxis 
                stroke="hsl(var(--muted-foreground))"
                tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                label={{ value: 'Temperature (°F)', angle: -90, position: 'insideLeft' }}
                domain={[yAxisTicks[0], yAxisTicks[yAxisTicks.length - 1]]}
                ticks={yAxisTicks}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'hsl(var(--card))', 
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px'
                }}
                formatter={(value: number, name: string) => [
                  `${value.toFixed(1)}°F`, 
                  name === 'indoor' ? 'Indoor' : 'Target'
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
                  label={{ value: `Target ${target}°F`, position: 'right' }}
                />
              ))}
              
              {/* Indoor temperature line */}
              <Line 
                type="monotone" 
                dataKey="indoor" 
                stroke="hsl(var(--error-500))" 
                strokeWidth={2}
                dot={{ r: 4 }}
                name="Indoor"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
      
    </div>
  );
}

