import { useState, useEffect, useMemo } from 'react';
import type { LibraryItem, FolderItem } from '@/types/library';
import { useTopicOperations, useDocumentOperations } from '@/hooks/use-api';
import { useFolderNavigation } from '@/hooks/use-folder-navigation';
import { processLibraryItems } from '@/components/library/library-utils';

interface UseLibraryTableOptions {
  enableFolderNavigation?: boolean;
  enableSelection?: boolean;
}

interface UseLibraryTableReturn {
  // Data
  libraryItems: LibraryItem[];
  filteredItems: LibraryItem[];
  selectedItems: LibraryItem[];

  // State
  searchTerm: string;
  typeFilter: 'all' | 'files' | 'folders';
  selectedIds: string[];
  folderState: any;

  // Loading and error states
  isLoading: boolean;
  error: string | null;

  // Actions
  setSearchTerm: (term: string) => void;
  setTypeFilter: (filter: 'all' | 'files' | 'folders') => void;
  setSelectedIds: (ids: string[]) => void;
  navigateToFolder: (folder: FolderItem) => void;
  navigateToRoot: () => void;

  // API operations
  uploadDocument: (params: any) => Promise<void>;
  clearError: () => void;
}

export function useLibraryTable(options: UseLibraryTableOptions = {}): UseLibraryTableReturn {
  const { enableFolderNavigation = true, enableSelection = false } = options;

  // API hooks
  const {
    fetchTopics,
    topics,
    isLoading: topicsLoading,
    error: topicsError,
    clearError: clearTopicsError,
  } = useTopicOperations();

  const {
    fetchDocuments,
    uploadDocument: uploadDocDocument,
    documents,
    isLoading: documentsLoading,
    error: documentsError,
    clearError: clearDocumentsError,
  } = useDocumentOperations();

  // Folder navigation
  const folderNavigation = useFolderNavigation();
  const { folderState, navigateToFolder, navigateToRoot, getItemsInCurrentFolder } =
    enableFolderNavigation
      ? folderNavigation
      : {
          folderState: { isInFolder: false },
          navigateToFolder: () => {},
          navigateToRoot: () => {},
          getItemsInCurrentFolder: (items: LibraryItem[]) => items,
        };

  // Local state
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<'all' | 'files' | 'folders'>('all');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  // Fetch data on mount
  useEffect(() => {
    fetchTopics();
    fetchDocuments();
  }, [fetchTopics, fetchDocuments]);

  // Process library items
  const libraryItems = useMemo(() => {
    return processLibraryItems(topics, documents);
  }, [topics, documents]);

  // Get items in current folder
  const currentFolderItems = useMemo(() => {
    return getItemsInCurrentFolder(libraryItems);
  }, [getItemsInCurrentFolder, libraryItems]);

  // Filter items based on search and type
  const filteredItems = useMemo(() => {
    return currentFolderItems.filter((item) => {
      const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase());

      // When inside a folder, only show files (folders are hidden)
      let matchesType = true;
      if (folderState.isInFolder) {
        matchesType = item.type === 'file';
      } else {
        matchesType =
          typeFilter === 'all' ||
          (typeFilter === 'files' && item.type === 'file') ||
          (typeFilter === 'folders' && item.type === 'folder');
      }

      return matchesSearch && matchesType;
    });
  }, [currentFolderItems, searchTerm, typeFilter, folderState.isInFolder]);

  // Selected items for sidebar (only if selection is enabled)
  const selectedItems = useMemo(() => {
    if (!enableSelection) return [];
    return libraryItems.filter((item) => selectedIds.includes(item.id));
  }, [libraryItems, selectedIds, enableSelection]);

  // Combined upload function
  const uploadDocument = async (params: any) => {
    return uploadDocDocument(params);
  };

  // Combined error handling
  const error = topicsError || documentsError;
  const isLoading = topicsLoading || documentsLoading;
  const clearError = () => {
    clearTopicsError();
    clearDocumentsError();
  };

  return {
    // Data
    libraryItems,
    filteredItems,
    selectedItems,

    // State
    searchTerm,
    typeFilter,
    selectedIds,
    folderState,

    // Loading and error states
    isLoading,
    error,

    // Actions
    setSearchTerm,
    setTypeFilter,
    setSelectedIds,
    navigateToFolder,
    navigateToRoot,

    // API operations
    uploadDocument,
    clearError,
  };
}
