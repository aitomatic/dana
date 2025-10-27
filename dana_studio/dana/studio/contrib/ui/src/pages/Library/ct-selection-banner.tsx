/* eslint-disable @typescript-eslint/no-explicit-any */
import { Button } from '@/components/ui/button';
import { CheckCircleSolid } from 'iconoir-react';

interface CTSelectionBannerProps {
  selectedCT: any | null; // Single Capture Template selection
  onCancel: () => void;
  onCreate: () => void;
}

export function CTSelectionBanner({ selectedCT, onCancel, onCreate }: CTSelectionBannerProps) {
  const isCTSelected = selectedCT !== null;

  return (
    <div className="border-b duration-300 animate-in slide-in-from-top bg-blue-800">
      <div className="px-6 py-4">
        <div className="flex justify-between items-center">
          <div className="flex gap-3 items-start">
            <div className="flex flex-col gap-1 ">
              <div className="flex gap-2 items-center">
                <span className="text-lg font-semibold text-white dark:text-gray-300">
                  Select a Capture Template to create Capture Knowledge
                </span>
              </div>
              <div className="mt-2 flex items-center gap-2 text-sm b text-white">
                {isCTSelected ? (
                  <>
                    <CheckCircleSolid className="w-4 h-4 text-whit" />
                    Selected: <span className="font-semibold">{selectedCT.name}</span>
                  </>
                ) : (
                  <span className="text-white">
                    Please select a Capture Template from the table below
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
              className="bg-transparent text-white border-gray-300 hover:bg-blue-900"
            >
              Cancel
            </Button>
            <Button variant='default' size="lg" onClick={onCreate} className="bg-white text-gray-700 border-gray-300 hover:bg-gray-100 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-900/30" disabled={!isCTSelected}>
              {isCTSelected ? (
                'Create Capture Knowledge'
              ) : (
                <span className="flex gap-2 items-center">
                  Select a Capture Template first
                </span>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
