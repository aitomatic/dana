import { useState, useMemo, useEffect } from 'react';
import { FileUpload } from '@/components/library/file-upload';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { IconSearch, IconFilter, IconArrowLeft, IconRefresh } from '@tabler/icons-react';
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

interface SelectKnowledgePageProps {
  onCreateAgent: () => Promise<void>;
  isCreating: boolean;
  error: string | null;
  form: any; // Add form prop to access form methods
}

export default function SelectKnowledgePage({
  onCreateAgent,
  isCreating,
  error,
  form,
}: SelectKnowledgePageProps) {
  // Use the new library table hook
  const {
    filteredItems,
    selectedItems,
    searchTerm,
    typeFilter,
    selectedIds,
    folderState,
    isLoading,
    error: libraryError,
    setSearchTerm,
    setTypeFilter,
    setSelectedIds,
    navigateToFolder,
    navigateToRoot,
    uploadDocument,
    clearError,
    libraryItems, // Add access to all library items
  } = useLibraryTable({
    enableFolderNavigation: true,
    enableSelection: true,
  });

  // Get topics and documents counts
  const topicsCount = libraryItems.filter(item => item.type === 'folder').length;
  const documentsCount = libraryItems.filter(item => item.type === 'file').length;

  console.log({ selectedItems, selectedIds });

  // Debug logging
  useEffect(() => {
    console.log('Library items loaded:', libraryItems);
    console.log('Topics count:', topicsCount);
    console.log('Documents count:', documentsCount);
    console.log('Is loading:', isLoading);
    console.log('Error:', libraryError);
  }, [libraryItems, topicsCount, documentsCount, isLoading, libraryError]);

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

  // Update form with selected knowledge when selection changes
  useEffect(() => {
    const selectedTopics: number[] = [];
    const selectedDocuments: number[] = [];

    selectedItems.forEach((item) => {
      if (item.type === 'folder') {
        // Topics are represented as folders
        const id = item.id.split('-')[1];
        selectedTopics.push(parseInt(id));
      } else if (item.type === 'file') {
        // Documents are represented as files
        const id = item.id.split('-')[1];
        selectedDocuments.push(parseInt(id));
      }
    });

    form.setValue('selectedKnowledge', {
      topics: selectedTopics,
      documents: selectedDocuments,
    });
  }, [selectedItems, form]);

  console.log('selectedKnowledge', form.getValues('selectedKnowledge'));

  return (
    <div className="flex flex-col h-[calc(100vh-70px)] w-full gap-4">
      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden px-6 pt-4 gap-4">
        {/* Left: Library & Upload */}
        <div className="flex flex-col flex-1 gap-6 overflow-hidden">
          <span className="text-lg font-semibold">Assign Knowledge Sources</span>

          {/* Loading and Data Status */}
          {isLoading && (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-blue-800">Loading topics and documents...</p>
            </div>
          )}

          {!isLoading && libraryItems.length === 0 && (
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-yellow-800">
                No topics or documents found. You can upload documents below or create topics first.
              </p>
            </div>
          )}

          {!isLoading && libraryItems.length > 0 && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-green-800">
                Found {libraryItems.length} items ({topicsCount} topics, {documentsCount} documents)
              </p>
            </div>
          )}
          {/* Upload */}
          <div className="bg-gray-50">
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
          <div className="flex items-center space-x-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                // Trigger a refresh of the data
                window.location.reload();
              }}
              className="flex items-center gap-2"
            >
              <IconRefresh className="w-4 h-4" />
              Refresh
            </Button>
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
          {(error || libraryError) && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg mb-4">
              <p className="text-red-800">{error || libraryError}</p>
              <Button variant="ghost" size="sm" onClick={clearError} className="mt-2">
                Dismiss
              </Button>
            </div>
          )}

          {/* Breadcrumb Navigation */}
          {folderState.isInFolder && (
            <div className="flex items-center space-x-2">
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
              allLibraryItems={libraryItems}
            />
          </div>
        </div>
        {/* Right: Selected Sidebar */}
        <div className="w-80 bg-white flex flex-col gap-2">
          <span className="font-semibold">Selected Items ({filteredSelectedItems.length})</span>
          <Input
            placeholder="Search"
            value={sidebarSearch}
            onChange={(e) => setSidebarSearch(e.target.value)}
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
        <Button variant="default" onClick={onCreateAgent} disabled={isCreating}>
          {isCreating ? 'Creating Agent...' : 'Save & Finish'}
        </Button>
      </div>
    </div>
  );
}
