/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState, useEffect, useRef } from 'react';
import { apiService } from '@/lib/api';

interface BlobUrlState {
  blobUrl: string | null;
  loading: boolean;
  error: string | null;
}

export const useDocumentPreview = (selectedFile: any): BlobUrlState => {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const lastFileRef = useRef<any>(null);
  const currentBlobUrlRef = useRef<string | null>(null);

  const createBlobUrlFromFile = (file: File): void => {
    if (!file) return;
    try {
      setLoading(true);
      setError(null);
      const url = URL.createObjectURL(file);
      setBlobUrl(url);
      currentBlobUrlRef.current = url;
      setLoading(false);
    } catch (err) {
      console.error('Error creating blob URL:', err);
      setError('Failed to load file');
      setLoading(false);
    }
  };

  const createBlobUrlFromDocument = async (documentId: number): Promise<void> => {
    try {
      setLoading(true);
      setError(null);

      // Download the document
      const blob = await apiService.downloadDocument(documentId);

      // Create blob URL
      const url = URL.createObjectURL(blob);
      setBlobUrl(url);
      currentBlobUrlRef.current = url;
      setLoading(false);
    } catch (err) {
      console.error('Error downloading document:', err);
      setError('Failed to load document');
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedFile && selectedFile !== lastFileRef.current) {
      // Clean up previous blob URL
      if (currentBlobUrlRef.current) {
        URL.revokeObjectURL(currentBlobUrlRef.current);
        setBlobUrl(null);
        currentBlobUrlRef.current = null;
      }

      // Handle different file types
      if (selectedFile.file && selectedFile.file instanceof File && selectedFile.file.size > 0) {
        // Regular File object (from upload) with actual content
        createBlobUrlFromFile(selectedFile.file);
      } else if (selectedFile.document_id && selectedFile.original_filename) {
        // Existing document from library - always download
        createBlobUrlFromDocument(selectedFile.document_id);
      } else {
        setError('Invalid file data');
        setLoading(false);
      }

      lastFileRef.current = selectedFile;
    }
  }, [selectedFile]);

  // Cleanup effect for blob URL
  useEffect(() => {
    return () => {
      if (currentBlobUrlRef.current) {
        URL.revokeObjectURL(currentBlobUrlRef.current);
      }
    };
  }, []);

  return { blobUrl, loading, error };
};
