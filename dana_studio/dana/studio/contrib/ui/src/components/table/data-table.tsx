/* eslint-disable @typescript-eslint/no-explicit-any */
import * as React from 'react';
import {
  type ColumnDef,
  type ColumnFiltersState,
  type PaginationState,
  type SortingState,
  type VisibilityState,
  flexRender,
  getCoreRowModel,
  getFacetedRowModel,
  getFacetedUniqueValues,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table';
import { TableHeader, TableRow, TableHead, TableBody, TableCell, Table } from '.';
import { DataTablePagination } from './data-table-pagination';
import { IconLoader } from '@tabler/icons-react';
import { cn } from '@/lib/utils';
import { useScreenHeight } from '@/hooks/useScreenHeight';
import { IconChevronDown, IconChevronRight } from '@tabler/icons-react';

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  loading?: boolean;
  handleRowClick?: (row: any) => void;
  is_border?: boolean;
  defaultSorting?: { id: string; desc: boolean }[];
  getRowChildren?: (row: TData) => TData[] | undefined; // Function to get child rows
}

export function DataTable<TData, TValue>({
  columns,
  data,
  loading = true,
  handleRowClick,
  is_border = true,
  defaultSorting = [],
  getRowChildren,
}: DataTableProps<TData, TValue>) {
  const { pageSize } = useScreenHeight();
  const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>({});
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([]);
  const [sorting, setSorting] = React.useState<SortingState>(defaultSorting);
  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize: pageSize,
  });
  const [expandedRows, setExpandedRows] = React.useState<Set<string>>(new Set());

  // Update pagination when pageSize changes
  React.useEffect(() => {
    setPagination((prev) => ({
      ...prev,
      pageSize: pageSize,
    }));
  }, [pageSize]);

  // Toggle row expansion
  const toggleRowExpansion = React.useCallback((rowId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    setExpandedRows((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(rowId)) {
        newSet.delete(rowId);
      } else {
        newSet.add(rowId);
      }
      return newSet;
    });
  }, []);

  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
      columnVisibility,
      columnFilters,
      pagination,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onColumnVisibilityChange: setColumnVisibility,
    onPaginationChange: setPagination,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFacetedRowModel: getFacetedRowModel(),
    getFacetedUniqueValues: getFacetedUniqueValues(),
  });

  return (
    <div className="flex flex-col max-h-full rounded-lg border">
      <div
        className={cn('flex flex-1 overflow-auto  scrollbar-hide rounded-t-lg', is_border && '')}
      >
        <Table>
          <TableHeader className="sticky top-0 z-10 bg-gray-50 rounded-t-lg">
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  const columnMeta = header.column.columnDef.meta as any;
                  return (
                    <TableHead
                      key={header.id}
                      colSpan={header.colSpan}
                      className={columnMeta?.className}
                      style={columnMeta?.style}
                    >
                      {header.isPlaceholder
                        ? null
                        : flexRender(header.column.columnDef.header, header.getContext())}
                    </TableHead>
                  );
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody className="cursor-pointer">
            {loading ? (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center text-semibold! text-gray-900!"
                >
                  <div className="flex justify-center items-center w-full">
                    <IconLoader className="animate-spin text-brand-700" size={30} />
                  </div>
                </TableCell>
              </TableRow>
            ) : table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => {
                const rowData = row.original;
                const children = getRowChildren ? getRowChildren(rowData) : undefined;
                const hasChildren = children && children.length > 0;
                const isExpanded = expandedRows.has(row.id);

                return (
                  <React.Fragment key={row.id}>
                    {/* Parent Row */}
                    <TableRow data-state={row.getIsSelected() && 'selected'} className="group">
                      {row.getVisibleCells().map((cell) => {
                        const columnMeta = cell.column.columnDef.meta as any;
                        const isExpandColumn = cell.column.id === 'expand';
                        
                        return (
                          <TableCell
                            key={cell.id}
                            onClick={() => handleRowClick && handleRowClick(row)}
                            className={columnMeta?.className}
                            style={columnMeta?.style}
                          >
                            {/* Render expand icon in expand column */}
                            {isExpandColumn && hasChildren ? (
                              <button
                                onClick={(e) => toggleRowExpansion(row.id, e)}
                                className="px-2 py-2 z-10 text-gray-500 rounded-md transition-colors hover:bg-gray-100 hover:text-gray-700"
                                aria-label={isExpanded ? 'Collapse' : 'Expand'}
                              >
                                {isExpanded ? (
                                  <IconChevronDown size={16} strokeWidth={2} />
                                ) : (
                                  <IconChevronRight size={16} strokeWidth={2} />
                                )}
                              </button>
                            ) : (
                              flexRender(cell.column.columnDef.cell, cell.getContext())
                            )}
                          </TableCell>
                        );
                      })}
                    </TableRow>

                    {/* Child Rows */}
                    {hasChildren &&
                      isExpanded &&
                      children.map((child: any, childIndex: number) => {
                        const childRowId = `${row.id}-child-${childIndex}`;
                        const childHasChildren = getRowChildren && getRowChildren(child);
                        const isChildExpanded = expandedRows.has(childRowId);

                        return (
                          <React.Fragment key={childRowId}>
                            <TableRow className="transition-colors bg-gray-50 hover:bg-gray-100">
                              {columns.map((column: any, colIndex: number) => {
                                const columnMeta = column.meta as any;
                                const isExpandColumn = column.id === 'expand';
                                
                                return (
                                  <TableCell
                                    key={`${childRowId}-${colIndex}`}
                                    className={cn(columnMeta?.className)}
                                    style={columnMeta?.style}
                                    onClick={() =>
                                      handleRowClick &&
                                      handleRowClick({
                                        original: child,
                                        id: childRowId,
                                      })
                                    }
                                  >
                                    {/* Expand column is empty for child rows - expand icon goes in Name column */}
                                    {isExpandColumn ? null : column.accessorKey === 'name' ? (
                                      // Add expand icon for child rows in Name column (no indentation before arrow)
                                      <div className="flex items-center gap-2">
                                          {/* Add expand button if child has children */}
                                          {childHasChildren ? (
                                            <button
                                              onClick={(e) => toggleRowExpansion(childRowId, e)}
                                              className="p-1.5 z-10 text-gray-600 rounded-md transition-colors hover:bg-gray-200 hover:text-gray-700"
                                              aria-label={isChildExpanded ? 'Collapse' : 'Expand'}
                                            >
                                              {isChildExpanded ? (
                                                <IconChevronDown size={16} strokeWidth={2} />
                                              ) : (
                                                <IconChevronRight size={16} strokeWidth={2} />
                                              )}
                                            </button>
                                          ) : null}
                                          <div className="flex-1">
                                            {column.cell ? (
                                              typeof column.cell === 'function' ? (
                                                column.cell({ row: { original: child } })
                                              ) : (
                                                column.cell
                                              )
                                            ) : (
                                              child[column.accessorKey as keyof typeof child]
                                            )}
                                          </div>
                                        </div>
                                    ) : column.cell ? (
                                      typeof column.cell === 'function' ? (
                                        column.cell({ row: { original: child } })
                                      ) : (
                                        column.cell
                                      )
                                    ) : (
                                      child[column.accessorKey as keyof typeof child]
                                    )}
                                  </TableCell>
                                );
                              })}
                            </TableRow>

                            {/* Nested Children (Grandchildren) */}
                            {childHasChildren &&
                              isChildExpanded &&
                              childHasChildren.map((grandchild: any, grandchildIndex: number) => (
                                <TableRow
                                  key={`${childRowId}-grandchild-${grandchildIndex}`}
                                  className="transition-colors bg-green-50/30 hover:bg-green-50/50"
                                >
                                  {columns.map((column: any, colIndex: number) => {
                                    const columnMeta = column.meta as any;
                                    const isExpandColumn = column.id === 'expand';
                                    
                                    return (
                                      <TableCell
                                        key={`${childRowId}-grandchild-${grandchildIndex}-${colIndex}`}
                                        className={cn(columnMeta?.className)}
                                        style={columnMeta?.style}
                                        onClick={() =>
                                          handleRowClick &&
                                          handleRowClick({
                                            original: grandchild,
                                            id: `${childRowId}-grandchild-${grandchildIndex}`,
                                          })
                                        }
                                      >
                                        {/* Expand column is empty for grandchildren */}
                                        {isExpandColumn ? null : column.accessorKey === 'name' ? (
                                          // Add deeper indentation for grandchild rows in Name column
                                          <div className="pl-12">
                                            {column.cell ? (
                                              typeof column.cell === 'function' ? (
                                                column.cell({ row: { original: grandchild } })
                                              ) : (
                                                column.cell
                                              )
                                            ) : (
                                              grandchild[column.accessorKey as keyof typeof grandchild]
                                            )}
                                          </div>
                                        ) : column.cell ? (
                                          typeof column.cell === 'function' ? (
                                            column.cell({ row: { original: grandchild } })
                                          ) : (
                                            column.cell
                                          )
                                        ) : (
                                          grandchild[column.accessorKey as keyof typeof grandchild]
                                        )}
                                      </TableCell>
                                    );
                                  })}
                                </TableRow>
                              ))}
                          </React.Fragment>
                        );
                      })}
                  </React.Fragment>
                );
              })
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center text-semibold! text-gray-900!"
                >
                  <span className="font-semibold! text-gray-700!">No data</span>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      {table.getPageCount() > 1 && (
        <div className="flex flex-shrink-0 items-center p-3 bg-gray-50 rounded-b-lg border-t">
          <DataTablePagination table={table} />
        </div>
      )}
    </div>
  );
}
