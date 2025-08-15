import type { Table } from '@tanstack/react-table';
import { Button } from '@/components/ui/button';
import { ArrowLeft, ArrowRight } from 'iconoir-react';

interface DataTablePaginationProps<TData> {
  table: Table<TData>;
}

export function DataTablePagination<TData>({ table }: DataTablePaginationProps<TData>) {
  const pageCount = table.getPageCount();
  const currentPage = table.getState().pagination.pageIndex;
  const pageSize = table.getState().pagination.pageSize;
  const totalRows = table.getFilteredRowModel().rows.length;

  // Debug logging
  console.log('📄 Pagination Debug:', {
    pageCount,
    currentPage,
    pageSize,
    totalRows,
    canPreviousPage: table.getCanPreviousPage(),
    canNextPage: table.getCanNextPage(),
  });

  // Don't show pagination if there's only one page or no data
  if (pageCount <= 1) {
    return null;
  }

  return (
    <div className="flex overflow-auto justify-between items-center w-full">
      <div className="flex justify-between items-center w-full">
        <div className="text-sm text-gray-600">
          Showing {currentPage * pageSize + 1} to{' '}
          {Math.min((currentPage + 1) * pageSize, totalRows)} of {totalRows} results
        </div>
        <div className="flex items-center gap-4">
          <Button
            size="default"
            variant="outline"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            Previous
            <ArrowLeft className="w-4 h-4" />
          </Button>

          <div className="flex gap-2 justify-center items-center text-sm font-medium text-gray-600">
            {Array.from({ length: table.getPageCount() }, (_, i) => {
              const currentPage = table.getState().pagination.pageIndex;
              const showPage =
                i === 0 || // First page
                i === table.getPageCount() - 1 || // Last page
                (i >= currentPage - 2 && i <= currentPage + 2) || // Pages around current
                Math.abs(i - currentPage) <= 1; // Adjacent pages

              if (!showPage) {
                if (i === 1 || i === table.getPageCount() - 2) {
                  return (
                    <span key={i} className="px-2">
                      ...
                    </span>
                  );
                }
                return null;
              }

              return (
                <span
                  key={i}
                  className={`cursor-pointer rounded w-10 h-10 flex items-center justify-center ${
                    currentPage === i ? 'bg-gray-50 text-gray-900' : 'text-gray-600'
                  }`}
                  onClick={() => table.setPageIndex(i)}
                >
                  {i + 1}
                </span>
              );
            })}
          </div>

          <Button
            variant="secondary"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            size="default"
          >
            Next
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
