import { cn } from '@/lib/utils';

interface DragOverComponentProps {
  title: string;
  description?: string;
  className?: string;
}

export function DragOverComponent({
  title,
  description,
  className,
}: DragOverComponentProps) {
  return (
    <div
      className={cn(
        'flex fixed inset-0 z-50 justify-center items-center backdrop-blur-sm bg-black/50',
        className
      )}
    >
      <div className='p-8 text-center bg-white rounded-lg shadow-lg dark:bg-gray-800'>
        <h3 className='mb-2 text-lg font-semibold text-gray-900 dark:text-gray-100'>
          {title}
        </h3>
        {description && (
          <p className='text-sm text-gray-600 dark:text-gray-400'>
            {description}
          </p>
        )}
      </div>
    </div>
  );
}
