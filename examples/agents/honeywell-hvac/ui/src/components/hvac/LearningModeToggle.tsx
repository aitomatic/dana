import { useHVACStore } from '@/stores/hvac-store';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';

export function LearningModeToggle() {
  const { withLearner, setWithLearner } = useHVACStore();

  return (
    <div className="flex items-center gap-3">
      <Label htmlFor="learning-toggle" className="text-sm font-medium cursor-pointer">
        Learning Mode:
      </Label>
      <button
        id="learning-toggle"
        type="button"
        role="switch"
        aria-checked={withLearner}
        onClick={() => setWithLearner(!withLearner)}
        className={cn(
          'relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50',
          withLearner ? 'bg-blue-600' : 'bg-gray-300'
        )}
      >
        <span
          className={cn(
            'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
            withLearner ? 'translate-x-6' : 'translate-x-1'
          )}
        />
      </button>
      <span className="text-sm text-muted-foreground min-w-[120px]">
        {withLearner ? 'With Learning' : 'Without Learning'}
      </span>
    </div>
  );
}

