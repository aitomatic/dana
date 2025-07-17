import { useState, useCallback, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
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
}

export function FileUpload({
  agentId,
  onFilesUploaded,
  className = '',
  compact = false,
  conversationContext,
  agentInfo
}: FileUploadProps) {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const uploadFile = useCallback(async (file: File): Promise<UploadedFile> => {
    if (agentInfo && !agentInfo.folder_path) {
      toast.error('Agent folder path is missing. Please complete agent creation before uploading knowledge files.');
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
      // Create FormData for file upload
      const formData = new FormData();
      formData.append('file', file);
      if (agentId) formData.append('agent_id', agentId);
      // Add conversation context and agent info for regeneration
      if (conversationContext) {
        formData.append('conversation_context', JSON.stringify(conversationContext));
      }
      if (agentInfo) {
        formData.append('agent_info', JSON.stringify(agentInfo));
      }

      // Upload file to backend
      const response = await apiService.uploadKnowledgeFile(formData);

      if (response.success) {
        uploadedFile.status = 'success';
        uploadedFile.path = response.file_path;
        uploadedFile.generatedResponse = response.generated_response;
        uploadedFile.updatedCapabilities = response.updated_capabilities;
        uploadedFile.readyForCodeGeneration = response.ready_for_code_generation;

        // Debug logging
        console.log('📁 File Upload Response:', {
          filename: file.name,
          success: response.success,
          ready_for_code_generation: response.ready_for_code_generation,
          updated_capabilities: response.updated_capabilities,
          generated_response: response.generated_response
        });

        // If we have a successful upload with file_path, trigger document processing
        if (response.file_path && conversationContext && agentInfo) {
          try {
            // Extract document folder from file path
            const documentFolder = response.file_path.split('/').slice(0, -1).join('/');
            
            // Convert conversation context to string array
            const conversation = conversationContext.map(msg => 
              `${msg.role}: ${msg.content}`
            );
            
            // Create summary from agent info and conversation
            const conversationSummary = conversationContext.length > 0 
              ? `Recent conversation:\n${conversationContext.slice(-3).map(msg => `${msg.role}: ${msg.content}`).join('\n')}`
              : 'No recent conversation available.';
            
            const summary = `Agent: ${agentInfo.name || 'Unknown'}\n` +
                          `Description: ${agentInfo.description || 'No description'}\n` +
                          `${conversationSummary}\n` +
                          `Context: User is uploading knowledge files to enhance the agent's capabilities.`;
            
            console.log('🔄 Starting document processing for:', {
              document_folder: documentFolder,
              conversation: conversation,
              summary: summary
            });
            
            const processResponse = await apiService.processAgentDocuments({
              document_folder: documentFolder,
              conversation: conversation,
              summary: summary
            });
            
            if (processResponse.success) {
              console.log('✅ Document processing started:', processResponse);
              toast.success(`Document processing started for ${file.name}`);
            } else {
              console.warn('⚠️ Document processing failed:', processResponse);
              toast.error('Document processing failed to start');
            }
          } catch (processError) {
            console.error('❌ Document processing error:', processError);
            toast.error('Failed to start document processing');
          }
        }

        toast.success(`Uploaded ${file.name} successfully`);
      } else {
        uploadedFile.status = 'error';
        uploadedFile.error = response.error || 'Upload failed';
        toast.error(`Failed to upload ${file.name}`);
      }
    } catch (error) {
      uploadedFile.status = 'error';
      uploadedFile.error = error instanceof Error ? error.message : 'Upload failed';
      toast.error(`Failed to upload ${file.name}`);
    }

    return uploadedFile;
  }, [agentId, conversationContext, agentInfo]);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    setIsUploading(true);

    // Create initial file entries
    const initialFiles: UploadedFile[] = acceptedFiles.map(file => ({
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'uploading',
    }));

    setUploadedFiles(prev => [...prev, ...initialFiles]);

    // Upload files one by one
    try {
      const results = await Promise.all(acceptedFiles.map(uploadFile));

      // Update the uploaded files with results
      setUploadedFiles(prev => {
        const updated = [...prev];
        results.forEach((result) => {
          const initialFileIndex = updated.findIndex(f => f.name === result.name && f.status === 'uploading');
          if (initialFileIndex !== -1) {
            updated[initialFileIndex] = result;
          }
        });
        return updated;
      });

      if (onFilesUploaded) {
        onFilesUploaded(results.filter(f => f.status === 'success'));
      }
    } catch (error) {
      console.error('Upload error:', error);
    } finally {
      setIsUploading(false);
    }
  }, [uploadFile, onFilesUploaded]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/csv': ['.csv'],
      'application/json': ['.json'],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    multiple: true,
  });

  const removeFile = (fileId: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
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
        return <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />;
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
    }
  };

  if (compact) {
    return (
      <div className={`${className}`}>
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors ${isDragActive
            ? 'border-blue-400 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
            }`}
        >
          <input {...getInputProps()} />
          <Upload className="w-6 h-6 mx-auto mb-2 text-gray-400" />
          <p className="text-sm text-gray-600">
            {isDragActive ? 'Drop files here' : 'Drag files or click to upload'}
          </p>
          <p className="text-xs text-gray-400 mt-1">
            PDF, DOC, TXT, MD, CSV, JSON (max 10MB)
          </p>
        </div>

        {uploadedFiles.length > 0 && (
          <div className="mt-4 space-y-2">
            {uploadedFiles.map((file) => (
              <div
                key={file.id}
                className="flex items-center gap-3 p-2 bg-gray-50 rounded-lg text-sm"
              >
                <FileText className="w-4 h-4 text-gray-400" />
                <div className="flex-1 min-w-0">
                  <div className="truncate font-medium">{file.name}</div>
                  <div className="text-xs text-gray-500">{formatFileSize(file.size)}</div>
                </div>
                {getStatusIcon(file.status)}
                <button
                  onClick={() => removeFile(file.id)}
                  className="text-gray-400 hover:text-red-500"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={`${className}`}>
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${isDragActive
          ? 'border-blue-400 bg-blue-50'
          : 'border-gray-300 hover:border-gray-400'
          }`}
      >
        <input {...getInputProps()} />
        <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          {isDragActive ? 'Drop files here' : 'Upload Knowledge Files'}
        </h3>
        <p className="text-gray-600 mb-4">
          Drag and drop files here, or click to browse
        </p>
        <p className="text-sm text-gray-500">
          Supported formats: PDF, DOC, DOCX, TXT, MD, CSV, JSON (max 10MB each)
        </p>
        <Button
          type="button"
          variant="outline"
          className="mt-4"
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading || (agentInfo && !agentInfo.folder_path)}
        >
          {isUploading ? 'Uploading...' : 'Browse Files'}
        </Button>
      </div>

      {uploadedFiles.length > 0 && (
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-900 mb-3">
            Uploaded Files ({uploadedFiles.length})
          </h4>
          <div className="space-y-3">
            {uploadedFiles.map((file) => (
              <div
                key={file.id}
                className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg"
              >
                <FileText className="w-5 h-5 text-gray-400" />
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate">{file.name}</div>
                  <div className="text-sm text-gray-500">
                    {formatFileSize(file.size)}
                    {file.path && (
                      <span className="ml-2 text-green-600">
                        → {file.path}
                      </span>
                    )}
                    {file.error && (
                      <span className="ml-2 text-red-600">
                        Error: {file.error}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
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