import { Dialog, DialogContent, DialogFooter, DialogHeader } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { WarningCircle } from 'iconoir-react';

interface DeleteTemplateDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  isDeleting: boolean;
  itemType: 'template' | 'session';
  itemName: string;
}

export function DeleteTemplateDialog({
  isOpen,
  onClose,
  onConfirm,
  isDeleting,
  itemType,
  itemName,
}: DeleteTemplateDialogProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex flex-col gap-3">
            <div className="flex justify-center items-center rounded-full size-12 bg-warning-50">
              <WarningCircle className="text-warning-600 size-6" strokeWidth={2} />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Delete {itemType === 'template' ? 'Capture Template' : 'Session'}?
              </h3>
              <p className="text-sm text-gray-600 mt-2 mb-6">
                This action will permanently delete "{itemName}" and all associated data. 
                This cannot be undone. Are you sure you want to continue?
              </p>
            </div>
          </div>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isDeleting} className="flex-1">
            Cancel
          </Button>
          <Button 
            variant="destructive" 
            onClick={onConfirm} 
            disabled={isDeleting}
            className="flex-1"
          >
            {isDeleting ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
