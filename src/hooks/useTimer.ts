import { useState, useEffect, useCallback, useRef } from 'react';
import type { TimerState } from '../types/timeblock';

interface UseTimerOptions {
  totalSeconds: number;
  onComplete?: () => void;
  onTick?: (currentSeconds: number) => void;
  autoStart?: boolean;
}

interface UseTimerReturn extends TimerState {
  start: () => void;
  pause: () => void;
  resume: () => void;
  reset: () => void;
  stop: () => void;
  setTime: (seconds: number) => void;
}

/**
 * Custom hook for timer functionality
 * Supports start, pause, resume, reset, and completion callbacks
 */
export function useTimer({
  totalSeconds,
  onComplete,
  onTick,
  autoStart = false,
}: UseTimerOptions): UseTimerReturn {
  const [isRunning, setIsRunning] = useState(autoStart);
  const [currentSeconds, setCurrentSeconds] = useState(totalSeconds);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const onCompleteRef = useRef(onComplete);
  const onTickRef = useRef(onTick);

  // Update refs when callbacks change
  useEffect(() => {
    onCompleteRef.current = onComplete;
    onTickRef.current = onTick;
  }, [onComplete, onTick]);

  // Calculate progress (0-100)
  const progress = totalSeconds > 0
    ? ((totalSeconds - currentSeconds) / totalSeconds) * 100
    : 0;

  // Timer tick logic
  useEffect(() => {
    if (isRunning && currentSeconds > 0) {
      intervalRef.current = setInterval(() => {
        setCurrentSeconds((prev) => {
          const next = prev - 1;

          // Call onTick callback
          if (onTickRef.current) {
            onTickRef.current(next);
          }

          // Check completion
          if (next <= 0) {
            setIsRunning(false);
            if (onCompleteRef.current) {
              onCompleteRef.current();
            }
            return 0;
          }

          return next;
        });
      }, 1000);

      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      };
    }
  }, [isRunning, currentSeconds]);

  // Start timer
  const start = useCallback(() => {
    if (currentSeconds > 0) {
      setIsRunning(true);
    }
  }, [currentSeconds]);

  // Pause timer
  const pause = useCallback(() => {
    setIsRunning(false);
  }, []);

  // Resume timer
  const resume = useCallback(() => {
    if (currentSeconds > 0) {
      setIsRunning(true);
    }
  }, [currentSeconds]);

  // Reset timer to initial value
  const reset = useCallback(() => {
    setIsRunning(false);
    setCurrentSeconds(totalSeconds);
  }, [totalSeconds]);

  // Stop timer (reset to 0)
  const stop = useCallback(() => {
    setIsRunning(false);
    setCurrentSeconds(0);
  }, []);

  // Set timer to specific value
  const setTime = useCallback((seconds: number) => {
    setCurrentSeconds(seconds);
  }, []);

  // Update total when prop changes
  useEffect(() => {
    if (!isRunning) {
      setCurrentSeconds(totalSeconds);
    }
  }, [totalSeconds, isRunning]);

  return {
    isRunning,
    currentSeconds,
    totalSeconds,
    progress,
    start,
    pause,
    resume,
    reset,
    stop,
    setTime,
  };
}

/**
 * Hook for multiple timers (sub-blocks)
 */
export function useMultiTimer(durations: number[]) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [completedIndices, setCompletedIndices] = useState<Set<number>>(new Set());

  const handleComplete = useCallback(() => {
    setCompletedIndices((prev) => new Set(prev).add(currentIndex));

    // Auto-advance to next timer
    if (currentIndex < durations.length - 1) {
      setCurrentIndex((prev) => prev + 1);
    }
  }, [currentIndex, durations.length]);

  const timer = useTimer({
    totalSeconds: durations[currentIndex] * 60, // Convert minutes to seconds
    onComplete: handleComplete,
    autoStart: false,
  });

  const goToTimer = useCallback((index: number) => {
    if (index >= 0 && index < durations.length) {
      timer.reset();
      setCurrentIndex(index);
    }
  }, [durations.length, timer]);

  const resetAll = useCallback(() => {
    timer.reset();
    setCurrentIndex(0);
    setCompletedIndices(new Set());
  }, [timer]);

  return {
    ...timer,
    currentIndex,
    completedIndices,
    goToTimer,
    resetAll,
    isLastTimer: currentIndex === durations.length - 1,
    totalTimers: durations.length,
  };
}
