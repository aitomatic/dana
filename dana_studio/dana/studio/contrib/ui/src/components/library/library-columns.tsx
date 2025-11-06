/* eslint-disable @typescript-eslint/no-explicit-any */
import type { ColumnDef } from '@tanstack/react-table';
import type { LibraryItem, FileItem } from '@/types/library';
import { DataTableColumnHeader } from '@/components/table/data-table-column-header';
import { Checkbox } from '@/components/ui/checkbox';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { IconDotsVertical, IconEye, IconEdit, IconTrash, IconSchool } from '@tabler/icons-react';
import { NetworkRightSolid, PasteClipboard } from 'iconoir-react';
import { cn } from '@/lib/utils';
import FileIcon from '@/components/file-icon';
import { formatDate } from './library-utils';
import {
  KNOWLEDGE_GENERATION_STATUS,
  TEMPLATE_GENERATION_STATUS,
  SESSION_STATUS,
} from '@/lib/constants';
import { toast } from 'sonner';

// Helper function to get extraction status
const getExtractionStatus = (metadata?: Record<string, any>) => {
  if (!metadata) return 'Not extracted';

  if (metadata.deep_extracted === true) {
    return 'Deep extracted';
  }

  if (metadata.deep_extracted === false && metadata.processing_status === 'processing') {
    return 'Deep extracting';
  }

  return 'Standard extracted';
};


