import { Dialog, DialogContent, DialogFooter, DialogHeader } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { HelpCircle } from 'iconoir-react';

interface DeleteAgentDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  onSuccess?: () => void;
  isDeleting?: boolean;
  agentName?: string;
}

export function DeleteAgentDialog({
  isOpen,
  onClose,
  onConfirm,
  onSuccess,
  isDeleting = false,
  agentName,
}: DeleteAgentDialogProps) {
  const handleConfirm = async () => {
    try {
      await onConfirm();
      // Call onSuccess callback if provided
      if (onSuccess) {
        onSuccess();
      }
    } catch (error) {
      // Error handling is done in the parent component
      console.error('Delete operation failed:', error);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <div className="flex flex-col gap-1">
            <div className="flex justify-center items-center rounded-full size-12 bg-warning-50">
              <HelpCircle className="text-warning-600 size-6" strokeWidth={2} />
            </div>
            <span className="text-lg font-semibold text-gray-900">Delete Agent?</span>
            <span className="text-sm text-gray-600">
              {agentName
                ? `This action will permanently delete "${agentName}" and all of its associated data. Are you sure you want to continue?`
                : 'This action will permanently delete the agent and all of its associated data. Are you sure you want to continue?'}
            </span>
          </div>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} className="w-1/2">
            Cancel
          </Button>
          <Button onClick={handleConfirm} className="w-1/2" disabled={isDeleting}>
            {isDeleting ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
