import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useFolderNavigation } from '../use-folder-navigation';
import type { LibraryItem, FolderItem } from '@/types/library';

// Mock console.log to avoid noise in tests
const originalConsoleLog = console.log;
beforeEach(() => {
  console.log = vi.fn();
});

afterEach(() => {
  console.log = originalConsoleLog;
});

describe('useFolderNavigation', () => {
  const mockFolder: FolderItem = {
    id: 'topic-1',
    name: 'Test Folder',
    type: 'folder',
    itemCount: 5,
    lastModified: new Date('2024-01-01'),
    path: '/test-folder',
    topicId: 1,
  };

  const mockFile: LibraryItem = {
    id: 'file-1',
    name: 'test.pdf',
    type: 'file',
    size: 1024,
    extension: 'pdf',
    lastModified: new Date('2024-01-01'),
    path: '/test-folder/test.pdf',
    topicId: 1,
  };

  const mockRootFile: LibraryItem = {
    id: 'file-2',
    name: 'root-file.pdf',
    type: 'file',
    size: 2048,
    extension: 'pdf',
    lastModified: new Date('2024-01-01'),
    path: '/root-file.pdf',
  };

  const mockLibraryItems: LibraryItem[] = [mockFolder, mockFile, mockRootFile];

  it('should initialize with root state', () => {
    const { result } = renderHook(() => useFolderNavigation());

    expect(result.current.folderState.currentPath).toBe('/');
    expect(result.current.folderState.currentFolderId).toBeUndefined();
    expect(result.current.folderState.isInFolder).toBe(false);
    expect(result.current.folderState.breadcrumbs).toEqual([
      { id: 'root', name: 'Library', path: '/', type: 'root' },
    ]);
  });

  it('should navigate to folder correctly', () => {
    const { result } = renderHook(() => useFolderNavigation());

    act(() => {
      result.current.navigateToFolder(mockFolder);
    });

    expect(result.current.folderState.currentPath).toBe('/test-folder');
    expect(result.current.folderState.currentFolderId).toBe('topic-1');
    expect(result.current.folderState.isInFolder).toBe(true);
  });

  it('should navigate to path correctly', () => {
    const { result } = renderHook(() => useFolderNavigation());

    act(() => {
      result.current.navigateToPath('/deep/nested/folder');
    });

    expect(result.current.folderState.currentPath).toBe('/deep/nested/folder');
    expect(result.current.folderState.currentFolderId).toBe('topic-folder');
    expect(result.current.folderState.isInFolder).toBe(true);
  });

  it('should navigate to root correctly', () => {
    const { result } = renderHook(() => useFolderNavigation());

    // First navigate to a folder
    act(() => {
      result.current.navigateToFolder(mockFolder);
    });

    expect(result.current.folderState.isInFolder).toBe(true);

    // Then navigate to root
    act(() => {
      result.current.navigateToRoot();
    });

    expect(result.current.folderState.currentPath).toBe('/');
    expect(result.current.folderState.currentFolderId).toBeUndefined();
    expect(result.current.folderState.isInFolder).toBe(false);
  });

  it('should generate breadcrumbs for root path', () => {
    const { result } = renderHook(() => useFolderNavigation());

    expect(result.current.folderState.breadcrumbs).toEqual([
      { id: 'root', name: 'Library', path: '/', type: 'root' },
    ]);
  });

  it('should generate breadcrumbs for single level path', () => {
    const { result } = renderHook(() => useFolderNavigation());

    act(() => {
      result.current.navigateToPath('/test-folder');
    });

    expect(result.current.folderState.breadcrumbs).toEqual([
      { id: 'root', name: 'Library', path: '/', type: 'root' },
      { id: 'folder-0', name: 'test-folder', path: '/test-folder', type: 'folder' },
    ]);
  });

  it('should generate breadcrumbs for nested path', () => {
    const { result } = renderHook(() => useFolderNavigation());

    act(() => {
      result.current.navigateToPath('/level1/level2/level3');
    });

    expect(result.current.folderState.breadcrumbs).toEqual([
      { id: 'root', name: 'Library', path: '/', type: 'root' },
      { id: 'folder-0', name: 'level1', path: '/level1', type: 'folder' },
      { id: 'folder-1', name: 'level2', path: '/level1/level2', type: 'folder' },
      { id: 'folder-2', name: 'level3', path: '/level1/level2/level3', type: 'folder' },
    ]);
  });

  it('should get root level items correctly', () => {
    const { result } = renderHook(() => useFolderNavigation());

    const rootItems = result.current.getItemsInCurrentFolder(mockLibraryItems);

    // Should show folders and files without topicId
    expect(rootItems).toHaveLength(2);
    expect(rootItems).toContain(mockFolder);
    expect(rootItems).toContain(mockRootFile);
    expect(rootItems).not.toContain(mockFile); // File with topicId should not be shown
  });

  it('should get folder items correctly when inside a folder', () => {
    const { result } = renderHook(() => useFolderNavigation());

    // Navigate to folder
    act(() => {
      result.current.navigateToFolder(mockFolder);
    });

    const folderItems = result.current.getItemsInCurrentFolder(mockLibraryItems);

    // Should show only files that belong to this topic, not folders
    expect(folderItems).toHaveLength(1);
    expect(folderItems).toContain(mockFile);
    expect(folderItems).not.toContain(mockFolder); // Folders should be hidden
    expect(folderItems).not.toContain(mockRootFile); // Files from other topics should not be shown
  });

  it('should return empty array when no folder ID is set', () => {
    const { result } = renderHook(() => useFolderNavigation());

    // Navigate to path but don't set folder ID
    act(() => {
      result.current.navigateToPath('/invalid-path');
    });

    const items = result.current.getItemsInCurrentFolder(mockLibraryItems);

    expect(items).toEqual([]);
  });

  it('should handle empty items array', () => {
    const { result } = renderHook(() => useFolderNavigation());

    const items = result.current.getItemsInCurrentFolder([]);

    expect(items).toEqual([]);
  });

  it('should handle items with undefined topicId', () => {
    const { result } = renderHook(() => useFolderNavigation());

    const itemsWithUndefinedTopicId: LibraryItem[] = [
      {
        id: 'file-3',
        name: 'no-topic.pdf',
        type: 'file',
        size: 512,
        extension: 'pdf',
        lastModified: new Date('2024-01-01'),
        path: '/no-topic.pdf',
        topicId: undefined,
      },
    ];

    const rootItems = result.current.getItemsInCurrentFolder(itemsWithUndefinedTopicId);

    expect(rootItems).toHaveLength(1);
    expect(rootItems[0].id).toBe('file-3');
  });

  it('should handle navigation with complex folder structure', () => {
    const { result } = renderHook(() => useFolderNavigation());

    // Navigate to nested path
    act(() => {
      result.current.navigateToPath('/documents/2024/reports');
    });

    expect(result.current.folderState.currentPath).toBe('/documents/2024/reports');
    expect(result.current.folderState.currentFolderId).toBe('topic-reports');
    expect(result.current.folderState.breadcrumbs).toHaveLength(4);
    expect(result.current.folderState.breadcrumbs[3].name).toBe('reports');
  });

  it('should maintain state consistency across multiple operations', () => {
    const { result } = renderHook(() => useFolderNavigation());

    // Navigate to folder
    act(() => {
      result.current.navigateToFolder(mockFolder);
    });

    expect(result.current.folderState.isInFolder).toBe(true);

    // Navigate to different path
    act(() => {
      result.current.navigateToPath('/another/path');
    });

    expect(result.current.folderState.currentPath).toBe('/another/path');
    expect(result.current.folderState.currentFolderId).toBe('topic-path');

    // Navigate back to root
    act(() => {
      result.current.navigateToRoot();
    });

    expect(result.current.folderState.currentPath).toBe('/');
    expect(result.current.folderState.currentFolderId).toBeUndefined();
    expect(result.current.folderState.isInFolder).toBe(false);
  });
});
