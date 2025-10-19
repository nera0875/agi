import { useState } from 'react';
import { Play, Lock, Check, Clock, Coffee, Edit2, Trash2, Copy, Plus } from 'lucide-react';
import { Card, CardContent, CardHeader } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Checkbox } from './ui/checkbox';
import type {
  BlockContainer,
  ContainerBlock,
  BlockTask,
  calculateBlockProportion,
  formatDuration,
} from '../types/timeblock';
import { calculateBlockProportion as calcProportion, formatDuration as fmtDuration } from '../types/timeblock';

interface ContainerCardProps {
  container: BlockContainer;
  onStart?: (containerId: string) => void;
  onEdit?: (containerId: string) => void;
  onDelete?: (containerId: string) => void;
  onDuplicate?: (containerId: string) => void;
  onAddTask?: (blockId: string, taskTitle: string) => void;
  onToggleTask?: (blockId: string, taskId: string) => void;
  compact?: boolean;
}

export function ContainerCard({
  container,
  onStart,
  onEdit,
  onDelete,
  onDuplicate,
  onAddTask,
  onToggleTask,
  compact = false,
}: ContainerCardProps) {
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [addingTaskToBlock, setAddingTaskToBlock] = useState<string | null>(null);

  const totalUsed = container.blocks.reduce((sum, b) => sum + b.duration, 0);
  const remaining = container.totalDuration - totalUsed;
  const isValid = remaining >= 0;
  const progressPercent = (container.progress / container.totalDuration) * 100;

  const handleAddTask = (blockId: string) => {
    if (newTaskTitle.trim() && onAddTask) {
      onAddTask(blockId, newTaskTitle.trim());
      setNewTaskTitle('');
      setAddingTaskToBlock(null);
    }
  };

  // Status badge
  const statusBadge = () => {
    if (container.status === 'completed') {
      return <Badge className="bg-green-900 text-green-100"><Check className="h-3 w-3 mr-1" />Completed</Badge>;
    }
    if (container.locked) {
      return <Badge className="bg-red-900 text-red-100"><Lock className="h-3 w-3 mr-1" />Locked</Badge>;
    }
    return <Badge variant="secondary"><Clock className="h-3 w-3 mr-1" />Ready</Badge>;
  };

  return (
    <Card className="bg-white border-zinc-300 hover:border-zinc-600 transition-colors">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-semibold text-black">{container.name}</h3>
              {statusBadge()}
            </div>
            <div className="flex items-center gap-3 text-xs text-zinc-400">
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {fmtDuration(container.totalDuration)}
              </span>
              <span className="flex items-center gap-1">
                <Coffee className="h-3 w-3" />
                {fmtDuration(container.pauseAfter)} pause
              </span>
              <span className={isValid ? 'text-green-400' : 'text-red-400'}>
                {totalUsed}/{container.totalDuration}min used
              </span>
              {remaining > 0 && (
                <span className="text-zinc-500">({fmtDuration(remaining)} free)</span>
              )}
            </div>
          </div>

          {/* Actions */}
          {!container.locked && (
            <div className="flex items-center gap-1">
              {onStart && container.status === 'idle' && isValid && (
                <Button
                  size="sm"
                  onClick={() => onStart(container.id)}
                  className="bg-white text-black hover:bg-zinc-200"
                >
                  <Play className="h-3 w-3 mr-1" />
                  Start
                </Button>
              )}
              {onEdit && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onEdit(container.id)}
                  className="h-8 w-8 p-0 text-zinc-400 hover:text-black hover:bg-zinc-800"
                >
                  <Edit2 className="h-3 w-3" />
                </Button>
              )}
              {onDuplicate && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onDuplicate(container.id)}
                  className="h-8 w-8 p-0 text-zinc-400 hover:text-black hover:bg-zinc-800"
                >
                  <Copy className="h-3 w-3" />
                </Button>
              )}
              {onDelete && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onDelete(container.id)}
                  className="h-8 w-8 p-0 text-red-400 hover:text-red-300 hover:bg-red-950/50"
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              )}
            </div>
          )}
        </div>

        {/* Progress bar (when active/locked) */}
        {container.locked && (
          <div className="mt-3">
            <div className="flex items-center justify-between text-xs text-zinc-400 mb-1">
              <span>{Math.floor(container.progress)}min elapsed</span>
              <span>{container.totalDuration - Math.floor(container.progress)}min remaining</span>
            </div>
            <Progress value={progressPercent} className="h-1" />
          </div>
        )}
      </CardHeader>

      <CardContent className="space-y-2">
        {/* Blocks - proportional display */}
        {container.blocks.length === 0 ? (
          <div className="text-center py-8 text-zinc-500 text-sm">
            No blocks yet. Add blocks to fill this container.
          </div>
        ) : (
          <div className="space-y-2">
            {container.blocks.map((block, index) => {
              const proportion = calcProportion(block.duration, container.totalDuration);
              const isActive = container.locked && container.currentBlockIndex === index;
              const isCompleted = container.locked && container.currentBlockIndex > index;

              return (
                <div
                  key={block.id}
                  className={`
                    relative border-l-4 rounded-md p-3 transition-all
                    ${isActive ? 'bg-zinc-700 border-white' :
                      isCompleted ? 'bg-zinc-800/50 border-green-500' :
                      'bg-zinc-900/50 border-zinc-600'}
                    ${container.locked ? 'cursor-not-allowed' : 'hover:bg-zinc-800/70'}
                  `}
                  style={{
                    borderLeftColor: block.color || (isActive ? '#fff' : isCompleted ? '#10b981' : '#3f3f46'),
                  }}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-black text-sm">{block.name}</span>
                        <span className="text-xs text-zinc-500">{fmtDuration(block.duration)}</span>
                        {isActive && <Badge variant="outline" className="text-xs">Active</Badge>}
                        {isCompleted && <Check className="h-3 w-3 text-green-500" />}
                      </div>

                      {/* Tasks */}
                      {block.tasks.length > 0 && !compact && (
                        <div className="space-y-1 mt-2">
                          {block.tasks.map((task) => (
                            <div key={task.id} className="flex items-center gap-2">
                              <Checkbox
                                checked={task.completed}
                                onCheckedChange={() => onToggleTask?.(block.id, task.id)}
                                disabled={container.locked}
                                className="h-3 w-3"
                              />
                              <span className={`text-xs ${task.completed ? 'line-through text-zinc-500' : 'text-zinc-300'}`}>
                                {task.title}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Add task */}
                      {!container.locked && !compact && addingTaskToBlock === block.id && (
                        <div className="flex items-center gap-2 mt-2">
                          <input
                            type="text"
                            value={newTaskTitle}
                            onChange={(e) => setNewTaskTitle(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleAddTask(block.id);
                              if (e.key === 'Escape') setAddingTaskToBlock(null);
                            }}
                            placeholder="Task title..."
                            className="flex-1 bg-zinc-800 border-zinc-700 text-black text-xs px-2 py-1 rounded"
                            autoFocus
                          />
                          <Button size="sm" onClick={() => handleAddTask(block.id)} className="h-6 text-xs">
                            Add
                          </Button>
                        </div>
                      )}
                    </div>

                    {/* Add task button */}
                    {!container.locked && !compact && addingTaskToBlock !== block.id && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setAddingTaskToBlock(block.id)}
                        className="h-6 w-6 p-0 text-zinc-500 hover:text-black"
                      >
                        <Plus className="h-3 w-3" />
                      </Button>
                    )}
                  </div>

                  {/* Proportional indicator (visual only) */}
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-zinc-700 rounded-l-md"
                       style={{ opacity: proportion / 100 }} />
                </div>
              );
            })}
          </div>
        )}

        {/* Validation warning */}
        {!isValid && (
          <div className="text-xs text-red-400 bg-red-950/30 border border-red-900 rounded p-2 mt-2">
            ⚠️ Blocks exceed container duration by {fmtDuration(Math.abs(remaining))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
