import { useState } from 'react';
import { Play, Pause, StopCircle, SkipForward, Plus, Trash2, Check } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardAction } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Checkbox } from './ui/checkbox';
import { Input } from './ui/input';
import type { TimeBlock, BlockTask } from '../types/timeblock';
import { formatTime } from '../types/timeblock';
import { useTimer } from '../hooks/useTimer';

interface TimeBlockCardProps {
  block: TimeBlock;
  onStart: () => void;
  onPause: () => void;
  onStop: () => void;
  onSkip: () => void;
  onAddTask: (title: string) => void;
  onToggleTask: (taskId: string) => void;
  onDeleteTask: (taskId: string) => void;
  isActive: boolean;
}

export function TimeBlockCard({
  block,
  onStart,
  onPause,
  onStop,
  onSkip,
  onAddTask,
  onToggleTask,
  onDeleteTask,
  isActive,
}: TimeBlockCardProps) {
  const [newTaskTitle, setNewTaskTitle] = useState('');

  // Get current sub-block
  const currentSubBlock = block.subBlocks[block.currentSubBlockIndex];
  const totalSeconds = currentSubBlock ? currentSubBlock.duration * 60 : 0;

  // Timer for current sub-block
  const timer = useTimer({
    totalSeconds,
    autoStart: false,
    onComplete: () => {
      // Auto-advance to next sub-block or complete
      if (block.currentSubBlockIndex < block.subBlocks.length - 1) {
        // TODO: Handle sub-block completion
      }
    },
  });

  const handleAddTask = () => {
    if (newTaskTitle.trim()) {
      onAddTask(newTaskTitle.trim());
      setNewTaskTitle('');
    }
  };

  const completedTasks = block.tasks.filter((t) => t.completed).length;
  const totalTasks = block.tasks.length;

  // Status badge color
  const statusColor = {
    pending: 'secondary',
    active: 'default',
    paused: 'outline',
    completed: 'secondary',
    skipped: 'destructive',
  }[block.status] as 'default' | 'secondary' | 'destructive' | 'outline';

  return (
    <Card className="relative">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="flex items-center gap-2">
              {block.name}
              <Badge variant={statusColor}>{block.status}</Badge>
            </CardTitle>
          </div>
          <CardAction>
            {isActive && (
              <div className="flex items-center gap-1">
                {block.status === 'active' ? (
                  <Button variant="outline" size="icon" onClick={onPause}>
                    <Pause className="h-4 w-4" />
                  </Button>
                ) : (
                  <Button variant="outline" size="icon" onClick={onStart}>
                    <Play className="h-4 w-4" />
                  </Button>
                )}
                <Button variant="outline" size="icon" onClick={onStop}>
                  <StopCircle className="h-4 w-4" />
                </Button>
                <Button variant="outline" size="icon" onClick={onSkip}>
                  <SkipForward className="h-4 w-4" />
                </Button>
              </div>
            )}
          </CardAction>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Timer Display */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-3xl font-mono font-bold">
              {formatTime(timer.currentSeconds)}
            </span>
            <span className="text-sm text-muted-foreground">
              {formatTime(timer.totalSeconds)}
            </span>
          </div>
          <Progress value={timer.progress} className="h-2" />
        </div>

        {/* Sub-blocks */}
        <div className="space-y-1">
          <div className="text-xs text-muted-foreground">Sub-blocks:</div>
          <div className="flex items-center gap-2">
            {block.subBlocks.map((subBlock, index) => {
              const isCurrentSubBlock = index === block.currentSubBlockIndex;
              const subBlockStatus = subBlock.status;

              return (
                <div
                  key={subBlock.id}
                  className={`flex-1 h-8 rounded-md border flex items-center justify-center text-xs font-medium transition-colors ${
                    isCurrentSubBlock
                      ? 'bg-primary text-primary-foreground border-primary'
                      : subBlockStatus === 'completed'
                      ? 'bg-green-500/20 border-green-500/30 text-green-700'
                      : 'bg-muted'
                  }`}
                >
                  {isCurrentSubBlock && block.status === 'active' && '▶'}
                  {subBlockStatus === 'completed' && '✓'}
                  {' '}
                  {subBlock.duration}min
                </div>
              );
            })}
          </div>
        </div>

        {/* Tasks */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="text-xs text-muted-foreground">
              Tasks ({completedTasks}/{totalTasks}):
            </div>
          </div>

          <div className="space-y-1.5">
            {block.tasks.map((task) => (
              <div
                key={task.id}
                className="flex items-center gap-2 group p-1.5 rounded hover:bg-muted/50 transition-colors"
              >
                <Checkbox
                  id={task.id}
                  checked={task.completed}
                  onCheckedChange={() => onToggleTask(task.id)}
                />
                <label
                  htmlFor={task.id}
                  className={`flex-1 text-sm cursor-pointer ${
                    task.completed ? 'line-through text-muted-foreground' : ''
                  }`}
                >
                  {task.title}
                </label>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={() => onDeleteTask(task.id)}
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
            ))}
          </div>

          {/* Add Task Input */}
          <div className="flex items-center gap-2 pt-1">
            <Input
              placeholder="Add a task..."
              value={newTaskTitle}
              onChange={(e) => setNewTaskTitle(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleAddTask();
                }
              }}
              className="h-8 text-sm"
            />
            <Button
              variant="outline"
              size="icon"
              onClick={handleAddTask}
              disabled={!newTaskTitle.trim()}
              className="h-8 w-8 shrink-0"
            >
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
