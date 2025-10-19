import { useState } from 'react';
import { Plus, Trash2, GripVertical, AlertCircle } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Slider } from './ui/slider';
import { Badge } from './ui/badge';
import type { ContainerBlock } from '../types/timeblock';
import { createContainerBlock, validateContainerBlocks, formatDuration } from '../types/timeblock';

interface BlockBuilderProps {
  blocks: ContainerBlock[];
  totalDuration: number;
  onChange: (blocks: ContainerBlock[]) => void;
  disabled?: boolean;
}

/**
 * BlockBuilder - REWRITTEN with Figma Make standards
 *
 * DESIGN SYSTEM (Semantic tokens only):
 * - bg-card: White panels (#ffffff)
 * - bg-muted: Subtle backgrounds (#f4f4f5)
 * - bg-accent: Hover states (#f4f4f5)
 * - border-border: Borders (#e4e4e7)
 * - text-foreground: Primary text (#000000)
 * - text-muted-foreground: Secondary text (#71717a)
 * - bg-chart-1 to bg-chart-5: Block colors (black to light gray)
 *
 * REMOVED ALL VIOLATIONS:
 * - NO hardcoded colors (bg-zinc-*, text-black, text-white)
 * - NO colored utilities (bg-red-*, text-red-*, bg-blue-*)
 * - NO typography overrides (font-bold, text-xl, text-[10px])
 * - NO inline color styles (backgroundColor: block.color)
 */

// Map blocks to semantic chart colors (NO COLOR PICKER - use chart tokens)
const CHART_COLORS = [
  { token: 'bg-chart-1', hex: '#000000', label: 'Black' },
  { token: 'bg-chart-2', hex: '#71717a', label: 'Gray 600' },
  { token: 'bg-chart-3', hex: '#a1a1aa', label: 'Gray 400' },
  { token: 'bg-chart-4', hex: '#d4d4d8', label: 'Gray 300' },
  { token: 'bg-chart-5', hex: '#e4e4e7', label: 'Gray 200' },
];

