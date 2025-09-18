import { useState, useEffect, useMemo } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Search } from 'iconoir-react';
import { ArrowLeft, ArrowRight } from 'iconoir-react';
import { toast } from 'sonner';
import { apiService } from '@/lib/api';
import type { DocumentRead } from '@/types/document';

interface LibraryFileSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (selectedFileIds: string[]) => void;
  currentAgentId: string;
}

export function LibraryFileSelectionModal({
  isOpen,
  onClose,
  onConfirm,
  currentAgentId,
}: LibraryFileSelectionModalProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFileIds, setSelectedFileIds] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Separate state for library documents to avoid conflicts with agent-specific documents
  const [libraryDocuments, setLibraryDocuments] = useState<DocumentRead[]>([]);
  const [isLoadingLibrary, setIsLoadingLibrary] = useState(false);
  const [libraryError, setLibraryError] = useState<string | null>(null);

  // State for current agent's associated documents
  const [currentAgentAssociatedDocuments, setCurrentAgentAssociatedDocuments] = useState<number[]>(
    [],
  );
  const [isLoadingAgent, setIsLoadingAgent] = useState(false);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10); // Show 20 items per page

  // Fetch current agent's associated documents
  const fetchCurrentAgentDetails = async () => {
    console.log('🔍 Fetching current agent details...');
    setIsLoadingAgent(true);

    try {
      const agent = await apiService.getAgent(parseInt(currentAgentId));
      const associatedDocs = agent.config?.associated_documents || [];
      console.log('📋 Current agent associated documents:', associatedDocs);
      setCurrentAgentAssociatedDocuments(associatedDocs);
    } catch (error) {
      console.error('❌ Failed to fetch current agent details:', error);
      setCurrentAgentAssociatedDocuments([]);
    } finally {
      setIsLoadingAgent(false);
    }
  };

  // Dedicated function to fetch library documents
  const fetchLibraryDocuments = async () => {
    console.log('🔍 Fetching library documents...');
    setIsLoadingLibrary(true);
    setLibraryError(null);

    try {
      // Use API service directly to avoid store conflicts
      const allDocuments = await apiService.getDocuments();
      console.log('📚 Library documents fetched:', {
        count: allDocuments?.length || 0,
        documents: allDocuments?.map((d: DocumentRead) => ({
          id: d.id,
          name: d.original_filename,
          agent_id: d.agent_id,
        })),
      });
      setLibraryDocuments(allDocuments || []);
    } catch (error) {
      console.error('❌ Failed to fetch library documents:', error);
      setLibraryError(error instanceof Error ? error.message : 'Failed to fetch library documents');
      setLibraryDocuments([]);
    } finally {
      setIsLoadingLibrary(false);
    }
  };

  // Fetch data when modal opens
  useEffect(() => {
    if (isOpen) {
      console.log('🔍 Modal opened, fetching data...');
      console.log('🔍 Current agent ID:', currentAgentId);
      fetchCurrentAgentDetails(); // Fetch agent details first
      fetchLibraryDocuments(); // Then fetch library documents
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, currentAgentId]); // Only depend on modal open state

  // Initialize selected files based on already associated documents
  useEffect(() => {
    if (currentAgentAssociatedDocuments.length > 0 && libraryDocuments.length > 0) {
      const alreadyAssociatedIds = currentAgentAssociatedDocuments.map((id) => id.toString());
      console.log('✅ Setting pre-selected files:', alreadyAssociatedIds);
      setSelectedFileIds(alreadyAssociatedIds);
    }
  }, [currentAgentAssociatedDocuments, libraryDocuments]);

  // Filter documents - now we show all documents but mark associated ones as checked
  const availableDocuments = useMemo(() => {
    console.log('🔍 Filtering available documents:', {
      totalDocuments: libraryDocuments?.length || 0,
      currentAgentId,
      searchTerm,
      associatedDocuments: currentAgentAssociatedDocuments,
    });

    const filtered = libraryDocuments.filter((doc) => {
      // Apply search filter
      if (searchTerm && !doc.original_filename.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }

      return true;
    });

    console.log('✅ Available documents after filtering:', {
      count: filtered.length,
      documents: filtered.map((d) => ({
        id: d.id,
        name: d.original_filename,
        agent_id: d.agent_id,
        isAssociated: currentAgentAssociatedDocuments.includes(d.id),
      })),
    });

    return filtered;
  }, [libraryDocuments, currentAgentId, searchTerm, currentAgentAssociatedDocuments]);

  // Pagination logic
  const totalPages = Math.ceil(availableDocuments.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedDocuments = availableDocuments.slice(startIndex, endIndex);

  // Debug logging for pagination
  console.log('🔢 Pagination debug:', {
    availableDocumentsLength: availableDocuments.length,
    itemsPerPage,
    totalPages,
    currentPage,
    startIndex,
    endIndex,
    paginatedDocumentsLength: paginatedDocuments.length,
    shouldShowPagination: totalPages > 1,
  });

  // Reset to first page when search changes
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm]);

  // Pagination handlers
  const goToPage = (page: number) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
  };

  const goToNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };

  const goToPreviousPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleFileSelection = (fileId: string, checked: boolean) => {
    if (checked) {
      setSelectedFileIds((prev) => [...prev, fileId]);
    } else {
      setSelectedFileIds((prev) => prev.filter((id) => id !== fileId));
    }
  };

  const handleConfirm = async () => {
    if (selectedFileIds.length === 0) {
      toast.error('Please select at least one file');
      return;
    }

    setIsLoading(true);
    try {
      onConfirm(selectedFileIds);
    } catch (error) {
      console.error('Error adding files:', error);
      toast.error('Failed to add files to agent');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setSelectedFileIds([]);
    setSearchTerm('');
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="!max-w-[880px]  gap-4 overflow-hidden">
        <DialogHeader className="">
          <DialogTitle className="flex justify-between">
            <span>Add Files from Library</span>
            {/* <Button
              variant="ghost"
              size="sm"
              onClick={handleClose}
              className="p-0 w-8 h-8"
            >
              <Xmark className="w-4 h-4" />
            </Button> */}
          </DialogTitle>
        </DialogHeader>

        <div className="flex overflow-y-auto flex-col space-y-4 max-h-full">
          {/* Search and Controls */}
          <div className="flex flex-shrink-0 items-center space-x-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 w-4 h-4 text-gray-400 transform -translate-y-1/2" />
              <Input
                placeholder="Search files..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          <div className="h-[520px] overflow-y-auto border rounded-lg">
            {isLoadingLibrary || isLoadingAgent ? (
              <div className="flex justify-center text-gray-500">
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 rounded-full border-b-2 border-blue-600 animate-spin"></div>
                  <span>Loading...</span>
                </div>
              </div>
            ) : libraryError ? (
              <div className="flex justify-center items-center text-red-500">
                <div className="text-center">
                  <div className="font-medium">Error loading documents</div>
                  <div className="text-sm text-red-400">{libraryError}</div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={fetchLibraryDocuments}
                    className="mt-2"
                  >
                    Retry
                  </Button>
                </div>
              </div>
            ) : availableDocuments.length === 0 ? (
              <div className="flex justify-center items-center h-32 text-gray-500">
                {searchTerm ? 'No files match your search' : 'No files available to add'}
              </div>
            ) : (
              <div className="divide-y">
                {paginatedDocuments.map((doc) => {
                  return (
                    <div key={doc.id} className="flex items-center p-3 space-x-3 hover:bg-gray-50">
                      <Checkbox
                        checked={selectedFileIds.includes(doc.id.toString())}
                        onCheckedChange={(checked) =>
                          handleFileSelection(doc.id.toString(), checked as boolean)
                        }
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center text-sm font-medium truncate">
                          {doc.original_filename}
                        </div>
                        <div className="text-xs text-gray-500">
                          {doc.file_size
                            ? `${(doc.file_size / 1024).toFixed(1)} KB`
                            : 'Unknown size'}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex flex-shrink-0 justify-between items-center pt-2">
              <div className="text-sm text-gray-500">
                Showing {startIndex + 1}-{Math.min(endIndex, availableDocuments.length)} of{' '}
                {availableDocuments.length} files
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={goToPreviousPage}
                  disabled={currentPage === 1}
                  className="p-0 w-8 h-8"
                >
                  <ArrowLeft className="w-4 h-4" />
                </Button>

                {/* Page numbers */}
                <div className="flex items-center space-x-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (currentPage <= 3) {
                      pageNum = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = currentPage - 2 + i;
                    }

                    return (
                      <Button
                        key={pageNum}
                        variant={currentPage === pageNum ? 'secondary' : 'outline'}
                        size="sm"
                        onClick={() => goToPage(pageNum)}
                        className={`w-8 h-8 p-0 ${
                          currentPage === pageNum
                            ? 'bg-gray-100 hover:bg-gray-100 text-gray-900 border-gray-300'
                            : ''
                        }`}
                      >
                        {pageNum}
                      </Button>
                    );
                  })}
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={goToNextPage}
                  disabled={currentPage === totalPages}
                  className="p-0 w-8 h-8"
                >
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}

          {/* Footer Actions */}
          <div className="flex flex-shrink-0 items-center pt-4 mt-auto border-t">
            <Button 
              variant="outline" 
              onClick={() => window.open('/library', '_blank')}
              className="mr-auto"
            >
              Go to Library
            </Button>
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button onClick={handleConfirm} disabled={selectedFileIds.length === 0 || isLoading}>
                {isLoading ? 'Adding...' : `Add ${selectedFileIds.length} File(s)`}
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
