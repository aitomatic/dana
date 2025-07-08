import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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

  if (!isOpen) return null;

  return (
    <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50'>
      <div className='bg-white rounded-lg p-6 w-full max-w-md mx-4'>
        <div className='flex items-center space-x-2 mb-4'>
          <IconFolderPlus className='h-5 w-5 text-blue-500' />
          <h2 className='text-lg font-semibold text-gray-900'>
            Create New Folder
          </h2>
        </div>

        <form onSubmit={handleSubmit} className='space-y-4'>
          <div>
            <Label
              htmlFor='folderName'
              className='text-sm font-medium text-gray-700'
            >
              Folder Name
            </Label>
            <Input
              id='folderName'
              type='text'
              value={folderName}
              onChange={e => {
                setFolderName(e.target.value);
                setError(null);
              }}
              placeholder='Enter folder name'
              className='mt-1'
              autoFocus
            />
            {error && <p className='mt-1 text-sm text-red-600'>{error}</p>}
          </div>

          <div>
            <Label className='text-sm font-medium text-gray-700'>
              Location
            </Label>
            <p className='mt-1 text-sm text-gray-500'>{currentPath}</p>
          </div>

          <div className='flex justify-end space-x-2 pt-4'>
            <Button type='button' variant='outline' onClick={handleCancel}>
              Cancel
            </Button>
            <Button type='submit'>Create Folder</Button>
          </div>
        </form>
      </div>
    </div>
  );
}
