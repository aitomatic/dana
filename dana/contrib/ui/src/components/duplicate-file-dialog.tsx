import { FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import type { ExtractionFile } from '@/stores/extraction-file-store';

interface DuplicateFileDialogProps {
  open: boolean;
  file: ExtractionFile | null;
  onAction: (action: 'replace' | 'copy' | 'cancel') => void;
  onClose: () => void;
}

export function DuplicateFileDialog({ open, file, onAction, onClose }: DuplicateFileDialogProps) {
  if (!file) return null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">Duplicate File Detected</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
            <FileText className="w-5 h-5 text-gray-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900">
                The file "{file.original_filename}" already exists
              </p>
              <p className="text-xs text-gray-700 mt-1">
                What would you like to do with this file?
              </p>
            </div>
          </div>

          <div className="flex gap-2">
            <Button onClick={() => onAction('cancel')} className="justify-start" variant="ghost">
              Cancel upload
            </Button>

            <Button onClick={() => onAction('copy')} className="justify-start" variant="outline">
              Upload as a copy
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
