/**
 * Time Blocking System Types
 * Pomodoro-style time management with flexible blocks
 */

export type BlockStatus = 'pending' | 'active' | 'paused' | 'completed' | 'skipped';
export type SubBlockStatus = 'pending' | 'active' | 'completed' | 'skipped';
export type PauseType = 'short' | 'long';

/**
 * Single sub-block within a time block (e.g., 20 minutes)
 */
export interface SubBlock {
  id: string;
  duration: number; // minutes
  status: SubBlockStatus;
  startedAt?: Date;
  completedAt?: Date;
  elapsedSeconds: number; // Track actual time spent
}

/**
 * Task associated with a time block
 */
export interface BlockTask {
  id: string;
  title: string;
  description?: string;
  completed: boolean;
  blockId: string;
  createdAt: Date;
  completedAt?: Date;
}

/**
 * Main time block (e.g., 60 minutes divided into 3x20min)
 */
export interface TimeBlock {
  id: string;
  name: string;
  duration: number; // Total duration in minutes
  subBlocks: SubBlock[];
  tasks: BlockTask[];
  status: BlockStatus;
  startedAt?: Date;
  completedAt?: Date;
  pausedAt?: Date;
  currentSubBlockIndex: number;
  color?: string; // Hex color for UI
}

/**
 * Pause period between blocks
 */
export interface PauseBlock {
  id: string;
  type: PauseType;
  duration: number; // minutes
  status: 'pending' | 'active' | 'completed' | 'skipped';
  startedAt?: Date;
  completedAt?: Date;
  elapsedSeconds: number;
}

/**
 * Complete work session with multiple blocks
 */
export interface WorkSession {
  id: string;
  name: string;
  blocks: TimeBlock[];
  currentBlockIndex: number;
  currentPause: PauseBlock | null;
  cycleCount: number; // Track completed cycles for long pause
  status: 'idle' | 'active' | 'paused' | 'completed';
  settings: SessionSettings;
  createdAt: Date;
  startedAt?: Date;
  completedAt?: Date;
}

/**
 * Session configuration
 */
export interface SessionSettings {
  defaultBlockDuration: number; // 60 minutes
  defaultSubBlockCount: number; // 3 sub-blocks
  shortPauseDuration: number; // 10 minutes
  longPauseDuration: number; // 60 minutes
  cyclesBeforeLongPause: number; // 4 cycles
  enableNotifications: boolean;
  enableSound: boolean;
  autoStartNextBlock: boolean;
  autoStartPause: boolean;
}

/**
 * Timer state for active block/pause
 */
export interface TimerState {
  isRunning: boolean;
  currentSeconds: number;
  totalSeconds: number;
  progress: number; // 0-100
}

/**
 * Statistics for completed sessions
 */
export interface SessionStats {
  totalSessions: number;
  totalBlocks: number;
  totalTimeMinutes: number;
  completedTasks: number;
  averageBlockCompletion: number; // percentage
  streakDays: number;
}

/**
 * Default settings
 */
export const DEFAULT_SETTINGS: SessionSettings = {
  defaultBlockDuration: 60,
  defaultSubBlockCount: 3,
  shortPauseDuration: 10,
  longPauseDuration: 60,
  cyclesBeforeLongPause: 4,
  enableNotifications: true,
  enableSound: true,
  autoStartNextBlock: false,
  autoStartPause: true,
};

/**
 * Helper to create a new sub-block
 */
export function createSubBlock(duration: number, index: number): SubBlock {
  return {
    id: `sub-${Date.now()}-${index}`,
    duration,
    status: 'pending',
    elapsedSeconds: 0,
  };
}

/**
 * Helper to create a new time block
 */
export function createTimeBlock(
  name: string,
  duration: number,
  subBlockCount: number
): TimeBlock {
  const subBlockDuration = Math.floor(duration / subBlockCount);
  const subBlocks = Array.from({ length: subBlockCount }, (_, i) =>
    createSubBlock(subBlockDuration, i)
  );

  return {
    id: `block-${Date.now()}`,
    name,
    duration,
    subBlocks,
    tasks: [],
    status: 'pending',
    currentSubBlockIndex: 0,
  };
}

/**
 * Helper to create a pause block
 */
export function createPauseBlock(type: PauseType, duration: number): PauseBlock {
  return {
    id: `pause-${Date.now()}`,
    type,
    duration,
    status: 'pending',
    elapsedSeconds: 0,
  };
}

/**
 * Helper to create a new work session
 */
export function createWorkSession(
  name: string,
  settings: SessionSettings = DEFAULT_SETTINGS
): WorkSession {
  return {
    id: `session-${Date.now()}`,
    name,
    blocks: [],
    currentBlockIndex: 0,
    currentPause: null,
    cycleCount: 0,
    status: 'idle',
    settings,
    createdAt: new Date(),
  };
}

/**
 * Calculate next pause type based on cycle count
 */
export function getNextPauseType(
  cycleCount: number,
  settings: SessionSettings
): PauseType {
  if ((cycleCount + 1) % settings.cyclesBeforeLongPause === 0) {
    return 'long';
  }
  return 'short';
}

/**
 * Calculate next pause duration
 */
export function getNextPauseDuration(
  cycleCount: number,
  settings: SessionSettings
): number {
  const pauseType = getNextPauseType(cycleCount, settings);
  return pauseType === 'long'
    ? settings.longPauseDuration
    : settings.shortPauseDuration;
}

/**
 * Format seconds to MM:SS
 */
export function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Format duration to human readable
 */
