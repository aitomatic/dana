import React, { useState } from 'react';
import { AgentEditor } from '@/components/agent-editor';
import { IconFileText } from '@tabler/icons-react';

// Mock file data
const mockFiles = [
  {
    id: '1',
    name: 'main.na',
    content: '# main agent file\nquery = "What is the weather today?"\nresponse = "I\'ll check the weather for you."',
  },
  {
    id: '2',
    name: 'utils.na',
    content: '# utility functions\n',
  },
  {
    id: '3',
    name: 'config.na',
    content: '# agent config\n',
  },
];

const CodeTab: React.FC = () => {
  const [selectedFileId, setSelectedFileId] = useState(mockFiles[0].id);
  const [files, setFiles] = useState(mockFiles);

  const selectedFile = files.find((f) => f.id === selectedFileId) || files[0];

  const handleFileSelect = (id: string) => {
    setSelectedFileId(id);
  };

  const handleEditorChange = (value: string) => {
    setFiles((prev) =>
      prev.map((file) =>
        file.id === selectedFileId ? { ...file, content: value } : file
      )
    );
  };

  return (
    <div className="flex h-full bg-white rounded-lg shadow overflow-hidden bg-white">
      {/* Sidebar */}
      <div className="w-56 border-r bg-white flex flex-col">
        <div className="flex items-center justify-between px-4 py-3 border-b">
          <span className="font-semibold text-gray-800 text-sm">Files</span>

        </div>
        <div className="flex-1 overflow-y-auto">
          {files.map((file) => (
            <button
              key={file.id}
              className={`w-full flex items-center px-4 py-2 text-left text-sm border-l-4 transition-colors ${file.id === selectedFileId
                ? 'bg-white border-blue-500 text-blue-700 font-semibold'
                : 'border-transparent text-gray-700 hover:bg-gray-100'
                }`}
              onClick={() => handleFileSelect(file.id)}
            >
              <IconFileText className="w-4 h-4 mr-2" />
              {file.name}
            </button>
          ))}
        </div>
      </div>
      {/* Main Content */}
      <div className="flex-1 min-w-0 flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b bg-white">
          <span className="font-semibold text-gray-900 text-lg">{selectedFile.name}</span>
        </div>
        <div className="flex-1 min-h-0">
          <AgentEditor
            value={selectedFile.content}
            onChange={handleEditorChange}
            placeholder={`Edit ${selectedFile.name}...`}
            enableValidation={selectedFile.name === 'main.na'}
            enableAutoValidation={selectedFile.name === 'main.na'}
            className="h-full"
          />
        </div>
      </div>
    </div>
  );
};

export default CodeTab; 