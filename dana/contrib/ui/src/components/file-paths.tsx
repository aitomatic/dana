import { toast } from 'sonner';
import { Folder, Page } from 'iconoir-react';
import { apiService, type MultiFileProject } from '@/lib/api';

interface FilePathsProps {
  multiFileProject: MultiFileProject | null;
  className?: string;
}

export function FilePaths({ multiFileProject, className = '' }: FilePathsProps) {
  const handleFileClick = async (fileName: string) => {
    try {
      // Construct file path based on auto-storage pattern
      // This matches the backend auto-storage folder structure
      const sanitizedName = (multiFileProject?.name || 'Generated_Agent')
        .toLowerCase()
        .replace(/[^a-zA-Z0-9_\-]/g, '_');
      
      // Since we don't have the exact unique ID, we'll use a pattern that the backend can match
      // The backend will need to handle partial path matching for the generated folders
      const filePath = `generated/generated_${sanitizedName}*/${fileName}`;
      
      const result = await apiService.openFileLocation(filePath);
      if (result.success) {
        toast.success('Opened file location!');
      } else {
        toast.error('Failed to open file location');
      }
    } catch (error) {
      console.error('Error opening file:', error);
      toast.error('Failed to open file location');
    }
  };

  const getFileType = (fileName: string) => {
    if (fileName.endsWith('.na')) return 'dana';
    if (fileName.endsWith('.json')) return 'metadata';
    return 'other';
  };

  if (!multiFileProject || !multiFileProject.files || multiFileProject.files.length === 0) {
    return null;
  }

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
        <Folder className="w-4 h-4" />
        Generated Files ({multiFileProject.files.length})
      </div>
      <div className="space-y-1">
        {multiFileProject.files.map((file, index) => {
          const fileType = getFileType(file.filename);
          
          return (
            <button
              key={index}
              onClick={() => handleFileClick(file.filename)}
              className="flex items-center gap-2 px-3 py-2 w-full text-left rounded-md bg-gray-50 hover:bg-gray-100 transition-colors group"
              title={`Click to open: ${file.filename}`}
            >
              <Page className="w-4 h-4 text-gray-500 group-hover:text-blue-600" />
              <div className="flex-1 min-w-0">
                <div className="text-sm text-gray-700 group-hover:text-blue-700 font-mono">
                  {file.filename}
                </div>
                {file.description && (
                  <div className="text-xs text-gray-400 truncate">
                    {file.description}
                  </div>
                )}
              </div>
              <span className="text-xs text-gray-400 ml-auto">
                {fileType}
              </span>
            </button>
          );
        })}
      </div>
      <div className="text-xs text-gray-500">
        💡 Click any filename to open its location in Finder/Explorer
      </div>
    </div>
  );
}