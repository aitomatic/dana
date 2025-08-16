import { useState, useEffect, useRef } from 'react';

interface BlobUrlState {
  blobUrl: string | null;
  loading: boolean;
  error: string | null;
}

export const useFilePreview = (file: File | null): BlobUrlState => {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const lastFileRef = useRef<File | null>(null);

  const createBlobUrl = (file: File): void => {
    if (!file) return;
    try {
      setLoading(true);
      setError(null);
      const url = URL.createObjectURL(file);
      setBlobUrl(url);
      setLoading(false);
    } catch (err) {
      console.error('Error creating blob URL:', err);
      setError('Failed to load file');
      setLoading(false);
    }
  };

  useEffect(() => {
    if (file && file !== lastFileRef.current) {
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
        setBlobUrl(null);
      }
      createBlobUrl(file);
      lastFileRef.current = file;
    }
    return () => {
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
      }
    };
  }, [file, blobUrl]);

  return { blobUrl, loading, error };
};
