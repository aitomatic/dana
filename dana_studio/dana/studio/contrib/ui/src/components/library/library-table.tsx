import React from 'react';
import { DataTable } from '@/components/table/data-table';
import type { LibraryItem, FileItem } from '@/types/library';
import { getLibraryColumns, getSelectionColumns } from './library-columns';
import { TEMPLATE_GENERATION_STATUS } from '@/lib/constants';

interface LibraryTableProps {
  data: LibraryItem[];
  loading?: boolean;
  mode: 'library' | 'selection';
  selectedIds?: string[];
  onSelectionChange?: ((ids: string[]) => void) | ((item: LibraryItem) => void);
  onRowClick?: (item: LibraryItem) => void;
  onViewItem?: (item: LibraryItem) => void;
  onEditItem?: (item: LibraryItem) => void;
  onDeleteItem?: (item: LibraryItem) => void;
  allLibraryItems?: LibraryItem[]; // Add prop for all library items
  // New props for Knowledge Pack file selection
  selectionMode?: 'none' | 'multiple' | 'single'; // Added 'single' for radio buttons
  selectedItems?: LibraryItem[];
  filterType?: 'all' | 'knowledge-packs' | 'contribution-templates'; // Filter items by type
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
  allLibraryItems,
  selectionMode = 'none',
  selectedItems = [],
  filterType = 'all',
}: LibraryTableProps) {
  // Filter data by type if needed
  const filteredData = React.useMemo(() => {
    if (filterType === 'knowledge-packs') {
      return data.filter((item) => item.type === 'file' && (item as FileItem).extension === 'kp');
    }
    if (filterType === 'contribution-templates') {
      return data.filter((item) => {
        if (item.type === 'file' && (item as FileItem).extension === 'template') {
          const fileItem = item as FileItem;
          // Only show completed templates for selection
          return fileItem.metadata?.status === TEMPLATE_GENERATION_STATUS.COMPLETED;
        }
        return false;
      });
    }
    return data;
  }, [data, filterType]);

  // Convert selectedItems to selectedIds for backward compatibility
  const effectiveSelectedIds = React.useMemo(() => {
    if ((selectionMode === 'multiple' || selectionMode === 'single') && selectedItems.length > 0) {
      return selectedItems.map((item) => item.id);
    }
    return selectedIds;
  }, [selectionMode, selectedItems, selectedIds]);

  // Wrapper for onSelectionChange to handle both patterns
  const handleSelectionChange = React.useCallback(
    (ids: string[]) => {
      if ((selectionMode === 'multiple' || selectionMode === 'single') && onSelectionChange) {
        // Find the item that was toggled
        const addedId = ids.find((id) => !effectiveSelectedIds.includes(id));
        const removedId = effectiveSelectedIds.find((id) => !ids.includes(id));
        const toggledId = addedId || removedId;
        const toggledItem = filteredData.find((item) => item.id === toggledId);

        if (toggledItem) {
          (onSelectionChange as (item: LibraryItem) => void)(toggledItem);
        }
      } else if (typeof onSelectionChange === 'function') {
        (onSelectionChange as (ids: string[]) => void)(ids);
      }
    },
    [selectionMode, onSelectionChange, effectiveSelectedIds, filteredData],
  );

  // Determine effective mode
  const effectiveMode =
    selectionMode === 'multiple' || selectionMode === 'single' ? 'selection' : mode;

  // Get appropriate columns based on mode
  const columns = React.useMemo(() => {
    if (effectiveMode === 'selection') {
      return getSelectionColumns(
        effectiveSelectedIds,
        handleSelectionChange,
        filteredData,
        allLibraryItems,
        selectionMode === 'single', // Pass radio button mode flag
      );
    } else {
      return getLibraryColumns(
        onViewItem || (() => {}),
        onEditItem || (() => {}),
        onDeleteItem || (() => {}),
      );
    }
  }, [
    effectiveMode,
    effectiveSelectedIds,
    handleSelectionChange,
    filteredData,
    allLibraryItems,
    onViewItem,
    onEditItem,
    onDeleteItem,
    selectionMode,
  ]);

  // Get children for expandable rows (e.g., templates within knowledge packs)
  const getRowChildren = React.useCallback((row: LibraryItem) => {
    // Check if row is a FileItem with children
    if (row.type === 'file' && 'children' in row) {
      return row.children;
    }
    return undefined;
  }, []);

  return (
    <DataTable
      columns={columns}
      data={filteredData}
      loading={loading}
      handleRowClick={onRowClick ? (row) => onRowClick(row.original) : undefined}
      defaultSorting={[{ id: 'created', desc: true }]}
      getRowChildren={getRowChildren}
    />
  );
}
