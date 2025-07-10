import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  IconSearch,
  IconFilter,
  IconUpload,
  IconFolderPlus,
  IconRefresh,
  IconArrowLeft,
} from '@tabler/icons-react';
import type { LibraryItem, FolderItem } from '@/types/library';
import { useTopicOperations, useDocumentOperations } from '@/hooks/use-api';
import { CreateFolderDialog } from '@/components/library/create-folder-dialog';
import { EditTopicDialog } from '@/components/library/edit-topic-dialog';
import { EditDocumentDialog } from '@/components/library/edit-document-dialog';
import { ConfirmDialog } from '@/components/library/confirm-dialog';

import { useFolderNavigation } from '@/hooks/use-folder-navigation';
import { toast } from 'sonner';
import { convertTopicToFolderItem, convertDocumentToFileItem } from '@/components/library';
import { LibraryTable } from '@/components/library';
import { PdfViewer } from '@/components/library/pdf-viewer';

export default function LibraryPage() {
  // API hooks
  const {
    fetchTopics,
    createTopic,
    updateTopic,
    deleteTopic,
    topics,
    isLoading: topicsLoading,
    isCreating: isCreatingTopic,
    isUpdating: isUpdatingTopic,
    error: topicsError,
    clearError: clearTopicsError,
  } = useTopicOperations();

  const {
    fetchDocuments,
    uploadDocument,
    updateDocument,
    deleteDocument,
    downloadDocument,
    documents,
    isLoading: documentsLoading,
    isUploading,
    isUpdating: isUpdatingDocument,
    error: documentsError,
    clearError: clearDocumentsError,
  } = useDocumentOperations();

  // Folder navigation
  const { folderState, navigateToFolder, navigateToRoot, getItemsInCurrentFolder } =
    useFolderNavigation();

  // Local state
  const [showCreateFolder, setShowCreateFolder] = useState(false);
  const [showEditTopic, setShowEditTopic] = useState(false);
  const [showEditDocument, setShowEditDocument] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [selectedItem, setSelectedItem] = useState<LibraryItem | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<'all' | 'files' | 'folders'>('all');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [pdfViewerOpen, setPdfViewerOpen] = useState(false);
  const [pdfFileUrl, setPdfFileUrl] = useState<string | null>(null);
  const [pdfFileName, setPdfFileName] = useState<string | undefined>(undefined);

  // Fetch data on component mount
  useEffect(() => {
    fetchTopics();
    fetchDocuments();
  }, [fetchTopics, fetchDocuments]);

  // Convert API data to LibraryItem format
  const libraryItems: LibraryItem[] = [
    ...(topics?.map(convertTopicToFolderItem) || []),
    ...(documents?.map(convertDocumentToFileItem) || []),
  ];
  console.log('📚 Library items:', {
    topics: topics?.length || 0,
    documents: documents?.length || 0,
    totalItems: libraryItems.length,
    documentsWithTopics: documents?.filter((d) => d.topic_id).length || 0,
  });

  // Calculate item counts for folders
  const itemsWithCounts = libraryItems.map((item) => {
    if (item.type === 'folder') {
      const topicId = item.topicId;
      const itemCount = documents?.filter((doc) => doc.topic_id === topicId).length || 0;
      return { ...item, itemCount };
    }
    return item;
  });

  // Get items in current folder
  const currentFolderItems = getItemsInCurrentFolder(itemsWithCounts);
  console.log('📋 Current folder items:', currentFolderItems.length, 'items');

  // Filter items based on search and type
  const filteredItems = currentFolderItems.filter((item) => {
    const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase());

    // When inside a folder, only show files (folders are hidden)
    let matchesType = true;
    if (folderState.isInFolder) {
      matchesType = item.type === 'file';
    } else {
      matchesType =
        typeFilter === 'all' ||
        (typeFilter === 'folders' && item.type === 'folder') ||
        (typeFilter === 'files' && item.type === 'file');
    }

    return matchesSearch && matchesType;
  });

  const handleViewItem = (item: LibraryItem) => {
    if (item.type === 'folder') {
      // Navigate to folder
      navigateToFolder(item as FolderItem);
    } else if (item.type === 'file' && (item as any).extension?.toLowerCase() === 'pdf') {
      setPdfFileUrl(item.path);
      setPdfFileName(item.name);
      setPdfViewerOpen(true);
    } else {
      // Open document preview (non-PDF)
      console.log('View document:', item);
    }
  };

  const handleEditItem = (item: LibraryItem) => {
    setSelectedItem(item);
    if (item.type === 'folder') {
      setShowEditTopic(true);
    } else {
      setShowEditDocument(true);
    }
  };

  const handleEditTopic = async (topicId: number, topic: { name: string; description: string }) => {
    try {
      await updateTopic(topicId, topic);
      toast.success('Topic updated successfully');
    } catch {
      toast.error('Failed to update topic');
    }
  };

  const handleEditDocument = async (
    documentId: number,
    document: { original_filename?: string; topic_id?: number },
  ) => {
    try {
      await updateDocument(documentId, document);
      toast.success('Document updated successfully');
    } catch {
      toast.error('Failed to update document');
    }
  };

  const handleDeleteItem = async (item: LibraryItem) => {
    setSelectedItem(item);
    setShowDeleteConfirm(true);
  };

  const handleConfirmDelete = async () => {
    if (!selectedItem) return;

    try {
      if (selectedItem.type === 'folder') {
        const topicId = parseInt(selectedItem.id.replace('topic-', ''));
        await deleteTopic(topicId);
        toast.success('Topic deleted successfully');
      } else {
        const documentId = parseInt(selectedItem.id.replace('doc-', ''));
        await deleteDocument(documentId);
        toast.success('Document deleted successfully');
      }
    } catch {
      toast.error('Failed to delete item');
    } finally {
      setShowDeleteConfirm(false);
      setSelectedItem(null);
    }
  };

  const handleDownloadDocument = async (item: LibraryItem) => {
    if (item.type === 'file') {
      try {
        const documentId = parseInt(item.id.replace('doc-', ''));
        await downloadDocument(documentId);
        toast.success('Document downloaded successfully');
      } catch {
        toast.error('Failed to download document');
      }
    }
  };

  const handleCreateFolder = async (name: string) => {
    await createTopic({ name, description: `Topic: ${name}` });
    setShowCreateFolder(false);
  };

  const handleFilesUploaded = async (files: File[]) => {
    for (const file of files) {
      await uploadDocument({
        file,
        title: file.name,
        description: `Uploaded: ${file.name}`,
        topic_id: folderState.currentFolderId
          ? parseInt(folderState.currentFolderId.replace('topic-', ''))
          : undefined,
      });
    }
  };

  const handleSearchChange = (value: string) => {
    setSearchTerm(value);
  };

  const handleTypeFilterChange = (type: 'all' | 'files' | 'folders') => {
    setTypeFilter(type);
  };

  const handleRefresh = () => {
    fetchTopics();
    fetchDocuments();
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      const fileArray = Array.from(files);
      await handleFilesUploaded(fileArray);
      // Reset the input
      event.target.value = '';
    }
  };

  const isLoading = topicsLoading || documentsLoading;
  const error = topicsError || documentsError;

  return (
    <div className="flex flex-col p-6 space-y-6 h-full">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Library</h1>
          <p className="text-gray-600">Manage your topics and documents</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={handleRefresh} disabled={isLoading}>
            <IconRefresh className="mr-2 w-4 h-4" />
            Refresh
          </Button>
          <Button
            variant="outline"
            onClick={() => setShowCreateFolder(true)}
            disabled={isCreatingTopic}
          >
            <IconFolderPlus className="mr-2 w-4 h-4" />
            New Topic
          </Button>
          <Button onClick={handleUploadClick} disabled={isUploading}>
            <IconUpload className="mr-2 w-4 h-4" />
            Add Documents
          </Button>
        </div>
      </div>

      {/* Breadcrumb Navigation */}
      {folderState.isInFolder && (
        <div className="flex items-center space-x-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={navigateToRoot}
            className="text-gray-600 hover:text-gray-900"
          >
            <IconArrowLeft className="w-4 h-4 mr-1" />
            Back to Library
          </Button>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">{error}</p>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              clearTopicsError();
              clearDocumentsError();
            }}
            className="mt-2"
          >
            Dismiss
          </Button>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-sm">
          <IconSearch className="absolute left-3 top-1/2 w-4 h-4 text-gray-400 transform -translate-y-1/2" />
          <Input
            placeholder="Search topics and documents..."
            value={searchTerm}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="pl-10"
          />
        </div>

        {!folderState.isInFolder && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                <IconFilter className="mr-2 w-4 h-4" />
                {typeFilter === 'all' ? 'All' : typeFilter === 'files' ? 'Documents' : 'Topics'}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => handleTypeFilterChange('all')}>
                All Items
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleTypeFilterChange('files')}>
                Documents Only
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleTypeFilterChange('folders')}>
                Topics Only
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>

      {/* Data Table */}
      <div className="flex-1">
        <LibraryTable
          data={filteredItems}
          loading={isLoading}
          mode="library"
          onRowClick={handleViewItem}
          onViewItem={handleViewItem}
          onEditItem={handleEditItem}
          onDeleteItem={handleDeleteItem}
          onDownloadItem={handleDownloadDocument}
          allLibraryItems={itemsWithCounts}
        />
      </div>

      {/* Hidden file input for upload */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        onChange={handleFileChange}
        style={{ display: 'none' }}
        accept="*/*"
      />

      {/* Dialogs */}
      <CreateFolderDialog
        isOpen={showCreateFolder}
        onClose={() => setShowCreateFolder(false)}
        onCreateFolder={handleCreateFolder}
        currentPath={folderState.currentPath}
      />

      {/* Edit Topic Dialog */}
      <EditTopicDialog
        topic={
          selectedItem?.type === 'folder'
            ? topics.find((t) => t.id === parseInt(selectedItem.id.replace('topic-', ''))) || null
            : null
        }
        isOpen={showEditTopic}
        onClose={() => {
          setShowEditTopic(false);
          setSelectedItem(null);
        }}
        onSave={handleEditTopic}
        isLoading={isUpdatingTopic}
      />

      {/* Edit Document Dialog */}
      <EditDocumentDialog
        document={
          selectedItem?.type === 'file'
            ? documents.find((d) => d.id === parseInt(selectedItem.id.replace('doc-', ''))) || null
            : null
        }
        topics={topics}
        isOpen={showEditDocument}
        onClose={() => {
          setShowEditDocument(false);
          setSelectedItem(null);
        }}
        onSave={handleEditDocument}
        isLoading={isUpdatingDocument}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        onClose={() => {
          setShowDeleteConfirm(false);
          setSelectedItem(null);
        }}
        onConfirm={handleConfirmDelete}
        title={`Delete ${selectedItem?.type === 'folder' ? 'Topic' : 'Document'}`}
        description={`Are you sure you want to delete "${selectedItem?.name}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="destructive"
      />
      <PdfViewer
        open={pdfViewerOpen}
        onClose={() => setPdfViewerOpen(false)}
        fileUrl={pdfFileUrl || ''}
        fileName={pdfFileName}
      />
    </div>
  );
}
