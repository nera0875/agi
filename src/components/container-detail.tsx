import { useState, useEffect, useCallback } from 'react';
import { useMutation } from '@apollo/client/react';
import { ArrowLeft, Plus, Settings, Play, X, GripVertical, Pause, RotateCcw } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Checkbox } from './ui/checkbox';
import { BlockBuilder } from './block-builder';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from './ui/dialog';
import { Label } from './ui/label';
import { Slider } from './ui/slider';
import type { BlockContainer, Block, Task } from '../types/timeblock';
import { formatDuration } from '../types/timeblock';
import { UPDATE_BLOCKS, GET_ALL_CONTAINERS } from '../graphql/containers';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  rectSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

interface ContainerDetailProps {
  container: BlockContainer;
  onBack: () => void;
  onUpdateContainer: (containerId: string, updates: Partial<BlockContainer>) => void;
  onAddTask: (containerId: string, blockId: string, taskTitle: string) => void;
  onToggleTask: (containerId: string, blockId: string, taskId: string) => void;
  onStartContainer: (containerId: string) => void;
}

interface SortableBlockProps {
  block: Block;
  containerId: string;
  containerExpired: boolean;
  containerRemainingSeconds: number;
  onContainerAdvance: () => void;
  onDelete: (blockId: string) => void;
  onToggleTask: (containerId: string, blockId: string, taskId: string) => void;
  onUpdateBlock: (blockId: string, updates: Partial<Block>) => void;
  addingTaskToBlock: string | null;
  setAddingTaskToBlock: (blockId: string | null) => void;
  newTaskTitle: string;
  setNewTaskTitle: (title: string) => void;
  handleAddTask: (blockId: string) => void;
}

