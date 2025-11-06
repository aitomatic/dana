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
import { calculateTemperaturePoints } from '@/lib/temperature-calculator';

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
    outdoor: point.outdoorTemp,
    target: point.targetTemp || null,
  }));
  
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
              />
              <YAxis 
                stroke="hsl(var(--muted-foreground))"
                tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                label={{ value: 'Temperature (°F)', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'hsl(var(--card))', 
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px'
                }}
                formatter={(value: number, name: string) => [
                  `${value.toFixed(1)}°F`, 
                  name === 'indoor' ? 'Indoor' : name === 'outdoor' ? 'Outdoor' : 'Target'
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
              
              {/* Outdoor temperature line (dashed) */}
              <Line 
                type="monotone" 
                dataKey="outdoor" 
                stroke="hsl(var(--blue-500))" 
                strokeDasharray="5 5"
                strokeWidth={2}
                dot={false}
                name="Outdoor"
              />
              
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

