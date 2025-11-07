import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useHVACStore } from '@/stores/hvac-store';
import { Sparkles, TrendingUp, Eye } from 'lucide-react';
import { useEffect, useState } from 'react';

export function CurrentLearningHighlight({ onShowLearnedInsights }: { onShowLearnedInsights?: () => void }) {
  const { currentExecutionLearning, feedback } = useHVACStore();
  const [isNew, setIsNew] = useState(false);

  useEffect(() => {
    if (currentExecutionLearning) {
      setIsNew(true);
      const timer = setTimeout(() => setIsNew(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [currentExecutionLearning]);

  // Only show this component when feedback exists (agent has run with results)
  if (!feedback) {
    return null;
  }

  if (!currentExecutionLearning) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>New Learning</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-sm text-muted-foreground text-center py-8">
            No learning yet. Run the agent to see what it learns.
          </div>
          {/* View All Learned Insights Button */}
          {onShowLearnedInsights && (
            <div className="pt-2 border-t border-border">
              <Button
                variant="outline"
                className="w-full"
                onClick={onShowLearnedInsights}
              >
                <Eye className="w-4 h-4 mr-2" />
                View all learned insights
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  const timestamp = new Date(currentExecutionLearning.timestamp).toLocaleString();

  return (
    <Card
      className={`transition-all duration-500 ${
        isNew
          ? 'border-green-500 bg-green-50 dark:bg-green-500/10 shadow-lg'
          : 'border-border'
      }`}
    >
      <CardHeader>
        <div className="flex  items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-green-500" />
            New Learning
          </CardTitle>
          {isNew && (
            <Badge className="bg-green-500 text-white animate-pulse">
              New!
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Learning Note - Prominently Displayed */}
        <div className="bg-background border border-border rounded-lg p-4">
          <div className="text-sm leading-relaxed text-foreground">
            {currentExecutionLearning.learning_note || 'No learning note available'}
          </div>
        </div>


        {/* View All Learned Insights Button */}
        {onShowLearnedInsights && (
          <div className="pt-0 border-border">
            <Button
              
              className="w-full bg-white/10"
              onClick={onShowLearnedInsights}
            >
              <Eye className="w-4 h-4 mr-2" />
              View all insights
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

