import { useState, useEffect, useRef, useCallback } from 'react';

interface UseSessionTimerOptions {
  initialDurationSeconds?: number;
  autoStart?: boolean;
  initialIsPaused?: boolean;
}

export interface UseSessionTimerReturn {
  elapsedSeconds: number;
  formattedTime: string;
  isPaused: boolean;
  pause: () => void;
  resume: () => void;
  toggle: () => void;
  getDurationSeconds: () => number;
  reset: () => void;
}

/**
 * Custom hook for managing a session timer with pause/resume functionality
 * @param options - Configuration options
 * @param options.initialDurationSeconds - Initial duration in seconds (for restoring from saved state)
 * @param options.autoStart - Whether to start the timer automatically on mount (default: true)
 * @param options.initialIsPaused - Initial paused state (for restoring from saved state)
 * @returns Timer state and control functions
 */
export function useSessionTimer(
  options: UseSessionTimerOptions = {}
): UseSessionTimerReturn {
  const { initialDurationSeconds = 0, autoStart = true, initialIsPaused } = options;

  // Determine initial paused state: use initialIsPaused if provided, otherwise use !autoStart
  const initialPausedState = initialIsPaused !== undefined ? initialIsPaused : !autoStart;

  const [elapsedSeconds, setElapsedSeconds] = useState(initialDurationSeconds);
  const [isPaused, setIsPaused] = useState(initialPausedState);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const baseElapsedRef = useRef<number>(initialDurationSeconds);
  const autoStartAttemptedRef = useRef<boolean>(false);
  const prevInitialIsPausedRef = useRef<boolean | undefined>(initialIsPaused);
  const lastRestoredDurationRef = useRef<number>(initialDurationSeconds);

  // Format seconds to HH:MM:SS
  const formatTime = useCallback((seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }, []);

  // Start the timer
  const start = useCallback(() => {
    if (intervalRef.current) {
      return; // Already running
    }

    startTimeRef.current = Date.now();
    baseElapsedRef.current = elapsedSeconds;

    intervalRef.current = setInterval(() => {
      if (startTimeRef.current !== null) {
        const now = Date.now();
        const deltaSeconds = Math.floor((now - startTimeRef.current) / 1000);
        setElapsedSeconds(baseElapsedRef.current + deltaSeconds);
      }
    }, 1000);
  }, [elapsedSeconds]);

  // Pause the timer
  const pause = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (startTimeRef.current !== null) {
      // Update base elapsed with current elapsed time
      baseElapsedRef.current = elapsedSeconds;
      startTimeRef.current = null;
    }
    setIsPaused(true);
  }, [elapsedSeconds]);

  // Resume the timer
  const resume = useCallback(() => {
    if (intervalRef.current) {
      return; // Already running
    }

    // Set base elapsed time to current elapsed time before updating state
    baseElapsedRef.current = elapsedSeconds;
    startTimeRef.current = Date.now();

    // Update paused state - this will trigger re-render and button label update
    setIsPaused(false);

    // Start the interval - use refs to capture current values
    intervalRef.current = setInterval(() => {
      if (startTimeRef.current !== null) {
        const now = Date.now();
        const deltaSeconds = Math.floor((now - startTimeRef.current) / 1000);
        setElapsedSeconds(baseElapsedRef.current + deltaSeconds);
      }
    }, 1000);
  }, [elapsedSeconds]);

  // Toggle pause/resume
  const toggle = useCallback(() => {
    if (isPaused) {
      resume();
    } else {
      pause();
    }
  }, [isPaused, pause, resume]);

  // Get current duration in seconds
  const getDurationSeconds = useCallback(() => {
    return elapsedSeconds;
  }, [elapsedSeconds]);

  // Reset the timer
  const reset = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setElapsedSeconds(initialDurationSeconds);
    baseElapsedRef.current = initialDurationSeconds;
    startTimeRef.current = null;
    lastRestoredDurationRef.current = initialDurationSeconds;
    autoStartAttemptedRef.current = false;
    setIsPaused(!autoStart);
  }, [initialDurationSeconds, autoStart]);

  // Update base elapsed when initialDurationSeconds changes (e.g., when session loads)
  // This allows restoration even if timer has already started (e.g., when session loads after page refresh)
  // Only restore when initialDurationSeconds prop changes, not when elapsedSeconds state changes
  useEffect(() => {
    // Only restore if initialDurationSeconds actually changed and we haven't already restored this value
    if (initialDurationSeconds !== lastRestoredDurationRef.current) {
      lastRestoredDurationRef.current = initialDurationSeconds;
      
      // Handle both new sessions (initialDurationSeconds = 0) and existing sessions (initialDurationSeconds > 0)
      if (initialDurationSeconds !== baseElapsedRef.current) {
        // If timer is not running (paused), restore the exact duration (0 for new sessions, saved value for existing)
        if (!intervalRef.current) {
          // Exact restoration - set to the saved value (or 0 for new sessions) without any calculations
          setElapsedSeconds(initialDurationSeconds);
          baseElapsedRef.current = initialDurationSeconds;
        } else {
          // Timer is running - update baseElapsedRef to "jump forward" to saved duration
          // This handles the case where session loads after timer has already auto-started
          // Use a function to get current elapsedSeconds value without depending on it
          setElapsedSeconds((currentElapsed) => {
            // For new sessions (initialDurationSeconds = 0), reset to 0
            // For existing sessions, only update if saved duration is greater
            if (initialDurationSeconds === 0 || initialDurationSeconds > currentElapsed) {
              // Reset the start time and base to continue from the saved duration (or 0 for new sessions)
              baseElapsedRef.current = initialDurationSeconds;
              startTimeRef.current = Date.now();
              return initialDurationSeconds;
            }
            return currentElapsed;
          });
        }
      }
    }
  }, [initialDurationSeconds]); // Removed elapsedSeconds from dependencies to prevent loop

  // Auto-start on mount if enabled and not paused
  // Only run once on mount (or when autoStart/initialIsPaused changes), not every time isPaused changes
  useEffect(() => {
    // Only attempt auto-start once, and only if we haven't already attempted it
    if (!autoStartAttemptedRef.current && autoStart && !isPaused && !intervalRef.current) {
      // Don't auto-start if we're restoring a paused state
      if (initialIsPaused !== true) {
        autoStartAttemptedRef.current = true;
        start();
      } else {
        // If we're restoring a paused state, mark as attempted so we don't try again
        autoStartAttemptedRef.current = true;
      }
    }
  }, [autoStart, initialIsPaused, isPaused, start]); // Keep isPaused but only attempt once via ref

  // Separate cleanup effect that only runs on unmount
  useEffect(() => {
    return () => {
      // Cleanup: clear interval on unmount only
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, []); // Empty deps - only cleanup on unmount

  // Update paused state when initialIsPaused prop changes (e.g., when session loads)
  // Only sync when the prop changes, not when user manually changes isPaused state
  useEffect(() => {
    // Only sync if initialIsPaused prop actually changed (not just isPaused state)
    if (initialIsPaused !== prevInitialIsPausedRef.current) {
      prevInitialIsPausedRef.current = initialIsPaused;
      
      if (initialIsPaused !== undefined) {
        if (initialIsPaused) {
          // If should be paused, pause the timer
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          if (startTimeRef.current !== null) {
            baseElapsedRef.current = elapsedSeconds;
            startTimeRef.current = null;
          }
          setIsPaused(true);
        } else if (!initialIsPaused && autoStart) {
          // If should not be paused and autoStart is enabled, start the timer
          if (!intervalRef.current) {
            start();
          }
        }
      }
    }
  }, [initialIsPaused, autoStart, elapsedSeconds, start]);

  return {
    elapsedSeconds,
    formattedTime: formatTime(elapsedSeconds),
    isPaused,
    pause,
    resume,
    toggle,
    getDurationSeconds,
    reset,
  };
}

