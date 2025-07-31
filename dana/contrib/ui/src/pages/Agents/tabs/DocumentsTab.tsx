import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { LibraryTable } from '@/components/library';
import type { LibraryItem } from '@/types/library';
import type { DocumentRead } from '@/types/document';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { IconSearch, IconPlus, IconLoader2, IconUpload } from '@tabler/icons-react';
import { apiService } from '@/lib/api';

// Convert DocumentRead to LibraryItem format
const convertDocumentToLibraryItem = (doc: DocumentRead): LibraryItem => {
  const extension = doc.original_filename.split('.').pop() || '';
  return {
    id: doc.id.toString(),
    name: doc.original_filename,
    type: 'file',
    size: doc.file_size,
    extension,
    lastModified: new Date(doc.updated_at),
    path: `/documents/${doc.id}`,
    topicId: doc.topic_id,
  };
};

const DocumentsTab: React.FC = () => {
  const { agent_id } = useParams<{ agent_id: string }>();
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<LibraryItem[]>([]);
  const [uploadingFiles, setUploadingFiles] = useState<string[]>([]); // Track which files are uploading
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Note: Using local uploadingFiles state instead of global document store for per-file tracking

  // Load agent-specific documents
  useEffect(() => {
    if (agent_id) {
      loadDocuments();
    }
  }, [agent_id]);

  const loadDocuments = async () => {
    if (!agent_id) return;

    setLoading(true);
    try {
      // Note: The API getDocuments doesn't currently support agent_id filtering
      // So we fetch all documents and filter client-side for now
      // TODO: Update API to support agent_id filtering in DocumentFilters
      const documents = await apiService.getDocuments();

      // Filter documents by agent_id (client-side filtering for now)
      const agentDocuments = documents.filter((doc) => doc.agent_id?.toString() === agent_id);

      const libraryItems = agentDocuments.map(convertDocumentToLibraryItem);
      setData(libraryItems);
    } catch (error) {
      console.error('Failed to load agent documents:', error);
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  const handleAddFileClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0 || !agent_id) return;
    
    const fileList = Array.from(files);
    const fileNames = fileList.map(f => f.name);
    
    // Set uploading state for these files
    setUploadingFiles(fileNames);
    
    try {
      for (const file of fileList) {
        await apiService.uploadAgentDocument(agent_id, file);
        // Remove this file from uploading list as it completes
        setUploadingFiles(prev => prev.filter(name => name !== file.name));
        // Reload documents immediately after each file upload for better UX
        await loadDocuments();
      }
    } catch (error) {
      console.error('Failed to upload file:', error);
      // Clear uploading state on error
      setUploadingFiles([]);
      // Still reload documents to show any files that were successfully uploaded before the error
      await loadDocuments();
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = '';
      // Ensure all files are cleared from uploading state
      setUploadingFiles([]);
    }
  };

  const filteredData = data.filter((item) =>
    item.name.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  if (!agent_id) {
    return (
      <div className="flex justify-center items-center h-full">
        <div className="text-gray-500">No agent selected</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 px-6 pb-6 h-full bg-white rounded-lg">
      <input
        type="file"
        ref={fileInputRef}
        style={{ display: 'none' }}
        multiple
        onChange={handleFileInputChange}
      />
      <div className="flex justify-between items-center">
        <div>
          <div className="text-lg font-semibold text-gray-700">Documents</div>
        </div>
        <div className="flex items-center space-x-2">
          <Button onClick={handleAddFileClick} disabled={uploadingFiles.length > 0}>
            {uploadingFiles.length > 0 ? (
              <IconLoader2 className="mr-2 w-4 h-4 animate-spin" />
            ) : (
              <IconPlus className="mr-2 w-4 h-4" />
            )}
            {uploadingFiles.length > 0 ? 'Uploading...' : 'Add file'}
          </Button>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-sm">
          <IconSearch className="absolute left-3 top-1/2 w-4 h-4 text-gray-400 transform -translate-y-1/2" />
          <Input
            placeholder="Search documents..."
            value={searchTerm}
            onChange={handleSearchChange}
            className="pl-10"
          />
        </div>
      </div>
      {/* Upload Progress Indicator */}
      {uploadingFiles.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <div className="flex items-center space-x-3">
            <IconUpload className="w-5 h-5 text-blue-600" />
            <div className="flex-1">
              <div className="font-medium text-blue-900">
                Uploading {uploadingFiles.length} file{uploadingFiles.length > 1 ? 's' : ''}...
              </div>
              <div className="text-sm text-blue-700 mt-1">
                {uploadingFiles.map((fileName, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <IconLoader2 className="w-3 h-3 animate-spin" />
                    <span>{fileName}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
      
      <div className="flex-1">
        <LibraryTable data={filteredData} loading={loading} mode="library" />
      </div>
    </div>
  );
};

export default DocumentsTab;
