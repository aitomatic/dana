/* eslint-disable @typescript-eslint/no-explicit-any */
import type { ColumnDef } from '@tanstack/react-table';
import { DataTableColumnHeader } from '@/components/table/data-table-column-header';
import { Button } from '@/components/ui/button';
import { IconSchool, IconLoader2 } from '@tabler/icons-react';
import { PasteClipboard, Trash } from 'iconoir-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { formatDate } from './library-utils';
import {
  TEMPLATE_GENERATION_STATUS,
  SESSION_STATUS,
} from '@/lib/constants';

// Helper function to get status badge
const getStatusBadge = (status?: string) => {
  switch (status) {
    case TEMPLATE_GENERATION_STATUS.COMPLETED:
      return <Badge className="bg-green-600 text-white">Completed</Badge>;
    case TEMPLATE_GENERATION_STATUS.GENERATING:
      return <Badge className="bg-purple-600 text-white">Generating</Badge>;
    case TEMPLATE_GENERATION_STATUS.PENDING:
      return <Badge className="bg-blue-600 text-white">Pending</Badge>;
    case TEMPLATE_GENERATION_STATUS.FAILED:
      return <Badge className="bg-red-600 text-white">Failed</Badge>;
    case TEMPLATE_GENERATION_STATUS.DRAFT:
    default:
      return <Badge className="bg-gray-600 text-white">Draft</Badge>;
  }
};

const getSessionStatusBadge = (status?: string) => {
  switch (status) {
    case SESSION_STATUS.COMPLETED:
      return <Badge className="bg-green-600 text-white">Completed</Badge>;
    case SESSION_STATUS.IN_PROGRESS:
      return <Badge className="bg-blue-600 text-white">In Progress</Badge>;
    case SESSION_STATUS.DRAFT:
    default:
      return <Badge className="bg-gray-600 text-white">Draft</Badge>;
  }
};

// Helper function to determine if item is a template or session
const isTemplate = (item: ExtendedLibraryItem) => {
  return item.type === 'file' && item.extension === 'template';
};

const isSession = (item: ExtendedLibraryItem) => {
  return item.type === 'file' && item.extension === 'ek';
};

// Extended LibraryItem type to include children and additional properties
interface ExtendedLibraryItem {
  id: number;
  name: string;
  type: 'file' | 'folder';
  extension: string;
  created: string;
  updated: string;
  children?: ExtendedLibraryItem[];
  template_metadata?: any;
  interview_sessions?: any[];
  status?: string;
  interviewee_name?: string;
  interviewee_role?: string;
  is_master?: boolean;
}

