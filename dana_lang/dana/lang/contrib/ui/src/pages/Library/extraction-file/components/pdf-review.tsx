/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState, useRef, useCallback, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { IconLoader } from '@tabler/icons-react';
import 'react-pdf/dist/Page/AnnotationLayer.css';

// Add custom styles for TextLayer and AnnotationLayer
const pdfStyles = `
  .react-pdf__Page__textContent {
    border: 1px solid rgba(0, 0, 0, 0.1);
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  }

  .react-pdf__Page__textContent--hidden {
    opacity: 0.2;
  }

  .react-pdf__Page__annotations {
    border: 1px solid rgba(0, 0, 0, 0.1);
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  }

  .react-pdf__Page__annotations--hidden {
    opacity: 0.2;
  }

  .react-pdf__Page__textContent,
  .react-pdf__Page__annotations {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    overflow: hidden;
    opacity: 0.2;
    line-height: 1.0;
  }

  .react-pdf__Page__textContent:hover,
  .react-pdf__Page__annotations:hover {
    opacity: 1;
  }

  .react-pdf__Page__textContent span,
  .react-pdf__Page__annotations span {
    color: transparent;
    position: absolute;
    white-space: pre;
    cursor: text;
    transform-origin: 0% 0%;
  }

  .react-pdf__Page__textContent span:hover,
  .react-pdf__Page__annotations span:hover {
    color: rgba(0, 0, 0, 0.8);
  }
`;

// Inject styles if not already present
if (typeof document !== 'undefined') {
  const existingStyle = document.getElementById('react-pdf-styles');
  if (!existingStyle) {
    const styleElement = document.createElement('style');
    styleElement.id = 'react-pdf-styles';
    styleElement.textContent = pdfStyles;
    document.head.appendChild(styleElement);
  }
}

// Set the worker source
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();

const options = {
  cMapUrl: `https://unpkg.com/pdfjs-dist@${pdfjs.version}/cmaps/`,
  cMapPacked: true,
};

interface PDFReviewProps {
  blobUrl: string;
  currentPage: number;
  setCurrentPage: (page: number) => void;
}

const LAZYLOAD_OFFSET = 2; // Number of pages to load ahead/behind the viewport

