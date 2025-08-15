import { create } from 'zustand';
import { apiService } from '@/lib/api';

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

export interface ExtractionFile {
  id: string;
  file: File;
  original_filename: string;
  filename: string;
  file_size: number;
  mime_type: string;
  document_id?: number; // Database document ID from upload response
  topic_id?: number; // Topic ID when saved (deprecated - not used anymore)
  extraction_file_id?: number; // ID of the saved JSON extraction file
  is_deep_extracted?: boolean;
  prompt?: string;
  documents?: Array<{
    text: string;
    page_content?: string;
    page_number?: number;
    [key: string]: any;
  }>;
  created_at?: string;
  updated_at?: string;
  status?: 'uploading' | 'extracting' | 'ready';
}

export interface ExtractionFileState {
  // UI State
  isExtractionPopupOpen: boolean;
  selectedFile: ExtractionFile | null;
  showConfirmDiscard: boolean;

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
  closeExtractionPopup: () => Promise<void>;
  setSelectedFile: (file: ExtractionFile | null) => void;
  setShowConfirmDiscard: (show: boolean) => void;
  setOnSaveCompletedCallback: (callback?: () => void) => void;

  // File Management
  addFile: (file: File) => void;
  removeFile: (fileId: string) => Promise<void>;
  clearFiles: () => Promise<void>;

  // Extraction Process
  startExtraction: () => Promise<void>;
  updateExtractionProgress: (progress: number) => void;
  setExtractionStep: (step: ExtractionFileState['currentExtractionStep']) => void;
  completeExtraction: () => void;
  saveAndFinish: () => Promise<void>;
  deleteTopicsForFiles: (fileIds: string[]) => Promise<void>;

  // Error Handling
  setError: (error: string | null) => void;
  clearError: () => void;

  // Reset
  reset: () => void;
}

