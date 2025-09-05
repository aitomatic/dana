import { create } from 'zustand';
import { apiService } from '@/lib/api';
import type {
  DocumentRead,
  DocumentUpdate,
  DocumentFilters,
  DocumentUploadData,
  DocumentState,
} from '@/types/document';

export interface DocumentStore extends DocumentState {
  // Actions
  // Document CRUD Operations
  fetchDocuments: (filters?: DocumentFilters) => Promise<void>;
  fetchDocument: (documentId: number) => Promise<void>;
  uploadDocument: (uploadData: DocumentUploadData) => Promise<void>;
  updateDocument: (documentId: number, document: DocumentUpdate) => Promise<void>;
  deleteDocument: (documentId: number) => Promise<void>;
  downloadDocument: (documentId: number) => Promise<void>;

  // Selection and UI Actions
  setSelectedDocument: (document: DocumentRead | null) => void;
  setUploadProgress: (progress: number) => void;
  clearError: () => void;
  reset: () => void;
}

export const useDocumentStore = create<DocumentStore>((set, get) => ({
  // Initial State
  documents: [],
  selectedDocument: null,
  isLoading: false,
  isCreating: false,
  isUpdating: false,
  isDeleting: false,
  isUploading: false,
  isDownloading: false,
  error: null,
  total: 0,
  skip: 0,
  limit: 100,
  uploadProgress: 0,

  // Actions
  fetchDocuments: async (filters?: DocumentFilters) => {
    console.log('🌐 Document store: fetchDocuments called with filters:', filters);
    set({ isLoading: true, error: null });

    try {
      const documents = await apiService.getDocuments(filters);
      console.log('📥 Document store: Received documents from API:', {
        count: documents?.length || 0,
        filters,
        documents: documents?.map((d) => ({
          id: d.id,
          name: d.original_filename,
          agent_id: d.agent_id,
        })),
      });

      set({
        documents,
        isLoading: false,
        skip: filters?.skip || 0,
        limit: filters?.limit || 100,
        total: documents.length, // Note: API doesn't return total count, using array length
      });

      console.log('✅ Document store: Documents updated successfully');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch documents';
      console.error('❌ Document store: Error fetching documents:', error);
      set({
        documents: [],
        isLoading: false,
        error: errorMessage,
      });
    }
  },

  fetchDocument: async (documentId: number) => {
    set({ isLoading: true, error: null });

    try {
      const document = await apiService.getDocument(documentId);
      set({
        selectedDocument: document,
        isLoading: false,
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch document';
      set({
        selectedDocument: null,
        isLoading: false,
        error: errorMessage,
      });
    }
  },

  uploadDocument: async (uploadData: DocumentUploadData) => {
    set({ isUploading: true, uploadProgress: 0, error: null });

    try {
      const newDocument = await apiService.uploadDocument(uploadData);
      set((state) => ({
        documents: [...state.documents, newDocument],
        isUploading: false,
        uploadProgress: 100,
      }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to upload document';
      set({
        isUploading: false,
        uploadProgress: 0,
        error: errorMessage,
      });
    }
  },

  updateDocument: async (documentId: number, document: DocumentUpdate) => {
    set({ isUpdating: true, error: null });

    try {
      const updatedDocument = await apiService.updateDocument(documentId, document);
      set((state) => ({
        documents: state.documents.map((d) => (d.id === documentId ? updatedDocument : d)),
        selectedDocument:
          state.selectedDocument?.id === documentId ? updatedDocument : state.selectedDocument,
        isUpdating: false,
      }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update document';
      set({
        isUpdating: false,
        error: errorMessage,
      });
    }
  },

  deleteDocument: async (documentId: number) => {
    set({ isDeleting: true, error: null });

    try {
      await apiService.deleteDocument(documentId);
      set((state) => ({
        documents: state.documents.filter((d) => d.id !== documentId),
        selectedDocument: state.selectedDocument?.id === documentId ? null : state.selectedDocument,
        isDeleting: false,
      }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete document';
      set({
        isDeleting: false,
        error: errorMessage,
      });
    }
  },

  downloadDocument: async (documentId: number) => {
    set({ isDownloading: true, error: null });

    try {
      const blob = await apiService.downloadDocument(documentId);

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;

      // Get filename from selected document or use default
      const doc = get().selectedDocument || get().documents.find((d) => d.id === documentId);
      a.download = doc?.original_filename || 'document';

      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      set({ isDownloading: false });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to download document';
      set({
        isDownloading: false,
        error: errorMessage,
      });
    }
  },

  setSelectedDocument: (document: DocumentRead | null) => {
    set({ selectedDocument: document });
  },

  setUploadProgress: (progress: number) => {
    set({ uploadProgress: progress });
  },

  clearError: () => {
    set({ error: null });
  },

  reset: () => {
    set({
      documents: [],
      selectedDocument: null,
      isLoading: false,
      isCreating: false,
      isUpdating: false,
      isDeleting: false,
      isUploading: false,
      isDownloading: false,
      error: null,
      total: 0,
      skip: 0,
      limit: 100,
      uploadProgress: 0,
    });
  },
}));
