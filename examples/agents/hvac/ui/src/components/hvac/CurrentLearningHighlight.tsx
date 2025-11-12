import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useHVACStore } from '@/stores/hvac-store';
import { Sparkles, Eye, Loader2, Maximize2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import type { Feedback, ComparisonMode } from '@/types/hvac';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface CurrentLearningHighlightProps {
  onShowLearnedInsights?: () => void;
  feedback?: Feedback | null;
  mode?: ComparisonMode;
}

export function CurrentLearningHighlight({ onShowLearnedInsights, feedback: propFeedback, mode }: CurrentLearningHighlightProps = {}) {
  const { episodicLearning, feedback: storeFeedback, executionStep, isLoading } = useHVACStore();
  const feedback = propFeedback ?? storeFeedback;
  const [isNew, setIsNew] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    if (episodicLearning?.content) {
      setIsNew(true);
      const timer = setTimeout(() => setIsNew(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [episodicLearning]);

  // In comparison mode, add white/50 border for WITH learning, white/10 border for WITHOUT learning
  const cardClassName = mode
    ? mode === 'withLearning'
      ? 'border-white/50 border-2'
      : 'bg-transparent border-white/10 border-2'
    : '';

  // Only show this component when feedback exists (agent has run with results)
  if (!feedback) {
    return null;
  }

  // Check if agent is currently processing learnings
  const isProcessingLearnings = executionStep === 'learning' || isLoading;

  if (!episodicLearning?.content) {
    return (
      <Card className={cardClassName}>
        <CardHeader>
          <CardTitle>New Learning</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {isProcessingLearnings ? (
            <div className="text-sm text-muted-foreground text-center py-8 flex flex-col items-center gap-2">
              <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
              <span>Waiting for new insights...</span>
            </div>
          ) : (
            <div className="text-sm text-muted-foreground text-center py-8">
              No learning yet. Run the agent to see what it learns.
            </div>
          )}
          {/* View All Learned Insights Button */}
          {onShowLearnedInsights && !isProcessingLearnings && (
            <div className="pt-2 border-t border-border">
              <Button
                variant="outline"
                className="w-full bg-transparent border border-white/50"
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

  // Combine comparison mode styling with new learning animation
  const combinedCardClassName = mode
    ? mode === 'withLearning'
      ? `border-white/50 border-2 ${isNew ? 'shadow-lg' : ''}`
      : 'bg-transparent border-white/10 border-2'
    : `transition-all duration-500 ${
        isNew
          ? 'border-green-500 bg-green-50 dark:bg-green-500/10 shadow-lg'
          : 'border-border'
      }`;

  return (
    <Card className={combinedCardClassName}>
      <CardHeader>
        <div className="flex  items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-green-500" />
            New Learning
          </CardTitle>
          <div className="flex items-center gap-2">
            {isNew && (
              <Badge className="bg-green-500 text-white animate-pulse">
                New!
              </Badge>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(true)}
              className="h-8 w-8 p-0"
              title="Expand to view full content"
            >
              <Maximize2 className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Learning Note - Prominently Displayed */}
        <div className="bg-background border border-border rounded-lg p-4">
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {episodicLearning?.content || 'No learning note available'}
            </ReactMarkdown>
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

      {/* Expand Dialog */}
      <Dialog open={isExpanded} onOpenChange={setIsExpanded}>
        <DialogContent className="min-w-[1200px] max-h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-green-500" />
              Episodic Learning Insights
            </DialogTitle>
          </DialogHeader>
          <div className="flex-1 overflow-y-auto pr-2 py-4">
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {episodicLearning?.content || 'No learning note available'}
              </ReactMarkdown>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </Card>
  );
}

