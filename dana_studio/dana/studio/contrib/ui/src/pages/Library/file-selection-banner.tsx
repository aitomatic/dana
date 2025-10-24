import { Button } from '@/components/ui/button';

interface FileSelectionBannerProps {
  selectedCount: number;
  onCancel: () => void;
  onCreate: () => void;
}

export function FileSelectionBanner({
  selectedCount,
  onCancel,
  onCreate,
}: FileSelectionBannerProps) {
  return (
    <div className="bg-gray-50 border-b border-gray-200 duration-300 dark:bg-gray-950/20 dark:border-gray-900 animate-in slide-in-from-top">
      <div className="px-6 py-4">
        <div className="flex justify-between items-center">
          <div className="flex flex-col gap-1">
            <div className="flex gap-2 items-center">
              <span className="text-lg font-semibold text-gray-900 dark:text-gray-300">
                Select Items to Create Knowledge Pack (Optional)
              </span>
            </div>
            <span className="text-sm text-gray-700 dark:text-gray-400">
              Ready-to-use knowledge pack from various sources
            </span>
            <div className="mt-2 text-sm font-medium text-gray-800 dark:text-gray-300">
              {selectedCount} selected
            </div>
          </div>

          <div className="flex gap-3 items-center">
            <Button
              variant="outline"
              size="lg"
              onClick={onCancel}
              className="text-gray-700 border-gray-300 hover:bg-gray-100 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-900/30"
            >
              Cancel
            </Button>
            <Button size="lg" onClick={onCreate}>
              {selectedCount === 0
                ? 'Create without file'
                : `Create with ${selectedCount} file${selectedCount > 1 ? 's' : ''}`}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
