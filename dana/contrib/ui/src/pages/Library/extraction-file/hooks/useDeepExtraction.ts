import { useState, useTransition } from 'react';
import { useDocumentStore } from '@/stores/document-store';

interface Document {
  text: string;
  [key: string]: any;
}

export const useDeepExtraction = (selectedFile: any) => {
  const { updateDocument } = useDocumentStore();
  const [isDeepExtracting, startTransition] = useTransition();
  const [deepExtractedDocuments, setDeepExtractedDocuments] = useState<Document[]>([]);
  const [isDeepExtracted, setIsDeepExtracted] = useState<boolean>(
    selectedFile?.is_deep_extracted || false,
  );
  const [prompt, setPrompt] = useState<string>(selectedFile?.prompt || '');

  const handleDeepExtract = async (usePrompt: boolean = true): Promise<void> => {
    setIsDeepExtracted(true);

    // Update the document with deep extraction status
    if (selectedFile?.id) {
      updateDocument(selectedFile.id, {
        // Note: The document store doesn't support these fields
        // This would need to be handled by a different API endpoint
      });
    }

    startTransition(async () => {
      // Simulate deep extraction process
      // In a real implementation, this would call the deep extraction API
      console.log('Deep extraction started with prompt:', usePrompt ? prompt : 'No prompt');

      // Simulate API response
      const mockResponse = {
        documents: {
          documents: [{ text: 'Extracted content from document...' }],
        },
      };

      setDeepExtractedDocuments(mockResponse?.documents?.documents || []);

      if (selectedFile?.id) {
        updateDocument(selectedFile.id, {
          // Note: The document store doesn't support these fields
          // This would need to be handled by a different API endpoint
        });
      }
    });
  };

  const handleDeepExtractWithPrompt = (): void => {
    handleDeepExtract(true);
  };

  const handleDeepExtractWithoutPrompt = (): void => {
    handleDeepExtract(false);
  };

  return {
    isDeepExtracting,
    isDeepExtracted,
    deepExtractedDocuments,
    prompt,
    setPrompt,
    handleDeepExtractWithPrompt,
    handleDeepExtractWithoutPrompt,
  };
};
