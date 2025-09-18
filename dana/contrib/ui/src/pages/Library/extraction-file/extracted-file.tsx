import { useState, useCallback } from 'react';
import FileIcon from '@/components/file-icon';
import { IconFile, IconLoader, IconUpload } from '@tabler/icons-react';

import { PDFReview } from './components/pdf-review';
import { ExcelReview } from './components/excel-review';
import TextReview from './components/text-review';
import DocReview from './components/doc-review';

import { Pagination } from './components/pagination';
import { useDeepExtraction } from './hooks/useDeepExtraction';
import { useDocumentEditing } from './hooks/useDocumentEditing';
import { useFilePreview } from './hooks/useFilePreview';
import { getFileType, hasPreviewPane } from './utils/fileUtils';
// import { PromptSection } from './components/PromptSection';
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

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0 && onFileUpload) {
      onFileUpload(files);
    }
  }, [onFileUpload]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0 && onFileUpload) {
      onFileUpload(files);
    }
  }, [onFileUpload]);

  return (
    <div
      className={`flex flex-col gap-4 justify-center items-center h-full p-8 border-1 border-dashed rounded-lg transition-colors ${
        isDragOver
          ? 'border-blue-400 bg-blue-50 text-blue-600'
          : 'border-gray-200 bg-gray-50 text-gray-500 hover:border-gray-400 hover:bg-gray-50'
      }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <div className="flex flex-col items-center gap-4">
        <div className={`p-4 rounded-full transition-colors ${
          isDragOver ? 'bg-blue-100' : 'bg-gray-100'
        }`}>
          <IconUpload className={`size-8 ${isDragOver ? 'text-blue-600' : 'text-gray-500'}`} />
        </div>
        <div className="text-center">
          <p className="font-medium text-lg mb-2">
            {isDragOver ? 'Drop files here' : 'Upload Files'}
          </p>
          <p className="text-sm mb-4">
            {isDragOver 
              ? 'Release to upload your files' 
              : 'Drag and drop files here, or click to browse'
            }
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
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            <IconUpload className="size-4 mr-2" />
            Browse Files
          </label>
        </div>
        <div className="text-sm text-gray-400 text-center max-w-md">
          (.pdf, .doc, .docx, .md. Max 5MB per file)
        </div>
      </div>
    </div>
  );
};

// Main component
export const ExtractedFile = ({ selectedFile, onFileUpload }: ExtractedFileProps) => {
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [showPromptInput, setShowPromptInput] = useState<boolean>(false);

  // Custom hooks
  const {
    isDeepExtracting,
    isDeepExtracted,
    deepExtractedDocuments,
    handleDeepExtractWithoutPrompt,
  } = useDeepExtraction(selectedFile);

  const { isEditing, value, setValue, handleSave, handleEdit } = useDocumentEditing(
    selectedFile,
    currentPage,
  );

  const { blobUrl, loading, error } = useFilePreview(selectedFile?.file || null);
  const { error: extractionError } = useExtractionFileStore();

  // File type detection
  const fileType = getFileType(selectedFile?.file?.name || '');
  const hasPreview = hasPreviewPane(selectedFile?.file?.name || '');

  // Get documents from either deep extraction or original data
  const documents =
    deepExtractedDocuments?.length > 0 ? deepExtractedDocuments : selectedFile?.documents || [];

  // Navigation functions
  const goBack = (): void => setCurrentPage((prev) => (prev > 1 ? prev - 1 : prev));
  const goNext = (): void =>
    setCurrentPage((prev) => (prev < (documents?.length || 0) ? prev + 1 : prev));

  // Wrapper functions to handle deep extraction and hide prompt input
  const handleDeepExtractWithoutPromptWrapper = (): void => {
    setShowPromptInput(false);
    handleDeepExtractWithoutPrompt();
  };

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
                <div className="flex justify-between items-center pb-4 pt-4  bg-white ">
                  <div className="flex gap-2 items-center">
                    <div className="flex size-6">
                      <FileIcon ext={fileType.extension} className="text-gray-600 size-5" />
                    </div>
                    <span className="text-sm font-medium text-gray-900 truncate max-w-[350px]">
                      {selectedFile.file.name}
                    </span>
                  </div>
                </div>

                {/* File Preview */}
                <div className="flex overflow-hidden flex-1 w-full min-h-0 rounded-lg scrollbar-hide">
                  <FilePreview
                    blobUrl={blobUrl}
                    file={selectedFile.file}
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
              <div className="flex border-1 border-gray-200 flex-col w-full h-full bg-gray-50 rounded-lg">
                {/* Header */}
                <div className="flex gap-2 justify-between items-center p-3">
                  <span className="text-sm font-semibold text-gray-600">
                    Extracted Content {documents.length > 0 && `(${documents.length} pages)`}
                  </span>
                  <div className="flex gap-2 items-center">
                    <ExtractionControls
                      isDeepExtracted={isDeepExtracted}
                      isDeepExtracting={isDeepExtracting}
                      showPromptInput={showPromptInput}
                      onShowPromptInput={() => setShowPromptInput(true)}
                      onDeepExtractWithPrompt={handleDeepExtractWithoutPromptWrapper}
                      onDeepExtractWithoutPrompt={handleDeepExtractWithoutPromptWrapper}
                      isEditing={isEditing}
                      onEdit={handleEdit}
                      onSave={handleSave}
                    />
                  </div>
                </div>

                {/* Content */}
                <div className="flex overflow-hidden flex-col flex-1 gap-4 p-4">
                  {/* Prompt Section */}
                  {/* <PromptSection
                    showPromptInput={showPromptInput}
                    setShowPromptInput={setShowPromptInput}
                    prompt={prompt}
                    setPrompt={setPrompt}
                    isDeepExtracting={isDeepExtracting}
                    isDeepExtracted={isDeepExtracted}
                    onDeepExtractWithPrompt={handleDeepExtractWithoutPromptWrapper}
                    onDeepExtractWithoutPrompt={handleDeepExtractWithoutPromptWrapper}
                  /> */}

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
                  {selectedFile.file.name}
                </span>
              </div>
            </div>

            {/* File Preview */}
            <div className="flex overflow-hidden flex-1 w-full min-h-0 rounded-lg scrollbar-hide">
              <FilePreview
                blobUrl={blobUrl}
                file={selectedFile.file}
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
