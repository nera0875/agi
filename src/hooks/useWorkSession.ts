import { useState, useCallback, useEffect } from 'react';
import { toast } from 'sonner';
import type {
  WorkSession,
  TimeBlock,
  BlockTask,
  PauseBlock,
  SessionSettings,
} from '../types/timeblock';
import {
  createWorkSession,
  createTimeBlock,
  createPauseBlock,
  getNextPauseType,
  getNextPauseDuration,
  DEFAULT_SETTINGS,
} from '../types/timeblock';

interface UseWorkSessionReturn {
  session: WorkSession | null;
  currentBlock: TimeBlock | null;
  currentPause: PauseBlock | null;
  createSession: (name: string, settings?: SessionSettings) => void;
  addBlock: (name: string, duration?: number) => void;
  removeBlock: (blockId: string) => void;
  startBlock: (blockId: string) => void;
  pauseBlock: () => void;
  resumeBlock: () => void;
  stopBlock: () => void;
  skipBlock: () => void;
  completeBlock: () => void;
  addTask: (blockId: string, title: string) => void;
  toggleTask: (blockId: string, taskId: string) => void;
  deleteTask: (blockId: string, taskId: string) => void;
  startPause: () => void;
  skipPause: () => void;
  updateSettings: (settings: Partial<SessionSettings>) => void;
  saveSession: () => void;
  loadSession: (sessionData: WorkSession) => void;
}

const STORAGE_KEY = 'work-session';

/**
 * Main hook for managing work sessions
 */
