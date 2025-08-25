import { useState, useEffect, useMemo } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Search } from 'iconoir-react';
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
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10); // Show 20 items per page

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
        documents: allDocuments?.map((d: DocumentRead) => ({ id: d.id, name: d.original_filename, agent_id: d.agent_id }))
      });
      setLibraryDocuments(allDocuments || []);
    } catch (error: any) {
      console.error('❌ Failed to fetch library documents:', error);
      setLibraryError(error.message || 'Failed to fetch library documents');
      setLibraryDocuments([]);
    } finally {
      setIsLoadingLibrary(false);
    }
  };

  // Fetch library documents when modal opens
  useEffect(() => {
    if (isOpen) {
      console.log('🔍 Modal opened, fetching library documents...');
      console.log('🔍 Current agent ID:', currentAgentId);
      fetchLibraryDocuments(); // Fresh fetch every time modal opens
    }
  }, [isOpen]); // Only depend on modal open state

  // Filter out documents that are already associated with the current agent
  const availableDocuments = useMemo(() => {
    console.log('🔍 Filtering available documents:', {
      totalDocuments: libraryDocuments?.length || 0,
      currentAgentId,
      searchTerm
    });

    const filtered = libraryDocuments.filter(doc => {
      // Exclude documents already associated with this agent
      if (doc.agent_id?.toString() === currentAgentId) {
        console.log('❌ Excluding document already in agent:', doc.original_filename);
        return false;
      }
      
      // Apply search filter
      if (searchTerm && !doc.original_filename.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }
      
      return true;
    });

    console.log('✅ Available documents after filtering:', {
      count: filtered.length,
      documents: filtered.map(d => ({ id: d.id, name: d.original_filename, agent_id: d.agent_id }))
    });

    return filtered;
  }, [libraryDocuments, currentAgentId, searchTerm]);

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
    shouldShowPagination: totalPages > 1
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
      setSelectedFileIds(prev => [...prev, fileId]);
    } else {
      setSelectedFileIds(prev => prev.filter(id => id !== fileId));
    }
  };

  const handleSelectAll = () => {
    if (selectedFileIds.length === availableDocuments.length) {
      setSelectedFileIds([]);
    } else {
      setSelectedFileIds(availableDocuments.map(doc => doc.id.toString()));
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
    <Dialog  open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="!max-w-[880px]  gap-2 overflow-hidden">
        <DialogHeader className="">
          <DialogTitle className="flex justify-between">
            <span>Add Files from Library</span>
            {/* <Button
              variant="ghost"
              size="sm"
              onClick={handleClose}
              className="h-8 w-8 p-0"
            >
              <Xmark className="h-4 w-4" />
            </Button> */}
          </DialogTitle>
        </DialogHeader>

        <div className="flex flex-col space-y-4 overflow-y-auto  max-h-full">
          {/* Search and Controls */}
          <div className="flex items-center space-x-4 flex-shrink-0">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 w-4 h-4 text-gray-400 transform -translate-y-1/2" />
              <Input
                placeholder="Search files..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleSelectAll}
              className="whitespace-nowrap"
            >
              {selectedFileIds.length === availableDocuments.length ? 'Deselect All' : 'Select All'}
            </Button>

          </div>

  
          <div className="h-[520px] overflow-y-auto border rounded-lg">
            {isLoadingLibrary ? (
              <div className="flex justify-center text-gray-500">
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  <span>Loading library documents...</span>
                </div>
              </div>
            ) : libraryError ? (
              <div className="flex items-center justify-center text-red-500">
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
              <div className="flex items-center justify-center h-32 text-gray-500">
                {searchTerm ? 'No files match your search' : 'No files available to add'}
              </div>
            ) : (
              <div className="divide-y">
                {paginatedDocuments.map((doc) => (
                  <div
                    key={doc.id}
                    className="flex items-center space-x-3 p-3 hover:bg-gray-50"
                  >
                    <Checkbox
        
                      onCheckedChange={(checked) => 
                        handleFileSelection(doc.id.toString(), checked as boolean)
                      }
                    />
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate">
                        {doc.original_filename}
                      </div>
                      <div className="text-xs text-gray-500">
                        {doc.file_size ? `${(doc.file_size / 1024).toFixed(1)} KB` : 'Unknown size'}
                     
                      
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-2 flex-shrink-0">
              <div className="text-sm text-gray-500">
                Showing {startIndex + 1}-{Math.min(endIndex, availableDocuments.length)} of {availableDocuments.length} files
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={goToPreviousPage}
                  disabled={currentPage === 1}
                  className="px-3"
                >
                  Previous
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
                        variant={currentPage === pageNum ? "default" : "outline"}
                        size="sm"
                        onClick={() => goToPage(pageNum)}
                        className="w-8 h-8 p-0"
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
                  className="px-3"
                >
                  Next
                </Button>
              </div>
            </div>
          )}

          {/* Footer Actions */}
          <div className="flex items-center justify-between pt-4 border-t flex-shrink-0 mt-auto">
            <div className="text-sm text-gray-600">
              {selectedFileIds.length > 0 ? (
                <span>{selectedFileIds.length} file(s) selected</span>
              ) : (
                <span>{availableDocuments.length} of {libraryDocuments.length} files available</span>
              )}
            </div>
            <div className="flex space-x-2">
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button
                onClick={handleConfirm}
                disabled={selectedFileIds.length === 0 || isLoading}
              >
                {isLoading ? 'Adding...' : `Add ${selectedFileIds.length} File(s)`}
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
