import { useState, useEffect, useRef, useCallback } from 'react';

interface UseSessionTimerOptions {
  initialDurationSeconds?: number;
  autoStart?: boolean;
  initialIsPaused?: boolean;
}

interface UseSessionTimerReturn {
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
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const baseElapsedRef = useRef<number>(initialDurationSeconds);

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

    startTimeRef.current = Date.now();
    baseElapsedRef.current = elapsedSeconds;

    intervalRef.current = setInterval(() => {
      if (startTimeRef.current !== null) {
        const now = Date.now();
        const deltaSeconds = Math.floor((now - startTimeRef.current) / 1000);
        setElapsedSeconds(baseElapsedRef.current + deltaSeconds);
      }
    }, 1000);

    setIsPaused(false);
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
    setIsPaused(!autoStart);
  }, [initialDurationSeconds, autoStart]);

  // Update base elapsed when initialDurationSeconds changes (e.g., when session loads)
  // This allows restoration even if timer has already started (e.g., when session loads after page refresh)
  useEffect(() => {
    if (initialDurationSeconds > 0 && initialDurationSeconds !== baseElapsedRef.current) {
      // If timer is not running, simply restore the duration
      if (!intervalRef.current) {
        setElapsedSeconds(initialDurationSeconds);
        baseElapsedRef.current = initialDurationSeconds;
      } else {
        // Timer is running - update baseElapsedRef to "jump forward" to saved duration
        // This handles the case where session loads after timer has already auto-started
        const currentElapsed = elapsedSeconds;
        if (initialDurationSeconds > currentElapsed) {
          // Only update if saved duration is greater (to restore from saved state)
          // Reset the start time and base to continue from the saved duration
          baseElapsedRef.current = initialDurationSeconds;
          startTimeRef.current = Date.now();
          // Set elapsed to the saved duration immediately
          setElapsedSeconds(initialDurationSeconds);
        }
      }
    }
  }, [initialDurationSeconds, elapsedSeconds]);

  // Auto-start on mount if enabled and not paused
  // Only auto-start if initialIsPaused is not true (allowing restoration of paused state)
  useEffect(() => {
    const shouldAutoStart = autoStart && !isPaused && !intervalRef.current;
    // Don't auto-start if we're restoring a paused state
    if (shouldAutoStart && initialIsPaused !== true) {
      start();
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [autoStart, isPaused, initialIsPaused, start]);

  // Update paused state when initialIsPaused changes (e.g., when session loads)
  useEffect(() => {
    if (initialIsPaused !== undefined && initialIsPaused !== isPaused) {
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
  }, [initialIsPaused, isPaused, autoStart, elapsedSeconds, start]);

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

