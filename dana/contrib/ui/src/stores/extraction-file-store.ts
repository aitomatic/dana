/* eslint-disable @typescript-eslint/no-explicit-any */
import { create } from 'zustand';
import { apiService } from '@/lib/api';
import { analytics } from '@/lib/analytics';

function unwrapMarkdownFences(content: string | undefined): string {
  if (!content) return '';
  const fencePattern = /^```(?:markdown|md)?\n([\s\S]*?)\n```\s*$/i;
  const match = content.match(fencePattern);
  return match ? match[1] : content;
}

function isAutoExtractCandidate(fileName: string): boolean {
  const ext = fileName.split('.').pop()?.toLowerCase() || '';
  return [
    'png',
    'jpg',
    'jpeg',
    'gif',
    'bmp',
    'tiff',
    'tif',
    'pdf',
    'docx',
    'doc',
    'pptx',
    'ppt',
    'xlsx',
    'xls',
    'txt',
    'md',
    'rtf',
  ].includes(ext);
}

function getFileStatus(file: ExtractionFile): 'uploading' | 'extracting' | 'ready' | 'error' {
  // If there's a duplicate error, it's an error state
  if (file.duplicate_error) {
    return 'error';
  }

  // If we have documents, the file is ready
  if (file.documents && file.documents.length > 0) {
    return 'ready';
  }

  // If we have a document_id but no documents yet, it's extracting
  if (file.document_id && (!file.documents || file.documents.length === 0)) {
    return 'extracting';
  }

  // If we have a file but no document_id yet, it's uploading
  if (file.file && !file.document_id) {
    return 'uploading';
  }

  // Default to ready for existing documents
  return 'ready';
}

export interface ExtractionFile {
  id: string;
  file: File | null; // Can be null for existing documents
  original_filename: string;
  filename: string;
  file_size: number;
  mime_type: string;
  document_id?: number; // Database document ID from upload response
  extraction_file_id?: number; // ID of the saved JSON extraction file
  documents?: Array<{
    text: string;
    page_content?: string;
    page_number?: number;
    [key: string]: any;
  }>;
  created_at?: string;
  updated_at?: string;
  // V2 API fields
  task_id?: number; // For background deep extraction
  deep_extraction_status?: 'running' | 'completed' | 'failed';
  duplicate_error?: string; // For duplicate detection errors
  is_deep_extracted?: boolean;
  deep_extracted_documents?: Array<{
    text: string;
    page_content?: string;
    page_number?: number;
    [key: string]: any;
  }>;
}

export interface ExtractionFileState {
  // UI State
  isExtractionPopupOpen: boolean;
  selectedFile: ExtractionFile | null;
  showConfirmDiscard: boolean;
  isDuplicateDialogOpen: boolean;
  duplicateFile: ExtractionFile | null;

  // Extraction Process State
  isExtracting: boolean;
  extractionProgress: number;
  extractedFiles: ExtractionFile[];
  currentExtractionStep: 'upload' | 'extract' | 'review' | 'saving' | 'complete';

  // Callback State
  onSaveCompletedCallback?: () => void;

  // Error State
  error: string | null;

  // Actions
  // UI Actions
  openExtractionPopup: () => void;
  openExtractionPopupWithDocument: (document: any) => void;
  closeExtractionPopup: () => Promise<void>;
  setSelectedFile: (file: ExtractionFile | null) => void;
  setShowConfirmDiscard: (show: boolean) => void;
  setOnSaveCompletedCallback: (callback?: () => void) => void;

  // File Management
  addFile: (file: File) => void;
  clearFiles: () => Promise<void>;

  // Extraction Process
  saveAndFinish: () => Promise<void>;

  // Duplicate File Handling
  openDuplicateDialog: (file: ExtractionFile) => void;
  closeDuplicateDialog: () => void;
  handleDuplicateAction: (
    action: 'replace' | 'copy' | 'cancel',
    file: ExtractionFile,
  ) => Promise<void>;

  // Reset
  reset: () => void;
}

