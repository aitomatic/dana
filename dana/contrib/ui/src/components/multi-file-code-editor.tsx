import { useState } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  FileText,
  Settings,
  GitBranch,
  Package,
  Zap,
  Copy,
  Check,
  Download,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';
import { toast } from 'sonner';
import { AgentEditor } from '@/components/agent-editor';
import { apiService } from '@/lib/api';
import type { MultiFileProject, DanaFile, CodeValidationResponse } from '@/lib/api';

interface MultiFileCodeEditorProps {
  project: MultiFileProject;
  onFileChange?: (file: DanaFile, newContent: string) => void;
  onDownload?: (project: MultiFileProject) => void;
  className?: string;
  enableValidation?: boolean;
}

// File type icons
const getFileTypeIcon = (fileType: string) => {
  switch (fileType) {
    case 'agent':
      return <Zap className="w-3 h-3" />;
    case 'workflow':
      return <GitBranch className="w-3 h-3" />;
    case 'resources':
      return <Package className="w-3 h-3" />;
    case 'methods':
      return <Settings className="w-3 h-3" />;
    case 'common':
      return <FileText className="w-3 h-3" />;
    default:
      return <FileText className="w-3 h-3" />;
  }
};

// File type colors
const getFileTypeColor = (fileType: string) => {
  switch (fileType) {
    case 'agent':
      return 'text-blue-500';
    case 'workflow':
      return 'text-green-500';
    case 'resources':
      return 'text-yellow-500';
    case 'methods':
      return 'text-purple-500';
    case 'common':
      return 'text-gray-500';
    default:
      return 'text-gray-500';
  }
};