export function BlockBuilder({
  blocks,
  totalDuration,
  onChange,
  disabled = false,
}: BlockBuilderProps) {
  const [newBlockName, setNewBlockName] = useState('');
  const [newBlockDuration, setNewBlockDuration] = useState(20);
  const [selectedColorHex, setSelectedColorHex] = useState(CHART_COLORS[0].hex);

  const validation = validateContainerBlocks(blocks, totalDuration);

  const handleAddBlock = () => {
    if (!newBlockName.trim()) return;
    if (validation.remaining < newBlockDuration) {
      alert(`Not enough space! Only ${validation.remaining}min remaining.`);
      return;
    }

    const newBlock = createContainerBlock(
      newBlockName.trim(),
      newBlockDuration,
      blocks.length
    );
    newBlock.color = selectedColorHex;

    onChange([...blocks, newBlock]);
    setNewBlockName('');
    setNewBlockDuration(20);
  };

  const handleRemoveBlock = (blockId: string) => {
    const updatedBlocks = blocks
      .filter((b) => b.id !== blockId)
      .map((b, index) => ({ ...b, position: index }));
    onChange(updatedBlocks);
  };

  const handleUpdateDuration = (blockId: string, newDuration: number) => {
    const updatedBlocks = blocks.map((b) =>
      b.id === blockId ? { ...b, duration: newDuration } : b
    );
    onChange(updatedBlocks);
  };

  const handleAutoFill = () => {
    if (blocks.length === 0) return;
    const durationPerBlock = Math.floor(totalDuration / blocks.length);
    const updatedBlocks = blocks.map((b) => ({
      ...b,
      duration: durationPerBlock,
    }));
    onChange(updatedBlocks);
  };

  // Get semantic token class for hex color
  const getChartTokenClass = (hexColor: string | undefined) => {
    if (!hexColor) return 'bg-chart-2';
    const found = CHART_COLORS.find(c => c.hex === hexColor);
    return found ? found.token : 'bg-chart-2';
  };

  return (
    <div className="space-y-4">
      {/* Header with validation */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-foreground">Blocks</h4>
            <p className="text-muted-foreground">
              {validation.totalUsed} / {totalDuration}min used
              {validation.remaining > 0 && (
                <span className="text-muted-foreground"> • {formatDuration(validation.remaining)} free</span>
              )}
            </p>
          </div>
          {blocks.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleAutoFill}
              disabled={disabled}
            >
              Auto-fill ({Math.floor(totalDuration / blocks.length)}min each)
            </Button>
          )}
        </div>

        {/* VISUAL CAPACITY BAR - Using semantic tokens only */}
        <div className="space-y-1">
          <div className="h-6 bg-muted rounded-md overflow-hidden flex border border-border">
            {blocks.map((block) => {
              const proportion = (block.duration / totalDuration) * 100;
              const chartClass = getChartTokenClass(block.color);

              return (
                <div
                  key={block.id}
                  className={`relative flex items-center justify-center ${chartClass}`}
                  style={{ width: `${proportion}%` }}
                  title={`${block.name}: ${block.duration}min (${proportion.toFixed(1)}%)`}
                >
                  {proportion > 8 && (
                    <span className="truncate px-1 text-primary-foreground">
                      {block.duration}m
                    </span>
                  )}
                </div>
              );
            })}
            {validation.remaining > 0 && (
              <div
                className="bg-muted border-l border-dashed border-border flex items-center justify-center text-muted-foreground"
                style={{ width: `${(validation.remaining / totalDuration) * 100}%` }}
              >
                Free
              </div>
            )}
            {!validation.valid && (
              <div
                className="bg-destructive border-l border-border flex items-center justify-center text-destructive-foreground"
                style={{ width: `${(Math.abs(validation.remaining) / totalDuration) * 100}%` }}
              >
                OVER
              </div>
            )}
          </div>
          <div className="flex items-center justify-between text-muted-foreground">
            <span>0min</span>
            <span>{totalDuration}min</span>
          </div>
        </div>
      </div>

      {/* Validation alert - Using semantic destructive tokens */}
      {!validation.valid && (
        <div className="flex items-start gap-2 bg-destructive/10 border border-destructive/20 rounded-md p-3">
          <AlertCircle className="h-4 w-4 text-destructive mt-0.5" />
          <div className="text-destructive">
            <p>Blocks exceed container duration</p>
            <p className="text-muted-foreground">
              Remove {formatDuration(Math.abs(validation.remaining))} or increase container size
            </p>
          </div>
        </div>
      )}

      {/* Blocks list */}
      {blocks.length > 0 && (
        <div className="space-y-2">
          {blocks.map((block, index) => (
            <div
              key={block.id}
              className="bg-card border border-border rounded-lg p-3"
            >
              <div className="flex items-start gap-3">
                <GripVertical className="h-4 w-4 text-muted-foreground mt-1" />

                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-3 h-3 rounded-full border border-border ${getChartTokenClass(block.color)}`}
                    />
                    <span className="text-foreground">{block.name}</span>
                    <Badge variant="secondary">
                      {formatDuration(block.duration)}
                    </Badge>
                  </div>

                  <div className="flex items-center gap-2">
                    <Label className="text-muted-foreground min-w-16">Duration:</Label>
                    <Slider
                      value={[block.duration]}
                      onValueChange={([v]) => handleUpdateDuration(block.id, v)}
                      min={5}
                      max={Math.min(120, totalDuration)}
                      step={5}
                      disabled={disabled}
                      className="flex-1"
                    />
                    <span className="text-muted-foreground min-w-12 text-right">
                      {block.duration}min
                    </span>
                  </div>

                  {/* Color picker - Semantic chart tokens only */}
                  <div className="flex items-center gap-2">
                    <Label className="text-muted-foreground min-w-16">Color:</Label>
                    <div className="flex items-center gap-1.5">
                      {CHART_COLORS.map((colorOption) => (
                        <button
                          key={colorOption.hex}
                          className={`w-5 h-5 rounded-md border transition-all ${colorOption.token} ${
                            block.color === colorOption.hex ? 'border-foreground scale-110' : 'border-border'
                          }`}
                          onClick={() => {
                            const updatedBlocks = blocks.map((b) =>
                              b.id === block.id ? { ...b, color: colorOption.hex } : b
                            );
                            onChange(updatedBlocks);
                          }}
                          disabled={disabled}
                          title={colorOption.label}
                        />
                      ))}
                    </div>
                  </div>
                </div>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleRemoveBlock(block.id)}
                  disabled={disabled}
                  className="h-8 w-8 p-0 text-destructive hover:bg-destructive/10"
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add new block */}
      {!disabled && (
        <div className="bg-card border border-dashed border-border rounded-lg p-4 space-y-3">
          <Label className="text-foreground">Add New Block</Label>

          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label className="text-muted-foreground">Name</Label>
              <Input
                placeholder="e.g., Deep Work, Code Review"
                value={newBlockName}
                onChange={(e) => setNewBlockName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAddBlock()}
                className="bg-card border-border text-foreground placeholder:text-muted-foreground"
              />
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label className="text-muted-foreground">Duration</Label>
                <span className="text-muted-foreground">
                  {newBlockDuration}min
                </span>
              </div>
              <Slider
                value={[newBlockDuration]}
                onValueChange={([v]) => setNewBlockDuration(v)}
                min={5}
                max={Math.min(120, validation.remaining || 120)}
                step={5}
                className="flex-1"
              />
            </div>

            <div className="space-y-1.5">
              <Label className="text-muted-foreground">Color</Label>
              <div className="flex items-center gap-2">
                {CHART_COLORS.map((colorOption) => (
                  <button
                    key={colorOption.hex}
                    className={`w-8 h-8 rounded-lg border transition-all ${colorOption.token} ${
                      selectedColorHex === colorOption.hex ? 'border-foreground scale-110' : 'border-border'
                    }`}
                    onClick={() => setSelectedColorHex(colorOption.hex)}
                    title={colorOption.label}
                  />
                ))}
              </div>
            </div>
          </div>

          <Button
            onClick={handleAddBlock}
            disabled={!newBlockName.trim() || validation.remaining < newBlockDuration}
            size="sm"
            className="w-full bg-primary text-primary-foreground hover:opacity-90"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Block ({newBlockDuration}min)
          </Button>

          {validation.remaining < newBlockDuration && (
            <p className="text-destructive text-center">
              Not enough space! Only {formatDuration(validation.remaining)} remaining
            </p>
          )}
        </div>
      )}

      {/* Empty state */}
      {blocks.length === 0 && (
        <div className="text-center py-6 text-muted-foreground">
          No blocks yet. Add blocks to fill this {formatDuration(totalDuration)} container.
        </div>
      )}
    </div>
  );
}