// Common columns that are shared between library and selection modes
export const getCommonColumns = (): ColumnDef<LibraryItem>[] => [
  {
    id: 'expand',
    header: () => null,
    size: 50,
    meta: {
      style: { width: '50px', minWidth: '50px', maxWidth: '50px' },
    },
    cell: () => null, // Empty cell - expand logic is handled in data-table.tsx
  },
  {
    accessorKey: 'name',
    enableSorting: true,
    size: 520,
    meta: {
      style: { maxWidth: '520px', overflow: 'hidden' },
    },
    header: ({ column }) => <DataTableColumnHeader column={column} title="Name" />,
    cell: ({ row }) => {
      const item = row.original;
      const isKnowledgePack = item.type === 'file' && (item as FileItem).extension === 'kp';
      const isTemplate = item.type === 'file' && (item as FileItem).extension === 'template';
      const isExpertKnowledge = item.type === 'file' && (item as FileItem).extension === 'ek';

      return (
        <div className="flex items-center gap-2">
          {isKnowledgePack ? (
            <NetworkRightSolid className="w-5 h-5 mt-0.5 text-orange-500 flex-shrink-0" />
          ) : isTemplate ? (
            <PasteClipboard className="w-5 h-5 mt-0.5 text-[#0BA5EC] flex-shrink-0" />
          ) : isExpertKnowledge ? (
            <IconSchool className="w-5 h-5 mt-0.5 text-green-600 flex-shrink-0" />
          ) : (
            <FileIcon ext={item.type === 'file' ? (item as FileItem).extension : undefined} className="flex-shrink-0" />
          )}
          <div className="flex flex-col min-w-0 flex-1">
            <span className="font-medium text-gray-900 truncate">{item.name}</span>
          </div>
        </div>
      );
    },
  },
  {
    accessorKey: 'type',
    enableSorting: true,
    sortingFn: (rowA, rowB) => {
      const itemA = rowA.original;
      const itemB = rowB.original;

      // First sort by type (folders first, then files)
      if (itemA.type !== itemB.type) {
        return itemA.type === 'folder' ? -1 : 1;
      }

      // If both are files, sort by extension
      if (itemA.type === 'file' && itemB.type === 'file') {
        const extA = (itemA as FileItem).extension.toLowerCase();
        const extB = (itemB as FileItem).extension.toLowerCase();
        return extA.localeCompare(extB);
      }

      return 0;
    },
    header: ({ column }) => <DataTableColumnHeader column={column} title="Type" />,
    cell: ({ row }) => {
      const item = row.original;
      const isTemplate = item.type === 'file' && (item as FileItem).extension === 'template';
      const isKnowledgePack = item.type === 'file' && (item as FileItem).extension === 'kp';
      const isExpertKnowledge = item.type === 'file' && (item as FileItem).extension === 'ek';

      let displayText = '';
      let colorClass = '';

      if (item.type === 'folder') {
        displayText = 'Topic';
        colorClass = 'bg-blue-100 text-blue-800';
      } else if (isKnowledgePack) {
        displayText = 'Knowledge Pack';
        colorClass = 'bg-cyan-50 text-cyan-800';
      } else if (isTemplate) {
        displayText = 'Capture Template';
        colorClass = 'bg-blue-50 text-blue-800';
      } else if (isExpertKnowledge) {
        displayText = 'Capture Knowledge';
        colorClass = 'bg-green-100 text-green-800';
      } else {
        displayText = (item as FileItem).extension.toUpperCase();
        colorClass = 'bg-gray-100 text-gray-800';
      }

      return (
        <div className="flex items-center">
          <span className={cn('px-2 py-1 text-xs font-medium rounded-full', colorClass)}>
            {displayText}
          </span>
        </div>
      );
    },
  },
  {
    accessorKey: 'status',
    enableSorting: true,
    sortingFn: (rowA, rowB) => {
      const itemA = rowA.original;
      const itemB = rowB.original;

      // Folders always show "-", deprioritize them
      if (itemA.type === 'folder' && itemB.type === 'folder') return 0;
      if (itemA.type === 'folder' && itemB.type === 'file') return 1;
      if (itemA.type === 'file' && itemB.type === 'folder') return -1;

      const fileA = itemA as FileItem;
      const fileB = itemB as FileItem;

      // Knowledge packs: sort by status (completed > generating > draft > failed)
      const isKpA = fileA.extension === 'kp';
      const isKpB = fileB.extension === 'kp';

      if (isKpA && isKpB) {
        const statusA = fileA.metadata?.status || KNOWLEDGE_GENERATION_STATUS.DRAFT;
        const statusB = fileB.metadata?.status || KNOWLEDGE_GENERATION_STATUS.DRAFT;
        const kpPriority = {
          [KNOWLEDGE_GENERATION_STATUS.COMPLETED]: 4,
          [KNOWLEDGE_GENERATION_STATUS.GENERATING]: 3,
          [KNOWLEDGE_GENERATION_STATUS.DRAFT]: 2,
          [KNOWLEDGE_GENERATION_STATUS.FAILED]: 1,
        };
        return (
          (kpPriority[statusB as keyof typeof kpPriority] || 1) -
          (kpPriority[statusA as keyof typeof kpPriority] || 1)
        );
      }

      // Templates: sort by their status (completed > generating > pending > draft > failed)
      const isTemplateA = fileA.extension === 'template';
      const isTemplateB = fileB.extension === 'template';

      if (isTemplateA && isTemplateB) {
        const statusA = fileA.metadata?.status || TEMPLATE_GENERATION_STATUS.DRAFT;
        const statusB = fileB.metadata?.status || TEMPLATE_GENERATION_STATUS.DRAFT;
        const templatePriority = {
          [TEMPLATE_GENERATION_STATUS.COMPLETED]: 5,
          [TEMPLATE_GENERATION_STATUS.GENERATING]: 4,
          [TEMPLATE_GENERATION_STATUS.PENDING]: 3,
          [TEMPLATE_GENERATION_STATUS.DRAFT]: 2,
          [TEMPLATE_GENERATION_STATUS.FAILED]: 1,
        };
        return (
          (templatePriority[statusB as keyof typeof templatePriority] || 1) -
          (templatePriority[statusA as keyof typeof templatePriority] || 1)
        );
      }

      if (isTemplateA && !isTemplateB) return 1;
      if (!isTemplateA && isTemplateB) return -1;

      // Capture Knowledge Sessions: sort by status (completed > in_progress > draft)
      const isEkA = fileA.extension === 'ek';
      const isEkB = fileB.extension === 'ek';

      if (isEkA && isEkB) {
        const statusA = fileA.metadata?.status || SESSION_STATUS.DRAFT;
        const statusB = fileB.metadata?.status || SESSION_STATUS.DRAFT;
        const ekPriority = {
          [SESSION_STATUS.COMPLETED]: 3,
          [SESSION_STATUS.IN_PROGRESS]: 2,
          [SESSION_STATUS.DRAFT]: 1,
        };
        return (
          (ekPriority[statusB as keyof typeof ekPriority] || 1) -
          (ekPriority[statusA as keyof typeof ekPriority] || 1)
        );
      }

      if (isEkA && !isEkB) return 1;
      if (!isEkA && isEkB) return -1;

      // Regular files: sort by extraction status
      const statusA = getExtractionStatus(fileA.metadata);
      const statusB = getExtractionStatus(fileB.metadata);

      const extractionPriority = {
        'Deep extracted': 3,
        'Standard extracted': 2,
        'Deep extracting': 1,
        'Not extracted': 0,
      };

      return (
        extractionPriority[statusB as keyof typeof extractionPriority] -
        extractionPriority[statusA as keyof typeof extractionPriority]
      );
    },
    size: 200,
    meta: {
      style: { width: '200px', minWidth: '200px', maxWidth: '200px' },
    },
    header: ({ column }) => <DataTableColumnHeader column={column} title="Status" />,
    cell: ({ row }) => {
      const item = row.original;

      // Folders don't have status
      if (item.type === 'folder') {
        return <span className="text-gray-400">-</span>;
      }

      const fileItem = item as FileItem;

      // Knowledge Packs: show their status (draft/generating/completed/failed)
      if (fileItem.extension === 'kp') {
        const status = fileItem.metadata?.status || KNOWLEDGE_GENERATION_STATUS.DRAFT;
        const getDotColor = (status: string) => {
          switch (status) {
            case KNOWLEDGE_GENERATION_STATUS.COMPLETED:
              return 'bg-green-500';
            case KNOWLEDGE_GENERATION_STATUS.DRAFT:
              return 'bg-gray-300';
            case KNOWLEDGE_GENERATION_STATUS.GENERATING:
              return 'bg-purple-500';
            case KNOWLEDGE_GENERATION_STATUS.FAILED:
              return 'bg-red-500';
            default:
              return 'bg-gray-400';
          }
        };
        
        return (
          <div className="flex items-center gap-2">
            <div className={cn('w-2 h-2 rounded-full', getDotColor(status))} />
            <span className="text-sm text-gray-700 capitalize">{status}</span>
          </div>
        );
      }

      // Templates: show their status (draft, completed, generating, etc.)
      if (fileItem.extension === 'template') {
        const templateStatus = fileItem.metadata?.status || TEMPLATE_GENERATION_STATUS.DRAFT;
        const getDotColor = (status: string) => {
          switch (status) {
            case TEMPLATE_GENERATION_STATUS.COMPLETED:
              return 'bg-green-500';
            case TEMPLATE_GENERATION_STATUS.DRAFT:
              return 'bg-gray-300';
            case TEMPLATE_GENERATION_STATUS.PENDING:
              return 'bg-blue-500';
            case TEMPLATE_GENERATION_STATUS.GENERATING:
              return 'bg-purple-500';
            case TEMPLATE_GENERATION_STATUS.FAILED:
              return 'bg-red-500';
            default:
              return 'bg-gray-400';
          }
        };
        
        return (
          <div className="flex items-center gap-2">
            <div className={cn('w-2 h-2 rounded-full', getDotColor(templateStatus))} />
            <span className="text-sm text-gray-700 capitalize">{templateStatus}</span>
          </div>
        );
      }

      // Capture Knowledge Sessions: show their status (draft, in_progress, completed)
      if (fileItem.extension === 'ek') {
        const sessionStatus = fileItem.metadata?.status || SESSION_STATUS.DRAFT;
        const getDotColor = (status: string) => {
          switch (status) {
            case SESSION_STATUS.COMPLETED:
              return 'bg-green-600';
            case SESSION_STATUS.DRAFT:
              return 'bg-gray-300';
            case SESSION_STATUS.IN_PROGRESS:
              return 'bg-yellow-500';
            default:
              return 'bg-gray-400';
          }
        };
        
        const displayStatus = sessionStatus === SESSION_STATUS.IN_PROGRESS ? 'In Progress' : sessionStatus;
        
        return (
          <div className="flex items-center gap-2">
            <div className={cn('w-2 h-2 rounded-full', getDotColor(sessionStatus))} />
            <span className="text-sm text-gray-700 capitalize">{displayStatus}</span>
          </div>
        );
      }

      // Regular documents: show extraction status
      const status = getExtractionStatus(fileItem.metadata);
      const getDotColor = (status: string) => {
        switch (status) {
          case 'Deep extracted':
            return 'bg-blue-500';
          case 'Deep extracting':
            return 'bg-yellow-500';
          case 'Standard extracted':
            return 'bg-gray-400';
          case 'Not extracted':
            return 'bg-gray-400';
          default:
            return 'bg-gray-400';
        }
      };

      return (
        <div className="flex items-center gap-2">
          <div className={cn('w-2 h-2 rounded-full', getDotColor(status))} />
          <span className="text-sm text-gray-700">{status}</span>
        </div>
      );
    },
  },
  {
    accessorKey: 'created',
    enableSorting: true,
    header: ({ column }) => <DataTableColumnHeader column={column} title="Created" />,
    cell: ({ row }) => {
      const created = row.original.created;
      // Handle both Date objects and string dates
      const dateString = typeof created === 'string' ? created : created?.toISOString?.() || '';
      return <span className="text-gray-600">{formatDate(dateString)}</span>;
    },
  },
];