const MultiFileCodeEditor = ({
  project,
  onFileChange,
  onDownload,
  className,
  enableValidation = true,
}: MultiFileCodeEditorProps) => {
  const [activeFile, setActiveFile] = useState<DanaFile>(project.files[0]);
  const [copiedFile, setCopiedFile] = useState<string | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<CodeValidationResponse | null>(null);

  console.log('Multiple file');
  const handleFileSelect = (file: DanaFile) => {
    setActiveFile(file);
  };

  const handleFileChange = (newContent: string) => {
    if (onFileChange) {
      onFileChange(activeFile, newContent);
    }
  };

  const handleCopyFile = async (file: DanaFile) => {
    try {
      await navigator.clipboard.writeText(file.content);
      setCopiedFile(file.filename);
      toast.success(`${file.filename} copied to clipboard`);
      setTimeout(() => setCopiedFile(null), 2000);
    } catch (error) {
      toast.error('Failed to copy file content');
    }
  };

  const handleDownload = () => {
    if (onDownload) {
      onDownload(project);
    }
  };

  const handleValidation = async () => {
    setIsValidating(true);
    try {
      console.log({
        multi_file_project: project,
        agent_name: project.name,
        description: project.description,
      });
      const result = await apiService.validateCode({
        multi_file_project: project,
        agent_name: project.name,
        description: project.description,
      });

      setValidationResult(result);

      if (result.is_valid) {
        toast.success('All files are valid!');
      } else {
        toast.error('Validation errors detected. Check the results below.');
      }
    } catch (error) {
      toast.error('Failed to validate project');
      console.error('Validation error:', error);
    } finally {
      setIsValidating(false);
    }
  };

  return (
    <div className={cn('flex flex-col h-full', className)}>
      {/* File tabs */}
      <div className="flex bg-gray-50 border-b border-gray-200">
        <div className="flex overflow-x-auto flex-1">
          {project.files.map((file) => (
            <button
              key={file.filename}
              className={cn(
                'flex items-center gap-2 px-3 py-2 text-sm font-medium border-r border-gray-200 hover:bg-gray-100 transition-colors min-w-0',
                activeFile.filename === file.filename
                  ? 'bg-white border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-600',
              )}
              onClick={() => handleFileSelect(file)}
            >
              <div className={cn('flex-shrink-0', getFileTypeColor(file.file_type))}>
                {getFileTypeIcon(file.file_type)}
              </div>
              <span className="truncate">{file.filename}</span>
              {file.filename === project.main_file && (
                <Badge variant="secondary" className="px-1 py-0 text-xs">
                  main
                </Badge>
              )}
            </button>
          ))}
        </div>

        {/* Actions */}
        <div className="flex gap-1 items-center px-2 border-l border-gray-200">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleCopyFile(activeFile)}
            className="p-1"
            title="Copy file content"
          >
            {copiedFile === activeFile.filename ? (
              <Check className="w-4 h-4 text-green-500" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </Button>
          {enableValidation && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleValidation}
              className="p-1"
              title="Validate project"
              disabled={isValidating}
            >
              {isValidating ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDownload}
            className="p-1"
            title="Download project"
          >
            <Download className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* File info */}
      <div className="px-3 py-2 bg-gray-50 border-b border-gray-200">
        <div className="flex gap-2 items-center text-sm text-gray-600">
          <div className={cn('flex items-center gap-1', getFileTypeColor(activeFile.file_type))}>
            {getFileTypeIcon(activeFile.file_type)}
            <span className="font-medium">{activeFile.filename}</span>
          </div>
          <span>•</span>
          <span>{activeFile.file_type}</span>
          {activeFile.description && (
            <>
              <span>•</span>
              <span className="truncate">{activeFile.description}</span>
            </>
          )}
        </div>
      </div>

      {/* Code editor */}
      <div className="flex-1 min-h-0">
        <AgentEditor
          value={activeFile.content}
          onChange={handleFileChange}
          placeholder="Edit your Dana code here..."
          className="h-full"
          enableAnimation={true}
          animationSpeed={25}
          enableAutoValidation={false} // Disable auto-validation for multi-file
          autoValidationDelay={1000}
        />
      </div>

      {/* Validation results */}
      {validationResult && !validationResult.is_valid && (
        <div className="p-3 bg-red-50 border-t border-gray-200">
          <div className="flex gap-2 items-center mb-2">
            <AlertCircle className="w-4 h-4 text-red-600" />
            <span className="text-sm font-medium text-red-700">Project Validation Issues</span>
          </div>

          {/* File-specific errors */}
          {validationResult.file_results && validationResult.file_results.length > 0 && (
            <div className="space-y-2">
              {validationResult.file_results.map((fileResult: any, index: number) => (
                <div key={index} className="text-sm">
                  <span className="font-medium text-red-700">{fileResult.filename}:</span>
                  {fileResult.errors && fileResult.errors.length > 0 && (
                    <ul className="mt-1 ml-4 space-y-1">
                      {fileResult.errors.map((error: any, errorIndex: number) => (
                        <li key={errorIndex} className="text-red-600">
                          • {error.message}
                        </li>
                      ))}
                    </ul>
                  )}
                  {fileResult.warnings && fileResult.warnings.length > 0 && (
                    <ul className="mt-1 ml-4 space-y-1">
                      {fileResult.warnings.map((warning: any, warningIndex: number) => (
                        <li key={warningIndex} className="text-orange-600">
                          ⚠ {warning.message}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Dependency errors */}
          {validationResult.dependency_errors && validationResult.dependency_errors.length > 0 && (
            <div className="mt-3">
              <span className="text-sm font-medium text-red-700">Dependency Issues:</span>
              <ul className="mt-1 ml-4 space-y-1">
                {validationResult.dependency_errors.map((depError: any, index: number) => (
                  <li key={index} className="text-sm text-red-600">
                    • {depError.message}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Overall errors */}
          {validationResult.overall_errors && validationResult.overall_errors.length > 0 && (
            <div className="mt-3">
              <span className="text-sm font-medium text-red-700">Project Issues:</span>
              <ul className="mt-1 ml-4 space-y-1">
                {validationResult.overall_errors.map((overallError: any, index: number) => (
                  <li key={index} className="text-sm text-red-600">
                    • {overallError.message}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Success message */}
      {validationResult && validationResult.is_valid && (
        <div className="p-3 bg-green-50 border-t border-gray-200">
          <div className="flex gap-2 items-center">
            <Check className="w-4 h-4 text-green-600" />
            <span className="text-sm font-medium text-green-700">All files are valid!</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default MultiFileCodeEditor;
