import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { IconFolderPlus } from '@tabler/icons-react';

interface CreateFolderDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onCreateFolder: (name: string) => void;
  currentPath?: string;
}

export function CreateFolderDialog({
  isOpen,
  onClose,
  onCreateFolder,
  currentPath = '/',
}: CreateFolderDialogProps) {
  const [folderName, setFolderName] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!folderName.trim()) {
      setError('Folder name is required');
      return;
    }

    if (folderName.includes('/') || folderName.includes('\\')) {
      setError('Folder name cannot contain slashes');
      return;
    }

    if (folderName.length > 255) {
      setError('Folder name is too long');
      return;
    }

    onCreateFolder(folderName.trim());
    setFolderName('');
    setError(null);
    onClose();
  };

  const handleCancel = () => {
    setFolderName('');
    setError(null);
    onClose();
  };

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      handleCancel();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogContent className="w-full max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <IconFolderPlus className="h-5 w-5 text-blue-500" />
            <span>Create New Folder</span>
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="folderName" className="text-sm font-medium text-gray-700">
              Folder Name
            </Label>
            <Input
              id="folderName"
              type="text"
              value={folderName}
              onChange={(e) => {
                setFolderName(e.target.value);
                setError(null);
              }}
              placeholder="Enter folder name"
              className="mt-1"
              autoFocus
            />
            {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
          </div>

          <div>
            <Label className="text-sm font-medium text-gray-700">Location</Label>
            <p className="mt-1 text-sm text-gray-500">{currentPath}</p>
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <Button type="button" variant="outline" onClick={handleCancel}>
              Cancel
            </Button>
            <Button type="submit">Create Folder</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
