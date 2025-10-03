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
          <div className="flex items-start mb-8 mt-2 gap-3 px-4 py-4 rounded-lg border">
            <div className="flex items-center gap-2 justify-center w-10 h-10 bg-gray-100 rounded-lg">
            <FileText className="w-5 h-5 text-gray-600 mt-0.5 flex-shrink-0" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-md text-gray-900">
                <span className='font-semibold'>{file.original_filename}</span> already exists
              </p>
              <p className="text-sm text-gray-700 mt-1">
               Do you want to upload this file as a copy?
              </p>
            </div>
          </div>

          <div className="flex justify-end gap-2">
            <Button onClick={() => onAction('cancel')} className="justify-start" variant="ghost">
              Cancel upload
            </Button>

            <Button onClick={() => onAction('copy')} className="justify-start" variant="default">
              Upload as a copy
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