// Selection mode columns (with checkboxes or radio buttons)
export const getSelectionColumns = (
  selectedIds: string[],
  onSelectionChange: (ids: string[]) => void,
  filteredItems: LibraryItem[],
  allLibraryItems?: LibraryItem[], // Add access to all library items for topic selection
  useRadioButtons = false, // NEW: Use radio buttons for single selection
): ColumnDef<LibraryItem>[] => [
  {
    id: 'select',
    header: () =>
      useRadioButtons ? null : (
        <Checkbox
          checked={
            filteredItems.length > 0
              ? filteredItems.every((item: LibraryItem) => selectedIds.includes(item.id))
                ? true
                : filteredItems.some((item: LibraryItem) => selectedIds.includes(item.id))
                  ? undefined
                  : false
              : false
          }
          onCheckedChange={(checked) => {
            if (checked) {
              // For header checkbox, select all visible items
              const visibleItemIds = filteredItems.map((item: LibraryItem) => item.id);
              onSelectionChange(Array.from(new Set([...selectedIds, ...visibleItemIds])));
            } else {
              // For header checkbox, deselect all visible items
              const visibleItemIds = filteredItems.map((item: LibraryItem) => item.id);
              onSelectionChange(selectedIds.filter((id) => !visibleItemIds.includes(id)));
            }
          }}
        />
      ),
    cell: ({ row }) => {
      const item = row.original;

      // Radio button mode - single selection only
      if (useRadioButtons) {
        const isSelected = selectedIds.includes(item.id);

        // Check if this is a KP and if it's completed
        const fileItem = item as FileItem;
        const isKP = item.type === 'file' && fileItem.extension === 'kp';
        const kpStatus = fileItem.metadata?.status;
        const isCompleted = kpStatus === KNOWLEDGE_GENERATION_STATUS.COMPLETED;
        const isDisabled = isKP && !isCompleted;

        return (
          <div
            onClick={(e) => e.stopPropagation()}
            title={isDisabled ? 'Only completed KPs can be selected' : ''}
          >
            <input
              type="radio"
              checked={isSelected}
              disabled={isDisabled}
              onChange={() => {
                if (isDisabled) {
                  toast.warning('Only completed Knowledge Packs can be used to create templates');
                  return;
                }
                // Radio button - only one selection at a time
                onSelectionChange([item.id]);
              }}
              className={cn(
                'w-4 h-4 border-gray-300 focus:ring-blue-500',
                isDisabled ? 'opacity-50 cursor-not-allowed' : 'text-blue-600 cursor-pointer',
              )}
            />
          </div>
        );
      }

      // For topics (folders), we need to handle selection of all files within the topic
      if (item.type === 'folder' && allLibraryItems) {
        const topicId = item.topicId;
        if (topicId) {
          // Find all documents that belong to this topic
          const topicDocuments = allLibraryItems.filter(
            (libraryItem) => libraryItem.type === 'file' && libraryItem.topicId === topicId,
          );
          const topicDocumentIds = topicDocuments.map((doc) => doc.id);

          // Check if all files in this topic are selected
          const allTopicFilesSelected =
            topicDocumentIds.length > 0 && topicDocumentIds.every((id) => selectedIds.includes(id));

          // Check if some files in this topic are selected
          const someTopicFilesSelected = topicDocumentIds.some((id) => selectedIds.includes(id));

          return (
            <div onClick={(e) => e.stopPropagation()}>
              <Checkbox
                checked={allTopicFilesSelected ? true : someTopicFilesSelected ? undefined : false}
                onCheckedChange={(checked) => {
                  if (checked) {
                    // Select all files in this topic
                    const newSelectedIds = Array.from(
                      new Set([...selectedIds, ...topicDocumentIds]),
                    );
                    onSelectionChange(newSelectedIds);
                  } else {
                    // Deselect all files in this topic
                    const newSelectedIds = selectedIds.filter(
                      (id) => !topicDocumentIds.includes(id),
                    );
                    onSelectionChange(newSelectedIds);
                  }
                }}
              />
            </div>
          );
        }
      }

      // For files, use the standard selection behavior
      return (
        <div onClick={(e) => e.stopPropagation()}>
          <Checkbox
            checked={selectedIds.includes(item.id)}
            onCheckedChange={(checked) => {
              onSelectionChange(
                checked ? [...selectedIds, item.id] : selectedIds.filter((id) => id !== item.id),
              );
            }}
          />
        </div>
      );
    },
  },
  ...getCommonColumns(),
];