export const getContributionTemplateColumns = (
  handleTemplateClick: (templateId: number) => void,
  handleSessionClick: (sessionId: number) => void,
  handleCaptureKnowledge: (templateId: number, templateName: string) => void,
  capturingKnowledge: Set<number>,
  handleDelete: (id: number, type: 'template' | 'session', name: string) => void,
): ColumnDef<ExtendedLibraryItem>[] => [
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
      const item = row.original as ExtendedLibraryItem;
      const templateItem = isTemplate(item);
      const sessionItem = isSession(item);

      // Determine padding based on hierarchy level
      const getPaddingClass = () => {
        if (templateItem) {
          return '-mx-6 px-4'; // Template level
        } else if (sessionItem) {
          return '-mx-6 px-8'; // Session level (more indented)
        }
        return '-mx-6 px-4'; // Default
      };

      // For master templates: only clickable when completed
      // For non-master templates: always clickable
      const isMasterTemplate = templateItem && item.is_master === true;
      const isCompletedTemplate = item.template_metadata?.status === TEMPLATE_GENERATION_STATUS.COMPLETED;
      const isClickable = templateItem 
        ? (isMasterTemplate ? isCompletedTemplate : true)  // Master: only if completed, Non-master: always
        : sessionItem;  // Sessions always clickable

      return (
        <div className={cn("flex items-center gap-2", getPaddingClass())}>
          <Tooltip>
            <TooltipTrigger asChild>
              <div 
                className={cn(
                  "flex items-center gap-2 transition-colors min-w-0 flex-1",
                  isClickable ? "cursor-pointer hover:text-blue-600" : "cursor-not-allowed opacity-60"
                )}
                onClick={(e) => {
                  e.stopPropagation();
                  if (isClickable) {
                    if (templateItem) {
                      handleTemplateClick(item.id);
                    } else if (sessionItem) {
                      handleSessionClick(item.id);
                    }
                  }
                }}
              >
                {templateItem ? (
                  <PasteClipboard className={cn(
                    "w-5 h-5 mt-0.5 flex-shrink-0",
                    !isClickable ? "text-gray-400" : "text-[#0BA5EC]"
                  )} />
                ) : sessionItem ? (
                  <IconSchool className="w-5 h-5 mt-0.5 text-green-600 flex-shrink-0" />
                ) : (
                  <div className="w-5 h-5 flex-shrink-0" />
                )}
                <div className="flex flex-col min-w-0 flex-1">
                  <span className={cn(
                    "font-medium truncate",
                    !isClickable ? "text-gray-500" : "text-gray-900"
                  )}>{item.name}</span>
                </div>
              </div>
            </TooltipTrigger>
            {templateItem && !isClickable && (
              <TooltipContent>
                <p>Master template must be completed before it can be viewed or edited</p>
              </TooltipContent>
            )}
          </Tooltip>
        </div>
      );
    },
  },
  {
    accessorKey: 'status',
    enableSorting: true,
    header: ({ column }) => <DataTableColumnHeader column={column} title="Status" />,
    cell: ({ row }) => {
      const item = row.original as ExtendedLibraryItem;
      const templateItem = isTemplate(item);
      const sessionItem = isSession(item);

      if (templateItem) {
        const metadata = (item as any).template_metadata;
        return getStatusBadge(metadata?.status);
      } else if (sessionItem) {
        const status = (item as any).status;
        return getSessionStatusBadge(status);
      }

      return <span className="text-gray-500">-</span>;
    },
  },
  {
    accessorKey: 'sessions',
    enableSorting: false,
    header: ({ column }) => <DataTableColumnHeader column={column} title="Sessions" />,
    cell: ({ row }) => {
      const item = row.original as ExtendedLibraryItem;
      const templateItem = isTemplate(item);

      if (templateItem) {
        const sessions = (item as any).interview_sessions || [];
        return (
          <span className="text-sm text-gray-600">
            {sessions.length} session{sessions.length !== 1 ? 's' : ''}
          </span>
        );
      }

      return <span className="text-gray-500">-</span>;
    },
  },
  {
    accessorKey: 'created_at',
    enableSorting: true,
    header: ({ column }) => <DataTableColumnHeader column={column} title="Created" />,
    cell: ({ row }) => {
      const item = row.original;
      const createdAt = (item as any).created_at;
      
      if (createdAt) {
        return (
          <span className="text-sm text-gray-600">
            {formatDate(createdAt)}
          </span>
        );
      }

      return <span className="text-gray-500">-</span>;
    },
  },
  {
    id: 'actions',
    enableSorting: false,
    header: () => <span className="text-sm font-medium">Actions</span>,
    cell: ({ row }) => {
      const item = row.original as ExtendedLibraryItem;
      const templateItem = isTemplate(item);
      const sessionItem = isSession(item);

      if (templateItem) {
        const metadata = (item as any).template_metadata;
        const isCompleted = metadata?.status === TEMPLATE_GENERATION_STATUS.COMPLETED;
        const isCapturing = capturingKnowledge.has(item.id);
        const isMasterTemplate = item.is_master === true;

        return (
          <div className="flex items-center gap-2">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCaptureKnowledge(item.id, item.name);
                  }}
                  disabled={isCapturing || !isCompleted}
                  size="sm"
                  className="gap-2"
                  variant="outline"
                >
                  {isCapturing ? (
                    <>
                      <IconLoader2 className="w-4 h-4 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                        />
                      </svg>
                      Capture knowledge
                    </>
                  )}
                </Button>
              </TooltipTrigger>
              {(isCapturing || !isCompleted) && (
                <TooltipContent>
                  <p>{!isCompleted ? 'Template must be completed to capture knowledge' : 'Creating knowledge session...'}</p>
                </TooltipContent>
              )}
            </Tooltip>
            
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className={cn(
                    "h-8 w-8 p-0",
                    isMasterTemplate 
                      ? "text-gray-400 cursor-not-allowed opacity-50" 
                      : "text-gray-600 hover:text-gray-700 hover:bg-gray-50"
                  )}
                  onClick={(e) => {
                    e.stopPropagation();
                    if (!isMasterTemplate) {
                      handleDelete(item.id, 'template', item.name);
                    }
                  }}
                  disabled={isMasterTemplate}
                >
                  <Trash className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              {isMasterTemplate && (
                <TooltipContent>
                  <p>Master templates cannot be deleted</p>
                </TooltipContent>
              )}
            </Tooltip>
          </div>
        );
      } else if (sessionItem) {
        return (
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 text-gray-600 hover:text-gray-700 hover:bg-gray-100"
            onClick={(e) => {
              e.stopPropagation();
              handleDelete(item.id, 'session', item.name);
            }}
          >
            <Trash className="h-4 w-4" />
          </Button>
        );
      }

      return null;
    },
  },
];
