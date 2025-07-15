import { useState } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { FileText, Settings, GitBranch, Package, Zap, Copy, Check, Download } from 'lucide-react';
import { toast } from 'sonner';
import { AgentEditor } from '@/components/agent-editor';
import type { MultiFileProject, DanaFile } from '@/lib/api';

interface MultiFileCodeEditorProps {
  project: MultiFileProject;
  onFileChange?: (file: DanaFile, newContent: string) => void;
  onDownload?: (project: MultiFileProject) => void;
  className?: string;
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
}: MultiFileCodeEditorProps) => {
  const [activeFile, setActiveFile] = useState<DanaFile>(project.files[0]);
  const [copiedFile, setCopiedFile] = useState<string | null>(null);

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

        {activeFile.dependencies && activeFile.dependencies.length > 0 && (
          <div className="flex gap-1 items-center mt-1">
            <span className="text-xs text-gray-500">Dependencies:</span>
            {activeFile.dependencies.map((dep) => (
              <Badge key={dep} variant="outline" className="text-xs">
                {dep}
              </Badge>
            ))}
          </div>
        )}
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
          enableAutoValidation={true}
          autoValidationDelay={1000}
        />
      </div>
    </div>
  );
};

export default MultiFileCodeEditor;
