import { IconButton } from '@/components/ui/button';
import { IconChevronLeft, IconChevronRight } from '@tabler/icons-react';

// Component for pagination controls
export const Pagination = ({
  currentPage,
  totalPages,
  onBack,
  onNext,
  isDisabled = false,
}: {
  currentPage: number;
  totalPages: number;
  onBack: () => void;
  onNext: () => void;
  isDisabled?: boolean;
}) => {
  return (
    <div className="flex items-center justify-center gap-2">
      <IconButton
        aria-label="Previous"
        variant="secondary"
        size="sm"
        className="flex items-center gap-1 text-gray-700 border-none"
        onClick={onBack}
        disabled={isDisabled || currentPage <= 1}
      >
        <IconChevronLeft className="w-4 h-4" />
      </IconButton>
      <div className="flex items-center gap-2">
        <span className="flex items-center justify-center text-sm text-gray-700 border border-gray-200 rounded-md size-8">
          {currentPage}
        </span>
        <span className="text-sm text-gray-700">of</span>
        <span className="text-sm text-gray-700">{totalPages}</span>
      </div>
      <IconButton
        aria-label="Next"
        variant="secondary"
        size="sm"
        className="flex items-center gap-1 text-gray-700 border-none"
        onClick={onNext}
        disabled={isDisabled || currentPage >= totalPages}
      >
        <IconChevronRight className="w-4 h-4" />
      </IconButton>
    </div>
  );
};
