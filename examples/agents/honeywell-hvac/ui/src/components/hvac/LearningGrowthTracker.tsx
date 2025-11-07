import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { useHVACStore } from '@/stores/hvac-store';
import { Trash2, ChevronDown, ChevronRight } from 'lucide-react';
import { useState } from 'react';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ConfirmDialog } from '@/components/library/confirm-dialog';
import { hvacApi } from '@/lib/hvac-api';

export function ExecutionLearningCard({
  learning,
  executionNumber,
  onDelete,
}: {
  learning: any;
  executionNumber: number;
  onDelete: (loopId: string) => Promise<void>;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const timestamp = new Date(learning.timestamp).toLocaleString();

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowDeleteDialog(true);
  };

  const handleConfirmDelete = async () => {
    setIsDeleting(true);
    try {
      await onDelete(learning.loop_id);
    } catch (error) {
      console.error('Failed to delete learning:', error);
    } finally {
      setIsDeleting(false);
      setShowDeleteDialog(false);
    }
  };

  return (
    <>
      <Card className="mb-4">
        <Collapsible open={isOpen} onOpenChange={setIsOpen}>
          <CollapsibleTrigger className="w-full">
            <CardHeader className="cursor-pointer p-4 hover:bg-muted/50 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex  gap-2">
                  {isOpen ? (
                    <ChevronDown className="w-4 h-4 text-muted-foreground" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-muted-foreground" />
                  )}
                  <CardTitle className="text-sm font-medium">
                    Execution #{executionNumber} - {timestamp}
                  </CardTitle>
                </div>
                <div className="flex  gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0 text-gray-500 hover:text-gray-500 hover:bg-destructive/10"
                    onClick={handleDeleteClick}
                    disabled={isDeleting}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
          </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent className="pt-0 space-y-4">
            {/* Learning Note - Prominently Displayed */}
            <div className="mt-2 bg-green-50 dark:bg-green-500/10 border border-green-200 dark:border-green-500/30 rounded-lg p-4">
              <div className="flex items-center mb-2">
        
                <span className="text-sm font-medium text-green-700 dark:text-green-400">
                  What the agent learned:
                </span>
              </div>
              <div className="text-sm leading-relaxed text-foreground">
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
    <ConfirmDialog
      isOpen={showDeleteDialog}
      onClose={() => setShowDeleteDialog(false)}
      onConfirm={handleConfirmDelete}
      title="Delete Learning"
      description="Are you sure you want to delete this learning? This action cannot be undone."
      confirmText="Delete"
      variant="destructive"
    />
  </>
  );
}

export function LearningGrowthTracker() {
  const { acquisitiveLearnings, currentSession, removeAcquisitiveLearning } = useHVACStore();

  const handleDeleteLearning = async (loopId: string) => {
    try {
      const sessionId = currentSession?.session_id || 'hvac-agent-session-001';
      await hvacApi.deleteAcquisitiveLearning(loopId, sessionId);
      removeAcquisitiveLearning(loopId);
    } catch (error) {
      console.error('Failed to delete learning:', error);
      throw error;
    }
  };

  if (acquisitiveLearnings.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
         
            Learned Insights
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
    
          Learned Insights
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="max-h-[600px] overflow-y-auto space-y-4 pr-2">
          {acquisitiveLearnings.map((learning, index) => (
            <ExecutionLearningCard
              key={learning.loop_id}
              learning={learning}
              executionNumber={acquisitiveLearnings.length - index}
              onDelete={handleDeleteLearning}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

