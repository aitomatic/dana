import { useState, useCallback, useRef, useEffect } from 'react';
import { Upload, X, FileText, AlertCircle, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import { apiService } from '@/lib/api';
import { Button } from '@/components/ui/button';

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  status: 'uploading' | 'success' | 'error';
  path?: string;
  error?: string;
  generatedResponse?: string;
  updatedCapabilities?: any;
  readyForCodeGeneration?: boolean;
}

interface FileUploadProps {
  agentId?: string;
  onFilesUploaded?: (files: UploadedFile[]) => void;
  className?: string;
  compact?: boolean;
  conversationContext?: Array<{ role: string; content: string }>;
  agentInfo?: any;
  autoOpen?: boolean;
}

export function FileUpload({
  agentId,
  onFilesUploaded,
  className = '',
  conversationContext,
  agentInfo,
  autoOpen = false,
}: FileUploadProps) {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-open file dialog on mount if autoOpen is true
  useEffect(() => {
    if (autoOpen && fileInputRef.current) {
      fileInputRef.current.click();
    }
  }, [autoOpen]);

  const uploadFile = useCallback(
    async (file: File): Promise<UploadedFile> => {
      if (agentInfo && !agentInfo.folder_path) {
        toast.error(
          'Agent folder path is missing. Please complete agent creation before uploading knowledge files.',
        );
        return {
          id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
          name: file.name,
          size: file.size,
          type: file.type,
          status: 'error',
          error: 'Missing agent folder path',
        };
      }
      const uploadedFile: UploadedFile = {
        id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
        name: file.name,
        size: file.size,
        type: file.type,
        status: 'uploading',
      };

      try {
        if (agentId) {
          // Use the new agent-specific upload endpoint
          const doc = await apiService.uploadAgentDocument(agentId, file);
          uploadedFile.status = 'success';
          uploadedFile.path = doc.filename;
        } else {
          // Fallback to the old upload endpoint
          const doc = await apiService.uploadDocument({ file, title: file.name });
          uploadedFile.status = 'success';
          uploadedFile.path = doc.filename;
        }
      } catch (error) {
        uploadedFile.status = 'error';
        uploadedFile.error = (error as Error).message;
      }

      return uploadedFile;
    },
    [agentId, conversationContext, agentInfo],
  );

  const handleFileInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    setIsUploading(true);
    const initialFiles: UploadedFile[] = Array.from(files).map((file) => ({
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'uploading',
    }));
    setUploadedFiles((prev) => [...prev, ...initialFiles]);
    try {
      const results = await Promise.all(Array.from(files).map(uploadFile));
      setUploadedFiles((prev) => {
        const updated = [...prev];
        results.forEach((result) => {
          const initialFileIndex = updated.findIndex(
            (f) => f.name === result.name && f.status === 'uploading',
          );
          if (initialFileIndex !== -1) {
            updated[initialFileIndex] = result;
          }
        });
        return updated;
      });
      if (onFilesUploaded) {
        onFilesUploaded(results.filter((f) => f.status === 'success'));
      }
    } catch (error) {
      console.error('Upload error:', error);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const removeFile = (fileId: string) => {
    setUploadedFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusIcon = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploading':
        return (
          <div className="w-4 h-4 rounded-full border-2 border-blue-500 animate-spin border-t-transparent" />
        );
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
    }
  };

  return (
    <div className={className}>
      <input
        type="file"
        ref={fileInputRef}
        style={{ display: 'none' }}
        multiple
        onChange={handleFileInputChange}
        disabled={isUploading || (agentInfo && !agentInfo.folder_path)}
      />
      <Button
        type="button"
        variant="outline"
        onClick={() => fileInputRef.current?.click()}
        disabled={isUploading || (agentInfo && !agentInfo.folder_path)}
      >
        {isUploading ? (
          'Uploading...'
        ) : (
          <>
            <Upload className="mr-2 w-4 h-4" />
            Select Files
          </>
        )}
      </Button>
      {uploadedFiles.length > 0 && (
        <div className="mt-6">
          <h4 className="mb-3 text-sm font-medium text-gray-900">
            Uploaded Files ({uploadedFiles.length})
          </h4>
          <div className="space-y-3">
            {uploadedFiles.map((file) => (
              <div key={file.id} className="flex gap-4 items-center p-3 bg-gray-50 rounded-lg">
                <FileText className="w-5 h-5 text-gray-400" />
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate">{file.name}</div>
                  <div className="text-sm text-gray-500">
                    {formatFileSize(file.size)}
                    {file.path && <span className="ml-2 text-green-600">→ {file.path}</span>}
                    {file.error && <span className="ml-2 text-red-600">Error: {file.error}</span>}
                  </div>
                </div>
                <div className="flex gap-2 items-center">
                  {getStatusIcon(file.status)}
                  <button
                    onClick={() => removeFile(file.id)}
                    className="text-gray-400 hover:text-red-500"
                    title="Remove file"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