export const useExtractionFileStore = create<ExtractionFileState>((set, get) => ({
  // Initial State
  isExtractionPopupOpen: false,
  selectedFile: null,
  showConfirmDiscard: false,
  isDuplicateDialogOpen: false,
  duplicateFile: null,
  isExtracting: false,
  extractionProgress: 0,
  extractedFiles: [],
  currentExtractionStep: 'upload',
  onSaveCompletedCallback: undefined,
  error: null,

  // UI Actions
  openExtractionPopup: () => {
    set({
      isExtractionPopupOpen: true,
      currentExtractionStep: 'upload',
      error: null,
    });
  },

  openExtractionPopupWithDocument: (document: any) => {
    // Convert document to ExtractionFile format
    const extractionFile: ExtractionFile = {
      id: `existing-${document.id}`,
      file: null, // No file object for existing documents - will be downloaded on demand
      original_filename: document.original_filename,
      filename: document.filename,
      file_size: document.file_size,
      mime_type: document.mime_type,
      document_id: document.id,
      extraction_file_id: document.metadata?.extraction_file_id, // Include extraction file ID if available
      created_at: document.created_at,
      updated_at: document.updated_at,
      // Try to get extraction data if available
      documents: document.metadata?.extraction_results?.documents || [],
      is_deep_extracted: document.metadata?.is_deep_extracted || false,
      deep_extraction_status: document.metadata?.deep_extraction_status || 'completed',
      deep_extracted_documents: document.metadata?.deep_extraction_results?.documents || [],
    };

    set({
      isExtractionPopupOpen: true,
      currentExtractionStep: 'review',
      extractedFiles: [extractionFile],
      selectedFile: extractionFile,
      error: null,
    });

    // Use v2 API to get document with deep extraction data
    (async () => {
      try {
        console.log('Fetching document with extraction results via v2 API...');
        const documentWithExtraction = await apiService.getExtractionResults(document.id);

        // Update the file with fresh extraction data from v2 API
        set((state) => {
          const updatedFiles = state.extractedFiles.map((f) =>
            f.id === extractionFile.id
              ? {
                  ...f,
                  // Update with fresh data from v2 API
                  // V2 API returns documents directly in the response
                  documents: documentWithExtraction.documents || f.documents || [],
                  is_deep_extracted: true, // Since we're getting extraction results, it's extracted
                  deep_extraction_status: 'completed' as const,
                  deep_extracted_documents:
                    documentWithExtraction.documents || f.deep_extracted_documents || [],
                  updated_at: new Date().toISOString(),
                }
              : f,
          );
          const updatedFile = updatedFiles.find((f) => f.id === extractionFile.id);

          return {
            extractedFiles: updatedFiles,
            selectedFile: updatedFile || state.selectedFile,
          };
        });

        console.log('Successfully updated document with v2 API extraction data');
      } catch (error) {
        console.log('Could not fetch document with v2 API, using existing data:', error);
        // If v2 API fails, we'll just use the existing data we already have
      }
    })();
  },

  closeExtractionPopup: async () => {
    set({
      isExtractionPopupOpen: false,
      selectedFile: null,
      showConfirmDiscard: false,
      error: null,
      extractedFiles: [],
      extractionProgress: 0,
      currentExtractionStep: 'upload',
    });
  },

  setSelectedFile: (file: ExtractionFile | null) => {
    set({ selectedFile: file });
  },

  setShowConfirmDiscard: (show: boolean) => {
    set({ showConfirmDiscard: show });
  },

  setOnSaveCompletedCallback: (callback?: () => void) => {
    set({ onSaveCompletedCallback: callback });
  },

  // File Management
  addFile: (file: File) => {
    const newExtractionFile: ExtractionFile = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      file,
      original_filename: file.name,
      filename: file.name,
      file_size: file.size,
      mime_type: file.type,
      created_at: new Date().toISOString(),
    };

    set((state) => ({
      extractedFiles: [...state.extractedFiles, newExtractionFile],
      selectedFile: state.selectedFile || newExtractionFile,
    }));

    // Auto-extract supported types
    if (isAutoExtractCandidate(file.name)) {
      const fileId = newExtractionFile.id;
      (async () => {
        let documentId: number | undefined;

        try {
          // Mark as uploading
          set((state) => ({
            extractedFiles: state.extractedFiles.map((f) => (f.id === fileId ? { ...f } : f)),
          }));

          const uploaded = await apiService.uploadDocumentRaw(file, {
            build_index: true,
            allow_duplicate: false,
          });

          // Handle upload failures (including duplicates at upload level)
          if (!uploaded.success) {
            if (uploaded.message?.includes('already exists')) {
              // Show duplicate dialog for upload-level duplicate detection
              const file = get().extractedFiles.find((f) => f.id === fileId);
              if (file) {
                get().openDuplicateDialog(file);
              }
              return;
            }
            throw new Error(uploaded.message || 'Upload failed');
          }

          // Use the document ID returned by the upload API
          documentId = uploaded.document?.id;

          // Mark as extracting
          set((state) => ({
            extractedFiles: state.extractedFiles.map((f) => (f.id === fileId ? { ...f } : f)),
          }));

          if (!documentId) {
            throw new Error('Document ID not available');
          }

          // Perform extraction with separate error handling
          try {
            // Get the document with extraction results from the v2 API
            const documentWithExtraction = await apiService.getExtractionResults(documentId);

            // Map documents from the response and unwrap fenced markdown
            const docs = (documentWithExtraction.documents || []).map((doc: any) => {
              return {
                text: unwrapMarkdownFences(doc.text),
                page_content: doc.text,
                page_number: doc.page_number,
              };
            });

            // Track successful extraction
            const fileExtension = file.name.split('.').pop() || 'unknown';
            analytics.trackEvent({
              action: 'file_extraction_success',
              category: 'library',
              label: `${fileExtension}_basic`,
            });

            // Store results
            set((state) => {
              const updatedFiles = state.extractedFiles.map((f) =>
                f.id === fileId
                  ? {
                      ...f,
                      document_id: documentId, // Store the database document ID
                      task_id: uploaded.task_id || undefined, // Store background task ID
                      documents: docs,
                      updated_at: new Date().toISOString(),
                      is_deep_extracted: true, // Deep extraction
                      deep_extraction_status: uploaded.task_id
                        ? ('running' as const)
                        : ('completed' as const),
                    }
                  : f,
              );
              const updatedFile = updatedFiles.find((f) => f.id === fileId);

              // Also update selectedFile if it's the same file
              const updatedSelectedFile =
                state.selectedFile?.id === fileId ? updatedFile : state.selectedFile;

              return {
                extractedFiles: updatedFiles,
                selectedFile: updatedSelectedFile,
              };
            });
          } catch (extractionError: any) {
            // Handle extraction-specific errors
            const errorMessage = extractionError?.message || '';

            // Track extraction error
            const fileExtension = file.name.split('.').pop() || 'unknown';
            analytics.trackEvent({
              action: 'file_extraction_failed',
              category: 'library',
              label: `${fileExtension}_basic`,
            });

            // Check if this is a duplicate-related extraction failure
            if (
              errorMessage.includes('already') ||
              errorMessage.includes('duplicate') ||
              errorMessage.includes('exists')
            ) {
              // Show duplicate dialog for extraction-level duplicate errors
              const file = get().extractedFiles.find((f) => f.id === fileId);
              if (file) {
                get().openDuplicateDialog(file);
                return;
              }
            }

            // If not duplicate-related, handle as extraction error
            set({ error: `Extraction failed: ${errorMessage}` });

            // Store document_id even if extraction fails, but clear status
            set((state) => ({
              extractedFiles: state.extractedFiles.map((f) =>
                f.id === fileId
                  ? {
                      ...f,
                      document_id: documentId, // Store the document ID even on extraction failure
                    }
                  : f,
              ),
            }));
          }
        } catch (uploadError: any) {
          // Handle upload-level errors (not extraction errors)
          set({ error: uploadError instanceof Error ? uploadError.message : 'Upload failed' });

          // Clear status on upload failure
          set((state) => ({
            extractedFiles: state.extractedFiles.map((f) =>
              f.id === fileId
                ? {
                    ...f,
                  }
                : f,
            ),
          }));
        }
      })();
    }
  },

  clearFiles: async () => {
    // Clear the files
    set({
      extractedFiles: [],
      selectedFile: null,
    });
  },

  saveAndFinish: async () => {
    const { extractedFiles } = get();

    // Filter files that have been successfully extracted
    const successfulFiles = extractedFiles.filter(
      (file) =>
        (getFileStatus(file) === 'ready' || file.documents) &&
        file.documents &&
        file.documents &&
        file.documents.length > 0,
    );

    if (successfulFiles.length === 0) {
      set({ error: 'No successfully extracted files to finish' });
      return;
    }

    set({
      isExtracting: true,
      error: null,
      currentExtractionStep: 'saving',
    });

    try {
      // Since extraction data is already saved during upload, we just need to finish the process
      console.log(`Finishing extraction process for ${successfulFiles.length} files`);

      // All done - show success and close
      set({
        currentExtractionStep: 'complete',
        isExtracting: false,
        extractionProgress: 100,
      });

      // Close the popup after a brief delay
      setTimeout(async () => {
        const { onSaveCompletedCallback } = get();
        // Call the callback to refresh the library
        if (onSaveCompletedCallback) {
          onSaveCompletedCallback();
        }
        await get().closeExtractionPopup();
      }, 1000);
    } catch (error) {
      console.error('Error in saveAndFinish:', error);
      set({
        error: error instanceof Error ? error.message : 'Failed to finish extraction process',
        isExtracting: false,
        extractionProgress: 0,
      });
    }
  },

  // Duplicate File Handling
  openDuplicateDialog: (file: ExtractionFile) => {
    set({
      isDuplicateDialogOpen: true,
      duplicateFile: file,
    });
  },

  closeDuplicateDialog: () => {
    set({
      isDuplicateDialogOpen: false,
      duplicateFile: null,
    });
  },

  handleDuplicateAction: async (action: 'replace' | 'copy' | 'cancel', file: ExtractionFile) => {
    const { closeDuplicateDialog } = get();

    if (action === 'cancel') {
      // Remove the file from the list
      set((state) => ({
        extractedFiles: state.extractedFiles.filter((f) => f.id !== file.id),
        selectedFile: state.selectedFile?.id === file.id ? null : state.selectedFile,
      }));
      closeDuplicateDialog();
      return;
    }

    try {
      // Mark file as uploading
      set((state) => ({
        extractedFiles: state.extractedFiles.map((f) => (f.id === file.id ? { ...f } : f)),
      }));

      // Upload with appropriate settings
      if (!file.file) {
        throw new Error('File content not available');
      }
      const uploaded = await apiService.uploadDocumentRaw(file.file, {
        build_index: true,
        allow_duplicate: action === 'copy', // true for copy, false for replace
      });

      if (!uploaded.success || !uploaded.document) {
        throw new Error(uploaded.message || 'Upload failed');
      }

      // Continue with extraction process
      const documentId = uploaded.document.id;

      // Get the document with extraction results from the v2 API
      const documentWithExtraction = await apiService.getExtractionResults(documentId);

      // Map documents from the response and unwrap fenced markdown
      const docs = (documentWithExtraction.documents || []).map((doc: any) => {
        return {
          text: unwrapMarkdownFences(doc.text),
          page_content: doc.text,
          page_number: doc.page_number,
        };
      });

      // Track successful deep extraction
      const fileExtension = file.file.name.split('.').pop() || 'unknown';
      analytics.trackEvent({
        action: 'file_extraction_success',
        category: 'library',
        label: `${fileExtension}_deep`,
      });

      // Update file with deep extraction results
      set((state) => {
        const updatedFiles = state.extractedFiles.map((f) =>
          f.id === file.id
            ? {
                ...f,
                document_id: documentId,
                task_id: uploaded.task_id || undefined,
                documents: docs,
                updated_at: new Date().toISOString(),
                is_deep_extracted: true, // Deep extraction
                deep_extraction_status: uploaded.task_id
                  ? ('running' as const)
                  : ('completed' as const),
              }
            : f,
        );
        const updatedFile = updatedFiles.find((f) => f.id === file.id);

        // Also update selectedFile if it's the same file
        const updatedSelectedFile =
          state.selectedFile?.id === file.id ? updatedFile : state.selectedFile;

        return {
          extractedFiles: updatedFiles,
          selectedFile: updatedSelectedFile,
        };
      });

      closeDuplicateDialog();
    } catch (error: any) {
      // Track deep extraction error
      const fileExtension = file.file?.name.split('.').pop() || 'unknown';
      analytics.trackEvent({
        action: 'file_extraction_failed',
        category: 'library',
        label: `${fileExtension}_deep`,
      });
      
      set({ error: error?.message || 'Deep extraction failed' });
      // Reset status on error
      set((state) => ({
        extractedFiles: state.extractedFiles.map((f) => (f.id === file.id ? { ...f } : f)),
      }));
      closeDuplicateDialog();
    }
  },

  // Reset
  reset: () => {
    set({
      isExtractionPopupOpen: false,
      selectedFile: null,
      showConfirmDiscard: false,
      isDuplicateDialogOpen: false,
      duplicateFile: null,
      isExtracting: false,
      extractionProgress: 0,
      extractedFiles: [],
      currentExtractionStep: 'upload',
      error: null,
    });
  },
}));
