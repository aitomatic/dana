import type { ColumnDef } from '@tanstack/react-table';
import type { LibraryItem, FileItem, FolderItem } from '@/types/library';
import { DataTableColumnHeader } from '@/components/table/data-table-column-header';
import { Checkbox } from '@/components/ui/checkbox';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { IconDotsVertical, IconEye, IconDownload, IconEdit, IconTrash } from '@tabler/icons-react';
import { cn } from '@/lib/utils';
import FileIcon from '@/components/file-icon';
import { formatFileSize, formatDate } from './library-utils';

// Common columns that are shared between library and selection modes
export const getCommonColumns = (): ColumnDef<LibraryItem>[] => [
  {
    accessorKey: 'name',
    header: ({ column }) => <DataTableColumnHeader column={column} title="Name" />,
    cell: ({ row }) => {
      const item = row.original;
      return (
        <div className="flex space-x-3">
          <FileIcon ext={item.type === 'file' ? (item as FileItem).extension : undefined} />
          <div className="flex flex-col">
            <span className="font-medium text-gray-900">{item.name}</span>
            <span className="text-sm text-gray-500">{item.path}</span>
          </div>
        </div>
      );
    },
  },
  {
    accessorKey: 'type',
    header: ({ column }) => <DataTableColumnHeader column={column} title="Type" />,
    cell: ({ row }) => {
      const item = row.original;
      return (
        <div className="flex items-center">
          <span
            className={cn(
              'px-2 py-1 text-xs font-medium rounded-full',
              item.type === 'folder' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800',
            )}
          >
            {item.type === 'folder' ? 'Topic' : (item as FileItem).extension.toUpperCase()}
          </span>
        </div>
      );
    },
  },
  {
    accessorKey: 'size',
    header: ({ column }) => <DataTableColumnHeader column={column} title="Size" />,
    cell: ({ row }) => {
      const item = row.original;
      if (item.type === 'folder') {
        return <span className="text-gray-500">{(item as FolderItem).itemCount} items</span>;
      }
      return <span className="text-gray-900">{formatFileSize((item as FileItem).size)}</span>;
    },
  },
  {
    accessorKey: 'lastModified',
    header: ({ column }) => <DataTableColumnHeader column={column} title="Last Modified" />,
    cell: ({ row }) => {
      return (
        <span className="text-gray-600">{formatDate(row.original.lastModified.toISOString())}</span>
      );
    },
  },
];

// Selection mode columns (with checkboxes)
export const getSelectionColumns = (
  selectedIds: string[],
  onSelectionChange: (ids: string[]) => void,
  filteredItems: LibraryItem[],
): ColumnDef<LibraryItem>[] => [
  {
    id: 'select',
    header: () => (
      <Checkbox
        checked={
          filteredItems.length > 0
            ? filteredItems.every((item: LibraryItem) => selectedIds.includes(item.id))
              ? true
              : filteredItems.some((item: LibraryItem) => selectedIds.includes(item.id))
                ? 'indeterminate'
                : false
            : false
        }
        onCheckedChange={(checked) => {
          if (checked) {
            onSelectionChange(
              Array.from(
                new Set([...selectedIds, ...filteredItems.map((item: LibraryItem) => item.id)]),
              ),
            );
          } else {
            onSelectionChange(
              selectedIds.filter(
                (id) => !filteredItems.map((item: LibraryItem) => item.id).includes(id),
              ),
            );
          }
        }}
      />
    ),
    cell: ({ row }) => (
      <Checkbox
        checked={selectedIds.includes(row.original.id)}
        onCheckedChange={(checked) => {
          onSelectionChange(
            checked
              ? [...selectedIds, row.original.id]
              : selectedIds.filter((id) => id !== row.original.id),
          );
        }}
      />
    ),
  },
  ...getCommonColumns(),
];

// Library mode columns (with actions dropdown)
export const getLibraryColumns = (
  onViewItem: (item: LibraryItem) => void,
  onEditItem: (item: LibraryItem) => void,
  onDeleteItem: (item: LibraryItem) => void,
  onDownloadItem?: (item: LibraryItem) => void,
): ColumnDef<LibraryItem>[] => [
  ...getCommonColumns(),
  {
    id: 'actions',
    header: ({ column }) => <DataTableColumnHeader column={column} title="Actions" />,
    cell: ({ row }) => {
      const item = row.original;
      return (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="p-0 w-8 h-8">
              <IconDotsVertical className="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => onViewItem(item)}>
              <IconEye className="mr-2 w-4 h-4" />
              View
            </DropdownMenuItem>
            {item.type === 'file' && onDownloadItem && (
              <DropdownMenuItem onClick={() => onDownloadItem(item)}>
                <IconDownload className="mr-2 w-4 h-4" />
                Download
              </DropdownMenuItem>
            )}
            <DropdownMenuItem onClick={() => onEditItem(item)}>
              <IconEdit className="mr-2 w-4 h-4" />
              Edit
            </DropdownMenuItem>
            <DropdownMenuItem className="text-red-600" onClick={() => onDeleteItem(item)}>
              <IconTrash className="mr-2 w-4 h-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
    },
  },
];
