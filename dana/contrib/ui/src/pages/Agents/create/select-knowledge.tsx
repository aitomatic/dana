import { useState, useMemo } from 'react';
import { FileUpload } from '@/components/library/file-upload';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { IconSearch, IconFilter, IconArrowLeft } from '@tabler/icons-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { toast } from 'sonner';
import type { LibraryItem, FileItem } from '@/types/library';
import FileIcon from '@/components/file-icon';
import { Trash } from 'iconoir-react';
import { LibraryTable, useLibraryTable } from '@/components/library';

export default function SelectKnowledgePage() {
  // Use the new library table hook
  const {
    filteredItems,
    selectedItems,
    searchTerm,
    typeFilter,
    selectedIds,
    folderState,
    isLoading,
    error,
    setSearchTerm,
    setTypeFilter,
    setSelectedIds,
    navigateToFolder,
    navigateToRoot,
    uploadDocument,
    clearError,
  } = useLibraryTable({
    enableFolderNavigation: true,
    enableSelection: true,
  });

  // Local state for sidebar search
  const [sidebarSearch, setSidebarSearch] = useState('');

  // Row click handlers
  const handleRowClick = (item: LibraryItem) => {
    if (item.type === 'folder') {
      // Navigate to folder
      navigateToFolder(item);
    } else {
      // For files, just log for now (could open preview later)
      console.log('View document:', item);
    }
  };

  // Filter selected items based on sidebar search
  const filteredSelectedItems = useMemo(
    () =>
      selectedItems.filter((item) => item.name.toLowerCase().includes(sidebarSearch.toLowerCase())),
    [selectedItems, sidebarSearch],
  );

  return (
    <div className="flex flex-col h-[calc(100vh-70px)] w-full">
      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Library & Upload */}
        <div className="flex flex-col flex-1 p-6 gap-4 overflow-hidden">
          <span className="text-lg font-semibold">Assign Knowledge Sources</span>
          {/* Upload */}
          <div className="mb-4 bg-gray-50">
            <FileUpload
              onFilesSelected={async (files: File[]) => {
                try {
                  for (const file of files) {
                    await uploadDocument({
                      file,
                      title: file.name,
                      description: `Uploaded: ${file.name}`,
                    });
                  }
                  toast.success('Documents uploaded successfully');
                } catch {
                  toast.error('Failed to upload documents');
                }
              }}
            />
          </div>
          {/* Search and Filters */}
          <div className="flex items-center space-x-4 mb-4">
            <div className="relative flex-1 max-w-sm">
              <IconSearch className="absolute left-3 top-1/2 w-4 h-4 text-gray-400 transform -translate-y-1/2" />
              <Input
                placeholder="Search topics and documents..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline">
                  <IconFilter className="mr-2 w-4 h-4" />
                  {typeFilter === 'all' ? 'All' : typeFilter === 'files' ? 'Documents' : 'Topics'}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => setTypeFilter('all')}>All Items</DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTypeFilter('files')}>
                  Documents Only
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTypeFilter('folders')}>
                  Topics Only
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {/* Error Display */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg mb-4">
              <p className="text-red-800">{error}</p>
              <Button variant="ghost" size="sm" onClick={clearError} className="mt-2">
                Dismiss
              </Button>
            </div>
          )}

          {/* Breadcrumb Navigation */}
          {folderState.isInFolder && (
            <div className="flex items-center space-x-2 mb-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={navigateToRoot}
                className="text-gray-600 hover:text-gray-900"
              >
                <IconArrowLeft className="w-4 h-4 mr-1" />
                Back to Library
              </Button>
            </div>
          )}

          {/* Library Table */}
          <div className="flex-1 min-h-0">
            <LibraryTable
              data={filteredItems}
              loading={isLoading}
              mode="selection"
              selectedIds={selectedIds}
              onSelectionChange={setSelectedIds}
              onRowClick={handleRowClick}
            />
          </div>
        </div>
        {/* Right: Selected Sidebar */}
        <div className="w-80 bg-white flex flex-col p-6">
          <span className="font-semibold mb-2">
            Selected Items ({filteredSelectedItems.length})
          </span>
          <Input
            placeholder="Search"
            value={sidebarSearch}
            onChange={(e) => setSidebarSearch(e.target.value)}
            className="mb-4"
          />
          <div className="flex-1 overflow-y-auto border border-gray-200 rounded-lg p-4">
            {filteredSelectedItems.length === 0 ? (
              <span className="text-gray-400">No items selected</span>
            ) : (
              <ul className="space-y-2">
                {filteredSelectedItems.map((item: LibraryItem) => (
                  <li
                    key={item.id}
                    className="flex items-center justify-between p-2 rounded hover:bg-gray-50"
                  >
                    <div className="flex items-center space-x-2 min-w-0 flex-1">
                      <div className="flex-shrink-0">
                        <FileIcon
                          ext={item.type === 'file' ? (item as FileItem).extension : undefined}
                        />
                      </div>
                      <span className="text-gray-900 text-sm font-medium truncate">
                        {item.name}
                      </span>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="flex-shrink-0 ml-2"
                      onClick={() => setSelectedIds(selectedIds.filter((id) => id !== item.id))}
                    >
                      <Trash className="size-4" strokeWidth={2} />
                    </Button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
      {/* Footer */}
      <div className="flex justify-end gap-4 px-6 py-4 border-t bg-white">
        <Button variant="default">Save & Finish</Button>
      </div>
    </div>
  );
}
