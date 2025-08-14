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
    if (!selectedFile?.file) return;

    setError(null);

    startTransition(async () => {
      try {
        // 1) Upload file to server uploads directory
        const uploaded = await apiService.uploadDocumentRaw(selectedFile.file);

        // 2) Build server-side file path for deep extraction
        const serverFilePath = `uploads/${uploaded.filename}`;

        // 3) Call deep extract endpoint
        const response = await apiService.deepExtract({
          file_path: serverFilePath,
          prompt: usePrompt ? prompt : undefined,
        });

        // 4) Map pages to our document structure and unwrap fenced markdown
        const docs = (response.file_object?.pages || []).map((p) => {
          console.log('[useDeepExtraction] Processing page:', {
            page_number: p.page_number,
            page_content_length: p.page_content?.length,
            page_content_preview: p.page_content?.substring(0, 100),
          });
          return {
            text: unwrapMarkdownFences(p.page_content),
            page_content: p.page_content,
            page_number: p.page_number,
          };
        });
        console.log('[useDeepExtraction] Final docs with page_content:', docs);
        console.log(
          '[useDeepExtraction] First doc page_content:',
          docs[0]?.page_content?.substring(0, 200),
        );
        setDeepExtractedDocuments(docs);
        setIsDeepExtracted(true);

        if (selectedFile?.id) {
          updateDocument(selectedFile.id, {} as any);
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