export const useExtractionFileStore = create<ExtractionFileState>((set, get) => ({
  // Initial State
  isExtractionPopupOpen: false,
  selectedFile: null,
  showConfirmDiscard: false,
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

  closeExtractionPopup: async () => {
    const { extractedFiles, deleteTopicsForFiles, currentExtractionStep } = get();

    // If user is closing without completing "Save & Finish", clean up any topics
    if (currentExtractionStep !== 'complete') {
      const fileIds = extractedFiles.map((f) => f.id);
      await deleteTopicsForFiles(fileIds);
    }

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
      status: undefined,
    };

    set((state) => ({
      extractedFiles: [...state.extractedFiles, newExtractionFile],
      selectedFile: state.selectedFile || newExtractionFile,
    }));

    // Auto-extract supported types
    if (isAutoExtractCandidate(file.name)) {
      const fileId = newExtractionFile.id;
      (async () => {
        try {
          // Mark as uploading
          set((state) => ({
            extractedFiles: state.extractedFiles.map((f) =>
              f.id === fileId ? { ...f, status: 'uploading' } : f,
            ),
          }));

          const uploaded = await apiService.uploadDocumentRaw(file);

          // Use the document ID returned by the upload API
          const documentId = uploaded.id;

          // Mark as extracting
          set((state) => ({
            extractedFiles: state.extractedFiles.map((f) =>
              f.id === fileId ? { ...f, status: 'extracting' } : f,
            ),
          }));

          const extractParams = {
            document_id: documentId,
            use_deep_extraction: true, // Enable deep extraction for auto-extraction
          };
          const deep = await apiService.deepExtract(extractParams);
          const docs = (deep.file_object?.pages || []).map((p) => {
            return {
              text: unwrapMarkdownFences(p.page_content),
              page_content: p.page_content,
              page_number: p.page_number,
            };
          });

          // Store results
          set((state) => {
            const updatedFiles = state.extractedFiles.map((f) =>
              f.id === fileId
                ? {
                    ...f,
                    document_id: documentId, // Store the database document ID
                    is_deep_extracted: true,
                    documents: docs,
                    updated_at: new Date().toISOString(),
                    status: 'ready' as const,
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
        } catch (err: any) {
          set({ error: err instanceof Error ? err.message : 'Auto extraction failed' });
          // Clear status on error
          set((state) => ({
            extractedFiles: state.extractedFiles.map((f) =>
              f.id === fileId ? { ...f, status: undefined } : f,
            ),
          }));
        }
      })();
    }
  },

  removeFile: async (fileId: string) => {
    const { deleteTopicsForFiles } = get();

    // Delete topic if it was created for this file
    await deleteTopicsForFiles([fileId]);

    // Remove the file
    set((state) => ({
      extractedFiles: state.extractedFiles.filter((f) => f.id !== fileId),
      selectedFile: state.selectedFile?.id === fileId ? null : state.selectedFile,
    }));
  },

  clearFiles: async () => {
    const { extractedFiles, deleteTopicsForFiles } = get();

    // Delete any topics that were created
    const fileIds = extractedFiles.map((f) => f.id);
    await deleteTopicsForFiles(fileIds);

    // Clear the files
    set({
      extractedFiles: [],
      selectedFile: null,
    });
  },

  // Extraction Process
  startExtraction: async () => {
    const { extractedFiles } = get();
    if (extractedFiles.length === 0) {
      set({ error: 'No files to extract' });
      return;
    }

    set({
      isExtracting: true,
      extractionProgress: 0,
      currentExtractionStep: 'extract',
      error: null,
    });

    try {
      const total = extractedFiles.length;
      let processed = 0;

      for (const fileItem of extractedFiles) {
        try {
          const uploaded = await apiService.uploadDocumentRaw(fileItem.file);

          // Use the document ID returned by the upload API
          const documentId = uploaded.id;

          const deep = await apiService.deepExtract({
            document_id: documentId,
            prompt: fileItem.prompt,
            use_deep_extraction: true, // Enable deep extraction for batch processing
          });
          const docs = (deep.file_object?.pages || []).map((p) => {
            return {
              text: unwrapMarkdownFences(p.page_content),
              page_content: p.page_content,
              page_number: p.page_number,
            };
          });

          set((state) => {
            const updatedFiles = state.extractedFiles.map((f) =>
              f.id === fileItem.id
                ? {
                    ...f,
                    document_id: documentId, // Store the database document ID
                    is_deep_extracted: true,
                    documents: docs,
                    updated_at: new Date().toISOString(),
                  }
                : f,
            );

            // Also update selectedFile if it's the same file
            const updatedSelectedFile =
              state.selectedFile?.id === fileItem.id
                ? updatedFiles.find((f) => f.id === fileItem.id)
                : state.selectedFile;

            return {
              extractedFiles: updatedFiles,
              selectedFile: updatedSelectedFile,
            };
          });
        } catch (innerErr) {
          set({
            error: innerErr instanceof Error ? innerErr.message : 'Extraction failed for a file',
          });
        } finally {
          processed += 1;
          set({ extractionProgress: Math.round((processed / total) * 100) });
        }
      }

      set({ currentExtractionStep: 'review', isExtracting: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Extraction failed',
        isExtracting: false,
        extractionProgress: 0,
      });
    }
  },

  updateExtractionProgress: (progress: number) => {
    set({ extractionProgress: progress });
  },

  setExtractionStep: (step: ExtractionFileState['currentExtractionStep']) => {
    set({ currentExtractionStep: step });
  },

  completeExtraction: () => {
    set({
      currentExtractionStep: 'complete',
      isExtracting: false,
      extractionProgress: 100,
    });
  },

  saveAndFinish: async () => {
    const { extractedFiles } = get();

    // Filter files that have been successfully extracted
    const successfulFiles = extractedFiles.filter(
      (file) =>
        (file.status === 'ready' || file.documents) &&
        (file.is_deep_extracted || file.documents) &&
        file.documents &&
        file.documents.length > 0,
    );

    if (successfulFiles.length === 0) {
      set({ error: 'No successfully extracted files to save' });
      return;
    }

    set({
      isExtracting: true,
      error: null,
      currentExtractionStep: 'saving',
    });

    try {
      const total = successfulFiles.length;
      let processed = 0;

      for (const extractedFile of successfulFiles) {
        try {
          // Ensure we have a document ID for the source file
          if (!extractedFile.document_id) {
            console.error(`No document ID found for file ${extractedFile.original_filename}`);
            continue;
          }

          console.log(
            `Saving extraction data for file "${extractedFile.original_filename}" (Document ID: ${extractedFile.document_id})`,
          );

          // Prepare extraction results
          const extractionResults = {
            original_filename: extractedFile.original_filename,
            extraction_date: new Date().toISOString(),
            total_pages: extractedFile.documents?.length || 0,
            documents: extractedFile.documents || [],
          };

          // Save extraction data via the new API endpoint
          const savedExtraction = await apiService.saveExtractionData({
            original_filename: extractedFile.original_filename,
            extraction_results: extractionResults,
            source_document_id: extractedFile.document_id,
          });

          console.log(`Successfully saved extraction JSON file with ID: ${savedExtraction.id}`);

          // Update the file state with the extraction file ID
          set((state) => ({
            extractedFiles: state.extractedFiles.map((f) =>
              f.id === extractedFile.id ? { ...f, extraction_file_id: savedExtraction.id } : f,
            ),
          }));

          processed += 1;
          set({ extractionProgress: Math.round((processed / total) * 100) });
        } catch (fileError) {
          console.error(`Error saving file ${extractedFile.original_filename}:`, fileError);
          // Continue with other files even if one fails
        }
      }

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
        error: error instanceof Error ? error.message : 'Failed to save extraction results',
        isExtracting: false,
        extractionProgress: 0,
      });
    }
  },

  deleteTopicsForFiles: async (fileIds: string[]) => {
    const { extractedFiles } = get();

    // Find files that have topic IDs
    const filesToCleanup = extractedFiles.filter(
      (file) => fileIds.includes(file.id) && file.topic_id,
    );

    if (filesToCleanup.length === 0) {
      console.log('No topics to delete for the specified files');
      return;
    }

    console.log(
      `Deleting ${filesToCleanup.length} topics for files:`,
      filesToCleanup.map((f) => f.original_filename),
    );

    for (const file of filesToCleanup) {
      try {
        if (file.topic_id) {
          console.log(`Deleting topic (ID: ${file.topic_id}) for file "${file.original_filename}"`);
          await apiService.deleteTopic(file.topic_id, true); // force=true to delete associated documents
          console.log(`Successfully deleted topic for file "${file.original_filename}"`);
        }
      } catch (error) {
        console.error(`Error deleting topic for file "${file.original_filename}":`, error);
        // Continue with other files even if one fails
      }
    }

    // Clear topic_id from the files after deletion
    set((state) => ({
      extractedFiles: state.extractedFiles.map((f) =>
        fileIds.includes(f.id) ? { ...f, topic_id: undefined } : f,
      ),
    }));
  },

  // Error Handling
  setError: (error: string | null) => {
    set({ error });
  },

  clearError: () => {
    set({ error: null });
  },

  // Reset
  reset: () => {
    set({
      isExtractionPopupOpen: false,
      selectedFile: null,
      showConfirmDiscard: false,
      isExtracting: false,
      extractionProgress: 0,
      extractedFiles: [],
      currentExtractionStep: 'upload',
      error: null,
    });
  },
}));