export function useWorkSession(): UseWorkSessionReturn {
  const [session, setSession] = useState<WorkSession | null>(null);

  // Load session from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        // Convert date strings back to Date objects
        parsed.createdAt = new Date(parsed.createdAt);
        if (parsed.startedAt) parsed.startedAt = new Date(parsed.startedAt);
        if (parsed.completedAt) parsed.completedAt = new Date(parsed.completedAt);
        setSession(parsed);
      } catch (error) {
        console.error('Failed to load session from localStorage:', error);
      }
    }
  }, []);

  // Auto-save to localStorage when session changes
  useEffect(() => {
    if (session) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    }
  }, [session]);

  // Get current block
  const currentBlock = session
    ? session.blocks[session.currentBlockIndex] || null
    : null;

  // Get current pause
  const currentPause = session?.currentPause || null;

  // Request notification permission
  useEffect(() => {
    if (session?.settings.enableNotifications && 'Notification' in window) {
      if (Notification.permission === 'default') {
        Notification.requestPermission();
      }
    }
  }, [session?.settings.enableNotifications]);

  // Show notification
  const showNotification = useCallback(
    (title: string, body: string) => {
      if (!session?.settings.enableNotifications) return;

      // Browser notification
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, { body, icon: '/favicon.ico' });
      }

      // Toast notification
      toast.success(title, { description: body });

      // Sound notification
      if (session.settings.enableSound) {
        const audio = new Audio('/notification.mp3');
        audio.play().catch(() => {
          // Fallback beep using Web Audio API
          const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
          const oscillator = audioContext.createOscillator();
          const gainNode = audioContext.createGain();

          oscillator.connect(gainNode);
          gainNode.connect(audioContext.destination);

          oscillator.frequency.value = 800;
          oscillator.type = 'sine';

          gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
          gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

          oscillator.start(audioContext.currentTime);
          oscillator.stop(audioContext.currentTime + 0.5);
        });
      }
    },
    [session?.settings]
  );

  const createSession = useCallback((name: string, settings?: SessionSettings) => {
    const newSession = createWorkSession(name, settings || DEFAULT_SETTINGS);
    setSession(newSession);
    toast.success('Session created', { description: `Started "${name}"` });
  }, []);

  const addBlock = useCallback((name: string, duration?: number) => {
    setSession((prev) => {
      if (!prev) return prev;

      const blockDuration = duration || prev.settings.defaultBlockDuration;
      const subBlockCount = prev.settings.defaultSubBlockCount;
      const newBlock = createTimeBlock(name, blockDuration, subBlockCount);

      return {
        ...prev,
        blocks: [...prev.blocks, newBlock],
      };
    });
  }, []);

  const removeBlock = useCallback((blockId: string) => {
    setSession((prev) => {
      if (!prev) return prev;

      const blockIndex = prev.blocks.findIndex((b) => b.id === blockId);
      if (blockIndex === -1) return prev;

      const newBlocks = prev.blocks.filter((b) => b.id !== blockId);
      const newCurrentIndex =
        prev.currentBlockIndex >= newBlocks.length
          ? Math.max(0, newBlocks.length - 1)
          : prev.currentBlockIndex;

      return {
        ...prev,
        blocks: newBlocks,
        currentBlockIndex: newCurrentIndex,
      };
    });
  }, []);

  const startBlock = useCallback(
    (blockId: string) => {
      setSession((prev) => {
        if (!prev) return prev;

        const blockIndex = prev.blocks.findIndex((b) => b.id === blockId);
        if (blockIndex === -1) return prev;

        const newBlocks = [...prev.blocks];
        newBlocks[blockIndex] = {
          ...newBlocks[blockIndex],
          status: 'active',
          startedAt: new Date(),
        };

        showNotification(
          'Block Started',
          `Working on: ${newBlocks[blockIndex].name}`
        );

        return {
          ...prev,
          blocks: newBlocks,
          currentBlockIndex: blockIndex,
          status: 'active',
          startedAt: prev.startedAt || new Date(),
        };
      });
    },
    [showNotification]
  );

  const pauseBlock = useCallback(() => {
    setSession((prev) => {
      if (!prev || !currentBlock) return prev;

      const newBlocks = [...prev.blocks];
      const blockIndex = prev.currentBlockIndex;
      newBlocks[blockIndex] = {
        ...newBlocks[blockIndex],
        status: 'paused',
        pausedAt: new Date(),
      };

      return {
        ...prev,
        blocks: newBlocks,
        status: 'paused',
      };
    });
  }, [currentBlock]);

  const resumeBlock = useCallback(() => {
    setSession((prev) => {
      if (!prev || !currentBlock) return prev;

      const newBlocks = [...prev.blocks];
      const blockIndex = prev.currentBlockIndex;
      newBlocks[blockIndex] = {
        ...newBlocks[blockIndex],
        status: 'active',
        pausedAt: undefined,
      };

      return {
        ...prev,
        blocks: newBlocks,
        status: 'active',
      };
    });
  }, [currentBlock]);

  const stopBlock = useCallback(() => {
    setSession((prev) => {
      if (!prev || !currentBlock) return prev;

      const newBlocks = [...prev.blocks];
      const blockIndex = prev.currentBlockIndex;
      newBlocks[blockIndex] = {
        ...newBlocks[blockIndex],
        status: 'pending',
        startedAt: undefined,
        pausedAt: undefined,
      };

      return {
        ...prev,
        blocks: newBlocks,
        status: 'idle',
      };
    });
  }, [currentBlock]);

  const skipBlock = useCallback(() => {
    setSession((prev) => {
      if (!prev || !currentBlock) return prev;

      const newBlocks = [...prev.blocks];
      const blockIndex = prev.currentBlockIndex;
      newBlocks[blockIndex] = {
        ...newBlocks[blockIndex],
        status: 'skipped',
        completedAt: new Date(),
      };

      // Move to next block if available
      const nextIndex = blockIndex + 1;
      if (nextIndex < newBlocks.length && prev.settings.autoStartNextBlock) {
        newBlocks[nextIndex] = {
          ...newBlocks[nextIndex],
          status: 'active',
          startedAt: new Date(),
        };
      }

      return {
        ...prev,
        blocks: newBlocks,
        currentBlockIndex: Math.min(nextIndex, newBlocks.length - 1),
        status: nextIndex < newBlocks.length ? 'active' : 'idle',
      };
    });
  }, [currentBlock]);

  const completeBlock = useCallback(() => {
    setSession((prev) => {
      if (!prev || !currentBlock) return prev;

      const newBlocks = [...prev.blocks];
      const blockIndex = prev.currentBlockIndex;
      newBlocks[blockIndex] = {
        ...newBlocks[blockIndex],
        status: 'completed',
        completedAt: new Date(),
      };

      const newCycleCount = prev.cycleCount + 1;

      showNotification(
        'Block Completed!',
        `Finished: ${newBlocks[blockIndex].name}`
      );

      // Check if there's a next block
      const nextIndex = blockIndex + 1;
      const hasNextBlock = nextIndex < newBlocks.length;

      // Start pause if auto-start enabled
      let newPause: PauseBlock | null = null;
      if (hasNextBlock && prev.settings.autoStartPause) {
        const pauseType = getNextPauseType(newCycleCount, prev.settings);
        const pauseDuration = getNextPauseDuration(newCycleCount, prev.settings);
        newPause = createPauseBlock(pauseType, pauseDuration);
        newPause.status = 'active';
        newPause.startedAt = new Date();

        showNotification(
          `${pauseType === 'long' ? 'Long' : 'Short'} Pause Started`,
          `Take a ${pauseDuration} minute break!`
        );
      }

      return {
        ...prev,
        blocks: newBlocks,
        currentBlockIndex: nextIndex,
        currentPause: newPause,
        cycleCount: newCycleCount,
        status: newPause ? 'active' : hasNextBlock ? 'idle' : 'completed',
        completedAt: !hasNextBlock ? new Date() : undefined,
      };
    });
  }, [currentBlock, showNotification]);

  const startPause = useCallback(() => {
    setSession((prev) => {
      if (!prev) return prev;

      const pauseType = getNextPauseType(prev.cycleCount, prev.settings);
      const pauseDuration = getNextPauseDuration(prev.cycleCount, prev.settings);
      const newPause = createPauseBlock(pauseType, pauseDuration);
      newPause.status = 'active';
      newPause.startedAt = new Date();

      showNotification(
        `${pauseType === 'long' ? 'Long' : 'Short'} Pause`,
        `Starting ${pauseDuration} minute break`
      );

      return {
        ...prev,
        currentPause: newPause,
        status: 'active',
      };
    });
  }, [showNotification]);

  const skipPause = useCallback(() => {
    setSession((prev) => {
      if (!prev) return prev;

      const nextIndex = prev.currentBlockIndex;
      const hasNextBlock = nextIndex < prev.blocks.length;

      if (hasNextBlock && prev.settings.autoStartNextBlock) {
        const newBlocks = [...prev.blocks];
        newBlocks[nextIndex] = {
          ...newBlocks[nextIndex],
          status: 'active',
          startedAt: new Date(),
        };

        showNotification(
          'Next Block Started',
          `Working on: ${newBlocks[nextIndex].name}`
        );

        return {
          ...prev,
          blocks: newBlocks,
          currentPause: null,
          status: 'active',
        };
      }

      return {
        ...prev,
        currentPause: null,
        status: 'idle',
      };
    });
  }, [showNotification]);

  const addTask = useCallback((blockId: string, title: string) => {
    setSession((prev) => {
      if (!prev) return prev;

      const blockIndex = prev.blocks.findIndex((b) => b.id === blockId);
      if (blockIndex === -1) return prev;

      const newBlocks = [...prev.blocks];
      const newTask: BlockTask = {
        id: `task-${Date.now()}`,
        title,
        completed: false,
        blockId,
        createdAt: new Date(),
      };

      newBlocks[blockIndex] = {
        ...newBlocks[blockIndex],
        tasks: [...newBlocks[blockIndex].tasks, newTask],
      };

      return { ...prev, blocks: newBlocks };
    });
  }, []);

  const toggleTask = useCallback((blockId: string, taskId: string) => {
    setSession((prev) => {
      if (!prev) return prev;

      const blockIndex = prev.blocks.findIndex((b) => b.id === blockId);
      if (blockIndex === -1) return prev;

      const newBlocks = [...prev.blocks];
      const taskIndex = newBlocks[blockIndex].tasks.findIndex((t) => t.id === taskId);
      if (taskIndex === -1) return prev;

      const task = newBlocks[blockIndex].tasks[taskIndex];
      newBlocks[blockIndex].tasks[taskIndex] = {
        ...task,
        completed: !task.completed,
        completedAt: !task.completed ? new Date() : undefined,
      };

      return { ...prev, blocks: newBlocks };
    });
  }, []);

  const deleteTask = useCallback((blockId: string, taskId: string) => {
    setSession((prev) => {
      if (!prev) return prev;

      const blockIndex = prev.blocks.findIndex((b) => b.id === blockId);
      if (blockIndex === -1) return prev;

      const newBlocks = [...prev.blocks];
      newBlocks[blockIndex] = {
        ...newBlocks[blockIndex],
        tasks: newBlocks[blockIndex].tasks.filter((t) => t.id !== taskId),
      };

      return { ...prev, blocks: newBlocks };
    });
  }, []);

  const updateSettings = useCallback((newSettings: Partial<SessionSettings>) => {
    setSession((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        settings: { ...prev.settings, ...newSettings },
      };
    });
  }, []);

  const saveSession = useCallback(() => {
    if (session) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
      toast.success('Session saved');
    }
  }, [session]);

  const loadSession = useCallback((sessionData: WorkSession) => {
    setSession(sessionData);
    toast.success('Session loaded');
  }, []);

  return {
    session,
    currentBlock,
    currentPause,
    createSession,
    addBlock,
    removeBlock,
    startBlock,
    pauseBlock,
    resumeBlock,
    stopBlock,
    skipBlock,
    completeBlock,
    addTask,
    toggleTask,
    deleteTask,
    startPause,
    skipPause,
    updateSettings,
    saveSession,
    loadSession,
  };
}
