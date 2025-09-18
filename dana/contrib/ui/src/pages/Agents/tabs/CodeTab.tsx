import React, { useState, useEffect } from 'react';
import { AgentEditor } from '@/components/agent-editor';
import { IconFileText, IconRefresh, IconCheck } from '@tabler/icons-react';
import { apiService } from '@/lib/api';
import { useAgentStore } from '@/stores/agent-store';

interface AgentFile {
  id: string;
  name: string;
  path: string;
  content: string;
  type: 'dana' | 'document' | 'other';
  size: number;
  modified: number;
}

const CodeTab: React.FC = () => {
  const { selectedAgent } = useAgentStore();
  const [selectedFileId, setSelectedFileId] = useState<string>('');
  const [files, setFiles] = useState<AgentFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showSaveSuccess, setShowSaveSuccess] = useState(false);
  const [saveSuccessTimeout, setSaveSuccessTimeout] = useState<number | null>(null);
  const [showBadgeTimeout, setShowBadgeTimeout] = useState<number | null>(null);

  const selectedFile = files.find((f) => f.id === selectedFileId) || files[0];

  // Load agent files on component mount
  useEffect(() => {
    loadAgentFiles();
  }, [selectedAgent]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (saveSuccessTimeout) {
        clearTimeout(saveSuccessTimeout);
      }
      if (showBadgeTimeout) {
        clearTimeout(showBadgeTimeout);
      }
    };
  }, [saveSuccessTimeout, showBadgeTimeout]);

  const loadAgentFiles = async () => {
    if (!selectedAgent?.id) return;

    setLoading(true);
    setError(null);

    try {
      const response = await apiService.getAgentFiles(selectedAgent.id);

      // Filter for .na files only and load their content
      const naFiles = response.files.filter((file) => file.type === 'dana');

      const filesWithContent = await Promise.all(
        naFiles.map(async (file, index) => {
          try {
            const contentResponse = await apiService.getAgentFileContent(
              selectedAgent.id,
              file.path,
            );
            return {
              id: `${index}`, // Simple ID based on index
              name: file.name,
              path: file.path,
              content: contentResponse.content,
              type: file.type,
              size: file.size,
              modified: file.modified,
            } as AgentFile;
          } catch (err) {
            console.error(`Failed to load content for ${file.name}:`, err);
            return {
              id: `${index}`,
              name: file.name,
              path: file.path,
              content: `// Error loading file: ${err}`,
              type: file.type,
              size: file.size,
              modified: file.modified,
            } as AgentFile;
          }
        }),
      );

      setFiles(filesWithContent);

      // Auto-select the first file
      if (filesWithContent.length > 0) {
        setSelectedFileId(filesWithContent[0].id);
      }
    } catch (err) {
      console.error('Failed to load agent files:', err);
      setError(err instanceof Error ? err.message : 'Failed to load files');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (id: string) => {
    setSelectedFileId(id);
  };

  const handleEditorChange = async (value: string) => {
    const file = files.find((f) => f.id === selectedFileId);
    if (!file || !selectedAgent?.id) return;

    // Update local state immediately for responsive UI
    setFiles((prev) => prev.map((f) => (f.id === selectedFileId ? { ...f, content: value } : f)));

    // Save to backend
    try {
      await apiService.updateAgentFileContent(selectedAgent.id, file.path, value);
      
      // Clear any existing timeouts
      if (saveSuccessTimeout) {
        clearTimeout(saveSuccessTimeout);
      }
      if (showBadgeTimeout) {
        clearTimeout(showBadgeTimeout);
      }
      
      // Show success badge after 500ms delay
      const showTimeout = setTimeout(() => {
        setShowSaveSuccess(true);
        
        // Auto-hide the badge after 4 seconds
        const hideTimeout = setTimeout(() => {
          setShowSaveSuccess(false);
        }, 4000);
        
        setSaveSuccessTimeout(hideTimeout);
      }, 500);
      
      setShowBadgeTimeout(showTimeout);
    } catch (err) {
      console.error('Failed to save file:', err);
      // Optionally show an error toast
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-full bg-white rounded-lg shadow">
        <div className="text-center">
          <IconRefresh className="mx-auto mb-4 w-8 h-8 text-blue-500 animate-spin" />
          <p className="text-gray-600">Loading agent files...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex justify-center items-center h-full bg-white rounded-lg shadow">
        <div className="text-center">
          <p className="mb-4 text-red-600">Error: {error}</p>
          <button
            onClick={loadAgentFiles}
            className="flex gap-2 items-center px-4 py-2 mx-auto text-white bg-blue-500 rounded hover:bg-blue-600"
          >
            <IconRefresh className="w-4 h-4" />
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (files.length === 0) {
    return (
      <div className="flex justify-center items-center h-full bg-white rounded-lg shadow">
        <div className="text-center">
          <IconFileText className="mx-auto mb-4 w-12 h-12 text-gray-400" />
          <p className="mb-2 text-gray-600">No Dana files found</p>
          <p className="text-sm text-gray-500">
            Dana files (.na) will appear here once the agent is created
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex overflow-hidden h-full bg-white rounded-lg shadow">
      {/* Sidebar */}
      <div className="flex flex-col w-56 bg-white border-r">
        <div className="flex justify-between items-center px-4 py-2 h-12 border-b">
          <span className="text-sm font-semibold text-gray-800">Dana Files</span>
          <button
            onClick={loadAgentFiles}
            className="p-1 text-gray-500 rounded hover:text-gray-700"
            title="Refresh files"
          >
            <IconRefresh className="w-4 h-4" />
          </button>
        </div>
        <div className="overflow-y-auto flex-1 custom-scrollbar">
          {files.map((file) => (
            <button
              key={file.id}
              className={`w-full flex items-center px-4 py-2 text-left text-sm transition-colors ${
                file.id === selectedFileId
                  ? 'bg-gray-100 text-gray-700 font-semibold border-none'
                  : 'border-transparent text-gray-600 hover:bg-gray-100'
              }`}
              onClick={() => handleFileSelect(file.id)}
            >
              <IconFileText className="mr-2 w-4 h-4" />
              {file.name}
            </button>
          ))}
        </div>
      </div>
      {/* Main Content */}
      <div className="flex flex-col flex-1 min-w-0">
        <div className="flex justify-between items-center px-6 py-2 h-12 bg-white border-b">
          <span className="text-md font-medium text-gray-900">
            {selectedFile?.name || 'No file selected'}
          </span>
          {showSaveSuccess && (
            <div className="flex items-center gap-1 px-2 py-1 text-sm font-medium text-green-700 bg-green-50 border border-green-200 rounded-full animate-in fade-in-0 slide-in-from-right-2 duration-200">
              <IconCheck className="w-3 h-3" />
              Changes saved
            </div>
          )}
        </div>
        <div className="flex-1 min-h-0">
          {selectedFile ? (
            <AgentEditor
              value={selectedFile.content}
              onChange={handleEditorChange}
              placeholder={`Edit ${selectedFile.name}...`}
              enableValidation={selectedFile.name === 'main.na'}
              enableAutoValidation={selectedFile.name === 'main.na'}
              className="h-full text-xs"
            />
          ) : (
            <div className="flex justify-center items-center h-full text-gray-500">
              Select a file to start editing
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CodeTab;
