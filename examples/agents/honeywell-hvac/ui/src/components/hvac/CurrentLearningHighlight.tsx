import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useHVACStore } from '@/stores/hvac-store';
import { Sparkles, TrendingUp } from 'lucide-react';
import { useEffect, useState } from 'react';

export function CurrentLearningHighlight() {
  const { currentExecutionLearning } = useHVACStore();
  const [isNew, setIsNew] = useState(false);

  useEffect(() => {
    if (currentExecutionLearning) {
      setIsNew(true);
      const timer = setTimeout(() => setIsNew(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [currentExecutionLearning]);

  if (!currentExecutionLearning) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Learning from This Execution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground text-center py-8">
            No learning yet. Run the agent to see what it learns.
          </div>
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
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-green-500" />
            New Learning from This Run
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
          <div className="text-base font-medium leading-relaxed text-foreground">
            {currentExecutionLearning.learning_note || 'No learning note available'}
          </div>
        </div>

        {/* Context */}
        <div className="text-sm text-muted-foreground">
          <div className="mb-1">
            <span className="font-medium">Learned at:</span> {timestamp}
          </div>
          <div className="mb-1">
            <span className="font-medium">Session:</span> {currentExecutionLearning.session_id}
          </div>
        </div>

        {/* Impact Preview */}
        <div className="bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/30 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-blue-500" />
            <span className="text-sm font-medium text-blue-700 dark:text-blue-400">
              This learning will help:
            </span>
          </div>
          <ul className="text-sm text-blue-600 dark:text-blue-300 space-y-1 ml-6 list-disc">
            <li>Improve future plan timing</li>
            <li>Reduce energy waste</li>
            <li>Better efficiency in similar scenarios</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}

