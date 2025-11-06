import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useHVACStore } from '@/stores/hvac-store';
import { hvacApi } from '@/lib/hvac-api';
import { BookOpen, RefreshCw } from 'lucide-react';
import { useState } from 'react';

export function AccumulatedKnowledgePanel() {
  const { episodicLearning, currentSession, setEpisodicLearning } = useHVACStore();
  const [isLoading, setIsLoading] = useState(false);

  const handleTriggerEpisodic = async () => {
    if (!currentSession) return;
    setIsLoading(true);
    try {
      const result = await hvacApi.triggerEpisodicLearning(currentSession.session_id);
      // Reload episodic learning
      const updated = await hvacApi.getEpisodicLearning(currentSession.session_id);
      setEpisodicLearning(updated);
    } catch (error) {
      console.error('Failed to trigger episodic learning:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-blue-500" />
            Accumulated Knowledge
          </CardTitle>
          {currentSession && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleTriggerEpisodic}
              disabled={isLoading}
            >
              <RefreshCw className={`w-4 h-4 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
              Trigger Episodic Learning
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {episodicLearning?.content ? (
          <div className="space-y-4">
            <div className="text-sm text-muted-foreground">
              Last updated: {episodicLearning.timestamp ? new Date(episodicLearning.timestamp).toLocaleString() : 'Unknown'}
            </div>
            <div className="prose prose-sm dark:prose-invert max-w-none bg-muted rounded-lg max-h-[400px] overflow-y-auto">
              <pre className="whitespace-pre-wrap font-sans text-sm">
                {episodicLearning.content}
              </pre>
            </div>
          </div>
        ) : (
          <div className="text-sm text-muted-foreground text-center py-8">
            No episodic learning yet. Episodic learning accumulates patterns across multiple executions.
            {currentSession && ' Click "Trigger Episodic Learning" to generate it.'}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
