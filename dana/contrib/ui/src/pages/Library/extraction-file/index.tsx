import { useRef, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { useExtractionFileStore } from '@/stores/extraction-file-store';
import FileIcon from '@/components/file-icon';
import { IconLoader2, IconUpload } from '@tabler/icons-react';
import { Check } from 'iconoir-react';
import { ExtractedFile } from './extracted-file';
import { cn } from '@/lib/utils';
import { useDeepExtraction } from './hooks/useDeepExtraction';

interface ExtractionFilePopupProps {
  onSaveCompleted?: () => void;
}

export const ExtractionFilePopup = ({ onSaveCompleted }: ExtractionFilePopupProps) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const {
    isExtractionPopupOpen,
    selectedFile,
    extractedFiles,
    isExtracting,
    currentExtractionStep,
    showConfirmDiscard,
    closeExtractionPopup,
    setSelectedFile,
    addFile,
    setShowConfirmDiscard,
    saveAndFinish,
    clearFiles,
    setOnSaveCompletedCallback,
  } = useExtractionFileStore();

  // Get deep extraction state for the selected file
  const { isDeepExtracting } = useDeepExtraction(selectedFile);

  // Set the callback when component mounts
  useEffect(() => {
    setOnSaveCompletedCallback(onSaveCompleted);
    // Cleanup: remove callback when component unmounts
    return () => setOnSaveCompletedCallback(undefined);
  }, [onSaveCompleted]); // Remove setOnSaveCompletedCallback from dependencies

  // Determine if buttons should be disabled (during extraction or deep extraction)
  const isDisabled = isExtracting || isDeepExtracting;

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      Array.from(files).forEach((file) => {
        addFile(file);
      });
    }
    // Reset the input
    event.target.value = '';
  };

  const handleFileUpload = (files: File[]) => {
    files.forEach((file) => {
      addFile(file);
    });
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleSaveAndFinish = async () => {
    await saveAndFinish();
  };

  const handleDeleteFile = async () => {
    // Clear the files (this will also delete any topics)
    await clearFiles();
    setShowConfirmDiscard(false);
  };

  // Update current file index when selected file changes
  const handleFileSelect = (file: any) => {
    console.log('[ExtractionPopup] File selected:', file);
    console.log('[ExtractionPopup] File documents:', file?.documents);
    console.log('[ExtractionPopup] File documents length:', file?.documents?.length);
    setSelectedFile(file);
  };

  return (
    <>
      <Dialog open={isExtractionPopupOpen} onOpenChange={closeExtractionPopup}>
        <DialogContent
          className="flex flex-col gap-0 rounded-none w-[100vw] max-w-[100vw] min-w-[100vw] h-full max-h-[100vh] pb-0"
          onOpenAutoFocus={(e) => e.preventDefault()}
          onInteractOutside={(e) => e.preventDefault()}
        >
          <DialogHeader>
            <DialogTitle>Deep Extract</DialogTitle>
            <DialogDescription className="text-sm text-gray-600">
              Process and extract content from your files
            </DialogDescription>
          </DialogHeader>

          <div className="flex flex-1 gap-2 py-2 w-full min-h-0">
            {/* Uploaded files */}
            <div className="flex flex-col min-w-[300px] max-w-[300px] border-t border-x border-gray-200 rounded-t-lg">
              <div className="flex flex-col gap-2 p-4">
                <div className="flex justify-between items-center">
                  <span className="font-semibold text-gray-600">
                    Uploaded Files ({extractedFiles.length ?? 0})
                  </span>
                  {/* <Button
                    variant="outline"
                    size="sm"
                    onClick={handleUploadClick}
                    disabled={isDisabled}
                  >
                    <IconUpload className="mr-2 w-4 h-4" />
                    Add Files
                  </Button> */}
                </div>
                <span className="text-sm text-gray-500">
                  Enable deep extraction for better content analysis
                </span>
              </div>
              <div className="flex overflow-y-auto flex-col flex-1 min-h-0 scrollbar-hide">
                {extractedFiles.map((file) => (
                  <div
                    onClick={() => handleFileSelect(file)}
                    key={file.id}
                    className={cn(
                      'flex w-full gap-2 p-4 border-b first:border-t dark:border-gray-300 cursor-pointer',
                      selectedFile?.id === file?.id && 'bg-gray-50',
                    )}
                  >
                    <div className="flex gap-2 w-[92%]">
                      <div className="flex justify-center items-center size-6 flex-1">
                        <FileIcon
                          className="size-6"
                          ext={file?.original_filename?.split('.').pop()}
                        />
                      </div>
                      <div className="flex flex-col gap-1 w-[90%] overflow-ellipsis">
                        <span className="text-sm font-medium text-gray-900 truncate block max-w-[90%]">
                          {file?.original_filename}
                        </span>
                        <span className="text-xs text-gray-500">
                          {file.status === 'uploading'
                            ? 'Uploading...'
                            : file.status === 'extracting'
                              ? 'Extracting...'
                              : file.status === 'ready'
                                ? 'Extraction complete'
                                : 'Ready for extraction'}
                        </span>
                      </div>
                    </div>

                    <div className="flex justify-center items-center size-6">
                      {(file.status === 'uploading' || file.status === 'extracting') && (
                        <IconLoader2 className="animate-spin size-4 text-brand-700" />
                      )}
                      {file.status === 'ready' && (
                        <div className="flex justify-center items-center bg-green-500 rounded-full size-4">
                          <Check className="text-white size-3" strokeWidth={3} />
                        </div>
                      )}
                      {!file.status && (
                        <div className="flex justify-center items-center bg-gray-400 rounded-full size-4">
                          <Check className="text-white size-3" strokeWidth={3} />
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Extracted file */}
            <div className="flex flex-col flex-1 gap-2 px-4 min-h-0">
              <ExtractedFile selectedFile={selectedFile ?? extractedFiles[0]} onFileUpload={handleFileUpload} />
            </div>
          </div>

          <div className="flex flex-col gap-4 p-4 border-t border-gray-200 dark:border-gray-300">
            {/* Action buttons */}
            <div className="flex gap-2 justify-end">
              <Button
                onClick={() => setShowConfirmDiscard(true)}
                variant="outline"
                disabled={isDisabled}
              >
                Discard
              </Button>
              <Button
                disabled={isDisabled || extractedFiles.length === 0}
                onClick={handleSaveAndFinish}
              >
                {currentExtractionStep === 'saving' && (
                  <IconLoader2 className="mr-2 animate-spin size-4" />
                )}
                {currentExtractionStep === 'saving' ? 'Saving...' : 'Save & Finish'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Hidden file input for upload */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        onChange={handleFileChange}
        style={{ display: 'none' }}
        accept="*/*"
      />

      {/* Confirm Discard Dialog */}
      <Dialog open={showConfirmDiscard} onOpenChange={setShowConfirmDiscard}>
        <DialogContent
          className="max-w-[400px]"
          onOpenAutoFocus={(e) => e.preventDefault()}
          onInteractOutside={(e) => e.preventDefault()}
        >
          <DialogHeader>
            <DialogTitle>Discard Files</DialogTitle>
            <DialogDescription className="text-sm text-gray-600">
              Are you sure you want to discard all uploaded files? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <div className="flex gap-2 justify-end">
            <Button variant="secondary" onClick={() => setShowConfirmDiscard(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDeleteFile}>
              Discard
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default ExtractionFilePopup;
