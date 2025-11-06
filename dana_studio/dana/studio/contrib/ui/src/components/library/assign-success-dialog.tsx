import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { CheckCircle, XmarkCircle, WarningCircle, ArrowUpRight } from 'iconoir-react';
import type { AssignmentResult } from '@/types/domainKnowledge';

interface AssignSuccessDialogProps {
  isOpen: boolean;
  onClose: () => void;
  knowledgePackName: string;
  results: AssignmentResult[];
}

export function AssignSuccessDialog({
  isOpen,
  onClose,
  knowledgePackName,
  results,
}: AssignSuccessDialogProps) {
  const successfulAssignments = results.filter((r) => r.success);
  const failedAssignments = results.filter((r) => !r.success);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            Assignment Complete
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Knowledge Pack Info */}
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">
              <span className="font-medium">Knowledge Pack:</span> {knowledgePackName}
            </p>
          </div>

          {/* Summary */}
          <div className="">
            <p className="text-sm text-gray-600">
              {successfulAssignments.length > 0 && (
                <span className=" font-medium">
                  Successfully assigned to {successfulAssignments.length} agent{successfulAssignments.length !== 1 ? 's' : ''}
                </span>
              )}
              {successfulAssignments.length > 0 && failedAssignments.length > 0 && (
                <span className="mx-2">•</span>
              )}
              {failedAssignments.length > 0 && (
                <span className="font-medium">
                  Failed to assign to {failedAssignments.length} agent{failedAssignments.length !== 1 ? 's' : ''}
                </span>
              )}
            </p>
          </div>

          {/* Successful Assignments */}
          {successfulAssignments.length > 0 && (
            <div>
              <div className="space-y-1">
                {successfulAssignments.map((result) => (
                  <div key={result.agentId} className="flex items-center justify-between py-2 rounded">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                      <span className="text-sm font-medium">{result.agentName}</span>
                    </div>
                    <a
                      href={`/agents/${result.agentId}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-xs text-gray-600 hover:text-blue-700 transition-colors"
                    >
                      <span>Go to agent</span>
                      <ArrowUpRight className="w-3 h-3" />
                    </a>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Failed Assignments */}
          {failedAssignments.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-red-600 mb-2 flex items-center gap-1">
                <XmarkCircle className="w-4 h-4" />
                Failed Assignments
              </h4>
              <div className="space-y-1">
                {failedAssignments.map((result) => (
                  <div key={result.agentId} className="p-2 bg-red-50 rounded">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <XmarkCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
                        <span className="text-sm font-medium">{result.agentName}</span>
                      </div>
                      <a
                        href={`/agents/${result.agentId}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-xs text-red-600 hover:text-red-700 transition-colors"
                      >
                        <span>Go to agent</span>
                        <ArrowUpRight className="w-3 h-3" />
                      </a>
                    </div>
                    {result.error && (
                      <p className="text-xs text-red-600 ml-6">{result.error}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Warning if all failed */}
          {successfulAssignments.length === 0 && failedAssignments.length > 0 && (
            <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-center gap-2">
                <WarningCircle className="w-4 h-4 text-yellow-600 flex-shrink-0" />
                <p className="text-sm text-yellow-800">
                  No agents were successfully assigned. Please check the error messages above and try again.
                </p>
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button onClick={onClose} variant='secondary' className="w-full">
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
