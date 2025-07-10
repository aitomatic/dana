import React from 'react';
import { DataTable } from '@/components/table/data-table';
import type { LibraryItem } from '@/types/library';
import { getLibraryColumns, getSelectionColumns } from './library-columns';

interface LibraryTableProps {
  data: LibraryItem[];
  loading?: boolean;
  mode: 'library' | 'selection';
  selectedIds?: string[];
  onSelectionChange?: (ids: string[]) => void;
  onRowClick?: (item: LibraryItem) => void;
  onViewItem?: (item: LibraryItem) => void;
  onEditItem?: (item: LibraryItem) => void;
  onDeleteItem?: (item: LibraryItem) => void;
  onDownloadItem?: (item: LibraryItem) => void;
  allLibraryItems?: LibraryItem[]; // Add prop for all library items
}

export function LibraryTable({
  data,
  loading = false,
  mode,
  selectedIds = [],
  onSelectionChange,
  onRowClick,
  onViewItem,
  onEditItem,
  onDeleteItem,
  onDownloadItem,
  allLibraryItems, // Add to destructuring
}: LibraryTableProps) {
  // Get appropriate columns based on mode
  const columns = React.useMemo(() => {
    if (mode === 'selection') {
      return getSelectionColumns(
        selectedIds,
        onSelectionChange || (() => {}),
        data,
        allLibraryItems,
      );
    } else {
      return getLibraryColumns(
        onViewItem || (() => {}),
        onEditItem || (() => {}),
        onDeleteItem || (() => {}),
        onDownloadItem,
      );
    }
  }, [
    mode,
    selectedIds,
    onSelectionChange,
    data,
    allLibraryItems, // Add to dependencies
    onViewItem,
    onEditItem,
    onDeleteItem,
    onDownloadItem,
  ]);

  return (
    <DataTable
      columns={columns}
      data={data}
      loading={loading}
      handleRowClick={onRowClick ? (row) => onRowClick(row.original) : undefined}
    />
  );
}
