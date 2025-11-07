/* eslint-disable @typescript-eslint/no-explicit-any */
import { create } from 'zustand';
import { apiService } from '@/lib/api';
import { toast } from 'sonner';
import type { BackgroundTaskResponse } from '@/lib/api';
import { useDocumentStore } from './document-store';

// Constants
const POLLING_INTERVAL = 10000; // 10 seconds
const AGGREGATED_TOAST_ID = 'deep-extraction-active';

// Types
interface DeepExtractionTask {
  task_id: number;
  document_id: number;
  filename: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  error?: string;
}

interface DeepExtractStatusManagerState {
  tasks: Map<number, DeepExtractionTask>;
  pollingInterval: ReturnType<typeof setInterval> | null;
  isPolling: boolean;
  lastStatusUpdate: number;

  // Actions
  initialize: () => Promise<void>;
  registerTask: (task_id: number, document_id: number, filename: string) => void;
  startPolling: () => void;
  stopPolling: () => void;
  updateTaskStatuses: (tasks: BackgroundTaskResponse[]) => void;
  cleanup: () => void;
}

// Helper Functions

/**
 * Extract a user-friendly error message from the error stack trace
 */
function extractErrorMessage(error: string | null | undefined): string {
  if (!error) return 'An unknown error occurred';

  // Look for "Unsupported file type: .ext" pattern
  const unsupportedMatch = error.match(/Unsupported file type: (\.\w+)/);
  if (unsupportedMatch) {
    return `Unsupported file type: ${unsupportedMatch[1]}`;
  }

  // Get last line of error as fallback
  const lines = error.split('\n').filter((line) => line.trim());
  const lastLine = lines[lines.length - 1] || 'An unknown error occurred';

  // Clean up common prefixes
  return lastLine
    .replace(/^(Error:|HTTPException:|fastapi\.exceptions\.HTTPException:)\s*/i, '')
    .trim();
}

/**
 * Show success toast for completed extraction
 */
function showCompletedToast(filename: string) {
  toast.success(`Deep extraction completed for "${filename}"`, {
    duration: 5000,
    position: 'bottom-left',
  });
}

/**
 * Show error toast for failed extraction
 */
function showFailedToast(filename: string, error: string) {
  const errorMessage = extractErrorMessage(error);
  toast.error(`Deep extraction failed for "${filename}"`, {
    description: errorMessage,
    duration: 5000,
    position: 'bottom-left',
  });
}

/**
 * Show or update aggregated toast for active tasks
 */
function showAggregatedToast(count: number) {
  if (count === 0) {
    // Dismiss aggregated toast
    toast.dismiss(AGGREGATED_TOAST_ID);
  } else {
    // Show or update aggregated toast
    toast.loading(`Deep extraction in progress (${count} file${count > 1 ? 's' : ''})`, {
      duration: Infinity,
      position: 'bottom-left',
      id: AGGREGATED_TOAST_ID,
      dismissible: true,
    });
  }
}

/**
 * Count active tasks (pending or running)
 */
function countActiveTasks(tasks: Map<number, DeepExtractionTask>): number {
  let count = 0;
  tasks.forEach((task) => {
    if (task.status === 'pending' || task.status === 'running') {
      count++;
    }
  });
  return count;
}

/**
 * Filter out stale completed/failed tasks (older than 24 hours)
 */
function filterStaleTasks(tasks: Map<number, DeepExtractionTask>): Map<number, DeepExtractionTask> {
  const filtered = new Map<number, DeepExtractionTask>();

  tasks.forEach((task, taskId) => {
    // Keep active tasks always
    if (task.status === 'pending' || task.status === 'running') {
      filtered.set(taskId, task);
    }
    // Keep completed/failed tasks if they're recent (within 24 hours)
    // Since we don't have timestamp in task, we'll keep all for now
    // This can be improved by adding a timestamp field
    else {
      filtered.set(taskId, task);
    }
  });

  return filtered;
}

