import { useHVACStore } from '@/stores/hvac-store';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';

export function ComparisonModeToggle() {
  const { comparisonMode, setComparisonMode } = useHVACStore();

  return (
    <div className="flex items-center gap-3">
      <Label htmlFor="comparison-toggle" className="text-sm font-medium cursor-pointer">
        Comparison Mode:
      </Label>
      <button
        id="comparison-toggle"
        type="button"
        role="switch"
        aria-checked={comparisonMode}
        onClick={() => setComparisonMode(!comparisonMode)}
        className={cn(
          'relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50',
          comparisonMode ? 'bg-blue-600' : 'bg-gray-300'
        )}
      >
        <span
          className={cn(
            'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
            comparisonMode ? 'translate-x-6' : 'translate-x-1'
          )}
        />
      </button>
      <span className="text-sm text-muted-foreground">
        {comparisonMode ? 'On' : 'Off'}
      </span>
    </div>
  );
}

// Keep the old export for backward compatibility during transition
export const LearningModeToggle = ComparisonModeToggle;

