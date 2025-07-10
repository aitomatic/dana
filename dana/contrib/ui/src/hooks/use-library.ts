import { useState, useMemo } from 'react';
import type { LibraryItem, LibraryFilters } from '@/types/library';

export function useLibrary(initialData: LibraryItem[] = []) {
  const [data, setData] = useState<LibraryItem[]>(initialData);
  const [filters, setFilters] = useState<LibraryFilters>({
    search: '',
    type: 'all',
  });

  const filteredData = useMemo(() => {
    return data.filter((item) => {
      const matchesSearch = item.name.toLowerCase().includes(filters.search.toLowerCase());
      const matchesType =
        filters.type === 'all' ||
        (filters.type === 'files' && item.type === 'file') ||
        (filters.type === 'folders' && item.type === 'folder');
      const matchesExtension =
        !filters.extension || (item.type === 'file' && item.extension === filters.extension);

      return matchesSearch && matchesType && matchesExtension;
    });
  }, [data, filters]);

  const updateFilters = (newFilters: Partial<LibraryFilters>) => {
    setFilters((prev) => ({ ...prev, ...newFilters }));
  };

  const addItem = (item: LibraryItem) => {
    setData((prev) => [...prev, item]);
  };

  const removeItem = (id: string) => {
    setData((prev) => prev.filter((item) => item.id !== id));
  };

  const updateItem = (id: string, updates: Partial<LibraryItem>) => {
    setData((prev) =>
      prev.map((item) => (item.id === id ? ({ ...item, ...updates } as LibraryItem) : item)),
    );
  };

  return {
    data,
    filteredData,
    filters,
    updateFilters,
    addItem,
    removeItem,
    updateItem,
  };
}
