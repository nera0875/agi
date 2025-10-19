import { useState, useEffect, useCallback, useRef } from 'react';
import type { BlockContainer } from '../types/timeblock';

interface ContainerTimerState {
  // Global container timer
  containerElapsedSeconds: number;
  containerTotalSeconds: number;
  containerProgress: number; // 0-100
  containerRemaining: number;

  // Current block timer
  currentBlockIndex: number;
  blockElapsedSeconds: number;
  blockTotalSeconds: number;
  blockProgress: number; // 0-100
  blockRemaining: number;

  // State
  isRunning: boolean;
  isCompleted: boolean;
  hasReachedLimit: boolean; // TRUE if container time limit reached
}

interface UseContainerTimerReturn extends ContainerTimerState {
  start: () => void;
  pause: () => void;
  resume: () => void;
  stop: () => void;
  nextBlock: () => void;
  previousBlock: () => void;
}

/**
 * STRICT TIMER for Asperger time-blocking
 *
 * RULES:
 * - Container has HARD LIMIT (e.g., 60min) - CANNOT be exceeded
 * - Blocks have individual durations (20min, 20min, 20min)
 * - If block finishes before container limit → auto-advance to next block
 * - If container limit reached → FORCE STOP even if blocks not finished
 * - Timer counts UP (not down) to show progress
 *
 * Example:
 * Container: 60min hard limit
 * Block 1: 20min → finishes at 20min container time
 * Block 2: 20min → finishes at 40min container time
 * Block 3: 20min → finishes at 60min container time
 * At 60min: FORCE STOP, session complete
 */
export function useContainerTimer(container: BlockContainer): UseContainerTimerReturn {
  const [isRunning, setIsRunning] = useState(false);
  const [containerElapsedSeconds, setContainerElapsedSeconds] = useState(0);
  const [currentBlockIndex, setCurrentBlockIndex] = useState(0);
  const [blockElapsedSeconds, setBlockElapsedSeconds] = useState(0);

  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Calculate totals
  const containerTotalSeconds = container.totalDuration * 60;
  const currentBlock = container.blocks[currentBlockIndex];
  const blockTotalSeconds = currentBlock ? currentBlock.duration * 60 : 0;

  // Calculate block start time in container
  const blockStartSeconds = container.blocks
    .slice(0, currentBlockIndex)
    .reduce((sum, b) => sum + b.duration * 60, 0);

  // Progress calculations
  const containerProgress = (containerElapsedSeconds / containerTotalSeconds) * 100;
  const blockProgress = blockTotalSeconds > 0 ? (blockElapsedSeconds / blockTotalSeconds) * 100 : 0;
  const containerRemaining = Math.max(0, containerTotalSeconds - containerElapsedSeconds);
  const blockRemaining = Math.max(0, blockTotalSeconds - blockElapsedSeconds);

  // Check completion states
  const hasReachedLimit = containerElapsedSeconds >= containerTotalSeconds;
  const isBlockComplete = blockElapsedSeconds >= blockTotalSeconds;
  const isCompleted = hasReachedLimit || (currentBlockIndex >= container.blocks.length - 1 && isBlockComplete);

  // MAIN TIMER TICK - STRICT RULES
  useEffect(() => {
    if (!isRunning) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    intervalRef.current = setInterval(() => {
      setContainerElapsedSeconds((prev) => {
        const next = prev + 1;

        // HARD LIMIT - FORCE STOP if container time exceeded
        if (next >= containerTotalSeconds) {
          setIsRunning(false);
          return containerTotalSeconds; // Cap at max
        }

        return next;
      });

      setBlockElapsedSeconds((prev) => {
        const next = prev + 1;

        // If block finished, auto-advance to next block
        if (next >= blockTotalSeconds && currentBlockIndex < container.blocks.length - 1) {
          setCurrentBlockIndex((idx) => idx + 1);
          setBlockElapsedSeconds(0);
          return 0;
        }

        // Cap block elapsed at its duration
        return Math.min(next, blockTotalSeconds);
      });
    }, 1000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isRunning, containerTotalSeconds, blockTotalSeconds, currentBlockIndex, container.blocks.length]);

  // Start timer
  const start = useCallback(() => {
    if (hasReachedLimit) return;
    setIsRunning(true);
  }, [hasReachedLimit]);

  // Pause timer
  const pause = useCallback(() => {
    setIsRunning(false);
  }, []);

  // Resume timer
  const resume = useCallback(() => {
    if (hasReachedLimit) return;
    setIsRunning(true);
  }, [hasReachedLimit]);

  // Stop timer (reset everything)
  const stop = useCallback(() => {
    setIsRunning(false);
    setContainerElapsedSeconds(0);
    setCurrentBlockIndex(0);
    setBlockElapsedSeconds(0);
  }, []);

  // Manual block navigation
  const nextBlock = useCallback(() => {
    if (currentBlockIndex < container.blocks.length - 1) {
      setCurrentBlockIndex((prev) => prev + 1);
      setBlockElapsedSeconds(0);
    }
  }, [currentBlockIndex, container.blocks.length]);

  const previousBlock = useCallback(() => {
    if (currentBlockIndex > 0) {
      setCurrentBlockIndex((prev) => prev - 1);
      setBlockElapsedSeconds(0);
    }
  }, [currentBlockIndex]);

  return {
    // Container state
    containerElapsedSeconds,
    containerTotalSeconds,
    containerProgress,
    containerRemaining,

    // Block state
    currentBlockIndex,
    blockElapsedSeconds,
    blockTotalSeconds,
    blockProgress,
    blockRemaining,

    // Status
    isRunning,
    isCompleted,
    hasReachedLimit,

    // Controls
    start,
    pause,
    resume,
    stop,
    nextBlock,
    previousBlock,
  };
}

/**
 * Format seconds to MM:SS
 */
export function formatTimerDisplay(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Format seconds to human readable duration
 */
export function formatTimerDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  if (mins < 60) {
    return `${mins}min`;
  }
  const hours = Math.floor(mins / 60);
  const remainingMins = mins % 60;
  return remainingMins > 0 ? `${hours}h ${remainingMins}min` : `${hours}h`;
}
