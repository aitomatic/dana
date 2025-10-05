/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { LibraryTable } from '@/components/library';
import { ConfirmDialog } from '@/components/library/confirm-dialog';
import { LibraryFileSelectionModal } from '@/components/library/library-file-selection-modal';
import type { LibraryItem } from '@/types/library';
import type { DocumentRead } from '@/types/document';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Search, SystemRestart, EmptyPage, Upload, MultiplePagesPlus } from 'iconoir-react';
import { apiService } from '@/lib/api';
import { useDocumentStore } from '@/stores/document-store';
import { useAgentStore } from '@/stores/agent-store';
import { toast } from 'sonner';
import { PdfViewer } from '@/components/library/pdf-viewer';
import { useDanaAnalytics } from '@/hooks/useAnalytics';

/**
 * DocumentsTab Component
 *
 * This component manages documents associated with a specific agent.
 * It distinguishes between two types of documents:
 * 1. Documents added from the library (have topic_id) - can only be disassociated, not deleted
 * 2. Documents uploaded directly to the agent (no topic_id) - can be completely deleted
 *
 * When deleting documents:
 * - Library documents: Removes association with agent, keeps document in library
 * - Direct uploads: Completely deletes document from system
 */

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
    metadata: doc.metadata, // Include metadata for extraction status
  };
};

