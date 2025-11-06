import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useHVACStore } from '@/stores/hvac-store';
import { CheckCircle, Clock, Brain } from 'lucide-react';
import { useState } from 'react';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ChevronDown, ChevronRight } from 'lucide-react';

export function ExecutionLearningCard({
  learning,
  executionNumber,
}: {
  learning: any;
  executionNumber: number;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const timestamp = new Date(learning.timestamp).toLocaleString();

  return (
    <Card className="mb-4">
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger className="w-full">
          <CardHeader className="cursor-pointer hover:bg-muted/50 transition-colors">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {isOpen ? (
                  <ChevronDown className="w-4 h-4 text-muted-foreground" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-muted-foreground" />
                )}
                <CardTitle className="text-base">
                  Execution #{executionNumber} - {timestamp}
                </CardTitle>
              </div>
              <Badge variant="outline" className="border-green-500 text-green-700 dark:text-green-400">
                <CheckCircle className="w-3 h-3 mr-1" />
                Learned
              </Badge>
            </div>
          </CardHeader>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent className="pt-0 space-y-4">
            {/* Learning Note - Prominently Displayed */}
            <div className="bg-green-50 dark:bg-green-500/10 border border-green-200 dark:border-green-500/30 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Brain className="w-4 h-4 text-green-500" />
                <span className="text-sm font-medium text-green-700 dark:text-green-400">
                  What the agent learned:
                </span>
              </div>
              <div className="text-sm font-medium leading-relaxed text-foreground ml-6">
                {learning.learning_note || 'No learning note available'}
              </div>
            </div>

            <Separator />

            {/* Execution Context */}
            {learning.context && (
              <div className="text-sm space-y-2">
                <div>
                  <span className="font-medium text-muted-foreground">Context:</span>
                  <div className="mt-1 text-foreground">
                    {learning.context.caller_message?.substring(0, 200)}
                    {learning.context.caller_message && learning.context.caller_message.length > 200 && '...'}
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}

export function LearningGrowthTracker() {
  const { acquisitiveLearnings } = useHVACStore();

  if (acquisitiveLearnings.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-green-500" />
            Learning Growth Tracker
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground text-center py-8">
            No learnings yet. Run the agent to see its learning progression.
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-green-500" />
          Learning Growth Tracker ({acquisitiveLearnings.length} learnings)
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="max-h-[600px] overflow-y-auto space-y-4 pr-2">
          {acquisitiveLearnings.map((learning, index) => (
            <ExecutionLearningCard
              key={learning.loop_id}
              learning={learning}
              executionNumber={acquisitiveLearnings.length - index}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

