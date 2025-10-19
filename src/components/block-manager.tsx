import { useState } from 'react';
import { Plus, Edit2, Trash2, Copy, Grid3x3, LayoutGrid } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Slider } from './ui/slider';
import type { TimeBlock } from '../types/timeblock';
import { createTimeBlock } from '../types/timeblock';

interface BlockManagerProps {
  blocks: TimeBlock[];
  onAddBlock: (block: TimeBlock) => void;
  onEditBlock: (blockId: string, updates: Partial<TimeBlock>) => void;
  onDeleteBlock: (blockId: string) => void;
  onDuplicateBlock: (blockId: string) => void;
}

const PRESET_COLORS = [
  '#3b82f6', // blue
  '#10b981', // green
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // purple
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#f97316', // orange
];

export function BlockManager({
  blocks,
  onAddBlock,
  onEditBlock,
  onDeleteBlock,
  onDuplicateBlock,
}: BlockManagerProps) {
  const [createOpen, setCreateOpen] = useState(false);
  const [editingBlock, setEditingBlock] = useState<TimeBlock | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    duration: 60,
    subBlockCount: 3,
    color: PRESET_COLORS[0],
  });

  const handleCreate = () => {
    const block = createTimeBlock(formData.name, formData.duration, formData.subBlockCount);
    block.color = formData.color;
    onAddBlock(block);
    setCreateOpen(false);
    setFormData({
      name: '',
      description: '',
      duration: 60,
      subBlockCount: 3,
      color: PRESET_COLORS[0],
    });
  };

  const handleEdit = () => {
    if (!editingBlock) return;

    const subBlockDuration = Math.floor(formData.duration / formData.subBlockCount);
    const newSubBlocks = Array.from({ length: formData.subBlockCount }, (_, i) => ({
      id: `sub-${Date.now()}-${i}`,
      duration: subBlockDuration,
      status: 'pending' as const,
      elapsedSeconds: 0,
    }));

    onEditBlock(editingBlock.id, {
      name: formData.name,
      duration: formData.duration,
      subBlocks: newSubBlocks,
      color: formData.color,
    });

    setEditingBlock(null);
  };

  const openEditDialog = (block: TimeBlock) => {
    setEditingBlock(block);
    setFormData({
      name: block.name,
      description: '',
      duration: block.duration,
      subBlockCount: block.subBlocks.length,
      color: block.color || PRESET_COLORS[0],
    });
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <LayoutGrid className="h-5 w-5" />
          <h3 className="font-semibold">Block Manager</h3>
          <Badge variant="secondary">{blocks.length} blocks</Badge>
        </div>

        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild>
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              New Block
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Time Block</DialogTitle>
              <DialogDescription>
                Create a new time block template
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="block-name">Block Name</Label>
                <Input
                  id="block-name"
                  placeholder="e.g., Deep Work"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="block-desc">Description (optional)</Label>
                <Textarea
                  id="block-desc"
                  placeholder="What will you work on?"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={2}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Duration: {formData.duration}min</Label>
                  <Slider
                    value={[formData.duration]}
                    onValueChange={([v]) => setFormData({ ...formData, duration: v })}
                    min={15}
                    max={120}
                    step={5}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Sub-blocks: {formData.subBlockCount}</Label>
                  <Slider
                    value={[formData.subBlockCount]}
                    onValueChange={([v]) => setFormData({ ...formData, subBlockCount: v })}
                    min={1}
                    max={6}
                    step={1}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Color</Label>
                <div className="flex items-center gap-2">
                  {PRESET_COLORS.map((color) => (
                    <button
                      key={color}
                      className={`w-8 h-8 rounded-md border-2 transition-all ${
                        formData.color === color ? 'border-foreground scale-110' : 'border-transparent'
                      }`}
                      style={{ backgroundColor: color }}
                      onClick={() => setFormData({ ...formData, color })}
                    />
                  ))}
                </div>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setCreateOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreate} disabled={!formData.name.trim()}>
                Create Block
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Blocks Grid */}
      <div className="grid grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-3">
        {blocks.map((block) => (
          <div
            key={block.id}
            className="group relative"
          >
            {/* Main Square Block */}
            <div
              className="aspect-square bg-zinc-900 border border-zinc-800 rounded-xl p-3 flex flex-col justify-between hover:border-zinc-700 hover:shadow-lg transition-all cursor-pointer relative overflow-hidden"
            >
              {/* Color accent - thin line at top */}
              <div
                className="absolute top-0 left-0 right-0 h-0.5"
                style={{ backgroundColor: block.color || PRESET_COLORS[0] }}
              />

              {/* Block name */}
              <div className="flex-1 flex items-start justify-center pt-1">
                <span className="text-xs font-semibold text-white text-center line-clamp-2 leading-tight">
                  {block.name}
                </span>
              </div>

              {/* Sub-blocks mini grid - simple dots */}
              <div className="flex items-center justify-center gap-1 mb-2">
                {block.subBlocks.map((sub, idx) => (
                  <div
                    key={sub.id}
                    className="w-1.5 h-1.5 rounded-full"
                    style={{
                      backgroundColor: sub.status === 'completed'
                        ? block.color || PRESET_COLORS[0]
                        : '#52525b',
                    }}
                  />
                ))}
              </div>

              {/* Duration badge */}
              <div className="text-[10px] font-medium text-center py-1 rounded-md bg-zinc-800 text-zinc-400">
                {block.duration}min
              </div>

              {/* Hover actions */}
              <div className="absolute inset-0 bg-black/90 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0 text-zinc-400 hover:text-white hover:bg-zinc-800"
                  onClick={() => openEditDialog(block)}
                >
                  <Edit2 className="h-3.5 w-3.5" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0 text-zinc-400 hover:text-white hover:bg-zinc-800"
                  onClick={() => onDuplicateBlock(block.id)}
                >
                  <Copy className="h-3.5 w-3.5" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0 text-red-400 hover:text-red-300 hover:bg-red-950/50"
                  onClick={() => onDeleteBlock(block.id)}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>

            {/* Task count indicator */}
            {block.tasks.length > 0 && (
              <div className="absolute -top-1.5 -right-1.5 bg-white text-black text-[9px] font-bold rounded-full h-5 w-5 flex items-center justify-center shadow-md">
                {block.tasks.length}
              </div>
            )}
          </div>
        ))}

        {/* Empty state */}
        {blocks.length === 0 && (
          <Card className="border-dashed col-span-2">
            <CardContent className="py-8 text-center">
              <Grid3x3 className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
              <p className="text-sm text-muted-foreground">
                No blocks yet. Create your first block!
              </p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Edit Dialog */}
      <Dialog open={!!editingBlock} onOpenChange={(open) => !open && setEditingBlock(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Time Block</DialogTitle>
            <DialogDescription>Update block settings</DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-block-name">Block Name</Label>
              <Input
                id="edit-block-name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Duration: {formData.duration}min</Label>
                <Slider
                  value={[formData.duration]}
                  onValueChange={([v]) => setFormData({ ...formData, duration: v })}
                  min={15}
                  max={120}
                  step={5}
                />
              </div>

              <div className="space-y-2">
                <Label>Sub-blocks: {formData.subBlockCount}</Label>
                <Slider
                  value={[formData.subBlockCount]}
                  onValueChange={([v]) => setFormData({ ...formData, subBlockCount: v })}
                  min={1}
                  max={6}
                  step={1}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Color</Label>
              <div className="flex items-center gap-2">
                {PRESET_COLORS.map((color) => (
                  <button
                    key={color}
                    className={`w-8 h-8 rounded-md border-2 transition-all ${
                      formData.color === color ? 'border-foreground scale-110' : 'border-transparent'
                    }`}
                    style={{ backgroundColor: color }}
                    onClick={() => setFormData({ ...formData, color })}
                  />
                ))}
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingBlock(null)}>
              Cancel
            </Button>
            <Button onClick={handleEdit} disabled={!formData.name.trim()}>
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
