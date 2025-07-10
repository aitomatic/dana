import { cn } from '@/lib/utils';
import { IconChevronDown, IconChevronUp, IconSelector } from '@tabler/icons-react';
import type { Column } from '@tanstack/react-table';

interface DataTableColumnHeaderProps<TData, TValue> extends React.HTMLAttributes<HTMLDivElement> {
  column: Column<TData, TValue>;
  title: string;
}

export function DataTableColumnHeader<TData, TValue>({
  column,
  title,
  className,
}: DataTableColumnHeaderProps<TData, TValue>) {
  if (!column.getCanSort()) {
    return (
      <div
        className={cn(
          'flex items-center py-2 space-x-2 text-xs font-medium text-gray-600',
          className,
        )}
      >
        {title.toUpperCase()}
      </div>
    );
  }

  return (
    <div
      className={cn(
        'flex items-center space-x-2 h-full text-xs font-medium text-gray-600 cursor-pointer',
        className,
      )}
    >
      {title.toUpperCase()}
      {column.getIsSorted() === 'desc' ? (
        <IconChevronDown
          onClick={() => column.toggleSorting(false)}
          className="text-gray-600"
          size={16}
        />
      ) : column.getIsSorted() === 'asc' ? (
        <IconChevronUp
          onClick={() => column.toggleSorting(true)}
          className="text-gray-600"
          size={16}
        />
      ) : (
        <IconSelector
          onClick={() => column.toggleSorting(true)}
          className="text-gray-600"
          size={16}
        />
      )}
    </div>
  );
}
