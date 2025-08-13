import { create } from 'zustand';

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
    [key: string]: any;
  }>;
  created_at?: string;
  updated_at?: string;
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
    };

    set((state) => ({
      extractedFiles: [...state.extractedFiles, newExtractionFile],
      selectedFile: state.selectedFile || newExtractionFile,
    }));
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
      // Simulate extraction process
      for (let i = 0; i <= 100; i += 10) {
        await new Promise((resolve) => setTimeout(resolve, 200));
        set({ extractionProgress: i });
      }

      // Update files with extraction status
      set((state) => ({
        extractedFiles: state.extractedFiles.map((file) => ({
          ...file,
          is_deep_extracted: true,
          documents: [
            {
              text: `Extracted content from ${file.original_filename}...`,
            },
          ],
          updated_at: new Date().toISOString(),
        })),
        currentExtractionStep: 'review',
        isExtracting: false,
        extractionProgress: 100,
      }));
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