export function formatDuration(minutes: number): string {
  if (minutes < 60) {
    return `${minutes}min`;
  }
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return mins > 0 ? `${hours}h ${mins}min` : `${hours}h`;
}

// ============================================================================
// CONTAINER SYSTEM - New hierarchical structure
// ============================================================================

export type ContainerStatus = 'idle' | 'locked' | 'completed';
export type DayOfWeek = 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday';
export type RepeatType = 'none' | 'daily' | 'weekly' | 'weekdays' | 'custom';

/**
 * Container Block - simplified block for container
 */
export interface ContainerBlock {
  id: string;
  name: string;
  duration: number; // minutes
  tasks: BlockTask[];
  color?: string;
  position: number; // Order in container
}

/**
 * Block Container - Main container with hard time limit
 * Contains multiple blocks that must fit within totalDuration
 */
export interface BlockContainer {
  id: string;
  name: string;
  totalDuration: number; // HARD LIMIT (e.g., 60min)
  pauseAfter: number; // Auto pause duration (e.g., 10min)
  blocks: ContainerBlock[];
  status: ContainerStatus;
  locked: boolean; // true = running, cannot stop
  progress: number; // minutes elapsed
  currentBlockIndex: number;
  color?: string; // Container accent color
  isTemplate: boolean; // Template vs active instance
  createdAt: Date;
  startedAt?: Date;
  completedAt?: Date;
}

/**
 * Repeat Pattern - for scheduled containers and routines
 */
export interface RepeatPattern {
  enabled: boolean;
  type: RepeatType;
  days?: DayOfWeek[]; // For weekly/custom
  sameTime: boolean; // Lock time for routine (energy saving)
  exceptions?: Date[]; // Skip dates
}

/**
 * Scheduled Container - Container assigned to time slot
 */
export interface ScheduledContainer {
  id: string;
  containerId: string;
  container: BlockContainer;
  date: Date;
  startTime: string; // "09:00"
  endTime: string; // "10:00"
  repeat?: RepeatPattern;
  status: 'pending' | 'active' | 'completed' | 'skipped';
}

/**
 * Daily Schedule - All containers for a day
 */
export interface DailySchedule {
  date: Date;
  scheduledContainers: ScheduledContainer[];
  totalDuration: number; // Sum of all containers
  completedDuration: number;
}

/**
 * Routine - Reusable scheduled container template
 */
export interface Routine {
  id: string;
  name: string;
  containerId: string;
  startTime: string; // "09:00"
  duration: number; // minutes
  repeatPattern: RepeatPattern;
  active: boolean;
  createdAt: Date;
}

// Counters to ensure unique IDs even when called rapidly
let blockIdCounter = 0;
let containerIdCounter = 0;

/**
 * Create a new container block with guaranteed unique ID
 */
export function createContainerBlock(
  name: string,
  duration: number,
  position: number
): ContainerBlock {
  blockIdCounter++;
  return {
    id: `cblock-${Date.now()}-${blockIdCounter}-${Math.random().toString(36).substr(2, 9)}`,
    name,
    duration,
    tasks: [],
    position,
  };
}

/**
 * Create a new block container with guaranteed unique ID
 */
export function createBlockContainer(
  name: string,
  totalDuration: number,
  pauseAfter: number = 10
): BlockContainer {
  containerIdCounter++;
  return {
    id: `container-${Date.now()}-${containerIdCounter}-${Math.random().toString(36).substr(2, 9)}`,
    name,
    totalDuration,
    pauseAfter,
    blocks: [],
    status: 'idle',
    locked: false,
    progress: 0,
    currentBlockIndex: 0,
    isTemplate: true,
    createdAt: new Date(),
  };
}

/**
 * Validate that blocks fit within container duration
 */
export function validateContainerBlocks(
  blocks: ContainerBlock[],
  totalDuration: number
): { valid: boolean; totalUsed: number; remaining: number } {
  const totalUsed = blocks.reduce((sum, block) => sum + block.duration, 0);
  return {
    valid: totalUsed <= totalDuration,
    totalUsed,
    remaining: totalDuration - totalUsed,
  };
}

/**
 * Calculate block proportional height for UI
 */
export function calculateBlockProportion(
  blockDuration: number,
  containerDuration: number
): number {
  return (blockDuration / containerDuration) * 100;
}

/**
 * Create scheduled container from template
 */
export function createScheduledContainer(
  container: BlockContainer,
  date: Date,
  startTime: string
): ScheduledContainer {
  const [hours, minutes] = startTime.split(':').map(Number);
  const endDate = new Date(date);
  endDate.setHours(hours);
  endDate.setMinutes(minutes + container.totalDuration);
  const endTime = `${endDate.getHours().toString().padStart(2, '0')}:${endDate.getMinutes().toString().padStart(2, '0')}`;

  return {
    id: `scheduled-${Date.now()}`,
    containerId: container.id,
    container,
    date,
    startTime,
    endTime,
    status: 'pending',
  };
}

/**
 * Create a routine template
 */
export function createRoutine(
  name: string,
  containerId: string,
  startTime: string,
  duration: number,
  repeatPattern: RepeatPattern
): Routine {
  return {
    id: `routine-${Date.now()}`,
    name,
    containerId,
    startTime,
    duration,
    repeatPattern,
    active: true,
    createdAt: new Date(),
  };
}

/**
 * Format time slot (09:00-10:00)
 */
export function formatTimeSlot(startTime: string, endTime: string): string {
  return `${startTime}-${endTime}`;
}
