/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState, useCallback } from 'react';
import FileIcon from '@/components/file-icon';
import { IconFile, IconLoader, IconUpload } from '@tabler/icons-react';

import { PDFReview } from './components/pdf-review';
import { ExcelReview } from './components/excel-review';
import TextReview from './components/text-review';
import DocReview from './components/doc-review';

import { Pagination } from './components/pagination';
import { useDocumentEditing } from './hooks/useDocumentEditing';
import { useDocumentPreview } from './hooks/useDocumentPreview';
import { getFileType, hasPreviewPane } from './utils/fileUtils';
import { ExtractionControls } from './components/ExtractionControls';
import { DocumentEditor } from './components/DocumentEditor';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable';
import { useExtractionFileStore } from '@/stores/extraction-file-store';

interface FilePreviewProps {
  blobUrl: string | null;
  file: File;
  isPdf: boolean;
  isExcel: boolean;
  isText: boolean;
  isDocx: boolean;
  currentPage: number;
  setCurrentPage: (page: number) => void;
  loading: boolean;
  error: string | null;
}

// Component for file preview
const FilePreview = ({
  blobUrl,
  file,
  isPdf,
  isExcel,
  isText,
  isDocx,
  currentPage,
  setCurrentPage,
  loading,
  error,
}: FilePreviewProps) => {
  if (loading) {
    return (
      <div className="flex flex-col gap-4 justify-center items-center p-8 h-full text-gray-500">
        <IconLoader className="animate-spin size-8" />
        <div className="text-center">
          <p className="font-medium">Loading Preview</p>
          <p className="text-sm">Preparing file...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col gap-4 justify-center items-center p-8 h-full">
        <IconFile className="size-16" />
        <div className="text-center">
          <p className="font-medium">Error Loading File</p>
          <p className="text-sm">{error}</p>
        </div>
      </div>
    );
  }

  if (!blobUrl) {
    return (
      <div className="flex flex-col gap-4 justify-center items-center p-8 h-full text-gray-500">
        <IconFile className="size-16" />
        <div className="text-center">
          <p className="font-medium">Preview Not Available</p>
          <p className="text-sm">File type not supported</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex w-full h-full">
      {isPdf ? (
        <PDFReview blobUrl={blobUrl} currentPage={currentPage} setCurrentPage={setCurrentPage} />
      ) : isExcel ? (
        <ExcelReview blobUrl={blobUrl} currentPage={currentPage} setCurrentPage={setCurrentPage} />
      ) : isText ? (
        <TextReview content={blobUrl} fileName={file.name} />
      ) : isDocx ? (
        <DocReview file={file} />
      ) : (
        <iframe
          src={blobUrl}
          title={`Preview of ${file.name}`}
          style={{ backgroundColor: 'white', width: '100%', height: '100%' }}
        />
      )}
    </div>
  );
};

interface ExtractedFileProps {
  selectedFile: any;
  onFileUpload?: (files: File[]) => void;
}

// Drag and Drop Component
const DragDropArea = ({ onFileUpload }: { onFileUpload?: (files: File[]) => void }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [fileSizeError, setFileSizeError] = useState<string | null>(null);

  const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB in bytes

  const validateFileSizes = (files: File[]): { isValid: boolean; errorMessage: string | null } => {
    const oversizedFiles = files.filter(file => file.size > MAX_FILE_SIZE);
    
    if (oversizedFiles.length === 0) {
      return { isValid: true, errorMessage: null };
    }

    if (oversizedFiles.length === 1) {
      const file = oversizedFiles[0];
      const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
      return { 
        isValid: false, 
        errorMessage: `"${file.name}" (${sizeMB}MB) exceeds the 50MB file size limit. Please choose a smaller file.` 
      };
    } else {
      const fileNames = oversizedFiles.map(file => file.name).join(', ');
      return { 
        isValid: false, 
        errorMessage: `Multiple files exceed the 50MB limit: ${fileNames}. Please choose smaller files.` 
      };
    }
  };

  const handleFileUpload = useCallback(
    (files: File[]) => {
      const validation = validateFileSizes(files);
      
      if (!validation.isValid) {
        setFileSizeError(validation.errorMessage);
        // Don't proceed with upload if validation fails
        return;
      }
      
      // Clear any previous error and proceed with upload
      setFileSizeError(null);
      if (onFileUpload) {
        onFileUpload(files);
      }
    },
    [onFileUpload],
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragOver(false);

      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        handleFileUpload(files);
      }
    },
    [handleFileUpload],
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files || []);
      if (files.length > 0) {
        handleFileUpload(files);
      }
    },
    [handleFileUpload],
  );

  return (
    <div
      className={`flex flex-col gap-4 justify-center items-center h-full p-8 border-1 border-dashed rounded-lg transition-colors ${
        isDragOver
          ? 'text-blue-600 bg-blue-50 border-blue-400'
          : 'text-gray-500 bg-gray-50 border-gray-200 hover:border-gray-400 hover:bg-gray-50'
      }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <div className="flex flex-col gap-4 items-center">
        <div
          className={`p-4 rounded-full transition-colors ${
            isDragOver ? 'bg-blue-100' : 'bg-gray-100'
          }`}
        >
          <IconUpload className={`size-8 ${isDragOver ? 'text-blue-600' : 'text-gray-500'}`} />
        </div>
        <div className="text-center">
          <p className="mb-2 text-lg font-medium">
            {isDragOver ? 'Drop files here' : 'Upload Files'}
          </p>
          <p className="mb-4 text-sm">
            {isDragOver
              ? 'Release to upload your files'
              : 'Drag and drop files here, or click to browse'}
          </p>
          <input
            type="file"
            multiple
            accept=".pdf,.doc,.docx,.txt,.xlsx,.xls,.csv,.pptx,.ppt"
            onChange={handleFileInput}
            className="hidden"
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            className={`inline-flex items-center px-4 py-2 rounded-lg font-medium transition-colors cursor-pointer ${
              isDragOver
                ? 'hidden'
                : 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50'
            }`}
          >
            <IconUpload className="mr-2 size-4" />
            Browse Files
          </label>
        </div>
        <div className="max-w-md text-sm text-center text-gray-400">
          (.pdf, .doc, .docx, .md. Max 50MB per file)
        </div>
        {/* File Size Error Message */}
        {fileSizeError && (
          <div className="max-w-lg p-3 mt-2 text-sm text-red-700 bg-red-50 rounded-md border border-red-200">
            <p className="font-medium">File size too large</p>
            <p className="mt-1">{fileSizeError}</p>
          </div>
        )}
      </div>
    </div>
  );
};

// Main component
export const ExtractedFile = ({ selectedFile, onFileUpload }: ExtractedFileProps) => {
  const [currentPage, setCurrentPage] = useState<number>(1);

  // Deep extraction status from selected file
  const isDeepExtracting = selectedFile?.deep_extraction_status === 'running';
  const deepExtractedDocuments = selectedFile?.deep_extracted_documents || [];

  const { isEditing, value, setValue, handleSave, handleEdit } = useDocumentEditing(
    selectedFile,
    currentPage,
  );

  const { blobUrl, loading, error } = useDocumentPreview(selectedFile);
  const { error: extractionError } = useExtractionFileStore();

  // File type detection
  const fileName = selectedFile?.file?.name || selectedFile?.original_filename || '';
  const fileType = getFileType(fileName);
  const hasPreview = hasPreviewPane(fileName);

  // Create a file-like object for existing documents
  // For existing documents, we'll use a placeholder file object since the actual content is downloaded separately
  const fileObject =
    selectedFile?.file ||
    ({
      name: fileName,
      type: selectedFile?.mime_type || 'application/octet-stream',
      size: selectedFile?.file_size || 0,
    } as File);

  // Get documents from either deep extraction or standard extraction
  const documents =
    selectedFile?.is_deep_extracted && selectedFile?.deep_extracted_documents?.length > 0
      ? selectedFile.deep_extracted_documents
      : deepExtractedDocuments?.length > 0
        ? deepExtractedDocuments
        : selectedFile?.documents || [];

  // Navigation functions
  const goBack = (): void => setCurrentPage((prev) => (prev > 1 ? prev - 1 : prev));
  const goNext = (): void =>
    setCurrentPage((prev) => (prev < (documents?.length || 0) ? prev + 1 : prev));

  if (!selectedFile) {
    return <DragDropArea onFileUpload={onFileUpload} />;
  }

  return (
    <div className="flex flex-col gap-4 w-full h-full">
      <div className="flex flex-1 gap-4 w-full min-h-0">
        {hasPreview ? (
          <ResizablePanelGroup direction="horizontal" className="w-full h-full">
            {/* File Preview */}
            <ResizablePanel defaultSize={50} minSize={30}>
              <div className="flex flex-col w-full h-full">
                {/* File Header */}
                <div className="flex justify-between items-center pt-4 pb-4 bg-white">
                  <div className="flex gap-2 items-center">
                    <div className="flex size-6">
                      <FileIcon ext={fileType.extension} className="text-gray-600 size-5" />
                    </div>
                    <span className="text-sm font-medium text-gray-900 truncate max-w-[350px]">
                      {fileName}
                    </span>
                  </div>
                </div>

                {/* File Preview */}
                <div className="flex overflow-hidden flex-1 w-full min-h-0 rounded-lg scrollbar-hide">
                  <FilePreview
                    blobUrl={blobUrl}
                    file={fileObject}
                    isPdf={fileType.isPdf}
                    isExcel={fileType.isExcel}
                    isText={fileType.isText}
                    isDocx={fileType.isDocx}
                    currentPage={currentPage}
                    setCurrentPage={setCurrentPage}
                    loading={loading}
                    error={error}
                  />
                </div>
              </div>
            </ResizablePanel>

            <ResizableHandle withHandle />

            {/* Extracted File */}
            <ResizablePanel defaultSize={50} minSize={30}>
              <div className="flex flex-col w-full h-full bg-gray-50 rounded-lg border-gray-200 border-1">
                {/* Header */}
                <div className="flex gap-2 justify-between items-center p-3">
                  <div className="flex flex-col gap-1">
                    <span className="text-sm font-semibold text-gray-600">
                      Extracted Content {documents.length > 0 && `(${documents.length} pages)`}
                    </span>
                    {selectedFile?.is_deep_extracted &&
                      selectedFile?.deep_extracted_documents?.length > 0 && (
                        <span className="text-xs font-medium text-blue-600">
                          Deep extraction results
                        </span>
                      )}
                    {selectedFile?.status === 'ready' &&
                      !selectedFile?.is_deep_extracted &&
                      selectedFile?.deep_extraction_status === 'running' && (
                        <span className="text-xs text-blue-500">
                          Standard extraction results - Deep extraction in progress
                        </span>
                      )}
                    {selectedFile?.status === 'ready' &&
                      !selectedFile?.is_deep_extracted &&
                      selectedFile?.deep_extraction_status === 'failed' && (
                        <span className="text-xs text-yellow-600">
                          Standard extraction results - Deep extraction failed
                        </span>
                      )}
                  </div>
                  <div className="flex gap-2 items-center">
                    <ExtractionControls
                      isDeepExtracted={selectedFile?.is_deep_extracted || false}
                      isDeepExtracting={isDeepExtracting}
                      showPromptInput={false}
                      onShowPromptInput={() => {}}
                      onDeepExtractWithPrompt={() => {}}
                      isEditing={isEditing}
                      onEdit={handleEdit}
                      onSave={handleSave}
                    />
                  </div>
                </div>

                {/* Content */}
                <div className="flex overflow-hidden flex-col flex-1 gap-4 p-4">
                  {/* Prompt Section */}

                  {/* Extraction Error Banner */}
                  {extractionError && (
                    <div className="p-3 text-red-700 bg-red-50 rounded-md border border-red-200">
                      <p className="text-sm font-medium">Extraction Error</p>
                      <p className="mt-1 text-xs">{extractionError}</p>
                    </div>
                  )}

                  {/* Document Editor */}
                  <div className="flex-1 min-h-0">
                    <DocumentEditor
                      isEditing={isEditing}
                      value={value}
                      setValue={setValue}
                      onSave={handleSave}
                      onEdit={handleEdit}
                      isUploading={selectedFile?.status === 'uploading'}
                      isDeepExtracting={isDeepExtracting || selectedFile?.status === 'extracting'}
                    />
                  </div>
                </div>
              </div>
            </ResizablePanel>
          </ResizablePanelGroup>
        ) : (
          <div className="flex flex-col gap-2 w-full h-full">
            {/* File Header */}
            <div className="flex justify-between items-center pb-2 border-b border-gray-200">
              <div className="flex gap-2 items-center">
                <div className="flex size-6">
                  <FileIcon ext={fileType.extension} className="text-gray-600 size-5" />
                </div>
                <span className="text-sm font-medium text-gray-900 truncate max-w-[350px]">
                  {fileName}
                </span>
              </div>
            </div>

            {/* File Preview */}
            <div className="flex overflow-hidden flex-1 w-full min-h-0 rounded-lg scrollbar-hide">
              <FilePreview
                blobUrl={blobUrl}
                file={fileObject}
                isPdf={fileType.isPdf}
                isExcel={fileType.isExcel}
                isText={fileType.isText}
                isDocx={fileType.isDocx}
                currentPage={currentPage}
                setCurrentPage={setCurrentPage}
                loading={loading}
                error={error}
              />
            </div>
          </div>
        )}
      </div>

      {/* Pagination */}
      {documents && documents.length > 1 && (
        <div className="flex justify-center pt-2 border-t border-gray-200">
          <Pagination
            currentPage={currentPage}
            totalPages={documents.length}
            onBack={goBack}
            onNext={goNext}
            isDisabled={isDeepExtracting}
          />
        </div>
      )}
    </div>
  );
};
