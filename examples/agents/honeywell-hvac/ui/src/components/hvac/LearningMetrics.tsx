import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useHVACStore } from '@/stores/hvac-store';
import { Brain, TrendingUp, Target } from 'lucide-react';

export function LearningMetrics() {
  const { learningMetrics, acquisitiveLearnings } = useHVACStore();

  const totalLearnings = acquisitiveLearnings.length;
  const metrics = learningMetrics || {
    total_learnings: totalLearnings,
    efficiency_improvement: 0,
    success_rate_improvement: 0,
    session_id: '',
  };

  return (
    <div className="flex items-center gap-4">
      <Badge variant="outline" className="border-blue-500 text-blue-700 dark:text-blue-400">
        <Brain className="w-4 h-4 mr-1" />
        {metrics.total_learnings} lessons learned
      </Badge>
      {metrics.efficiency_improvement > 0 && (
        <Badge variant="outline" className="border-green-500 text-green-700 dark:text-green-400">
          <TrendingUp className="w-4 h-4 mr-1" />
          {metrics.efficiency_improvement.toFixed(1)}% efficiency improvement
        </Badge>
      )}
      {metrics.success_rate_improvement > 0 && (
        <Badge variant="outline" className="border-purple-500 text-purple-700 dark:text-purple-400">
          <Target className="w-4 h-4 mr-1" />
          {metrics.success_rate_improvement.toFixed(1)}% success improvement
        </Badge>
      )}
    </div>
  );
}