const DocumentsTab: React.FC = () => {
  const { agent_id } = useParams<{ agent_id: string }>();
  const [searchTerm, setSearchTerm] = useState('');
  const [uploadingFiles, setUploadingFiles] = useState<string[]>([]);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [selectedItem, setSelectedItem] = useState<LibraryItem | null>(null);
  const [pdfViewerOpen, setPdfViewerOpen] = useState(false);
  const [pdfFileUrl, setPdfFileUrl] = useState<string | null>(null);
  const [pdfFileName, setPdfFileName] = useState<string | undefined>(undefined);
  const [libraryModalOpen, setLibraryModalOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Use document store for state management
  const { documents, isLoading, fetchDocuments } = useDocumentStore();

  // Use agent store to get agent's associated_documents
  const { selectedAgent, fetchAgent } = useAgentStore();

  // Analytics tracking
  const { trackDocumentAssociation, trackFileUpload, trackError } = useDanaAnalytics();

  // Cleanup function to reset deletion state
  const resetDeletionState = () => {
    setShowDeleteConfirm(false);
    setSelectedItem(null);
  };

  // Load all documents and filter by agent's associated_documents
  useEffect(() => {
    console.log('🔄 DocumentsTab: Fetching all documents');
    fetchDocuments(); // Fetch all documents, no agent_id filter
  }, [fetchDocuments]);

  // Refetch documents when component becomes visible (handles navigation back)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        console.log('👁️ DocumentsTab: Component became visible, refetching all documents');
        fetchDocuments(); // Fetch all documents, no agent_id filter
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [fetchDocuments]);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  const handleAddFromLibrary = () => {
    setLibraryModalOpen(true);
  };

  const handleLibraryFileSelection = async (selectedFileIds: string[]) => {
    if (!agent_id) {
      toast.error('No agent selected');
      return;
    }

    try {
      const documentIds = selectedFileIds.map((id) => parseInt(id));
      console.log('🔗 Associating documents:', { agent_id, documentIds });

      const result = await apiService.associateDocumentsWithAgent(agent_id, documentIds);
      console.log('✅ Association result:', result);

      // Track document association
      trackDocumentAssociation(agent_id, selectedFileIds.length);

      toast.success(`Successfully added ${selectedFileIds.length} file(s) to agent`);

      // Refetch agent data to get updated associated_documents
      if (agent_id) {
        await fetchAgent(parseInt(agent_id));
      }

      await fetchDocuments(); // Fetch all documents
      setLibraryModalOpen(false);
    } catch (error: any) {
      console.error('❌ Failed to add files to agent:', error);
      console.error('❌ Error details:', {
        message: error.message,
        status: error.response?.status,
        data: error.response?.data,
        stack: error.stack,
      });
      
      // Track association error
      trackError('document_association_failed', error?.message || 'Unknown error', agent_id);
      
      toast.error('Failed to add files to agent');
    }
  };

  const handleFileInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0 || !agent_id) return;

    const fileList = Array.from(files);
    const fileNames = fileList.map((f) => f.name);

    // Set uploading state for these files
    setUploadingFiles(fileNames);

    try {
      // Upload all files first to library, then associate with agent
      for (const file of fileList) {
        // Step 1: Upload to library
        const uploadedResponse = await apiService.uploadDocumentRaw(file, {
          build_index: true,
          allow_duplicate: false,
        });

        if (!uploadedResponse.success || !uploadedResponse.document) {
          throw new Error(uploadedResponse.message || 'Upload failed');
        }
        
        // Track file upload
        const fileExtension = file.name.split('.').pop() || 'unknown';
        trackFileUpload(fileExtension, file.size);
        // Step 2: Associate with agent
        await apiService.associateDocumentsWithAgent(agent_id, [uploadedResponse.document.id]);
        // Remove this file from uploading list as it completes
        setUploadingFiles((prev) => prev.filter((name) => name !== file.name));
      }

      // Wait a moment for backend processing, then refresh documents list
      await new Promise((resolve) => setTimeout(resolve, 500));

      // Refetch agent data to get updated associated_documents
      if (agent_id) {
        await fetchAgent(parseInt(agent_id));
      }

      await fetchDocuments(); // Fetch all documents

      toast.success(`Successfully uploaded ${fileList.length} file(s)`);
    } catch (error) {
      console.error('Failed to upload or associate files:', error);
      
      // Track upload error
      trackError('file_upload_failed', error instanceof Error ? error.message : 'Unknown error', `agent_${agent_id}`);
      
      toast.error('Failed to upload files. Please try again.');
      // Clear uploading state on error
      setUploadingFiles([]);
      // Still reload documents to show any files that were successfully uploaded before the error
      await fetchDocuments(); // Fetch all documents
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
    // Simple deletion - always disassociate from agent
    console.log('🗑️ Delete item requested:', {
      itemId: item.id,
      itemName: item.name,
    });

    setSelectedItem(item);
    setShowDeleteConfirm(true);
  };

  /**
   * Handle document removal from agent
   *
   * SIMPLIFIED: Always disassociate documents from agents instead of deleting them.
   * This ensures documents remain in the library and can be re-added to other agents.
   */
  const handleConfirmDelete = async () => {
    if (!selectedItem) return;

    try {
      const documentId = parseInt(selectedItem.id);

      await apiService.disassociateDocumentFromAgent(agent_id!, documentId);
      toast.success(`"${selectedItem.name}" removed successfully.`);

      console.log('🔄 Refreshing documents after disassociation...');

      // Refetch agent data to get updated associated_documents
      if (agent_id) {
        await fetchAgent(parseInt(agent_id));
      }

      await fetchDocuments(); // Fetch all documents

      console.log('✅ Document disassociation and refresh completed');
    } catch (error) {
      console.error('❌ Failed to remove document from agent:', error);
      toast.error('Failed to remove document from agent');
    } finally {
      setShowDeleteConfirm(false);
      setSelectedItem(null);
    }
  };

  // Empty state component
  const EmptyState = () => {
    return (
      <div className="flex flex-col items-center justify-center h-[100%] border-2 border-dashed border-gray-300 rounded-lg">
        <div className="flex flex-col items-center justify-center mb-4 w-22 h-22 rounded-full bg-gray-100">
          <EmptyPage className="w-10 h-10 text-gray-400" />
        </div>

        <div className="space-y-2 mb-4 text-center">
          <h3 className="text-lg font-semibold text-gray-700">No documents yet</h3>
          <p className="text-sm text-gray-500">Add documents from your library</p>
        </div>
        <Button
          onClick={handleAddFromLibrary}
          disabled={uploadingFiles.length > 0}
          variant="outline"
        >
          <MultiplePagesPlus className="mr-2 w-4 h-4" />
          Add from Library
        </Button>
      </div>
    );
  };

  // Filter documents by agent's associated_documents
  const agentAssociatedDocuments = selectedAgent?.config?.associated_documents || [];
  const agentDocuments = documents.filter((doc) => agentAssociatedDocuments.includes(doc.id));
  const data = agentDocuments.map(convertDocumentToLibraryItem);

  // Debug logging for document state
  console.log('📊 DocumentsTab: Current state:', {
    agent_id,
    selectedAgentId: selectedAgent?.id,
    agentAssociatedDocuments,
    documentsCount: documents.length,
    agentDocumentsCount: agentDocuments.length,
    documents: documents.map((d) => ({
      id: d.id,
      name: d.original_filename,
    })),
    dataCount: data.length,
    isLoading,
  });

  // Apply search filter
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
          {data.length > 0 && (
            <div className="text-sm text-gray-500">
              {data.length} document{data.length !== 1 ? 's' : ''}
            </div>
          )}
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

      <div className="flex space-between w-full items-center space-x-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 w-4 h-4 text-gray-400 transform -translate-y-1/2" />
          <Input
            placeholder="Search documents..."
            value={searchTerm}
            onChange={handleSearchChange}
            className="pl-10"
          />
        </div>

        <Button
          onClick={handleAddFromLibrary}
          disabled={uploadingFiles.length > 0}
          variant="outline"
        >
          <MultiplePagesPlus className="mr-2 w-4 h-4" />
          Add from Library
        </Button>
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
        {filteredData.length === 0 && !isLoading ? (
          <EmptyState />
        ) : (
          <LibraryTable
            data={filteredData}
            loading={isLoading}
            mode="library"
            onViewItem={handleViewItem}
            onDeleteItem={handleDeleteItem}
          />
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        onClose={resetDeletionState}
        onConfirm={handleConfirmDelete}
        title="Remove from Agent"
        description={`Are you sure you want to remove "${selectedItem?.name}" from this agent? The document will remain in the library and can be added to other agents.`}
        confirmText="Remove from Agent"
        cancelText="Cancel"
        variant="default"
      />

      {/* PDF Viewer */}
      <PdfViewer
        open={pdfViewerOpen}
        onClose={() => setPdfViewerOpen(false)}
        fileUrl={pdfFileUrl || ''}
        fileName={pdfFileName}
      />

      {/* Library File Selection Modal */}
      <LibraryFileSelectionModal
        isOpen={libraryModalOpen}
        onClose={() => setLibraryModalOpen(false)}
        onConfirm={handleLibraryFileSelection}
        currentAgentId={agent_id || ''}
      />
    </div>
  );
};

export default DocumentsTab;
