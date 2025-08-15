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
  currentExtractionStep: 'upload' | 'extract' | 'review' | 'complete';

  // Error State
  error: string | null;

  // Actions
  // UI Actions
  openExtractionPopup: () => void;
  closeExtractionPopup: () => void;
  setSelectedFile: (file: ExtractionFile | null) => void;
  setShowConfirmDiscard: (show: boolean) => void;

  // File Management
  addFile: (file: File) => void;
  removeFile: (fileId: string) => void;
  clearFiles: () => void;

  // Extraction Process
  startExtraction: () => Promise<void>;
  updateExtractionProgress: (progress: number) => void;
  setExtractionStep: (step: ExtractionFileState['currentExtractionStep']) => void;
  completeExtraction: () => void;

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
  error: null,

  // UI Actions
  openExtractionPopup: () => {
    set({
      isExtractionPopupOpen: true,
      currentExtractionStep: 'upload',
      error: null,
    });
  },

  closeExtractionPopup: () => {
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

          const extractParams = { document_id: documentId };
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

  removeFile: (fileId: string) => {
    set((state) => ({
      extractedFiles: state.extractedFiles.filter((f) => f.id !== fileId),
      selectedFile: state.selectedFile?.id === fileId ? null : state.selectedFile,
    }));
  },

  clearFiles: () => {
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
