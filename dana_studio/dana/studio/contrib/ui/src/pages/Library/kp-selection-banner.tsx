/* eslint-disable @typescript-eslint/no-explicit-any */
import { Button } from '@/components/ui/button';

interface KPSelectionBannerProps {
  selectedKP: any | null; // Single Knowledge Pack selection
  onCancel: () => void;
  onCreate: () => void;
}

export function KPSelectionBanner({ selectedKP, onCancel, onCreate }: KPSelectionBannerProps) {
  const isKPSelected = selectedKP !== null;

  return (
    <div className="bg-gray-50 border-b border-gray-200 duration-300 dark:bg-gray-950/20 dark:border-gray-900 animate-in slide-in-from-top">
      <div className="px-6 py-4">
        <div className="flex justify-between items-center">
          <div className="flex gap-3 items-start">
            <div className="flex flex-col gap-1">
              <div className="flex gap-2 items-center">
                <span className="text-lg font-semibold text-gray-900 dark:text-gray-300">
                  Select a knowledge pack to create Capture Template
                </span>
              </div>
              <div className="mt-2 text-sm font-medium text-gray-800 dark:text-gray-300">
                {isKPSelected ? (
                  <>
                    <span className="text-green-600 dark:text-green-400">✓</span> 1 Knowledge Pack
                    selected: <span className="font-semibold">{selectedKP.name}</span>
                  </>
                ) : (
                  <span className="text-orange-600 dark:text-orange-400">
                    Please select a Knowledge Pack from the table below
                  </span>
                )}
              </div>
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
            <Button size="lg" onClick={onCreate} disabled={!isKPSelected}>
              {isKPSelected ? (
                'Create Capture Template'
              ) : (
                <span className="flex gap-2 items-center">Select a Knowledge Pack first</span>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
