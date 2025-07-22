import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { LibraryTable } from '@/components/library';
import type { LibraryItem } from '@/types/library';
import type { DocumentRead } from '@/types/document';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { IconSearch, IconPlus } from '@tabler/icons-react';
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
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const handleRefresh = () => {
    loadDocuments();
  };

  const handleAddFileClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0 || !agent_id) return;
    try {
      for (const file of Array.from(files)) {
        await apiService.uploadAgentDocument(agent_id, file);
      }
      loadDocuments();
    } catch (error) {
      console.error('Failed to upload file:', error);
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = '';
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
    <div className="flex flex-col gap-4 p-6 h-full">
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
          <Button variant="outline" onClick={handleRefresh} disabled={loading}>
            {loading ? 'Loading...' : 'Refresh'}
          </Button>
          <Button onClick={handleAddFileClick}>
            <IconPlus className="mr-2 w-4 h-4" />
            Add file
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
      <div className="flex-1">
        <LibraryTable data={filteredData} loading={loading} mode="library" />
      </div>
    </div>
  );
};

export default DocumentsTab;
