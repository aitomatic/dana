import { useState, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogClose,
} from '@/components/ui/dialog';
import {
  IconX,
  IconChevronLeft,
  IconChevronRight,
  IconZoomIn,
  IconZoomOut,
} from '@tabler/icons-react';

// Configure PDF.js worker - use a minimal approach
const configurePdfWorker = () => {
  try {
    // Use a minimal worker URL that should work
    pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;
    console.log('PDF.js worker configured');
  } catch (error) {
    console.warn('PDF.js worker configuration failed, will use fallback:', error);
  }
};

configurePdfWorker();

interface PdfViewerProps {
  open: boolean;
  onClose: () => void;
  fileUrl: string;
  fileName?: string;
}

export function PdfViewer({ open, onClose, fileUrl, fileName }: PdfViewerProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const [retryKey, setRetryKey] = useState<number>(0);
  const [showThumbnails, setShowThumbnails] = useState<boolean>(true);
  const [scale, setScale] = useState<number>(1);
  const [documentLoaded, setDocumentLoaded] = useState<boolean>(false);

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setNumPages(numPages);
    setPageNumber(1);
    setPdfError(null);
    setDocumentLoaded(true);
  }

  function onDocumentLoadError(error: Error) {
    console.error('PDF load error:', error);

    // Don't show worker-related errors immediately as they might be temporary
    if (error.message.includes('fake worker') || error.message.includes('worker')) {
      // Worker errors are usually temporary, don't show error immediately
      console.log('Worker error detected, PDF.js will retry automatically');
      return;
    }

    // Provide user-friendly error messages for other errors
    if (error.message.includes('Failed to fetch')) {
      setPdfError('Unable to load PDF file. Please check your internet connection and try again.');
    } else {
      setPdfError('Failed to load PDF. Please check the file URL or try again.');
    }
  }

  // Handle keyboard shortcuts
  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      } else if (event.key === 'ArrowLeft' && pageNumber > 1) {
        setPageNumber((prev) => prev - 1);
      } else if (event.key === 'ArrowRight' && pageNumber < numPages) {
        setPageNumber((prev) => prev + 1);
      } else if (event.key === '+' || event.key === '=') {
        event.preventDefault();
        setScale((prev) => Math.min(prev + 0.25, 3));
      } else if (event.key === '-') {
        event.preventDefault();
        setScale((prev) => Math.max(prev - 0.25, 0.5));
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [open, onClose, pageNumber, numPages]);

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent
        className="min-w-screen max-w-screen w-screen h-screen flex flex-col rounded-none p-0 gap-0"
        showCloseButton={false}
      >
        <DialogHeader>
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <DialogTitle>{fileName || 'PDF Viewer'}</DialogTitle>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowThumbnails(!showThumbnails)}
                className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                title={showThumbnails ? 'Hide thumbnails' : 'Show thumbnails'}
              >
                {showThumbnails ? 'Hide Sidebar' : 'Show Sidebar'}
              </button>
              <DialogClose asChild>
                <IconX className="size-10 p-2 text-gray-400 hover:text-gray-900 rounded-md hover:bg-gray-100 transition-colors cursor-pointer" />
              </DialogClose>
            </div>
          </div>
        </DialogHeader>
        <div className="flex-1 flex bg-gray-50">
          {pdfError ? (
            <div className="flex flex-col items-center justify-center text-center p-8 w-full">
              <div className="text-red-500 text-lg font-medium mb-2">PDF Loading Error</div>
              <div className="text-gray-600 mb-4">{pdfError}</div>
              <button
                onClick={() => {
                  setPdfError(null);
                  setRetryKey((prev) => prev + 1);
                }}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
              >
                Retry
              </button>
            </div>
          ) : (
            <>
              {/* Thumbnails Sidebar */}
              {showThumbnails && (
                <div className="w-64 bg-white border-r border-gray-200 overflow-y-auto">
                  <div className="px-4 h-12 flex items-center border-b border-gray-200">
                    <h3 className="text-sm font-medium text-gray-700">
                      Pages {documentLoaded ? `(${numPages})` : ''}
                    </h3>
                  </div>
                  <div className="p-2">
                    {!documentLoaded ? (
                      <div className="flex items-center justify-center py-8">
                        <div className="text-sm text-gray-500">Loading pages...</div>
                      </div>
                    ) : (
                      Array.from(new Array(numPages), (_, index) => (
                        <div
                          key={index + 1}
                          onClick={() => setPageNumber(index + 1)}
                          className={`mb-2 p-2 rounded cursor-pointer transition-colors ${
                            pageNumber === index + 1
                              ? 'bg-blue-100 border border-blue-300'
                              : 'hover:bg-gray-100'
                          }`}
                        >
                          <Document file={fileUrl}>
                            <Page
                              pageNumber={index + 1}
                              width={120}
                              className="border border-gray-200 rounded"
                            />
                          </Document>
                          <div className="text-xs text-center mt-1 text-gray-600">
                            Page {index + 1}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}

              {/* Main PDF Viewer */}
              <div className="flex-1 flex flex-col">
                {/* Toolbar */}
                <div className="bg-white border-b border-gray-200 h-12 flex items-center justify-between ">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setPageNumber((prev) => Math.max(1, prev - 1))}
                      disabled={pageNumber <= 1}
                      className="p-2 text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed rounded hover:bg-gray-100"
                      title="Previous page"
                    >
                      <IconChevronLeft className="w-5 h-5" />
                    </button>
                    <span className="text-sm text-gray-700 min-w-[80px] text-center">
                      {pageNumber} of {numPages}
                    </span>
                    <button
                      onClick={() => setPageNumber((prev) => Math.min(numPages, prev + 1))}
                      disabled={pageNumber >= numPages}
                      className="p-2 text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed rounded hover:bg-gray-100"
                      title="Next page"
                    >
                      <IconChevronRight className="w-5 h-5" />
                    </button>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setScale((prev) => Math.max(prev - 0.25, 0.5))}
                      disabled={scale <= 0.5}
                      className="p-2 text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed rounded hover:bg-gray-100"
                      title="Zoom out"
                    >
                      <IconZoomOut className="w-4 h-4" />
                    </button>
                    <span className="text-sm text-gray-700 min-w-[60px] text-center">
                      {Math.round(scale * 100)}%
                    </span>
                    <button
                      onClick={() => setScale((prev) => Math.min(prev + 0.25, 3))}
                      disabled={scale >= 3}
                      className="p-2 text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed rounded hover:bg-gray-100"
                      title="Zoom in"
                    >
                      <IconZoomIn className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* PDF Content */}
                <div className="flex-1 overflow-auto flex justify-center items-start p-4">
                  <Document
                    key={retryKey}
                    file={fileUrl}
                    onLoadSuccess={onDocumentLoadSuccess}
                    onLoadError={onDocumentLoadError}
                    loading="Loading PDF..."
                  >
                    <Page
                      pageNumber={pageNumber}
                      width={Math.min(
                        (window.innerWidth - (showThumbnails ? 320 : 100)) * scale,
                        1200 * scale,
                      )}
                    />
                  </Document>
                </div>
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
