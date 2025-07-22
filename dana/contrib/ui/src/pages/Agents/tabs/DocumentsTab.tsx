import React, { useState } from 'react';
import { LibraryTable } from '@/components/library';
import type { LibraryItem } from '@/types/library';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { IconSearch, IconRefresh } from '@tabler/icons-react';

// Mock data for demonstration
const mockDocuments: LibraryItem[] = [
  {
    id: 'doc-1',
    name: 'SOX Compliance Audit Report',
    type: 'file',
    size: 2.2 * 1024 * 1024,
    extension: 'pdf',
    lastModified: new Date(),
    path: '/documents/1',
    topicId: 1,
  },
  {
    id: 'doc-2',
    name: 'Internal Control Assessment Checklist',
    type: 'file',
    size: 40.1 * 1024 * 1024,
    extension: 'docx',
    lastModified: new Date(Date.now() - 1000 * 60 * 60 * 2),
    path: '/documents/2',
    topicId: 2,
  },
  {
    id: 'doc-3',
    name: 'SOX Compliance Audit Report',
    type: 'file',
    size: 2.2 * 1024 * 1024,
    extension: 'pdf',
    lastModified: new Date(Date.now() - 1000 * 60 * 60 * 4),
    path: '/documents/3',
    topicId: 3,
  },
  // Add more mock items as needed
];

const DocumentsTab: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<LibraryItem[]>(mockDocuments);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  const handleRefresh = () => {
    setLoading(true);
    // Simulate refresh delay
    setTimeout(() => {
      setData([...mockDocuments]);
      setLoading(false);
    }, 500);
  };

  const filteredData = data.filter((item) =>
    item.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="flex flex-col p-6 space-y-6 h-full">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
          <p className="text-gray-600">Browse and manage your documents</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={handleRefresh} disabled={loading}>
            <IconRefresh className="mr-2 w-4 h-4" />
            Refresh
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
        <LibraryTable
          data={filteredData}
          loading={loading}
          mode="library"
        />
      </div>
    </div>
  );
};

export default DocumentsTab; 