import { useState } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Download, 
  FileText, 
  Settings, 
  GitBranch, 
  Package, 
  Zap,
  Copy,
  Check,
  Edit,
  Save,
  X
} from 'lucide-react';
import { toast } from 'sonner';
import { AgentEditor } from '@/components/agent-editor';
import type { MultiFileProject, DanaFile } from '@/lib/api';

interface MultiFileViewerProps {
  project: MultiFileProject;
  onFileSelect?: (file: DanaFile) => void;
  onFileChange?: (file: DanaFile, newContent: string) => void;
  onDownload?: (project: MultiFileProject) => void;
  className?: string;
}

// File type icons
const getFileTypeIcon = (fileType: string) => {
  switch (fileType) {
    case 'agent':
      return <Zap className="h-4 w-4" />;
    case 'workflow':
      return <GitBranch className="h-4 w-4" />;
    case 'resources':
      return <Package className="h-4 w-4" />;
    case 'methods':
      return <Settings className="h-4 w-4" />;
    case 'common':
      return <FileText className="h-4 w-4" />;
    default:
      return <FileText className="h-4 w-4" />;
  }
};

// File type colors
const getFileTypeColor = (fileType: string) => {
  switch (fileType) {
    case 'agent':
      return 'bg-blue-500';
    case 'workflow':
      return 'bg-green-500';
    case 'resources':
      return 'bg-yellow-500';
    case 'methods':
      return 'bg-purple-500';
    case 'common':
      return 'bg-gray-500';
    default:
      return 'bg-gray-500';
  }
};

const MultiFileViewer = ({ 
  project, 
  onFileSelect, 
  onFileChange,
  onDownload, 
  className 
}: MultiFileViewerProps) => {
  const [selectedFile, setSelectedFile] = useState<DanaFile | null>(null);
  const [copiedFile, setCopiedFile] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState('');
  const [activeTab, setActiveTab] = useState<'files' | 'preview'>('files');

  const handleFileSelect = (file: DanaFile) => {
    setSelectedFile(file);
    setEditedContent(file.content);
    setIsEditing(false);
    if (onFileSelect) {
      onFileSelect(file);
    }
  };

  const handleEditStart = () => {
    if (selectedFile) {
      setEditedContent(selectedFile.content);
      setIsEditing(true);
    }
  };

  const handleEditSave = () => {
    if (selectedFile && onFileChange) {
      onFileChange(selectedFile, editedContent);
      setIsEditing(false);
      toast.success(`${selectedFile.filename} saved successfully`);
    }
  };

  const handleEditCancel = () => {
    if (selectedFile) {
      setEditedContent(selectedFile.content);
      setIsEditing(false);
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
    <div className={cn('w-full border rounded-lg bg-white', className)}>
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Package className="h-5 w-5" />
              {project.name}
            </h2>
            <p className="text-sm text-muted-foreground">{project.description}</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline">
              {project.structure_type}
            </Badge>
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownload}
              className="gap-2"
            >
              <Download className="h-4 w-4" />
              Download
            </Button>
          </div>
        </div>
      </div>
      <div className="p-4">
        <div className="w-full">
          <div className="flex border-b">
            <button
              className={cn(
                'px-4 py-2 text-sm font-medium',
                activeTab === 'files' 
                  ? 'border-b-2 border-blue-500 text-blue-600' 
                  : 'text-gray-500 hover:text-gray-700'
              )}
              onClick={() => setActiveTab('files')}
            >
              Files
            </button>
            <button
              className={cn(
                'px-4 py-2 text-sm font-medium',
                activeTab === 'preview' 
                  ? 'border-b-2 border-blue-500 text-blue-600' 
                  : 'text-gray-500 hover:text-gray-700'
              )}
              onClick={() => setActiveTab('preview')}
            >
              Preview
            </button>
          </div>
          
          {activeTab === 'files' && (
            <div className="mt-4 space-y-4">
              <div className="grid gap-2">
                {project.files.map((file) => (
                  <div
                    key={file.filename}
                    className={cn(
                      'flex items-center justify-between p-3 rounded-lg border cursor-pointer hover:bg-gray-50 transition-colors',
                      selectedFile?.filename === file.filename && 'border-blue-500 bg-blue-50'
                    )}
                    onClick={() => handleFileSelect(file)}
                  >
                    <div className="flex items-center gap-3">
                      <div className={cn(
                        'p-2 rounded-full text-white',
                        getFileTypeColor(file.file_type)
                      )}>
                        {getFileTypeIcon(file.file_type)}
                      </div>
                      <div>
                        <p className="font-medium">{file.filename}</p>
                        <p className="text-sm text-gray-600">
                          {file.description || 'Dana code file'}
                        </p>
                        {file.dependencies && file.dependencies.length > 0 && (
                          <div className="flex items-center gap-1 mt-1">
                            <span className="text-xs text-gray-500">Depends on:</span>
                            {file.dependencies.map((dep) => (
                              <Badge key={dep} variant="secondary" className="text-xs">
                                {dep}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs">
                        {file.file_type}
                      </Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCopyFile(file);
                        }}
                      >
                        {copiedFile === file.filename ? (
                          <Check className="h-4 w-4 text-green-500" />
                        ) : (
                          <Copy className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {activeTab === 'preview' && (
            <div className="mt-4 space-y-4">
              {selectedFile ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={cn(
                        'p-2 rounded-full text-white',
                        getFileTypeColor(selectedFile.file_type)
                      )}>
                        {getFileTypeIcon(selectedFile.file_type)}
                      </div>
                      <div>
                        <h3 className="font-medium">{selectedFile.filename}</h3>
                        <p className="text-sm text-gray-600">
                          {selectedFile.description || 'Dana code file'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {isEditing ? (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={handleEditSave}
                            className="gap-2"
                          >
                            <Save className="h-4 w-4" />
                            Save
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={handleEditCancel}
                            className="gap-2"
                          >
                            <X className="h-4 w-4" />
                            Cancel
                          </Button>
                        </>
                      ) : (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={handleEditStart}
                            className="gap-2"
                          >
                            <Edit className="h-4 w-4" />
                            Edit
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleCopyFile(selectedFile)}
                          >
                            {copiedFile === selectedFile.filename ? (
                              <Check className="h-4 w-4 text-green-500" />
                            ) : (
                              <Copy className="h-4 w-4" />
                            )}
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                  
                  <div className="h-96 w-full rounded-md border">
                    {isEditing ? (
                      <AgentEditor
                        value={editedContent}
                        onChange={setEditedContent}
                        placeholder="Edit your Dana code here..."
                        className="h-full"
                        enableAutoValidation={true}
                        autoValidationDelay={1000}
                      />
                    ) : (
                      <div className="h-full overflow-auto">
                        <pre className="p-4 text-sm font-mono">
                          <code>{selectedFile.content}</code>
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Select a file to preview its contents</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MultiFileViewer;