// Create the Zustand store
export const useDeepExtractStatusManager = create<DeepExtractStatusManagerState>((set, get) => ({
  tasks: new Map(),
  pollingInterval: null,
  isPolling: false,
  lastStatusUpdate: Date.now(),

  /**
   * Initialize the manager by fetching all existing deep extraction tasks
   */
  initialize: async () => {
    console.log('[DeepExtractStatusManager] Initializing...');
    try {
      const allTasks = await apiService.getAllDeepExtractionStatus();
      console.log('[DeepExtractStatusManager] Fetched all tasks:', allTasks);

      const tasksMap = new Map<number, DeepExtractionTask>();

      // Populate tasks map with backend data
      allTasks.forEach((task) => {
        if (task.type === 'deep_extract') {
          const document_id = task.data?.document_id;
          const filename = task.data?.original_filename || 'Unknown file';

          if (document_id) {
            tasksMap.set(task.id, {
              task_id: task.id,
              document_id,
              filename,
              status: task.status,
              error: task.error || undefined,
            });
          }
        }
      });

      set({ tasks: tasksMap, lastStatusUpdate: Date.now() });

      // Start polling if there are active tasks
      const activeCount = countActiveTasks(tasksMap);
      console.log('[DeepExtractStatusManager] Active tasks count:', activeCount);

      if (activeCount > 0) {
        get().startPolling();
        showAggregatedToast(activeCount);
      }
    } catch (error) {
      console.error('[DeepExtractStatusManager] Error initializing:', error);
    }
  },

  /**
   * Register a new task and start polling if needed
   */
  registerTask: (task_id: number, document_id: number, filename: string) => {
    console.log('[DeepExtractStatusManager] Registering task:', { task_id, document_id, filename });

    const { tasks } = get();
    const newTasks = new Map(tasks);

    // Add or update task
    newTasks.set(task_id, {
      task_id,
      document_id,
      filename,
      status: 'pending',
    });

    set({ tasks: newTasks, lastStatusUpdate: Date.now() });

    // Start polling if not already polling
    if (!get().isPolling) {
      get().startPolling();
    }

    // Update aggregated toast
    const activeCount = countActiveTasks(newTasks);
    showAggregatedToast(activeCount);
  },

  /**
   * Start polling for task status updates
   */
  startPolling: () => {
    const { isPolling, pollingInterval } = get();

    // Don't start if already polling
    if (isPolling && pollingInterval) {
      console.log('[DeepExtractStatusManager] Already polling');
      return;
    }

    console.log('[DeepExtractStatusManager] Starting polling...');

    const interval = setInterval(async () => {
      try {
        const allTasks = await apiService.getAllDeepExtractionStatus();
        get().updateTaskStatuses(allTasks);

        // Check if we should stop polling
        const activeCount = countActiveTasks(get().tasks);
        if (activeCount === 0) {
          const timeSinceLastUpdate = Date.now() - get().lastStatusUpdate;
          // Stop polling after 30 seconds of no active tasks
          if (timeSinceLastUpdate > 30000) {
            console.log('[DeepExtractStatusManager] No active tasks, stopping polling');
            get().stopPolling();
          }
        }
      } catch (error) {
        console.error('[DeepExtractStatusManager] Error polling:', error);
        // Don't stop polling on error, retry on next interval
      }
    }, POLLING_INTERVAL);

    set({ pollingInterval: interval, isPolling: true });
  },

  /**
   * Stop polling for task status updates
   */
  stopPolling: () => {
    const { pollingInterval } = get();

    if (pollingInterval) {
      console.log('[DeepExtractStatusManager] Stopping polling');
      clearInterval(pollingInterval);
      set({ pollingInterval: null, isPolling: false });
    }
  },

  /**
   * Update task statuses from backend response
   */
  updateTaskStatuses: (backendTasks: BackgroundTaskResponse[]) => {
    const { tasks } = get();
    const newTasks = new Map(tasks);
    let hasChanges = false;
    let hasCompletedTasks = false;

    // Process backend tasks
    backendTasks.forEach((backendTask) => {
      if (backendTask.type === 'deep_extract') {
        const existingTask = newTasks.get(backendTask.id);

        // Only process tasks we're tracking
        if (existingTask) {
          const oldStatus = existingTask.status;
          const newStatus = backendTask.status;

          // Detect status change
          if (oldStatus !== newStatus) {
            hasChanges = true;
            console.log(
              `[DeepExtractStatusManager] Task ${backendTask.id} status changed: ${oldStatus} -> ${newStatus}`,
            );

            // Show individual toast for completion/failure
            if (
              (oldStatus === 'pending' || oldStatus === 'running') &&
              newStatus === 'completed'
            ) {
              showCompletedToast(existingTask.filename);
              hasCompletedTasks = true;
            } else if (
              (oldStatus === 'pending' || oldStatus === 'running') &&
              newStatus === 'failed'
            ) {
              showFailedToast(existingTask.filename, backendTask.error || '');
            }
          }

          // Update task
          newTasks.set(backendTask.id, {
            ...existingTask,
            status: newStatus,
            error: backendTask.error || undefined,
          });
        }
      }
    });

    if (hasChanges) {
      // Filter out stale tasks
      const filteredTasks = filterStaleTasks(newTasks);

      set({ tasks: filteredTasks, lastStatusUpdate: Date.now() });

      // Update aggregated toast
      const activeCount = countActiveTasks(filteredTasks);
      showAggregatedToast(activeCount);

      // Refresh documents in Knowledge Center when tasks complete
      if (hasCompletedTasks) {
        console.log('[DeepExtractStatusManager] Refreshing documents in Knowledge Center...');
        try {
          const documentStore = useDocumentStore.getState();
          documentStore.fetchDocuments();
        } catch (error) {
          console.error('[DeepExtractStatusManager] Error refreshing documents:', error);
        }
      }
    }
  },

  /**
   * Cleanup resources
   */
  cleanup: () => {
    console.log('[DeepExtractStatusManager] Cleaning up...');
    get().stopPolling();
    toast.dismiss(AGGREGATED_TOAST_ID);
    set({ tasks: new Map(), pollingInterval: null, isPolling: false });
  },
}));

