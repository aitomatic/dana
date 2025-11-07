import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useHVACStore } from '@/stores/hvac-store';
import { Thermometer, Zap, Snowflake, Flame, Brain } from 'lucide-react';
import { UnifiedTimeline } from './UnifiedTimeline';
import type { AgentPlan, ComparisonMode } from '@/types/hvac';

interface AgentPlanVisualizationProps {
  agentPlan?: AgentPlan | null;
  mode?: ComparisonMode;
}

export function AgentPlanVisualization({
  agentPlan: propAgentPlan,
  mode,
}: AgentPlanVisualizationProps = {}) {
  const { agentPlan: storeAgentPlan, acquisitiveLearnings } = useHVACStore();
  const agentPlan = propAgentPlan ?? storeAgentPlan;

  if (!agentPlan) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Agent Plan</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-muted-foreground py-8">No plan generated yet</div>
        </CardContent>
      </Card>
    );
  }

  const targetTemps = Array.isArray(agentPlan.target_temps)
    ? agentPlan.target_temps
    : [agentPlan.target_temps];
  const uniqueTargets = [...new Set(targetTemps)];

  // Calculate total duration
  const totalDuration = agentPlan.plan.reduce((total, action) => {
    const [onH, onM] = action.time_on.split(':').map(Number);
    const [offH, offM] = action.time_off.split(':').map(Number);
    const start = onH * 60 + onM;
    const end = offH * 60 + offM;
    return total + (end - start);
  }, 0);

  const totalHours = Math.floor(totalDuration / 60);
  const totalMinutes = totalDuration % 60;

  // Count turbo actions
  const turboActionsCount = agentPlan.plan.filter((action) => action.use_turbo).length;

  // In comparison mode, add white/50 border for WITH learning, white/10 border for WITHOUT learning
  const cardClassName = mode
    ? mode === 'withLearning'
      ? 'border-white/50 border-2'
      : 'bg-transparent border-white/10 border-2'
    : '';

  return (
    <Card className={cardClassName}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Control Plan</CardTitle>
          {mode && (
            <div className="flex items-center gap-2">
              {mode === 'withLearning' && acquisitiveLearnings.length > 0 && (
                <Badge
                  variant="outline"
                  className="border-success-500 text-success-700 dark:text-success-400 bg-success-50 dark:bg-success-500/10 justify-start "
                >
                  <Brain className="w-4 h-4 mr-1" />
                  {acquisitiveLearnings.length} previous learning
                  {acquisitiveLearnings.length !== 1 ? 's' : ''} inform this plan
                </Badge>
              )}
              <Badge
                variant={mode === 'withLearning' ? 'default' : 'outline'}
                className={
                  mode === 'withLearning'
                    ? 'bg-blue-600 text-white'
                    : 'border-gray-400 text-gray-700 dark:text-gray-300'
                }
              >
                {mode === 'withLearning' ? 'With Learning' : 'Without Learning'}
              </Badge>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Summary Section */}
        <div className="space-y-3">
          <div className="flex items-center gap-4 space-between ">
            <div className="flex items-center gap-2">
              <Badge
                variant="default"
                className={
                  agentPlan.mode === 'cool' ? 'bg-blue-500 text-white' : 'bg-red-500 text-white'
                }
              >
                {agentPlan.mode === 'cool' ? (
                  <Snowflake className="w-5 h-5 mr-2 " />
                ) : (
                  <Flame className="w-5 h-5 mr-2 " />
                )}
                {agentPlan.mode === 'cool' ? 'Cooling' : 'Heating'} Mode
              </Badge>
            </div>
            <div className="flex items-center gap-2">
              <Thermometer className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Target:</span>
              <span className="text-sm font-medium">
                {uniqueTargets.map((t) => `${t}°F`).join(', ')}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-4 gap-4 text-sm">
            <div>
              <div className="text-muted-foreground">Actions</div>
              <div className="font-medium">{agentPlan.plan.length}</div>
            </div>
            <div>
              <div className="text-muted-foreground">Total Duration</div>
              <div className="font-medium">
                {totalHours > 0 && `${totalHours}h `}
                {totalMinutes}m
              </div>
            </div>
            <div>
              <div className="text-muted-foreground">Current Temp</div>
              <div className="font-medium">{agentPlan.current_temp.toFixed(1)}°F</div>
            </div>
            <div>
              <div className="text-muted-foreground">Turbo Actions</div>
              <div className="font-medium flex items-center gap-1">
                {turboActionsCount > 0 ? (
                  <>
                    <Zap className="w-3 h-3 text-yellow-500" />
                    {turboActionsCount}
                  </>
                ) : (
                  '0'
                )}
              </div>
            </div>
          </div>
        </div>

        <Separator />

        {/* Unified Timeline - Shows meetings and actions chronologically */}
        <UnifiedTimeline agentPlan={agentPlan} />
      </CardContent>
    </Card>
  );
}