export const PDFReview = ({ blobUrl, currentPage, setCurrentPage }: PDFReviewProps) => {
  const [numPages, setNumPages] = useState<number>(0);
  const [visiblePages, setVisiblePages] = useState<Set<number>>(new Set([1]));
  const [pdfLoadError, setPdfLoadError] = useState<string | null>(null);
  const [pageWidth, setPageWidth] = useState<number>(450);

  const containerRef = useRef<HTMLDivElement>(null);
  const pageRefs = useRef<Map<number, HTMLDivElement>>(new Map());
  const resizeTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const resizeEndTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Track the page that is most visible due to scroll, separate from currentPage prop
  const [scrollPage, setScrollPage] = useState<number>(1);

  // Track last currentPage to detect user click (next/back) vs scroll
  const lastCurrentPageRef = useRef<number>(currentPage);

  // Update page width based on container width with debouncing
  const updatePageWidth = useCallback(() => {
    if (!containerRef.current) return;

    const containerWidth = containerRef.current.clientWidth;
    // Set page width to 90% of container width with min/max constraints
    const newWidth = Math.max(300, Math.min(containerWidth * 0.9, 800));

    // Only update if the width has changed significantly to avoid unnecessary re-renders
    if (Math.abs(newWidth - pageWidth) > 10) {
      setPageWidth(newWidth);
    }
  }, [pageWidth]);

  // Debounced version of updatePageWidth
  const debouncedUpdatePageWidth = useCallback(() => {
    if (resizeTimeoutRef.current) {
      clearTimeout(resizeTimeoutRef.current);
    }
    resizeTimeoutRef.current = setTimeout(() => {
      updatePageWidth();
    }, 100); // Reduced debounce time for more responsive resizing
  }, [updatePageWidth]);

  // Helper to determine which pages should be visible based on scroll
  const handleScroll = useCallback(() => {
    if (!containerRef.current || numPages === 0) return;

    const container = containerRef.current;
    const containerRect = container.getBoundingClientRect();
    const containerTop = containerRect.top;
    const containerBottom = containerRect.bottom;

    let firstVisible = numPages;
    let lastVisible = 1;
    let mostVisiblePage = 1;
    let maxVisibleHeight = 0;

    // Check each page's visibility and find the most visible page
    for (let pageNum = 1; pageNum <= numPages; pageNum++) {
      const pageElement = pageRefs.current.get(pageNum);
      if (pageElement) {
        const rect = pageElement.getBoundingClientRect();
        const visibleTop = Math.max(rect.top, containerTop);
        const visibleBottom = Math.min(rect.bottom, containerBottom);
        const visibleHeight = Math.max(0, visibleBottom - visibleTop);

        const isVisible = rect.bottom > containerTop && rect.top < containerBottom;

        if (isVisible) {
          firstVisible = Math.min(firstVisible, pageNum);
          lastVisible = Math.max(lastVisible, pageNum);

          if (visibleHeight > maxVisibleHeight) {
            maxVisibleHeight = visibleHeight;
            mostVisiblePage = pageNum;
          }
        }
      }
    }

    // If no pages are visible, keep current state
    if (firstVisible > lastVisible) {
      return;
    }

    // Calculate the range of pages to load (including offset)
    const start = Math.max(1, firstVisible - LAZYLOAD_OFFSET);
    const end = Math.min(numPages, lastVisible + LAZYLOAD_OFFSET);

    const newVisiblePages = new Set<number>();
    for (let i = start; i <= end; i++) {
      newVisiblePages.add(i);
    }

    // Only update if the set has actually changed
    if (
      newVisiblePages.size !== visiblePages.size ||
      [...newVisiblePages].some((page) => !visiblePages.has(page))
    ) {
      setVisiblePages(newVisiblePages);
    }

    // Update scrollPage if changed
    if (mostVisiblePage !== scrollPage) {
      setScrollPage(mostVisiblePage);
      // Only setCurrentPage if the user is scrolling (not from next/back click)
      // If currentPage !== mostVisiblePage, update currentPage
      // But only if currentPage matches lastCurrentPageRef (i.e. not just changed by click)
      if (currentPage !== mostVisiblePage && currentPage === lastCurrentPageRef.current) {
        setCurrentPage(mostVisiblePage);
        lastCurrentPageRef.current = mostVisiblePage;
      }
    }
  }, [numPages, visiblePages, scrollPage, currentPage, setCurrentPage]);

  // When PDF loads, set initial visible pages
  const handleLoadSuccess = (pdf: any) => {
    if (!pdf || typeof pdf.numPages !== 'number' || isNaN(pdf.numPages) || pdf.numPages < 1) {
      setPdfLoadError('Failed to load PDF: Invalid document');
      setNumPages(0);
      setVisiblePages(new Set([1]));
      setScrollPage(1);
      return;
    }
    setNumPages(pdf.numPages);
    // Show first few pages initially
    const initialPages = new Set<number>();
    for (let i = 1; i <= Math.min(3, pdf.numPages); i++) {
      initialPages.add(i);
    }
    setVisiblePages(initialPages);
    setPdfLoadError(null);
    setScrollPage(1);
  };

  // Defensive: handle error from react-pdf
  const handleLoadError = (error: any) => {
    setPdfLoadError(error?.message ? `Failed to load PDF: ${error.message}` : 'Failed to load PDF');
    setNumPages(0);
    setVisiblePages(new Set([1]));
    setScrollPage(1);
  };

  // Attach scroll event with throttling
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    let timeoutId: ReturnType<typeof setTimeout>;
    const throttledScroll = () => {
      if (timeoutId) clearTimeout(timeoutId);
      timeoutId = setTimeout(handleScroll, 100);
    };

    container.addEventListener('scroll', throttledScroll, { passive: true });

    // Initial check
    setTimeout(handleScroll, 100);

    return () => {
      container.removeEventListener('scroll', throttledScroll);
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [handleScroll]);

  // Detect user click (next/back) and auto scroll to page index
  useEffect(() => {
    // If currentPage changed by user click (not by scroll), auto scroll to that page
    if (!containerRef.current) return;
    if (currentPage !== scrollPage) {
      // Only scroll if the page is rendered (in visiblePages)
      const pageEl = pageRefs.current.get(currentPage);
      if (pageEl && visiblePages.has(currentPage)) {
        pageEl.scrollIntoView({ behavior: 'smooth', block: 'start', inline: 'nearest' });
      }
      // Update lastCurrentPageRef so scroll handler doesn't setCurrentPage back
      lastCurrentPageRef.current = currentPage;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage, visiblePages]);

  // Handle resize events to update page width with debouncing
  useEffect(() => {
    updatePageWidth();

    window.addEventListener('resize', debouncedUpdatePageWidth);

    // Use ResizeObserver for more precise container size changes
    const resizeObserver = new ResizeObserver(() => {
      debouncedUpdatePageWidth();
    });

    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    return () => {
      window.removeEventListener('resize', debouncedUpdatePageWidth);
      resizeObserver.disconnect();
      if (resizeTimeoutRef.current) {
        clearTimeout(resizeTimeoutRef.current);
      }
      if (resizeEndTimeoutRef.current) {
        clearTimeout(resizeEndTimeoutRef.current);
      }
    };
  }, [updatePageWidth, debouncedUpdatePageWidth]);

  if (!blobUrl) {
    return (
      <div className="flex flex-col gap-4 justify-center items-center p-8 h-full text-gray-500">
        <IconLoader className="animate-spin size-8" />
        <div className="text-center">
          <p className="font-medium">Preparing PDF...</p>
        </div>
      </div>
    );
  }

  if (pdfLoadError) {
    return (
      <div className="flex flex-col gap-4 justify-center items-center p-8 h-full text-red-500">
        <div className="text-center">
          <p className="font-medium">Error Loading PDF</p>
          <p className="text-sm">{pdfLoadError}</p>
        </div>
      </div>
    );
  }

  return (
    <div
      className="flex overflow-auto flex-col items-center w-full transition-all duration-200 ease-in-out scrollbar-hide"
      ref={containerRef}
      style={{ scrollBehavior: 'smooth' }}
    >
      <Document
        className="w-full transition-all duration-200 ease-in-out"
        options={options}
        file={blobUrl}
        onLoadSuccess={handleLoadSuccess}
        onLoadError={handleLoadError}
        error={
          <div className="flex flex-col gap-4 justify-center items-center p-8 text-red-500">
            <div className="text-center">
              <p className="font-medium">Error Loading PDF</p>
              <p className="text-sm">Failed to load PDF</p>
            </div>
          </div>
        }
        loading={
          <div className="flex flex-col gap-4 justify-center items-center p-8 text-gray-500">
            <IconLoader className="animate-spin size-8" />
            <div className="text-center">
              <p className="font-medium">Loading PDF</p>
              <p className="text-sm">Please wait while the document loads...</p>
            </div>
          </div>
        }
      >
        {typeof numPages === 'number' && numPages > 0
          ? Array.from({ length: numPages }).map((_, index) => {
              const pageNumber = index + 1;
              const shouldRender = visiblePages.has(pageNumber);
              const placeholderHeight = (pageWidth * 11) / 8.5; // Approximate A4 ratio

              return (
                <div
                  key={pageNumber}
                  ref={(el) => {
                    if (el) {
                      pageRefs.current.set(pageNumber, el);
                    } else {
                      pageRefs.current.delete(pageNumber);
                    }
                  }}
                  id={`page-${pageNumber}`}
                  data-page-number={pageNumber}
                  className={`flex my-1 w-full border-b border-gray-200 transition-all ease-in-out`}
                  style={{
                    minHeight: shouldRender ? 'auto' : placeholderHeight,
                    maxHeight: shouldRender ? 'auto' : placeholderHeight,
                    width: pageWidth,
                  }}
                >
                  {shouldRender ? (
                    <div className={`transition-all ease-in-out`}>
                      <Page
                        pageNumber={pageNumber}
                        width={pageWidth}
                        renderMode="canvas"
                        renderTextLayer={true}
                        renderAnnotationLayer={true}
                      />
                    </div>
                  ) : (
                    <div
                      className={`flex justify-center items-center bg-gray-100 rounded transition-all ease-in-out`}
                      style={{ height: placeholderHeight, width: pageWidth }}
                    >
                      <div className="text-sm text-gray-400">Page {pageNumber}</div>
                    </div>
                  )}
                </div>
              );
            })
          : null}
      </Document>
    </div>
  );
};
