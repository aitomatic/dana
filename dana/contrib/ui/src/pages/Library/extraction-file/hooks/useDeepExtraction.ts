import { useExtractionFileStore } from '@/stores/extraction-file-store';

export const useDeepExtraction = (selectedFile: any) => {
  const { deepExtract, error } = useExtractionFileStore();

  const handleDeepExtract = async (
    useDeepExtraction: boolean = true,
    prompt?: string,
  ): Promise<void> => {
    if (!selectedFile?.id) {
      return;
    }

    await deepExtract(selectedFile.id, useDeepExtraction, prompt);
  };

  const handleDeepExtractWithPrompt = (prompt: string): void => {
    handleDeepExtract(true, prompt);
  };

  const handleDeepExtractWithoutPrompt = (): void => {
    handleDeepExtract(true);
  };

  return {
    isDeepExtracting: selectedFile?.status === 'extracting',
    isDeepExtracted: selectedFile?.is_deep_extracted || false,
    deepExtractedDocuments: selectedFile?.documents || [],
    deepExtractionError: error,
    handleDeepExtractWithPrompt,
    handleDeepExtractWithoutPrompt,
  };
};
