import { useEffect, useState } from 'react';
import { LibraryTable } from '@/components/library';
import type { LibraryItem } from '@/types/library';
import { convertDocumentToFileItem } from '@/components/library';
import { apiService } from '@/lib/api';
import type { DocumentRead } from '@/types/document';
import { useExtractionFileStore } from '@/stores/extraction-file-store';
import { ExtractionFilePopup } from '../extraction-file';

interface DocumentsTabProps {
  documentIds: number[];
}

export function DocumentsTab({ documentIds }: DocumentsTabProps) {
  const [documents, setDocuments] = useState<LibraryItem[]>([]);
  const [documentData, setDocumentData] = useState<DocumentRead[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { openExtractionPopupWithDocument, isExtractionPopupOpen } = useExtractionFileStore();

  useEffect(() => {
    const fetchDocuments = async () => {
      if (!documentIds || documentIds.length === 0) {
        setDocuments([]);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        // Fetch each document by ID
        const documentPromises = documentIds.map((id) => apiService.getDocument(id));
        const fetchedDocuments = await Promise.all(documentPromises);

        // Store full DocumentRead objects for popup
        setDocumentData(fetchedDocuments);

        // Convert to LibraryItem format for table display
        const libraryItems = fetchedDocuments.map(convertDocumentToFileItem);
        setDocuments(libraryItems);
      } catch (err) {
        console.error('Failed to fetch documents:', err);
        setError('Failed to load documents');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDocuments();
  }, [documentIds]);

  // Handle viewing a document
  const handleViewItem = (item: LibraryItem) => {
    // Extract document ID from LibraryItem.id (format: doc-{id})
    const documentId = parseInt(item.id.replace('doc-', ''));
    const document = documentData.find((d) => d.id === documentId);
    
    if (document) {
      // Open extraction popup with the document
      openExtractionPopupWithDocument(document);
    }
  };

  return (
    <div className="flex flex-col max-w-[1200px] h-full overflow-hidden">
      {/* Header */}
      <div className="py-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Documents ({documents.length})
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Source documents used to create this knowledge pack
          </p>
        </div>
      </div>

      {/* Show empty state if no documents */}
      {!documentIds || documentIds.length === 0 ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <p className="text-gray-500 dark:text-gray-400">No documents associated with this knowledge pack.</p>
          </div>
        </div>
      ) : isLoading ? (
        // Show loading state
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="mx-auto mb-4 w-12 h-12 rounded-full border-b-2 border-blue-600 animate-spin"></div>
            <p className="text-gray-500 dark:text-gray-400">Loading documents...</p>
          </div>
        </div>
      ) : error ? (
        // Show error state
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <p className="text-red-500">{error}</p>
          </div>
        </div>
      ) : (
        // Show documents table
        <div className="flex-1 overflow-hidden">
          <LibraryTable
            data={documents}
            loading={isLoading}
            mode="library"
            filterType="all"
            onRowClick={handleViewItem}
            onViewItem={handleViewItem}
          />
        </div>
      )}

      {/* Extraction File Popup */}
      {isExtractionPopupOpen && <ExtractionFilePopup />}
    </div>
  );
}
