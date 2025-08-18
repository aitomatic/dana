import { useState, useTransition } from 'react';
import { useDocumentStore } from '@/stores/document-store';
import { apiService } from '@/lib/api';

interface Document {
  text: string;
  page_content?: string;
  page_number?: number;
  [key: string]: any;
}

function unwrapMarkdownFences(content: string | undefined): string {
  if (!content) return '';
  const fencePattern = /^```(?:markdown|md)?\n([\s\S]*?)\n```\s*$/i;
  const match = content.match(fencePattern);
  return match ? match[1] : content;
}

export const useDeepExtraction = (selectedFile: any) => {
  const { updateDocument } = useDocumentStore();
  const [isDeepExtracting, startTransition] = useTransition();
  const [deepExtractedDocuments, setDeepExtractedDocuments] = useState<Document[]>([]);
  const [isDeepExtracted, setIsDeepExtracted] = useState<boolean>(
    selectedFile?.is_deep_extracted || false,
  );
  const [prompt, setPrompt] = useState<string>(selectedFile?.prompt || '');
  const [error, setError] = useState<string | null>(null);

  const handleDeepExtract = async (usePrompt: boolean = true): Promise<void> => {
    if (!selectedFile?.document_id) {
      setError('No document ID available for extraction');
      return;
    }

    setError(null);

    startTransition(async () => {
      try {
        const response = await apiService.deepExtract({
          document_id: selectedFile.document_id,
          prompt: usePrompt ? prompt : undefined,
          use_deep_extraction: true, // Enable deep extraction by default
        });

        // Map pages to our document structure and unwrap fenced markdown
        const docs = (response.file_object?.pages || []).map((p) => {
          return {
            text: unwrapMarkdownFences(p.page_content),
            page_content: p.page_content,
            page_number: p.page_number,
          };
        });
        setDeepExtractedDocuments(docs);
        setIsDeepExtracted(true);

        if (selectedFile?.document_id) {
          updateDocument(selectedFile.document_id, {} as any);
        }
      } catch (e: any) {
        setError(e?.message || 'Deep extraction failed');
        setIsDeepExtracted(false);
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
    error,
    handleDeepExtractWithPrompt,
    handleDeepExtractWithoutPrompt,
  };
};
