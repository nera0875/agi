import { Clock, Box, CheckSquare } from 'lucide-react';
import { Badge } from './ui/badge';
import type { BlockContainer } from '../types/timeblock';
import { formatDuration, calculateBlockProportion } from '../types/timeblock';

interface ContainerCardCompactProps {
  container: BlockContainer;
  onClick?: (container: BlockContainer) => void;
}

/**
 * ContainerCardCompact - Redesigned with Figma Make standards
 *
 * DESIGN SYSTEM (Semantic tokens only):
 * - bg-card: Card background (white #ffffff)
 * - bg-muted: Subtle backgrounds (gray #f4f4f5)
 * - bg-accent: Hover states (gray #f4f4f5)
 * - border-border: Borders (gray #e4e4e7)
 * - text-foreground: Primary text (black #000000)
 * - text-muted-foreground: Secondary text (gray #71717a)
 * - bg-primary: Black for emphasis (#000000)
 *
 * NO hardcoded colors (bg-zinc-*, bg-white, etc.)
 * NO typography overrides (font-bold, text-xl, etc.)
 * NO colored utilities (bg-red-*, bg-blue-*, etc.)
 */

export function ContainerCardCompact({
  container,
  onClick,
}: ContainerCardCompactProps) {
  const totalUsed = container.blocks.reduce((sum, b) => sum + b.duration, 0);
  const taskCount = container.blocks.reduce((sum, b) => sum + (b.tasks?.length || 0), 0);
  const completedTasks = container.blocks.reduce(
    (sum, b) => sum + (b.tasks?.filter(t => t.completed).length || 0),
    0
  );
  const blockCount = container.blocks.length;
  const progress = container.totalDuration > 0 ? (totalUsed / container.totalDuration) * 100 : 0;

  return (
    <button
      onClick={() => onClick?.(container)}
      className="w-full bg-card border-2 border-border hover:border-foreground hover:bg-accent rounded-lg p-4 transition-all text-left group relative overflow-hidden"
    >
      {/* RUNNING indicator - Semantic token only */}
      {container.locked && (
        <div className="absolute top-0 left-0 right-0 h-1 bg-primary" />
      )}

      {/* STATUS badge - Semantic tokens */}
      <div className="absolute top-3 right-3">
        {container.locked ? (
          <Badge variant="default" className="bg-primary text-primary-foreground">
            RUNNING
          </Badge>
        ) : container.status === 'completed' ? (
          <Badge variant="default" className="bg-primary text-primary-foreground">
            DONE
          </Badge>
        ) : (
          <Badge variant="outline" className="border-border text-foreground">
            READY
          </Badge>
        )}
      </div>

      {/* NAME */}
      <h3 className="text-foreground mb-3 pr-16 line-clamp-2">
        {container.name}
      </h3>

      {/* DURATION */}
      <div className="flex items-center gap-2 mb-3">
        <Clock className="h-4 w-4" />
        <span className="text-foreground">
          {formatDuration(container.totalDuration)}
        </span>
        <span className="text-muted-foreground">
          + {formatDuration(container.pauseAfter)} break
        </span>
      </div>

      {/* VISUAL BLOCKS - Using semantic chart tokens */}
      <div className="mb-3">
        <div className="h-8 bg-muted rounded-md overflow-hidden flex border border-border">
          {blockCount > 0 ? (
            container.blocks.map((block, idx) => {
              const proportion = calculateBlockProportion(block.duration, container.totalDuration);

              // Map block colors to semantic chart tokens
              const getChartToken = (color: string | undefined) => {
                if (!color) return 'bg-chart-2';
                const colorMap: Record<string, string> = {
                  '#000000': 'bg-chart-1', // Black
                  '#71717a': 'bg-chart-2', // Gray-600
                  '#a1a1aa': 'bg-chart-3', // Gray-400
                  '#d4d4d8': 'bg-chart-4', // Gray-300
                  '#e4e4e7': 'bg-chart-5', // Gray-200
                };
                return colorMap[color] || 'bg-chart-2';
              };

              return (
                <div
                  key={block.id}
                  className={`relative group/block ${getChartToken(block.color)}`}
                  style={{
                    width: `${proportion}%`,
                  }}
                  title={`${block.name} (${block.duration}min)`}
                >
                  {/* Block name on hover */}
                  <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover/block:opacity-100 transition-opacity bg-primary/60">
                    <span className="text-primary-foreground truncate px-1">
                      {block.name}
                    </span>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="flex-1 flex items-center justify-center text-muted-foreground">
              No blocks
            </div>
          )}
        </div>

        {/* Progress indicator */}
        {totalUsed !== container.totalDuration && (
          <div className="mt-1 text-muted-foreground">
            {totalUsed}/{container.totalDuration}min used ({progress.toFixed(0)}%)
          </div>
        )}
      </div>

      {/* FOOTER - Stats */}
      <div className="flex items-center justify-between text-muted-foreground pt-2 border-t border-border">
        <div className="flex items-center gap-1">
          <Box className="h-3 w-3" />
          <span>{blockCount} block{blockCount !== 1 ? 's' : ''}</span>
        </div>
        {taskCount > 0 && (
          <div className="flex items-center gap-1">
            <CheckSquare className="h-3 w-3" />
            <span>{completedTasks}/{taskCount} tasks</span>
          </div>
        )}
      </div>
    </button>
  );
}
