import { useState, useEffect, useCallback } from 'react';
import * as XLSX from 'xlsx';
import {
  IconLoader,
  IconChevronLeft,
  IconChevronRight,
  IconChevronsLeft,
  IconChevronsRight,
} from '@tabler/icons-react';
import { IconButton } from '@/components/ui/button';

interface ExcelReviewProps {
  blobUrl: string;
  currentPage: number;
  setCurrentPage: (page: number) => void;
}

export const ExcelReview = ({ blobUrl, currentPage, setCurrentPage }: ExcelReviewProps) => {
  const [sheets, setSheets] = useState<{ [sheetName: string]: any[] }>({});
  const [sheetNames, setSheetNames] = useState<string[]>([]);
  const [activeSheet, setActiveSheet] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [isPartialData, setIsPartialData] = useState(false);
  const [sheetRowCounts, setSheetRowCounts] = useState<{ [sheetName: string]: number }>({});

  // Configuration constants
  const ROWS_PER_PAGE = 100;
  const MAX_PREVIEW_SIZE = 5 * 1024 * 1024; // 5MB in bytes
  const MAX_PROCESSING_SIZE = 20 * 1024 * 1024; // 20MB in bytes

  // Process excel file with appropriate options based on size
  const processExcelFile = useCallback(
    async (arrayBuffer: ArrayBuffer, fileSize: number) => {
      try {
        // For large files, use limited processing options
        const options: XLSX.ParsingOptions = {
          type: 'array',
          cellDates: true,
          cellNF: false, // Don't parse number formats for better performance
          cellStyles: false, // Skip styles for better performance with large files
        };

        // Additional options for smaller files
        if (fileSize <= MAX_PREVIEW_SIZE) {
          options.cellStyles = true;
          options.cellNF = true;
        }

        const workbook = XLSX.read(new Uint8Array(arrayBuffer), options);

        const sheetsData: { [sheetName: string]: any[] } = {};
        const rowCountsData: { [sheetName: string]: number } = {};

        // Set partial data flag for large files
        setIsPartialData(fileSize > MAX_PREVIEW_SIZE);

        workbook.SheetNames.forEach((sheetName) => {
          const worksheet = workbook.Sheets[sheetName];

          // Get sheet range to determine total rows
          const range = XLSX.utils.decode_range(worksheet['!ref'] || 'A1');
          rowCountsData[sheetName] = range.e.r + 1;

          // For large files, limit the amount of data we process
          if (fileSize > MAX_PREVIEW_SIZE) {
            // Create a limited range to read (first ~1000 rows)
            const limitedRange = {
              s: { r: 0, c: 0 },
              e: { r: Math.min(1000, range.e.r), c: range.e.c },
            };
            worksheet['!ref'] = XLSX.utils.encode_range(limitedRange);
          }

          // Convert to JSON with headers option for first row
          const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
          sheetsData[sheetName] = jsonData;
        });

        setSheets(sheetsData);
        setSheetNames(workbook.SheetNames);
        setSheetRowCounts(rowCountsData);
        setActiveSheet(workbook.SheetNames[0]); // Set the first sheet as active by default
        setError(null);
      } catch (error) {
        console.error('Error processing Excel file:', error);
        setError('Failed to process Excel file');
      } finally {
        setIsLoading(false);
      }
    },
    [MAX_PREVIEW_SIZE],
  );

  useEffect(() => {
    const fetchExcelFile = async (url: string) => {
      try {
        setIsLoading(true);
        setError(null);

        const response = await fetch(url);
        const blob = await response.blob();

        if (blob.size > MAX_PROCESSING_SIZE) {
          setError(
            `File too large (${(blob.size / (1024 * 1024)).toFixed(1)}MB). Maximum size is ${MAX_PROCESSING_SIZE / (1024 * 1024)}MB.`,
          );
          setIsLoading(false);
          return;
        }

        const arrayBuffer = await blob.arrayBuffer();
        await processExcelFile(arrayBuffer, blob.size);
      } catch (error: any) {
        console.error('Error fetching Excel file:', error);
        setError(`Failed to load Excel file: ${error.message}`);
        setIsLoading(false);
      }
    };

    if (blobUrl) {
      fetchExcelFile(blobUrl);
      setPage(0); // Reset pagination when loading a new file
    }
  }, [blobUrl, processExcelFile, MAX_PROCESSING_SIZE]);

  // When changing sheets, reset to first page
  useEffect(() => {
    setPage(0);
  }, [activeSheet]);

  // Sync with parent currentPage prop
  useEffect(() => {
    if (currentPage !== page + 1) {
      setPage(Math.max(0, currentPage - 1));
    }
  }, [currentPage, page]);

  // Pagination logic
  const activeSheetData = sheets[activeSheet] || [];
  // Skip the header row in pagination calculations
  const dataRowsCount = activeSheetData.length > 0 ? activeSheetData.length - 1 : 0;
  const totalPages = Math.ceil(dataRowsCount / ROWS_PER_PAGE);

  const goToFirstPage = () => {
    setPage(0);
    setCurrentPage(1);
  };

  const goToPrevPage = () => {
    const newPage = Math.max(0, page - 1);
    setPage(newPage);
    setCurrentPage(newPage + 1);
  };

  const goToNextPage = () => {
    const newPage = Math.min(totalPages - 1, page + 1);
    setPage(newPage);
    setCurrentPage(newPage + 1);
  };

  const goToLastPage = () => {
    const newPage = totalPages - 1;
    setPage(newPage);
    setCurrentPage(newPage + 1);
  };

  // Get current page data - include header row plus the current page of data rows
  const paginatedData =
    activeSheetData.length > 0
      ? [
          activeSheetData[0], // Header row
          ...activeSheetData.slice(1 + page * ROWS_PER_PAGE, 1 + (page + 1) * ROWS_PER_PAGE),
        ]
      : [];

  if (!blobUrl) {
    return (
      <div className="flex flex-col gap-4 justify-center items-center p-8 h-full text-gray-500">
        <IconLoader className="animate-spin size-8" />
        <div className="text-center">
          <p className="font-medium">Preparing Excel...</p>
        </div>
      </div>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="flex flex-col gap-4 justify-center items-center p-8 h-full text-gray-500">
        <IconLoader className="animate-spin size-8" />
        <div className="text-center">
          <p className="font-medium">Loading Excel Data</p>
          <p className="text-sm">Please wait while the spreadsheet loads...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex flex-col gap-4 justify-center items-center p-8 h-full text-red-500">
        <div className="text-center">
          <p className="font-medium">Error Loading Excel</p>
          <p className="text-sm">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col w-full text-sm">
      {/* Sheet tabs */}
      <div className="flex overflow-x-auto border-b border-gray-200 bg-background">
        {sheetNames.map((sheetName) => (
          <button
            key={sheetName}
            onClick={() => setActiveSheet(sheetName)}
            className={`px-4 py-2 text-sm whitespace-nowrap border-b-2 transition-colors ${
              activeSheet === sheetName
                ? 'border-brand-500 text-brand-500 font-medium'
                : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            }`}
          >
            {sheetName}
            {sheetRowCounts[sheetName] && (
              <span className="ml-2 text-xs text-gray-500">{sheetRowCounts[sheetName]} rows</span>
            )}
          </button>
        ))}
      </div>

      {/* Excel data */}
      <div className="overflow-auto flex-1 p-4 scrollbar-hide">
        {activeSheetData.length > 0 ? (
          <div className="overflow-hidden rounded-lg border border-gray-200 shadow-xs bg-background">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="sticky top-0 bg-gray-50">
                  {paginatedData.length > 0 && (
                    <tr>
                      {paginatedData[0].map((cell: any, cellIndex: number) => (
                        <th
                          key={cellIndex}
                          className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase"
                        >
                          {cell !== undefined ? String(cell) : ''}
                        </th>
                      ))}
                    </tr>
                  )}
                </thead>
                <tbody className="divide-y divide-gray-200 bg-background">
                  {paginatedData.slice(1).map((row, rowIndex) => (
                    <tr key={rowIndex} className="transition-colors hover:bg-gray-50">
                      {row.map((cell: any, cellIndex: number) => (
                        <td
                          key={cellIndex}
                          className="px-6 py-4 text-sm text-gray-500 whitespace-nowrap"
                        >
                          {cell !== undefined ? String(cell) : ''}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="flex justify-center items-center h-full">
            <div className="text-gray-500">No data available</div>
          </div>
        )}
      </div>

      {/* Pagination controls */}
      {dataRowsCount > ROWS_PER_PAGE && (
        <div className="flex justify-between items-center p-4 border-t border-gray-200 bg-background">
          <div className="text-sm text-gray-500">
            Showing rows {page * ROWS_PER_PAGE + 1} to{' '}
            {Math.min((page + 1) * ROWS_PER_PAGE, dataRowsCount)} of{' '}
            {isPartialData ? `${dataRowsCount}+ (Preview only)` : dataRowsCount}
          </div>
          <div className="flex gap-2 items-center">
            <IconButton
              aria-label="First page"
              variant="outline"
              onClick={goToFirstPage}
              disabled={page === 0}
            >
              <IconChevronsLeft size={16} />
            </IconButton>
            <IconButton
              aria-label="Previous page"
              variant="outline"
              onClick={goToPrevPage}
              disabled={page === 0}
            >
              <IconChevronLeft size={16} />
            </IconButton>
            <span className="mx-2 text-sm">
              Page {page + 1} of {totalPages}
            </span>
            <IconButton
              aria-label="Next page"
              variant="outline"
              onClick={goToNextPage}
              disabled={page === totalPages - 1}
            >
              <IconChevronRight size={16} />
            </IconButton>
            <IconButton
              aria-label="Last page"
              variant="outline"
              onClick={goToLastPage}
              disabled={page === totalPages - 1}
            >
              <IconChevronsRight size={16} />
            </IconButton>
          </div>
        </div>
      )}
    </div>
  );
};