// Library mode columns (with actions dropdown)
export const getLibraryColumns = (
  onViewItem: (item: LibraryItem) => void,
  onEditItem: (item: LibraryItem) => void,
  onDeleteItem: (item: LibraryItem) => void,
): ColumnDef<LibraryItem>[] => [
  ...getCommonColumns(),
  {
    id: 'actions',
    header: ({ column }) => <DataTableColumnHeader column={column} title="Actions" />,
    meta: {
      style: { maxWidth: '100px', width: '100px' },
      className: 'max-w-[100px] w-[100px]',
    },
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
            <DropdownMenuItem
              onClick={(e) => {
                e.stopPropagation();
                onViewItem(item);
              }}
            >
              <IconEye className="mr-2 w-4 h-4" />
              View
            </DropdownMenuItem>
            <DropdownMenuItem
              disabled={
                item.type === 'file' && 
                ((item as FileItem).extension.toLowerCase() === 'pdf' ||
                 (item as FileItem).extension === 'kp')
              }
              onClick={(e) => {
                e.stopPropagation();
                if (item.type === 'file' && (item as FileItem).extension.toLowerCase() === 'pdf')
                  return;
                if (item.type === 'file' && (item as FileItem).extension === 'kp')
                  return;
                onEditItem(item);
              }}
            >
              <IconEdit className="mr-2 w-4 h-4" />
              Edit
            </DropdownMenuItem>
            <DropdownMenuItem
              className="text-red-600"
              disabled={
                item.type === 'file' &&
                (item as FileItem).extension === 'template' &&
                (item as FileItem).metadata?.is_master === true
              }
              onClick={(e) => {
                e.stopPropagation();
                const fileItem = item as FileItem;
                // Prevent deletion of master templates
                if (
                  item.type === 'file' &&
                  fileItem.extension === 'template' &&
                  fileItem.metadata?.is_master
                ) {
                  toast.error('Master templates cannot be deleted');
                  return;
                }
                onDeleteItem(item);
              }}
            >
              <IconTrash className="mr-2 w-4 h-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
    },
  },
];
