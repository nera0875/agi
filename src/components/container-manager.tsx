import { useState } from 'react';
import { Plus, Package } from 'lucide-react';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Slider } from './ui/slider';
import { Badge } from './ui/badge';
import { ContainerCardCompact } from './container-card-compact';
import { ContainerDetail } from './container-detail';
import { ContainerFocusMode } from './container-focus-mode';
import { BlockBuilder } from './block-builder';
import type { BlockContainer, ContainerBlock, BlockTask } from '../types/timeblock';
import { createBlockContainer, formatDuration } from '../types/timeblock';

interface ContainerManagerProps {
  containers: BlockContainer[];
  onCreateContainer: (container: BlockContainer) => void;
  onUpdateContainer: (containerId: string, updates: Partial<BlockContainer>) => void;
  onDeleteContainer: (containerId: string) => void;
  onDuplicateContainer: (containerId: string) => void;
  onStartContainer: (containerId: string) => void;
  onAddTask: (containerId: string, blockId: string, taskTitle: string) => void;
  onToggleTask: (containerId: string, blockId: string, taskId: string) => void;
}

export function ContainerManager({
  containers,
  onCreateContainer,
  onUpdateContainer,
  onDeleteContainer,
  onDuplicateContainer,
  onStartContainer,
  onAddTask,
  onToggleTask,
}: ContainerManagerProps) {
  const [createOpen, setCreateOpen] = useState(false);
  const [editingContainer, setEditingContainer] = useState<BlockContainer | null>(null);
  const [viewingContainerId, setViewingContainerId] = useState<string | null>(() => {
    // Restore last viewed container from localStorage
    return localStorage.getItem('lastViewedContainerId');
  });

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    totalDuration: 60,
    pauseAfter: 10,
    blocks: [] as ContainerBlock[],
  });

  const resetForm = () => {
    setFormData({
      name: '',
      totalDuration: 60,
      pauseAfter: 10,
      blocks: [],
    });
  };

  const handleCreate = () => {
    if (!formData.name.trim()) return;

    const container = createBlockContainer(
      formData.name.trim(),
      formData.totalDuration,
      formData.pauseAfter
    );
    container.blocks = formData.blocks;

    onCreateContainer(container);
    setCreateOpen(false);
    resetForm();
  };

  const handleEdit = () => {
    if (!editingContainer) return;

    onUpdateContainer(editingContainer.id, {
      name: formData.name,
      totalDuration: formData.totalDuration,
      pauseAfter: formData.pauseAfter,
      blocks: formData.blocks,
    });

    setEditingContainer(null);
    resetForm();
  };

  const openEditDialog = (container: BlockContainer) => {
    setEditingContainer(container);
    setFormData({
      name: container.name,
      totalDuration: container.totalDuration,
      pauseAfter: container.pauseAfter,
      blocks: [...container.blocks],
    });
  };

  const closeEditDialog = () => {
    setEditingContainer(null);
    resetForm();
  };

  const handleEnterContainer = (container: BlockContainer) => {
    setViewingContainerId(container.id);
    localStorage.setItem('lastViewedContainerId', container.id);
  };

  const handleBackToList = () => {
    setViewingContainerId(null);
    localStorage.removeItem('lastViewedContainerId');
  };

  // Get current viewing container from containers state
  const viewingContainer = viewingContainerId ? containers.find(c => c.id === viewingContainerId) : null;

  // Check if any container is locked (running)
  const runningContainer = containers.find(c => c.locked);

  // If a container is running, show focus mode fullscreen
  if (runningContainer) {
    return (
      <ContainerFocusMode
        container={runningContainer}
        onToggleTask={onToggleTask}
      />
    );
  }

  // If viewing a container, show detail view
  if (viewingContainer) {
    return (
      <ContainerDetail
        container={viewingContainer}
        onBack={handleBackToList}
        onUpdateContainer={onUpdateContainer}
        onAddTask={onAddTask}
        onToggleTask={onToggleTask}
        onStartContainer={onStartContainer}
      />
    );
  }

  return (
    <div className="h-full">
      {/* Header - Notion style */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Package className="h-4 w-4 text-black" />
          <span className="text-sm font-medium text-black">{containers.length} containers</span>
        </div>

        {/* Create Dialog */}
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild>
            <Button size="sm" className="bg-black text-white hover:bg-zinc-800 h-8 text-xs">
              <Plus className="h-3 w-3 mr-1" />
              New
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-md bg-white">
            <DialogHeader>
              <DialogTitle className="text-black">Create Container</DialogTitle>
              <DialogDescription className="text-zinc-600">
                Create an empty time container. Click on it later to add blocks inside.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="container-name" className="text-sm font-medium text-black">Container Name</Label>
                <Input
                  id="container-name"
                  placeholder="e.g., Morning Deep Work"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="bg-white border-zinc-300 text-black placeholder:text-zinc-400"
                />
              </div>

              <div className="space-y-2">
                <Label className="text-sm font-medium text-black">Total Duration: {formatDuration(formData.totalDuration)}</Label>
                <Slider
                  value={[formData.totalDuration]}
                  onValueChange={([v]) => setFormData({ ...formData, totalDuration: v })}
                  min={15}
                  max={240}
                  step={5}
                  className="py-2"
                />
                <p className="text-xs text-zinc-500">
                  Hard limit - cannot exceed once started
                </p>
              </div>

              <div className="space-y-2">
                <Label className="text-sm font-medium text-black">Pause After: {formatDuration(formData.pauseAfter)}</Label>
                <Slider
                  value={[formData.pauseAfter]}
                  onValueChange={([v]) => setFormData({ ...formData, pauseAfter: v })}
                  min={5}
                  max={60}
                  step={5}
                  className="py-2"
                />
                <p className="text-xs text-zinc-500">
                  Auto pause when container completes
                </p>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => { setCreateOpen(false); resetForm(); }} className="bg-white">
                Cancel
              </Button>
              <Button
                onClick={handleCreate}
                disabled={!formData.name.trim()}
                className="bg-black text-white hover:bg-zinc-800"
              >
                Create Container
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Containers Grid - Notion-style DENSE */}
      {containers.length === 0 ? (
        <div className="text-center py-12 border-2 border-dashed border-zinc-300 rounded-lg bg-white">
          <Package className="h-12 w-12 mx-auto text-zinc-400 mb-3" />
          <p className="text-black mb-1 font-semibold">No containers</p>
          <p className="text-xs text-zinc-600 mb-4">
            Create your first time block
          </p>
          <Button
            onClick={() => setCreateOpen(true)}
            className="bg-black text-white hover:bg-zinc-800 h-8 text-xs"
          >
            <Plus className="h-3 w-3 mr-1" />
            Create
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
          {containers.map((container) => (
            <ContainerCardCompact
              key={container.id}
              container={container}
              onClick={handleEnterContainer}
            />
          ))}
        </div>
      )}
    </div>
  );
}
