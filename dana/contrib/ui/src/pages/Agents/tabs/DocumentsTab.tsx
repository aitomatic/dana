import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { LibraryTable } from '@/components/library';
import { ConfirmDialog } from '@/components/library/confirm-dialog';
import type { LibraryItem } from '@/types/library';
import type { DocumentRead } from '@/types/document';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Search, SystemRestart, Upload, EmptyPage } from 'iconoir-react';
import { apiService } from '@/lib/api';
import { useDocumentOperations } from '@/hooks/use-api';
import { toast } from 'sonner';
import { PdfViewer } from '@/components/library/pdf-viewer';

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
  const [uploadingFiles, setUploadingFiles] = useState<string[]>([]);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [selectedItem, setSelectedItem] = useState<LibraryItem | null>(null);
  const [pdfViewerOpen, setPdfViewerOpen] = useState(false);
  const [pdfFileUrl, setPdfFileUrl] = useState<string | null>(null);
  const [pdfFileName, setPdfFileName] = useState<string | undefined>(undefined);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // API hooks
  const { deleteDocument, isDeleting } = useDocumentOperations();

  const handleDragDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (!e.dataTransfer.files || e.dataTransfer.files.length === 0 || !agent_id) return;

    const files = Array.from(e.dataTransfer.files);
    const fileNames = files.map((f) => f.name);

    setUploadingFiles(fileNames);

    try {
      for (const file of files) {
        await apiService.uploadAgentDocument(agent_id, file);
        setUploadingFiles((prev) => prev.filter((name) => name !== file.name));
      }
      await loadDocuments();
    } catch (error) {
      console.error('Failed to upload files:', error);
      setUploadingFiles([]);
    }
  };

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
    const fileNames = fileList.map((f) => f.name);

    // Set uploading state for these files
    setUploadingFiles(fileNames);

    try {
      for (const file of fileList) {
        await apiService.uploadAgentDocument(agent_id, file);
        // Remove this file from uploading list as it completes
        setUploadingFiles((prev) => prev.filter((name) => name !== file.name));
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

  const handleViewItem = (item: LibraryItem) => {
    if (item.type === 'file' && (item as any).extension?.toLowerCase() === 'pdf') {
      // Use the API download endpoint for the PDF viewer
      const documentId = parseInt(item.id);
      const fileUrl = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api'}/documents/${documentId}/download`;
      setPdfFileUrl(fileUrl);
      setPdfFileName(item.name);
      setPdfViewerOpen(true);
    } else {
      // For non-PDF files, could implement other viewing logic
      console.log('View document:', item);
      // Could show a preview modal or download the file
    }
  };

  const handleDeleteItem = async (item: LibraryItem) => {
    setSelectedItem(item);
    setShowDeleteConfirm(true);
  };

  const handleConfirmDelete = async () => {
    if (!selectedItem) return;

    try {
      const documentId = parseInt(selectedItem.id);
      await deleteDocument(documentId);
      toast.success('Document deleted successfully');
      await loadDocuments(); // Refresh the documents list
    } catch (error) {
      console.error('Failed to delete document:', error);
      toast.error('Failed to delete document');
    } finally {
      setShowDeleteConfirm(false);
      setSelectedItem(null);
    }
  };

  // Empty state component
  const EmptyState = () => {
    const [isDragOver, setIsDragOver] = useState(false);

    const handleDragOver = (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragOver(true);
    };

    const handleDragLeave = (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragOver(false);
    };

    const handleDrop = (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragOver(false);
      handleDragDrop(e);
    };

    return (
      <div
        className={`flex flex-col items-center justify-center h-[100%] border-2 border-dashed rounded-lg transition-colors ${
          isDragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div
          className={`flex flex-col items-center justify-center mb-4 w-22 h-22 rounded-full ${
            isDragOver ? 'bg-white' : 'bg-gray-100'
          }`}
        >
          <EmptyPage className="w-10 h-10 text-gray-400" />
        </div>

        <div className="space-y-2 text-center">
          <h3 className="text-lg font-semibold text-gray-700">No documents yet</h3>
          <p className="text-sm text-gray-500">Drag and drop files here to upload</p>
        </div>
        <Button
          onClick={handleAddFileClick}
          className="mt-4 font-semibold cursor-pointer"
          disabled={uploadingFiles.length > 0}
        >
          {uploadingFiles.length > 0 ? (
            <>
              <SystemRestart className="mr-2 w-4 h-4 animate-spin" />
              Uploading...
            </>
          ) : (
            <>
              <Upload className="mr-2 w-4 h-4" />
              Browse Files
            </>
          )}
        </Button>
      </div>
    );
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
          {/* <Button onClick={handleAddFileClick} disabled={uploadingFiles.length > 0}>
            {uploadingFiles.length > 0 ? (
              <IconLoader2 className="animate-spin size-4" />
            ) : (
              <IconPlus className="size-4" />
            )}
            {uploadingFiles.length > 0 ? 'Uploading...' : 'Add file'}
          </Button> */}
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 w-4 h-4 text-gray-400 transform -translate-y-1/2" />
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
        <div className="p-4 mb-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-center space-x-3">
            <Upload className="w-5 h-5 text-blue-600" />
            <div className="flex-1">
              <div className="font-medium text-blue-900">
                Uploading {uploadingFiles.length} file{uploadingFiles.length > 1 ? 's' : ''}...
              </div>
              <div className="mt-1 text-sm text-blue-700">
                {uploadingFiles.map((fileName, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <SystemRestart className="w-3 h-3 animate-spin" />
                    <span>{fileName}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="flex-1">
        {filteredData.length === 0 && !loading ? (
          <EmptyState />
        ) : (
          <LibraryTable
            data={filteredData}
            loading={loading}
            mode="library"
            onViewItem={handleViewItem}
            onDeleteItem={handleDeleteItem}
          />
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        onClose={() => {
          setShowDeleteConfirm(false);
          setSelectedItem(null);
        }}
        onConfirm={handleConfirmDelete}
        title="Delete Document"
        description={`Are you sure you want to delete "${selectedItem?.name}"? This action cannot be undone.`}
        confirmText={isDeleting ? 'Deleting...' : 'Delete'}
        cancelText="Cancel"
        variant="destructive"
      />

      {/* PDF Viewer */}
      <PdfViewer
        open={pdfViewerOpen}
        onClose={() => setPdfViewerOpen(false)}
        fileUrl={pdfFileUrl || ''}
        fileName={pdfFileName}
      />
    </div>
  );
};

export default DocumentsTab;
