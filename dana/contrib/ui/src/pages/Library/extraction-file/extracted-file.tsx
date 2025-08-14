import { useState } from 'react';
import FileIcon from '@/components/file-icon';
import { IconFile, IconLoader } from '@tabler/icons-react';

import { PDFReview } from './components/pdf-review';
import { ExcelReview } from './components/excel-review';
import TextReview from './components/text-review';
import DocReview from './components/doc-review';

import { Pagination } from './components/pagination';
import { useDeepExtraction } from './hooks/useDeepExtraction';
import { useDocumentEditing } from './hooks/useDocumentEditing';
import { useFilePreview } from './hooks/useFilePreview';
import { getFileType, hasPreviewPane } from './utils/fileUtils';
import { PromptSection } from './components/PromptSection';
import { ExtractionControls } from './components/ExtractionControls';
import { DocumentEditor } from './components/DocumentEditor';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable';

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
}

// Main component
export const ExtractedFile = ({ selectedFile }: ExtractedFileProps) => {
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [showPromptInput, setShowPromptInput] = useState<boolean>(false);

  // Custom hooks
  const {
    isDeepExtracting,
    isDeepExtracted,
    deepExtractedDocuments,
    prompt,
    setPrompt,
    handleDeepExtractWithPrompt,
    handleDeepExtractWithoutPrompt,
  } = useDeepExtraction(selectedFile);

  const { isEditing, value, setValue, handleSave, handleEdit } = useDocumentEditing(
    selectedFile,
    currentPage,
  );

  const { blobUrl, loading, error } = useFilePreview(selectedFile?.file || null);

  // File type detection
  const fileType = getFileType(selectedFile?.file?.name || '');
  const hasPreview = hasPreviewPane(selectedFile?.file?.name || '');

  // Get documents from either deep extraction or original data
  const documents =
    deepExtractedDocuments?.length > 0 ? deepExtractedDocuments : selectedFile?.documents || [];

  console.log('[ExtractedFile] selectedFile:', selectedFile);
  console.log('[ExtractedFile] selectedFile?.documents:', selectedFile?.documents);
  console.log('[ExtractedFile] selectedFile?.documents?.length:', selectedFile?.documents?.length);
  console.log(
    '[ExtractedFile] selectedFile?.documents[0]?.page_content:',
    selectedFile?.documents?.[0]?.page_content?.substring(0, 100),
  );
  console.log('[ExtractedFile] deepExtractedDocuments:', deepExtractedDocuments);
  console.log('[ExtractedFile] deepExtractedDocuments?.length:', deepExtractedDocuments?.length);
  console.log(
    '[ExtractedFile] deepExtractedDocuments[0]?.page_content:',
    deepExtractedDocuments?.[0]?.page_content?.substring(0, 100),
  );
  console.log(
    '[ExtractedFile] Using documents from:',
    deepExtractedDocuments?.length > 0 ? 'deepExtractedDocuments' : 'selectedFile.documents',
  );
  console.log('[ExtractedFile] final documents array:', documents);
  console.log('[ExtractedFile] final documents.length:', documents.length);
  console.log('[ExtractedFile] currentPage:', currentPage);
  console.log('[ExtractedFile] current document:', documents[currentPage - 1]);
  console.log(
    '[ExtractedFile] current document page_content:',
    documents[currentPage - 1]?.page_content?.substring(0, 100),
  );

  // Navigation functions
  const goBack = (): void => setCurrentPage((prev) => (prev > 1 ? prev - 1 : prev));
  const goNext = (): void =>
    setCurrentPage((prev) => (prev < (documents?.length || 0) ? prev + 1 : prev));

  // Wrapper functions to handle deep extraction and hide prompt input
  const handleDeepExtractWithPromptWrapper = (): void => {
    setShowPromptInput(false);
    handleDeepExtractWithPrompt();
  };

  const handleDeepExtractWithoutPromptWrapper = (): void => {
    setShowPromptInput(false);
    handleDeepExtractWithoutPrompt();
  };

  if (!selectedFile) {
    return (
      <div className="flex flex-col gap-4 justify-center items-center h-full text-gray-500">
        <IconFile className="size-12" />
        <div className="text-center">
          <p className="font-medium">No Files Extracted</p>
          <p className="text-sm">Upload and extract files to get started</p>
        </div>
      </div>
    );
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
            </ResizablePanel>

            <ResizableHandle withHandle />

            {/* Extracted File */}
            <ResizablePanel defaultSize={50} minSize={30}>
              <div className="flex flex-col w-full h-full bg-gray-50 rounded-lg">
                {/* Header */}
                <div className="flex gap-2 justify-between items-center p-4 border-b border-gray-200">
                  <span className="text-sm font-semibold text-gray-600">
                    Extract {documents.length > 0 && `(${documents.length} pages)`}
                  </span>
                  <div className="flex gap-2 items-center">
                    <ExtractionControls
                      isDeepExtracted={isDeepExtracted}
                      isDeepExtracting={isDeepExtracting}
                      showPromptInput={showPromptInput}
                      onShowPromptInput={() => setShowPromptInput(true)}
                      onDeepExtractWithPrompt={handleDeepExtractWithPromptWrapper}
                      isEditing={isEditing}
                      onEdit={handleEdit}
                      onSave={handleSave}
                    />
                  </div>
                </div>

                {/* Content */}
                <div className="flex overflow-hidden flex-col flex-1 gap-4 p-4">
                  {/* Prompt Section */}
                  <PromptSection
                    showPromptInput={showPromptInput}
                    setShowPromptInput={setShowPromptInput}
                    prompt={prompt}
                    setPrompt={setPrompt}
                    isDeepExtracting={isDeepExtracting}
                    isDeepExtracted={isDeepExtracted}
                    onDeepExtractWithPrompt={handleDeepExtractWithPromptWrapper}
                    onDeepExtractWithoutPrompt={handleDeepExtractWithoutPromptWrapper}
                  />

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
          />
        </div>
      )}
    </div>
  );
};
