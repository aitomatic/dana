import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useDocumentStore } from '../document-store';
import type {
  DocumentRead,
  DocumentUpdate,
  DocumentFilters,
  DocumentUploadData,
} from '@/types/document';

// Mock the API service
vi.mock('@/lib/api', () => ({
  apiService: {
    getDocuments: vi.fn(),
    getDocument: vi.fn(),
    uploadDocument: vi.fn(),
    updateDocument: vi.fn(),
    deleteDocument: vi.fn(),
    downloadDocument: vi.fn(),
  },
}));

import { apiService } from '@/lib/api';

// Mock DOM methods
Object.defineProperty(window, 'URL', {
  value: {
    createObjectURL: vi.fn(() => 'blob:mock-url'),
    revokeObjectURL: vi.fn(),
  },
  writable: true,
});

Object.defineProperty(document, 'createElement', {
  value: vi.fn(() => ({
    href: '',
    download: '',
    click: vi.fn(),
  })),
  writable: true,
});

Object.defineProperty(document.body, 'appendChild', {
  value: vi.fn(),
  writable: true,
});

Object.defineProperty(document.body, 'removeChild', {
  value: vi.fn(),
  writable: true,
});

describe('Document Store', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset the store state
    useDocumentStore.getState().reset();
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = useDocumentStore.getState();

      expect(state.documents).toEqual([]);
      expect(state.selectedDocument).toBeNull();
      expect(state.isLoading).toBe(false);
      expect(state.isCreating).toBe(false);
      expect(state.isUpdating).toBe(false);
      expect(state.isDeleting).toBe(false);
      expect(state.isUploading).toBe(false);
      expect(state.isDownloading).toBe(false);
      expect(state.error).toBeNull();
      expect(state.total).toBe(0);
      expect(state.skip).toBe(0);
      expect(state.limit).toBe(100);
      expect(state.uploadProgress).toBe(0);
    });
  });

  describe('fetchDocuments', () => {
    it('should fetch documents successfully', async () => {
      const mockDocuments: DocumentRead[] = [
        {
          id: 1,
          original_filename: 'test1.pdf',
          filename: 'uuid-test1.pdf',
          file_size: 1024,
          mime_type: 'application/pdf',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        {
          id: 2,
          original_filename: 'test2.pdf',
          filename: 'uuid-test2.pdf',
          file_size: 2048,
          mime_type: 'application/pdf',
          created_at: '2024-01-02T00:00:00Z',
          updated_at: '2024-01-02T00:00:00Z',
        },
      ];

      (apiService.getDocuments as any).mockResolvedValue(mockDocuments);

      await useDocumentStore.getState().fetchDocuments();

      expect(apiService.getDocuments).toHaveBeenCalledWith(undefined);
      expect(useDocumentStore.getState().documents).toEqual(mockDocuments);
      expect(useDocumentStore.getState().isLoading).toBe(false);
      expect(useDocumentStore.getState().error).toBeNull();
      expect(useDocumentStore.getState().total).toBe(2);
    });

    it('should fetch documents with filters', async () => {
      const mockDocuments: DocumentRead[] = [
        {
          id: 1,
          original_filename: 'filtered.pdf',
          filename: 'uuid-filtered.pdf',
          file_size: 1024,
          mime_type: 'application/pdf',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ];

      const filters: DocumentFilters = {
        skip: 0,
        limit: 10,
        mime_type: 'application/pdf',
      };

      (apiService.getDocuments as any).mockResolvedValue(mockDocuments);

      await useDocumentStore.getState().fetchDocuments(filters);

      expect(apiService.getDocuments).toHaveBeenCalledWith(filters);
      expect(useDocumentStore.getState().documents).toEqual(mockDocuments);
      expect(useDocumentStore.getState().skip).toBe(0);
      expect(useDocumentStore.getState().limit).toBe(10);
    });

    it('should handle fetch documents error', async () => {
      const error = new Error('Failed to fetch documents');
      (apiService.getDocuments as any).mockRejectedValue(error);

      await useDocumentStore.getState().fetchDocuments();

      expect(useDocumentStore.getState().documents).toEqual([]);
      expect(useDocumentStore.getState().isLoading).toBe(false);
      expect(useDocumentStore.getState().error).toBe('Failed to fetch documents');
    });
  });

  describe('fetchDocument', () => {
    it('should fetch single document successfully', async () => {
      const mockDocument: DocumentRead = {
        id: 1,
        original_filename: 'test.pdf',
        filename: 'uuid-test.pdf',
        file_size: 1024,
        mime_type: 'application/pdf',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      (apiService.getDocument as any).mockResolvedValue(mockDocument);

      await useDocumentStore.getState().fetchDocument(1);

      expect(apiService.getDocument).toHaveBeenCalledWith(1);
      expect(useDocumentStore.getState().selectedDocument).toEqual(mockDocument);
      expect(useDocumentStore.getState().isLoading).toBe(false);
      expect(useDocumentStore.getState().error).toBeNull();
    });

    it('should handle fetch document error', async () => {
      const error = new Error('Failed to fetch document');
      (apiService.getDocument as any).mockRejectedValue(error);

      await useDocumentStore.getState().fetchDocument(1);

      expect(useDocumentStore.getState().selectedDocument).toBeNull();
      expect(useDocumentStore.getState().isLoading).toBe(false);
      expect(useDocumentStore.getState().error).toBe('Failed to fetch document');
    });
  });

  describe('uploadDocument', () => {
    it('should upload document successfully', async () => {
      const mockUploadedDocument: DocumentRead = {
        id: 3,
        original_filename: 'uploaded.pdf',
        filename: 'uuid-uploaded.pdf',
        file_size: 3072,
        mime_type: 'application/pdf',
        created_at: '2024-01-03T00:00:00Z',
        updated_at: '2024-01-03T00:00:00Z',
      };

      const uploadData: DocumentUploadData = {
        file: new File(['test'], 'test.pdf', { type: 'application/pdf' }),
        title: 'Test Document',
      };

      (apiService.uploadDocument as any).mockResolvedValue(mockUploadedDocument);

      // Set initial documents
      useDocumentStore.setState({
        documents: [
          {
            id: 1,
            original_filename: 'existing.pdf',
            filename: 'uuid-existing.pdf',
            file_size: 1024,
            mime_type: 'application/pdf',
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
        ],
      });

      await useDocumentStore.getState().uploadDocument(uploadData);

      expect(apiService.uploadDocument).toHaveBeenCalledWith(uploadData);
      expect(useDocumentStore.getState().documents).toContainEqual(mockUploadedDocument);
      expect(useDocumentStore.getState().isUploading).toBe(false);
      expect(useDocumentStore.getState().error).toBeNull();
      expect(useDocumentStore.getState().uploadProgress).toBe(100);
    });

    it('should handle upload document error', async () => {
      const error = new Error('Failed to upload document');
      const uploadData: DocumentUploadData = {
        file: new File(['test'], 'test.pdf', { type: 'application/pdf' }),
        title: 'Test Document',
      };

      (apiService.uploadDocument as any).mockRejectedValue(error);

      await useDocumentStore.getState().uploadDocument(uploadData);

      expect(useDocumentStore.getState().documents).toEqual([]);
      expect(useDocumentStore.getState().isUploading).toBe(false);
      expect(useDocumentStore.getState().error).toBe('Failed to upload document');
    });
  });

  describe('updateDocument', () => {
    it('should update document successfully', async () => {
      const mockUpdatedDocument: DocumentRead = {
        id: 1,
        original_filename: 'updated.pdf',
        filename: 'uuid-test.pdf',
        file_size: 1024,
        mime_type: 'application/pdf',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      const updateData: DocumentUpdate = { original_filename: 'updated.pdf' };

      (apiService.updateDocument as any).mockResolvedValue(mockUpdatedDocument);

      // Set initial documents
      useDocumentStore.setState({
        documents: [
          {
            id: 1,
            original_filename: 'original.pdf',
            filename: 'uuid-test.pdf',
            file_size: 1024,
            mime_type: 'application/pdf',
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
        ],
      });

      await useDocumentStore.getState().updateDocument(1, updateData);

      expect(apiService.updateDocument).toHaveBeenCalledWith(1, updateData);
      expect(useDocumentStore.getState().documents[0]).toEqual(mockUpdatedDocument);
      expect(useDocumentStore.getState().isUpdating).toBe(false);
      expect(useDocumentStore.getState().error).toBeNull();
    });

    it('should handle update document error', async () => {
      const error = new Error('Failed to update document');
      const updateData: DocumentUpdate = { original_filename: 'updated.pdf' };

      (apiService.updateDocument as any).mockRejectedValue(error);

      await useDocumentStore.getState().updateDocument(1, updateData);

      expect(useDocumentStore.getState().isUpdating).toBe(false);
      expect(useDocumentStore.getState().error).toBe('Failed to update document');
    });
  });

  describe('deleteDocument', () => {
    it('should delete document successfully', async () => {
      (apiService.deleteDocument as any).mockResolvedValue({ message: 'Document deleted' });

      // Set initial documents
      useDocumentStore.setState({
        documents: [
          {
            id: 1,
            original_filename: 'to-delete.pdf',
            filename: 'uuid-to-delete.pdf',
            file_size: 1024,
            mime_type: 'application/pdf',
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
          {
            id: 2,
            original_filename: 'keep.pdf',
            filename: 'uuid-keep.pdf',
            file_size: 2048,
            mime_type: 'application/pdf',
            created_at: '2024-01-02T00:00:00Z',
            updated_at: '2024-01-02T00:00:00Z',
          },
        ],
      });

      await useDocumentStore.getState().deleteDocument(1);

      expect(apiService.deleteDocument).toHaveBeenCalledWith(1);
      expect(useDocumentStore.getState().documents).toHaveLength(1);
      expect(useDocumentStore.getState().documents[0].id).toBe(2);
      expect(useDocumentStore.getState().isDeleting).toBe(false);
      expect(useDocumentStore.getState().error).toBeNull();
    });

    it('should handle delete document error', async () => {
      const error = new Error('Failed to delete document');
      (apiService.deleteDocument as any).mockRejectedValue(error);

      await useDocumentStore.getState().deleteDocument(1);

      expect(useDocumentStore.getState().isDeleting).toBe(false);
      expect(useDocumentStore.getState().error).toBe('Failed to delete document');
    });
  });

  describe('downloadDocument', () => {
    it('should download document successfully', async () => {
      const mockBlob = new Blob(['test content'], { type: 'application/pdf' });
      (apiService.downloadDocument as any).mockResolvedValue(mockBlob);

      // Set selected document
      useDocumentStore.setState({
        selectedDocument: {
          id: 1,
          original_filename: 'test.pdf',
          filename: 'uuid-test.pdf',
          file_size: 1024,
          mime_type: 'application/pdf',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      });

      await useDocumentStore.getState().downloadDocument(1);

      expect(apiService.downloadDocument).toHaveBeenCalledWith(1);
      expect(useDocumentStore.getState().isDownloading).toBe(false);
      expect(useDocumentStore.getState().error).toBeNull();
    });

    it('should handle download document error', async () => {
      const error = new Error('Failed to download document');
      (apiService.downloadDocument as any).mockRejectedValue(error);

      await useDocumentStore.getState().downloadDocument(1);

      expect(useDocumentStore.getState().isDownloading).toBe(false);
      expect(useDocumentStore.getState().error).toBe('Failed to download document');
    });
  });

  describe('UI Actions', () => {
    it('should set selected document', () => {
      const mockDocument: DocumentRead = {
        id: 1,
        original_filename: 'test.pdf',
        filename: 'uuid-test.pdf',
        file_size: 1024,
        mime_type: 'application/pdf',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      useDocumentStore.getState().setSelectedDocument(mockDocument);

      expect(useDocumentStore.getState().selectedDocument).toEqual(mockDocument);
    });

    it('should clear selected document', () => {
      // Set selected document first
      useDocumentStore.setState({
        selectedDocument: {
          id: 1,
          original_filename: 'test.pdf',
          filename: 'uuid-test.pdf',
          file_size: 1024,
          mime_type: 'application/pdf',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      });

      expect(useDocumentStore.getState().selectedDocument).toBeTruthy();

      useDocumentStore.getState().setSelectedDocument(null);

      expect(useDocumentStore.getState().selectedDocument).toBeNull();
    });

    it('should set upload progress', () => {
      expect(useDocumentStore.getState().uploadProgress).toBe(0);

      useDocumentStore.getState().setUploadProgress(50);

      expect(useDocumentStore.getState().uploadProgress).toBe(50);
    });

    it('should clear error', () => {
      // Set an error first
      useDocumentStore.setState({ error: 'Test error' });

      expect(useDocumentStore.getState().error).toBe('Test error');

      useDocumentStore.getState().clearError();

      expect(useDocumentStore.getState().error).toBeNull();
    });
  });

  describe('Reset', () => {
    it('should reset store to initial state', () => {
      // Modify state
      useDocumentStore.setState({
        documents: [
          {
            id: 1,
            original_filename: 'test.pdf',
            filename: 'uuid-test.pdf',
            file_size: 1024,
            mime_type: 'application/pdf',
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
        ],
        selectedDocument: {
          id: 1,
          original_filename: 'test.pdf',
          filename: 'uuid-test.pdf',
          file_size: 1024,
          mime_type: 'application/pdf',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        isLoading: true,
        isCreating: true,
        isUpdating: true,
        isDeleting: true,
        isUploading: true,
        isDownloading: true,
        error: 'Test error',
        total: 1,
        skip: 10,
        limit: 50,
        uploadProgress: 75,
      });

      // Reset
      useDocumentStore.getState().reset();

      expect(useDocumentStore.getState().documents).toEqual([]);
      expect(useDocumentStore.getState().selectedDocument).toBeNull();
      expect(useDocumentStore.getState().isLoading).toBe(false);
      expect(useDocumentStore.getState().isCreating).toBe(false);
      expect(useDocumentStore.getState().isUpdating).toBe(false);
      expect(useDocumentStore.getState().isDeleting).toBe(false);
      expect(useDocumentStore.getState().isUploading).toBe(false);
      expect(useDocumentStore.getState().isDownloading).toBe(false);
      expect(useDocumentStore.getState().error).toBeNull();
      expect(useDocumentStore.getState().total).toBe(0);
      expect(useDocumentStore.getState().skip).toBe(0);
      expect(useDocumentStore.getState().limit).toBe(100);
      expect(useDocumentStore.getState().uploadProgress).toBe(0);
    });
  });

  describe('Integration Tests', () => {
    it('should handle complete document workflow', async () => {
      const mockDocuments: DocumentRead[] = [
        {
          id: 1,
          original_filename: 'test1.pdf',
          filename: 'uuid-test1.pdf',
          file_size: 1024,
          mime_type: 'application/pdf',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        {
          id: 2,
          original_filename: 'test2.pdf',
          filename: 'uuid-test2.pdf',
          file_size: 2048,
          mime_type: 'application/pdf',
          created_at: '2024-01-02T00:00:00Z',
          updated_at: '2024-01-02T00:00:00Z',
        },
      ];

      (apiService.getDocuments as any).mockResolvedValue(mockDocuments);

      // Fetch documents
      await useDocumentStore.getState().fetchDocuments();

      expect(useDocumentStore.getState().documents).toEqual(mockDocuments);

      // Select a document
      useDocumentStore.getState().setSelectedDocument(mockDocuments[0]);

      expect(useDocumentStore.getState().selectedDocument).toEqual(mockDocuments[0]);

      // Update document
      const updateData: DocumentUpdate = { original_filename: 'updated.pdf' };
      const updatedDocument = { ...mockDocuments[0], original_filename: 'updated.pdf' };

      (apiService.updateDocument as any).mockResolvedValue(updatedDocument);

      await useDocumentStore.getState().updateDocument(1, updateData);

      expect(useDocumentStore.getState().documents[0]).toEqual(updatedDocument);
      expect(useDocumentStore.getState().selectedDocument).toEqual(updatedDocument);

      // Delete document
      (apiService.deleteDocument as any).mockResolvedValue({ message: 'Deleted' });

      await useDocumentStore.getState().deleteDocument(1);

      expect(useDocumentStore.getState().documents).toHaveLength(1);
      expect(useDocumentStore.getState().selectedDocument).toBeNull();
    });
  });
});
