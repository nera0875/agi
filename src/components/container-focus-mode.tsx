import { AlertTriangle, Check, ChevronLeft, ChevronRight, Pause, Play, Square } from 'lucide-react';
import { Button } from './ui/button';
import { Checkbox } from './ui/checkbox';
import type { BlockContainer } from '../types/timeblock';
import { useContainerTimer, formatTimerDisplay, formatTimerDuration } from '../hooks/useContainerTimer';

interface ContainerFocusModeProps {
  container: BlockContainer;
  onToggleTask: (containerId: string, blockId: string, taskId: string) => void;
}

export function ContainerFocusMode({
  container,
  onToggleTask,
}: ContainerFocusModeProps) {
  const timer = useContainerTimer(container);

  const currentBlock = container.blocks[timer.currentBlockIndex];
  const isLastBlock = timer.currentBlockIndex === container.blocks.length - 1;
  const isNearLimit = timer.containerRemaining <= 300; // Last 5 minutes

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-black via-zinc-900 to-black flex flex-col z-50">
      {/* HEADER - Container Info */}
      <div className="border-b border-zinc-800 bg-black/50 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs text-zinc-500 uppercase tracking-wider mb-1">FOCUS MODE</div>
              <h1 className="text-2xl font-bold text-white">{container.name}</h1>
            </div>

            {/* Controls */}
            <div className="flex items-center gap-3">
              {!timer.isRunning && !timer.isCompleted && (
                <Button onClick={timer.start} size="lg" className="bg-green-600 hover:bg-green-700">
                  <Play className="h-5 w-5 mr-2" />
                  Start
                </Button>
              )}
              {timer.isRunning && (
                <Button onClick={timer.pause} size="lg" variant="outline" className="border-zinc-700 text-white">
                  <Pause className="h-5 w-5 mr-2" />
                  Pause
                </Button>
              )}
              {!timer.isRunning && timer.containerElapsedSeconds > 0 && !timer.isCompleted && (
                <Button onClick={timer.resume} size="lg" className="bg-green-600 hover:bg-green-700">
                  <Play className="h-5 w-5 mr-2" />
                  Resume
                </Button>
              )}
              <Button onClick={timer.stop} size="lg" variant="destructive">
                <Square className="h-4 w-4 mr-2" />
                Stop
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-6xl mx-auto px-6 py-8">
          {/* HARD LIMIT WARNING */}
          {isNearLimit && !timer.hasReachedLimit && (
            <div className="mb-6 bg-red-900/30 border-2 border-red-500 rounded-lg p-4 flex items-center gap-3 animate-pulse">
              <AlertTriangle className="h-6 w-6 text-red-500" />
              <div className="flex-1">
                <p className="text-red-400 font-bold">Container time limit approaching!</p>
                <p className="text-sm text-red-300">{formatTimerDuration(timer.containerRemaining)} remaining</p>
              </div>
            </div>
          )}

          {/* COMPLETED STATE */}
          {timer.isCompleted && (
            <div className="mb-6 bg-green-900/30 border-2 border-green-500 rounded-lg p-6 text-center">
              <Check className="h-12 w-12 mx-auto text-green-500 mb-3" />
              <p className="text-2xl font-bold text-green-400 mb-2">Session Complete!</p>
              <p className="text-zinc-400">
                {timer.hasReachedLimit
                  ? 'Container time limit reached'
                  : 'All blocks completed'
                }
              </p>
            </div>
          )}

          {/* CONTAINER TIMER - MASSIVE AND PROMINENT */}
          <div className="bg-zinc-900/50 border-2 border-zinc-700 rounded-xl p-8 mb-6">
            <div className="flex items-baseline justify-between mb-4">
              <div>
                <div className="text-xs text-zinc-500 uppercase tracking-wider mb-2">Container Time</div>
                <div className="flex items-baseline gap-3">
                  <span className={`text-6xl font-mono font-bold ${isNearLimit ? 'text-red-400' : 'text-white'}`}>
                    {formatTimerDisplay(timer.containerElapsedSeconds)}
                  </span>
                  <span className="text-2xl text-zinc-600">/</span>
                  <span className="text-2xl text-zinc-400 font-mono">
                    {formatTimerDisplay(timer.containerTotalSeconds)}
                  </span>
                </div>
              </div>

              <div className="text-right">
                <div className="text-xs text-zinc-500 uppercase tracking-wider mb-2">Remaining</div>
                <div className={`text-3xl font-mono font-bold ${isNearLimit ? 'text-red-400' : 'text-zinc-300'}`}>
                  {formatTimerDisplay(timer.containerRemaining)}
                </div>
              </div>
            </div>

            {/* HARD LIMIT Progress Bar */}
            <div className="relative">
              <div className="h-6 bg-zinc-800 rounded-full overflow-hidden border-2 border-zinc-700">
                <div
                  className={`h-full transition-all duration-1000 ${
                    timer.hasReachedLimit ? 'bg-red-500' :
                    isNearLimit ? 'bg-orange-500' :
                    'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(100, timer.containerProgress)}%` }}
                />
              </div>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-xs font-bold text-white drop-shadow-lg">
                  {timer.containerProgress.toFixed(1)}%
                </span>
              </div>
            </div>

            {timer.hasReachedLimit && (
              <div className="mt-3 text-center text-red-400 text-sm font-bold uppercase">
                ⚠️ HARD LIMIT REACHED - SESSION ENDED
              </div>
            )}
          </div>

          {/* CURRENT BLOCK */}
          {currentBlock && (
            <div className="bg-zinc-900/50 border-2 border-blue-700 rounded-xl p-6 mb-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: currentBlock.color || '#3b82f6' }}
                  />
                  <div>
                    <div className="text-xs text-zinc-500 uppercase tracking-wider">Current Block</div>
                    <h3 className="text-2xl font-bold text-white">{currentBlock.name}</h3>
                  </div>
                </div>

                {/* Block navigation */}
                <div className="flex items-center gap-2">
                  <Button
                    onClick={timer.previousBlock}
                    disabled={timer.currentBlockIndex === 0}
                    size="sm"
                    variant="outline"
                    className="border-zinc-700"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <span className="text-sm text-zinc-400 px-3">
                    Block {timer.currentBlockIndex + 1} / {container.blocks.length}
                  </span>
                  <Button
                    onClick={timer.nextBlock}
                    disabled={isLastBlock}
                    size="sm"
                    variant="outline"
                    className="border-zinc-700"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {/* Block timer */}
              <div className="mb-4">
                <div className="flex items-baseline justify-between mb-2">
                  <span className="text-3xl font-mono font-bold text-blue-400">
                    {formatTimerDisplay(timer.blockElapsedSeconds)}
                  </span>
                  <span className="text-lg text-zinc-500">
                    / {formatTimerDisplay(timer.blockTotalSeconds)}
                  </span>
                </div>
                <div className="relative h-3 bg-zinc-800 rounded-full overflow-hidden border border-zinc-700">
                  <div
                    className="h-full bg-blue-500 transition-all duration-1000"
                    style={{ width: `${Math.min(100, timer.blockProgress)}%` }}
                  />
                </div>
              </div>

              {/* Tasks */}
              {currentBlock.tasks && currentBlock.tasks.length > 0 && (
                <div className="space-y-2 mt-4 pt-4 border-t border-zinc-800">
                  <div className="text-sm text-zinc-400 mb-3">Tasks:</div>
                  {currentBlock.tasks.map((task) => (
                    <div
                      key={task.id}
                      className="flex items-center gap-3 p-3 hover:bg-zinc-800/50 rounded-lg transition-colors"
                    >
                      <Checkbox
                        checked={task.completed}
                        onCheckedChange={() => onToggleTask(container.id, currentBlock.id, task.id)}
                        className="h-5 w-5"
                      />
                      <span className={`flex-1 text-lg ${task.completed ? 'line-through text-zinc-500' : 'text-white'}`}>
                        {task.title}
                      </span>
                      {task.completed && <Check className="h-5 w-5 text-green-500" />}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ALL BLOCKS TIMELINE */}
          <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
            <div className="text-sm text-zinc-400 mb-4 uppercase tracking-wider">All Blocks</div>
            <div className="space-y-2">
              {container.blocks.map((block, idx) => {
                const isPast = idx < timer.currentBlockIndex;
                const isCurrent = idx === timer.currentBlockIndex;

                return (
                  <div
                    key={block.id}
                    className={`flex items-center gap-4 p-3 rounded-lg transition-all ${
                      isCurrent ? 'bg-blue-900/30 border-2 border-blue-500' :
                      isPast ? 'bg-zinc-800/30 border border-zinc-800' :
                      'bg-zinc-800/10 border border-zinc-800/50 opacity-50'
                    }`}
                  >
                    <div className={`h-3 w-3 rounded-full ${
                      isPast ? 'bg-green-500' :
                      isCurrent ? 'bg-blue-500 animate-pulse' :
                      'bg-zinc-700'
                    }`} />
                    <div
                      className="w-1 h-8 rounded"
                      style={{ backgroundColor: block.color || '#3b82f6' }}
                    />
                    <span className={`flex-1 font-medium ${isCurrent ? 'text-white text-lg' : 'text-zinc-400'}`}>
                      {block.name}
                    </span>
                    <span className="text-sm text-zinc-500">{block.duration}min</span>
                    {isPast && <Check className="h-5 w-5 text-green-500" />}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* FOOTER - Warning */}
      <div className="border-t border-zinc-800 bg-black/50 backdrop-blur-sm py-3">
        <div className="max-w-6xl mx-auto px-6 text-center">
          <p className="text-sm text-zinc-500">
            {timer.hasReachedLimit
              ? '⚠️ Container time limit reached - session automatically ended'
              : '⏱️ Timer will automatically stop when container limit is reached'
            }
          </p>
        </div>
      </div>
    </div>
  );
}