// Sortable Block Component
function SortableBlock({
  block,
  containerId,
  containerExpired,
  containerRemainingSeconds,
  onContainerAdvance,
  onDelete,
  onToggleTask,
  onUpdateBlock,
  addingTaskToBlock,
  setAddingTaskToBlock,
  newTaskTitle,
  setNewTaskTitle,
  handleAddTask
}: SortableBlockProps) {
  const [isEditingName, setIsEditingName] = useState(false);
  const [editedName, setEditedName] = useState(block.name);

  // TIMER integrated into block
  const [isTimerRunning, setIsTimerRunning] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const totalSeconds = block.duration * 60;
  const blockRemainingSeconds = totalSeconds - elapsedSeconds;

  // Check if can start (enough time in container)
  const canStart = containerRemainingSeconds >= blockRemainingSeconds;

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: block.id });

  // Timer tick - SYNCHRONIZED with container
  useEffect(() => {
    if (!isTimerRunning || containerExpired) return;

    const interval = setInterval(() => {
      setElapsedSeconds((prev) => {
        if (prev >= totalSeconds) {
          setIsTimerRunning(false);
          return totalSeconds;
        }
        // CRITICAL: Advance container timer in sync with block timer
        onContainerAdvance();
        return prev + 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isTimerRunning, totalSeconds, containerExpired, onContainerAdvance]);

  const handleStartTimer = () => setIsTimerRunning(true);
  const handlePauseTimer = () => setIsTimerRunning(false);
  const handleResetTimer = () => {
    setIsTimerRunning(false);
    setElapsedSeconds(0);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const progress = (elapsedSeconds / totalSeconds) * 100;
  const isComplete = elapsedSeconds >= totalSeconds;

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const customStyle = {
    ...style,
    height: '200px',
  };

  const handleSaveName = () => {
    if (editedName.trim() && editedName !== block.name) {
      onUpdateBlock(block.id, { name: editedName.trim() });
    }
    setIsEditingName(false);
  };

  // Determine color indicator class (semantic tokens only)
  const getColorIndicatorClass = () => {
    if (!block.color) return '';
    // Map hex colors to semantic chart tokens
    const colorMap: Record<string, string> = {
      '#000000': 'bg-chart-1', // Black
      '#71717a': 'bg-chart-2', // Zinc-600
      '#a1a1aa': 'bg-chart-3', // Zinc-400
      '#d4d4d8': 'bg-chart-4', // Zinc-300
      '#e4e4e7': 'bg-chart-5', // Zinc-200
    };
    return colorMap[block.color] || 'bg-chart-2'; // Default to chart-2
  };

  return (
    <div
      ref={setNodeRef}
      style={customStyle}
      className="border-2 border-border rounded-lg bg-card p-3 flex flex-col shadow-sm hover:shadow-md hover:border-border transition-all cursor-pointer relative group"
    >
      {/* Color indicator bar - THICK */}
      {block.color && (
        <div
          className={`absolute top-0 left-0 right-0 h-2 rounded-t-lg ${getColorIndicatorClass()}`}
        />
      )}

      {/* Drag handle + Delete button - COMPACT */}
      <div className="absolute top-2 right-2 flex items-center gap-0.5 z-10">
        <button
          onClick={() => onDelete(block.id)}
          className="opacity-0 group-hover:opacity-100 p-1 hover:bg-accent rounded transition-opacity"
        >
          <X className="h-3 w-3 text-foreground" />
        </button>
        <div {...attributes} {...listeners} className="cursor-grab active:cursor-grabbing p-1 hover:bg-accent rounded">
          <GripVertical className="h-3 w-3 text-muted-foreground" />
        </div>
      </div>

      {/* Block Header - COMPACT with INLINE EDIT */}
      <div className="mb-2 pb-2 border-b border-border pr-12 pt-2">
        {isEditingName ? (
          <Input
            value={editedName}
            onChange={(e) => setEditedName(e.target.value)}
            onBlur={handleSaveName}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSaveName();
              if (e.key === 'Escape') {
                setEditedName(block.name);
                setIsEditingName(false);
              }
            }}
            className="h-5 bg-card border-border text-foreground placeholder:text-muted-foreground px-1 py-0 mb-1"
            autoFocus
          />
        ) : (
          <h4
            className="text-foreground truncate cursor-text hover:text-muted-foreground mb-1"
            onDoubleClick={() => setIsEditingName(true)}
            title="Double-click to edit"
          >
            {block.name}
          </h4>
        )}

        {/* TIMER integrated */}
        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground px-0">{formatTime(elapsedSeconds)} / {formatTime(totalSeconds)}</span>
            <span className={`${isComplete ? 'text-foreground' : isTimerRunning ? 'text-foreground' : 'text-muted-foreground'}`}>
              {isComplete ? 'DONE' : isTimerRunning ? 'RUNNING' : 'READY'}
            </span>
          </div>

          {/* Progress bar */}
          <div className="h-1 bg-muted rounded-full overflow-hidden">
            <div
              className={`h-full transition-all ${isComplete ? 'bg-chart-3' : 'bg-chart-2'}`}
              style={{ width: `${Math.min(100, progress)}%` }}
            />
          </div>

          {/* Timer controls */}
          <div className="flex items-center gap-1 pt-1">
            {!isTimerRunning ? (
              <button
                onClick={handleStartTimer}
                disabled={isComplete || containerExpired || !canStart}
                className="flex-1 py-1 bg-primary hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed rounded flex items-center justify-center gap-1 text-primary-foreground"
                title={
                  containerExpired
                    ? 'Container session expired - cannot start block timers'
                    : !canStart
                    ? `Not enough time in container (need ${Math.ceil(blockRemainingSeconds/60)}min, have ${Math.ceil(containerRemainingSeconds/60)}min)`
                    : ''
                }
              >
                <Play className="h-2.5 w-2.5" />
                {containerExpired ? 'LOCKED' : !canStart ? 'NO TIME' : 'Start'}
              </button>
            ) : (
              <button
                onClick={handlePauseTimer}
                disabled={containerExpired}
                className="flex-1 py-1 bg-primary hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed rounded flex items-center justify-center gap-1 text-primary-foreground"
              >
                <Pause className="h-2.5 w-2.5" />
                Pause
              </button>
            )}
            <button
              onClick={handleResetTimer}
              disabled={containerExpired}
              className="px-2 py-1 bg-muted hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed rounded flex items-center justify-center text-foreground"
            >
              <RotateCcw className="h-2.5 w-2.5" />
            </button>
          </div>

          {/* Container expired warning */}
          {containerExpired && (
            <div className="text-destructive text-center pt-1">
              Container expired
            </div>
          )}
        </div>
      </div>

      {/* Tasks nested inside block - COMPACT */}
      <div className="flex-1 overflow-y-auto space-y-1 mb-1.5">
        {block.tasks.map((task: Task) => (
          <div key={task.id} className="flex items-start gap-1.5 hover:bg-accent px-1.5 py-1 rounded">
            <Checkbox
              checked={task.completed}
              onCheckedChange={() => onToggleTask(containerId, block.id, task.id)}
              className="h-3 w-3 mt-0.5 border-border"
            />
            <span className={`flex-1 ${task.completed ? 'text-muted-foreground' : 'text-foreground'}`}>
              {task.title}
            </span>
          </div>
        ))}
      </div>

      {/* Add task button - COMPACT */}
      {addingTaskToBlock === block.id ? (
        <Input
          value={newTaskTitle}
          onChange={(e) => setNewTaskTitle(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleAddTask(block.id);
            if (e.key === 'Escape') setAddingTaskToBlock(null);
          }}
          placeholder="Task..."
          className="h-6 bg-card border-border text-foreground placeholder:text-muted-foreground"
          autoFocus
        />
      ) : (
        <button
          onClick={() => setAddingTaskToBlock(block.id)}
          className="w-full py-1 border border-dashed border-border rounded text-muted-foreground hover:border-foreground hover:text-foreground hover:bg-accent"
        >
          <Plus className="h-2.5 w-2.5 inline mr-0.5" />
          Task
        </button>
      )}
    </div>
  );
}

export function ContainerDetail({
  container,
  onBack,
  onUpdateContainer,
  onAddTask,
  onToggleTask,
  onStartContainer,
}: ContainerDetailProps) {
  // Use container.blocks directly instead of local state
  const blocks = container.blocks;
  const [addingTaskToBlock, setAddingTaskToBlock] = useState<string | null>(null);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [addBlockOpen, setAddBlockOpen] = useState(false);
  const [settingsForm, setSettingsForm] = useState({
    name: container.name,
    totalDuration: container.totalDuration,
    pauseAfter: container.pauseAfter,
  });

  // GraphQL mutation for updating blocks
  const [updateBlocksMutation] = useMutation(UPDATE_BLOCKS);

  // CONTAINER GLOBAL TIMER
  const [containerElapsedSeconds, setContainerElapsedSeconds] = useState(0);
  const containerTotalSeconds = container.totalDuration * 60;
  const containerRemainingSeconds = Math.max(0, containerTotalSeconds - containerElapsedSeconds);
  const containerExpired = containerElapsedSeconds >= containerTotalSeconds;

  // CONTAINER GLOBAL TIMER - Manual advance (driven by blocks)
  const handleContainerAdvance = useCallback(() => {
    setContainerElapsedSeconds((prev) => {
      const next = prev + 1;
      if (next >= containerTotalSeconds) {
        // Container expired - unlock it
        onUpdateContainer(container.id, {
          locked: false,
          status: 'completed',
          completedAt: new Date(),
        });
        return containerTotalSeconds;
      }
      return next;
    });
  }, [containerTotalSeconds, container.id, onUpdateContainer]);

  // Handler for updating blocks via GraphQL
  const handleUpdateBlocks = useCallback(
    async (updatedBlocks: Block[]) => {
      try {
        await updateBlocksMutation({
          variables: {
            containerId: container.id,
            blocks: updatedBlocks.map((block) => ({
              name: block.name,
              duration: block.duration,
              position: block.position,
              color: block.color,
            })),
          },
          refetchQueries: [{ query: GET_ALL_CONTAINERS }],
        });
      } catch (err) {
        console.error('Failed to update blocks:', err);
      }
    },
    [container.id, updateBlocksMutation]
  );

  const totalUsed = blocks.reduce((sum, b) => sum + b.duration, 0);
  const remaining = container.totalDuration - totalUsed;
  const isValid = remaining >= 0;

  // Drag & drop sensors
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = blocks.findIndex((item) => item.id === active.id);
      const newIndex = blocks.findIndex((item) => item.id === over.id);
      const reorderedBlocks = arrayMove(blocks, oldIndex, newIndex);
      handleUpdateBlocks(reorderedBlocks);
    }
  };

  const handleDeleteBlock = (blockId: string) => {
    const updatedBlocks = blocks.filter((item) => item.id !== blockId);
    handleUpdateBlocks(updatedBlocks);
  };

  const handleSaveSettings = () => {
    onUpdateContainer(container.id, settingsForm);
    setSettingsOpen(false);
  };

  const handleAddTask = (blockId: string) => {
    if (newTaskTitle.trim()) {
      onAddTask(container.id, blockId, newTaskTitle.trim());
      setNewTaskTitle('');
      setAddingTaskToBlock(null);
    }
  };

  const handleUpdateBlockField = (blockId: string, updates: Partial<Block>) => {
    const updatedBlocks = blocks.map((b) =>
      b.id === blockId ? { ...b, ...updates } : b
    );
    handleUpdateBlocks(updatedBlocks);
  };

  // Format time for container timer
  const formatContainerTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="h-full flex flex-col">
      {/* CONTAINER GLOBAL TIMER - BIG and PROMINENT */}
      {container.locked && (
        <div className={`px-6 py-4 border-b-2 flex items-center justify-between ${
          containerExpired ? 'bg-destructive/10 border-destructive' : 'bg-primary/5 border-primary'
        }`}>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Clock className={`h-6 w-6 ${containerExpired ? 'text-destructive' : 'text-primary'}`} />
              <div>
                <div className={`${containerExpired ? 'text-destructive' : 'text-foreground'}`}>
                  {formatContainerTime(containerRemainingSeconds)}
                </div>
                <div className="text-muted-foreground">
                  {containerExpired ? 'SESSION EXPIRED' : 'Time remaining'}
                </div>
              </div>
            </div>

            {/* Progress bar */}
            <div className="flex-1 max-w-md">
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all ${containerExpired ? 'bg-destructive' : 'bg-primary'}`}
                  style={{ width: `${(containerElapsedSeconds / containerTotalSeconds) * 100}%` }}
                />
              </div>
              <div className="flex items-center justify-between mt-1 text-muted-foreground">
                <span>{formatContainerTime(containerElapsedSeconds)} elapsed</span>
                <span>{formatContainerTime(containerTotalSeconds)} total</span>
              </div>
            </div>
          </div>

          {containerExpired && (
            <div className="text-destructive">
              All block timers are now locked
            </div>
          )}
        </div>
      )}

      {/* Header - Fixed */}
      <div className="flex items-center justify-between mb-4 flex-shrink-0 px-6 pt-4">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={onBack} className="text-foreground hover:bg-accent">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <div>
            <h2 className="text-foreground">{container.name}</h2>
            <p className="text-muted-foreground">
              {formatDuration(container.totalDuration)} • {formatDuration(container.pauseAfter)} pause
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* START Button - BIG and CLEAR */}
          {!container.locked && blocks.length > 0 && isValid && (
            <Button
              onClick={() => onStartContainer(container.id)}
              className="bg-primary hover:opacity-90 text-primary-foreground px-6"
              size="lg"
            >
              <Play className="h-5 w-5 mr-2" />
              START SESSION
            </Button>
          )}

          {/* Settings Dialog */}
          <Dialog open={settingsOpen} onOpenChange={setSettingsOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm" className="text-foreground">
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md bg-card">
              <DialogHeader>
                <DialogTitle className="text-foreground">Container Settings</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label className="text-foreground">Name</Label>
                  <Input
                    value={settingsForm.name}
                    onChange={(e) => setSettingsForm({ ...settingsForm, name: e.target.value })}
                    className="bg-card border-border text-foreground placeholder:text-muted-foreground"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-foreground">Total Duration: {formatDuration(settingsForm.totalDuration)}</Label>
                  <Slider
                    value={[settingsForm.totalDuration]}
                    onValueChange={([v]) => setSettingsForm({ ...settingsForm, totalDuration: v })}
                    min={15}
                    max={240}
                    step={5}
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-foreground">Pause After: {formatDuration(settingsForm.pauseAfter)}</Label>
                  <Slider
                    value={[settingsForm.pauseAfter]}
                    onValueChange={([v]) => setSettingsForm({ ...settingsForm, pauseAfter: v })}
                    min={5}
                    max={60}
                    step={5}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setSettingsOpen(false)} className="bg-card">Cancel</Button>
                <Button onClick={handleSaveSettings} className="bg-primary text-primary-foreground hover:opacity-90">Save</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* LEGO BLOCKS - Drag & Drop Grid */}
      <div className="flex-1 overflow-y-auto bg-muted">
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <SortableContext items={blocks.map(b => b.id)} strategy={rectSortingStrategy}>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3 p-4">
              {blocks.map((block) => (
                <SortableBlock
                  key={block.id}
                  block={block}
                  containerId={container.id}
                  containerExpired={containerExpired}
                  containerRemainingSeconds={containerRemainingSeconds}
                  onContainerAdvance={handleContainerAdvance}
                  onDelete={handleDeleteBlock}
                  onToggleTask={onToggleTask}
                  onUpdateBlock={handleUpdateBlockField}
                  addingTaskToBlock={addingTaskToBlock}
                  setAddingTaskToBlock={setAddingTaskToBlock}
                  newTaskTitle={newTaskTitle}
                  setNewTaskTitle={setNewTaskTitle}
                  handleAddTask={handleAddTask}
                />
              ))}

              {/* Add Block button */}
              <Dialog open={addBlockOpen} onOpenChange={setAddBlockOpen}>
                <DialogTrigger asChild>
                  <button
                    className="border-2 border-dashed border-border rounded-lg bg-accent hover:bg-accent/80 hover:border-foreground hover:scale-105 transition-all flex items-center justify-center group"
                    style={{ height: '180px' }}
                  >
                    <div className="text-center">
                      <Plus className="h-8 w-8 mx-auto text-muted-foreground group-hover:text-foreground mb-2" />
                      <span className="text-muted-foreground group-hover:text-foreground">Add Block</span>
                      <p className="text-muted-foreground group-hover:text-foreground mt-1">
                        {formatDuration(remaining)} available
                      </p>
                    </div>
                  </button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto bg-card">
                  <DialogHeader>
                    <DialogTitle className="text-foreground">Manage Blocks</DialogTitle>
                  </DialogHeader>
                  <div className="py-4">
                    <BlockBuilder
                      blocks={blocks}
                      totalDuration={container.totalDuration}
                      onChange={handleUpdateBlocks}
                      disabled={container.locked}
                    />
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setAddBlockOpen(false)} className="bg-card">Close</Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>
          </SortableContext>
        </DndContext>

        {/* Footer - Stats bar */}
        <div className="sticky bottom-0 bg-card/95 backdrop-blur-sm border-t-2 border-border p-4 flex items-center justify-between shadow-lg">
          <span className={`${isValid ? 'text-muted-foreground' : 'text-destructive'}`}>
            {totalUsed}/{container.totalDuration}min {!isValid && '⚠️ Exceeds limit - remove blocks'}
          </span>
          {isValid && (
            <span className="text-muted-foreground">
              {remaining}min available
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
