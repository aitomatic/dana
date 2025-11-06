/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable react-hooks/exhaustive-deps */
import { useRef, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { useExtractionFileStore, isDeepExtractionSupported } from '@/stores/extraction-file-store';
import FileIcon from '@/components/file-icon';
import { IconLoader2 } from '@tabler/icons-react';
import { Check } from 'iconoir-react';
import { ExtractedFile } from './extracted-file';
import { cn } from '@/lib/utils';
import { DuplicateFileDialog } from '@/components/duplicate-file-dialog';

// Helper function to get file status
function getFileStatus(file: any): 'uploading' | 'extracting' | 'ready' | 'error' {
  // If there's a duplicate error, it's an error state
  if (file.duplicate_error) {
    return 'error';
  }

  // If we have documents, the file is ready
  if (file.documents && file.documents.length > 0) {
    return 'ready';
  }

  // If we have a document_id but no documents yet, it's extracting
  if (file.document_id && (!file.documents || file.documents.length === 0)) {
    return 'extracting';
  }

  // If we have a file but no document_id yet, it's uploading
  if (file.file && !file.document_id) {
    return 'uploading';
  }

  // Default to ready for existing documents
  return 'ready';
}

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
    isDuplicateDialogOpen,
    duplicateFile,
    closeExtractionPopup,
    setSelectedFile,
    addFile,
    setShowConfirmDiscard,
    saveAndFinish,
    clearFiles,
    setOnSaveCompletedCallback,
    closeDuplicateDialog,
    handleDuplicateAction,
  } = useExtractionFileStore();

  // Set the callback when component mounts
  useEffect(() => {
    setOnSaveCompletedCallback(onSaveCompleted);
    // Cleanup: remove callback when component unmounts
    return () => setOnSaveCompletedCallback(undefined);
  }, [onSaveCompleted]); // Remove setOnSaveCompletedCallback from dependencies

  // Determine if buttons should be disabled (during extraction, but allow finishing during deep extraction)
  const isDisabled = isExtracting;

  // Determine if we're in review mode (viewing existing document) vs upload mode
  const isReviewMode = selectedFile?.id?.startsWith('existing-') || selectedFile?.file === null;

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
            <DialogTitle>{isReviewMode ? 'Review Document' : 'Upload Files'}</DialogTitle>
            <DialogDescription className="text-sm text-gray-600">
              {isReviewMode
                ? 'Review extracted content from the document'
                : 'File upload will be used to extract content'}
            </DialogDescription>
          </DialogHeader>

          <div className="flex flex-1 gap-2 py-2 w-full min-h-0">
            {/* Uploaded files */}
            <div className="flex flex-col min-w-[300px] max-w-[300px] border-t border-x border-gray-200 rounded-t-lg">
              <div className="flex flex-col gap-2 p-4">
                <div className="flex justify-between items-center">
                  <span className="font-semibold text-gray-600">
                    Files ({extractedFiles.length ?? 0})
                  </span>
                </div>
                <span className="text-sm text-gray-500">No file uploaded yet</span>

                {/* Deep Extraction Tip - Only show when user is actively waiting for deep extraction */}
                {selectedFile &&
                  getFileStatus(selectedFile) === 'ready' &&
                  (selectedFile.deep_extraction_status === 'running' || selectedFile.task_id) &&
                  isDeepExtractionSupported(selectedFile.original_filename) &&
                  !selectedFile.deep_extracted_documents?.length && // Don't show if already has deep extraction results
                  extractedFiles.some((f) => f.id === selectedFile.id) && (
                    <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                      <div className="flex gap-2 items-start">
                        <div className="text-xs text-blue-800">
                          <p className="font-medium">Deep extraction in progress</p>
                          <p className="mt-1">
                            The process runs in the background and may take a while. You can close
                            this dialog anytime.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
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
                      <div className="flex flex-1 justify-center items-center size-6">
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
                          {getFileStatus(file) === 'uploading'
                            ? 'Uploading...'
                            : getFileStatus(file) === 'extracting'
                              ? 'Standard extracting...'
                              : file.duplicate_error
                                ? 'Duplicate file'
                                : getFileStatus(file) === 'ready' &&
                                    (file.deep_extraction_status === 'running' || file.task_id) &&
                                    isDeepExtractionSupported(file.original_filename)
                                  ? 'Deep extracting in progress...'
                                  : getFileStatus(file) === 'ready' &&
                                      file.deep_extraction_status === 'completed' &&
                                      isDeepExtractionSupported(file.original_filename)
                                    ? 'Deep extraction complete'
                                    : getFileStatus(file) === 'ready' &&
                                        file.deep_extraction_status === 'failed' &&
                                        isDeepExtractionSupported(file.original_filename)
                                      ? 'Deep extraction failed - Standard results available'
                                      : getFileStatus(file) === 'ready'
                                        ? 'Standard extraction complete'
                                        : 'Ready for extraction'}
                        </span>
                      </div>
                    </div>

                    <div className="flex justify-center items-center size-6">
                      {/* Only show icons in upload mode, not in review mode */}
                      {!isReviewMode && (
                        <>
                          {/* Phase 1: Upload and Standard Extraction */}
                          {(getFileStatus(file) === 'uploading' ||
                            getFileStatus(file) === 'extracting') && (
                            <IconLoader2 className="animate-spin size-4 text-brand-700" />
                          )}

                          {/* Phase 2: Deep Extraction */}
                          {getFileStatus(file) === 'ready' &&
                            file.deep_extraction_status === 'running' &&
                            isDeepExtractionSupported(file.original_filename) && (
                              <IconLoader2 className="text-blue-600 animate-spin size-4" />
                            )}

                          {/* Final States */}
                          {getFileStatus(file) === 'ready' &&
                            file.deep_extraction_status === 'completed' && (
                              <div className="flex justify-center items-center bg-green-500 rounded-full size-4">
                                <Check className="text-white size-3" strokeWidth={3} />
                              </div>
                            )}
                          {getFileStatus(file) === 'ready' &&
                            file.deep_extraction_status === 'failed' && (
                              <div className="flex justify-center items-center bg-yellow-500 rounded-full size-4">
                                <span className="text-xs text-white">!</span>
                              </div>
                            )}
                          {getFileStatus(file) === 'ready' && !file.deep_extraction_status && (
                            <div className="flex justify-center items-center bg-green-500 rounded-full size-4">
                              <Check className="text-white size-3" strokeWidth={3} />
                            </div>
                          )}

                          {/* Error States */}
                          {file.duplicate_error && (
                            <div className="flex justify-center items-center bg-orange-500 rounded-full size-4">
                              <span className="text-xs text-white">!</span>
                            </div>
                          )}

                          {/* Default State */}
                          {getFileStatus(file) === 'ready' &&
                            !file.deep_extraction_status &&
                            !file.duplicate_error && (
                              <div className="flex justify-center items-center bg-gray-400 rounded-full size-4">
                                <Check className="text-white size-3" strokeWidth={3} />
                              </div>
                            )}
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Extracted file */}
            <div className="flex overflow-auto flex-col flex-1 gap-2 px-4 max-w-full min-h-0">
              <ExtractedFile
                selectedFile={selectedFile ?? extractedFiles[0]}
                onFileUpload={handleFileUpload}
              />
            </div>
          </div>

          {/* Only show footer/action buttons when not in review mode */}
          {!isReviewMode && (
            <div className="flex flex-col gap-4 p-4 border-t border-gray-200 dark:border-gray-300">
              {/* Action buttons */}
              <div className="flex gap-2 justify-end">
                {extractedFiles.length > 0 && (
                  <Button
                    onClick={() => setShowConfirmDiscard(true)}
                    variant="outline"
                    disabled={isDisabled}
                  >
                    Discard
                  </Button>
                )}
                <Button
                  disabled={isDisabled || extractedFiles.length === 0}
                  onClick={handleSaveAndFinish}
                >
                  {currentExtractionStep === 'saving' && (
                    <IconLoader2 className="mr-2 animate-spin size-4" />
                  )}
                  {currentExtractionStep === 'saving' ? 'Finishing...' : 'Finish'}
                </Button>
              </div>
            </div>
          )}
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
            <Button variant="outline" onClick={() => setShowConfirmDiscard(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDeleteFile}>
              Discard
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Duplicate File Dialog */}
      <DuplicateFileDialog
        open={isDuplicateDialogOpen}
        file={duplicateFile}
        onAction={(action) => {
          if (duplicateFile) {
            handleDuplicateAction(action, duplicateFile);
          }
        }}
        onClose={closeDuplicateDialog}
      />
    </>
  );
};

export default ExtractionFilePopup;
