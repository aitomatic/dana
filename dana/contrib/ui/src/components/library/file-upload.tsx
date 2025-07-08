import React, { useCallback } from 'react';
import { IconUpload, IconX } from '@tabler/icons-react';
import { cn } from '@/lib/utils';

interface FileUploadProps {
  onFilesSelected: (files: File[]) => void;
  multiple?: boolean;
  accept?: string;
  maxSize?: number; // in bytes
  className?: string;
}

export function FileUpload({
  onFilesSelected,
  multiple = true,
  accept = '*/*',
  maxSize = 50 * 1024 * 1024, // 50MB default
  className,
}: FileUploadProps) {
  const [isDragOver, setIsDragOver] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const validateFiles = useCallback(
    (files: FileList): File[] => {
      const validFiles: File[] = [];
      const errors: string[] = [];

      Array.from(files).forEach(file => {
        if (file.size > maxSize) {
          errors.push(
            `${file.name} is too large. Maximum size is ${formatFileSize(maxSize)}`
          );
        } else {
          validFiles.push(file);
        }
      });

      if (errors.length > 0) {
        setError(errors.join(', '));
        return [];
      }

      setError(null);
      return validFiles;
    },
    [maxSize]
  );

  const handleFileSelect = useCallback(
    (files: FileList) => {
      const validFiles = validateFiles(files);
      if (validFiles.length > 0) {
        onFilesSelected(validFiles);
      }
    },
    [validateFiles, onFilesSelected]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      handleFileSelect(e.dataTransfer.files);
    },
    [handleFileSelect]
  );

  const handleFileInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files) {
        handleFileSelect(files);
      }
    },
    [handleFileSelect]
  );

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className={cn('w-full', className)}>
      <div
        className={cn(
          'border-2 border-dashed rounded-lg p-6 text-center transition-colors',
          isDragOver
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400',
          error && 'border-red-500 bg-red-50'
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <IconUpload className='mx-auto h-12 w-12 text-gray-400 mb-4' />
        <div className='space-y-2'>
          <p className='text-sm text-gray-600'>
            Drag and drop files here, or{' '}
            <label className='text-blue-600 hover:text-blue-500 cursor-pointer'>
              browse
              <input
                type='file'
                multiple={multiple}
                accept={accept}
                onChange={handleFileInputChange}
                className='hidden'
              />
            </label>
          </p>
          <p className='text-xs text-gray-500'>
            Maximum file size: {formatFileSize(maxSize)}
          </p>
        </div>
      </div>

      {error && (
        <div className='mt-2 flex items-center space-x-2 text-sm text-red-600'>
          <IconX className='h-4 w-4' />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
