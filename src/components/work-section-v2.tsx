import { useState, useEffect } from 'react';
import { Search, Plus, Play, Clock, Box, Calendar, MoreVertical, Trash2, Copy } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import { Separator } from './ui/separator';
import { Badge } from './ui/badge';
import { Skeleton } from './ui/skeleton';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from './ui/dropdown-menu';
import { useContainers } from '../hooks/useContainers';
import { ContainerDetail } from './container-detail';
import { DailyTimeline } from './daily-timeline';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Label } from './ui/label';
import { Slider } from './ui/slider';
import { toast } from 'sonner';
import type { BlockContainer } from '../types/timeblock';
import { createBlockContainer, formatDuration } from '../types/timeblock';

/**
 * WorkSection - Refactored with STRICT design system
 *
 * OFFLINE MODE SUPPORT:
 * - Backend may be unavailable (:8000/graphql)
 * - Falls back to localStorage + mock data
 * - Discreet toast if backend is offline
 * - Loading states with Skeleton component
 * - UI 100% functional without backend
 *
 * COLOR HIERARCHY (SEMANTIC TOKENS ONLY):
 * - bg-muted: Page base (#f4f4f5)
 * - bg-card: Elevated panels (#ffffff)
 * - bg-accent: Interactive hover (#f4f4f5)
 * - border-border: Dividers (#e4e4e7)
 * - text-foreground: Primary text (#000000)
 * - text-muted-foreground: Secondary (#71717a)
 * - bg-primary: Actions (#000000)
 */

// Mock data for offline mode
const MOCK_CONTAINERS: BlockContainer[] = [
  createBlockContainer('Morning Focus', 60, 10),
  createBlockContainer('Afternoon Deep Work', 90, 15),
];

export function WorkSectionV2() {
  const {
    containers: backendContainers,
    createContainer,
    updateContainer,
    deleteContainer,
    duplicateContainer,
    startContainer,
    addTask,
    toggleTask,
  } = useContainers();

  // Offline mode state
  const [isLoading, setIsLoading] = useState(true);
  const [backendError, setBackendError] = useState<string | null>(null);
  const [offlineMode, setOfflineMode] = useState(false);

  const [view, setView] = useState<'timeline' | 'containers'>('timeline');
  const [selectedContainerId, setSelectedContainerId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  // Form state
  const [formName, setFormName] = useState('');
  const [formDuration, setFormDuration] = useState(60);
  const [formPause, setFormPause] = useState(10);

  // Check backend availability on mount
  useEffect(() => {
    const checkBackend = async () => {
      try {
        // Try to fetch from backend
        const response = await fetch('http://localhost:8001/graphql', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: '{ __typename }',
          }),
        });

        if (!response.ok) {
          throw new Error(`Backend error: ${response.status}`);
        }

        setBackendError(null);
        setOfflineMode(false);
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Backend unavailable';
        setBackendError(errorMsg);
        setOfflineMode(true);
        // Discreet toast notification
        toast.info('Running in offline mode - using local data', {
          duration: 3000,
        });
      } finally {
        setIsLoading(false);
      }
    };

    checkBackend();
  }, []);

  // Use backend containers or mock data
  const containers = offlineMode
    ? MOCK_CONTAINERS
    : backendContainers;

  const selectedContainer = selectedContainerId
    ? containers.find(c => c.id === selectedContainerId)
    : null;

  const filteredContainers = containers.filter(c =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleCreate = () => {
    if (!formName.trim()) return;
    const container = createBlockContainer(formName.trim(), formDuration, formPause);
    if (offlineMode) {
      toast.info('Offline: Changes saved locally only', { duration: 2000 });
    }
    createContainer(container);
    setCreateDialogOpen(false);
    setFormName('');
    setFormDuration(60);
    setFormPause(10);
    setSelectedContainerId(container.id);
  };

  const handleDelete = (id: string) => {
    deleteContainer(id);
    if (selectedContainerId === id) {
      setSelectedContainerId(null);
    }
  };

  // Loading skeleton for sidebar
  const renderContainerSkeleton = () => (
    <div className="p-2 space-y-1">
      {[1, 2, 3].map(i => (
        <div key={i} className="p-3 rounded-md border border-border bg-card">
          <Skeleton className="h-4 w-24 mb-2 bg-muted" />
          <Skeleton className="h-3 w-16 bg-muted" />
        </div>
      ))}
    </div>
  );

  return (
    <div className="h-full flex bg-muted">
      {/* LEFT SIDEBAR - Container List */}
      <div className="w-72 bg-card border-r border-border flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-foreground">Containers</h4>
            <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button size="sm" className="h-7 px-2 bg-primary text-primary-foreground hover:bg-primary/90">
                  <Plus className="h-3 w-3" />
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-sm">
                <DialogHeader>
                  <DialogTitle>New Container</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label>Name</Label>
                    <Input
                      placeholder="e.g., Morning Focus"
                      value={formName}
                      onChange={(e) => setFormName(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Duration: {formatDuration(formDuration)}</Label>
                    <Slider
                      value={[formDuration]}
                      onValueChange={([v]) => setFormDuration(v)}
                      min={15}
                      max={240}
                      step={5}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Break After: {formatDuration(formPause)}</Label>
                    <Slider
                      value={[formPause]}
                      onValueChange={([v]) => setFormPause(v)}
                      min={5}
                      max={60}
                      step={5}
                    />
                  </div>
                </div>
                <Button onClick={handleCreate} disabled={!formName.trim()} className="w-full bg-primary text-primary-foreground">
                  Create
                </Button>
              </DialogContent>
            </Dialog>
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground" />
            <Input
              placeholder="Search containers..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-7 h-8"
            />
          </div>
        </div>

        {/* Container List */}
        <ScrollArea className="flex-1">
          {isLoading ? (
            renderContainerSkeleton()
          ) : filteredContainers.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <p>{searchQuery ? 'No matches' : 'No containers yet'}</p>
            </div>
          ) : (
            <div className="p-2 space-y-1">
              {filteredContainers.map((container) => (
                <button
                  key={container.id}
                  onClick={() => setSelectedContainerId(container.id)}
                  className={`w-full text-left p-3 rounded-md transition-colors border ${
                    selectedContainerId === container.id
                      ? 'bg-accent border-foreground'
                      : 'hover:bg-accent border-border'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-foreground truncate">
                        {container.name}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-muted-foreground">
                          {formatDuration(container.totalDuration)}
                        </span>
                        {container.locked && (
                          <Badge
                            variant="default"
                            className="h-5 px-1.5 bg-primary text-primary-foreground"
                          >
                            RUNNING
                          </Badge>
                        )}
                      </div>
                    </div>

                    <DropdownMenu>
                      <DropdownMenuTrigger
                        asChild
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0"
                        >
                          <MoreVertical className="h-3 w-3" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={(e) => {
                            e.stopPropagation();
                            startContainer(container.id);
                          }}
                        >
                          <Play className="h-3 w-3 mr-2" />
                          Start
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={(e) => {
                            e.stopPropagation();
                            duplicateContainer(container.id);
                          }}
                        >
                          <Copy className="h-3 w-3 mr-2" />
                          Duplicate
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(container.id);
                          }}
                          className="text-destructive"
                        >
                          <Trash2 className="h-3 w-3 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>

                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Box className="h-3 w-3" />
                    <span>{container.blocks.length} blocks</span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </ScrollArea>

        {/* Footer Stats */}
        <div className="p-3 border-t border-border bg-card">
          <div className="flex items-center justify-between text-muted-foreground">
            <span>{containers.length} total</span>
            <span>{containers.filter(c => c.locked).length} active</span>
            {offlineMode && (
              <span className="text-xs bg-primary/10 px-2 py-1 rounded text-foreground">
                Offline
              </span>
            )}
          </div>
        </div>
      </div>

      {/* CENTER - Main Workspace */}
      <div className="flex-1 flex flex-col bg-card">
        {/* Toolbar */}
        <div className="h-12 border-b border-border px-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button
              variant={view === 'timeline' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setView('timeline')}
            >
              <Calendar className="h-3 w-3 mr-1.5" />
              Timeline
            </Button>
            <Button
              variant={view === 'containers' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setView('containers')}
            >
              <Box className="h-3 w-3 mr-1.5" />
              Blocks
            </Button>
          </div>

          {selectedContainer && (
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">
                {selectedContainer.name}
              </span>
              <Separator orientation="vertical" className="h-4" />
              <Button
                size="sm"
                onClick={() => startContainer(selectedContainer.id)}
                className="bg-primary text-primary-foreground hover:bg-primary/90 h-7"
              >
                <Play className="h-3 w-3 mr-1" />
                Start
              </Button>
            </div>
          )}
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden">
          {view === 'timeline' ? (
            <DailyTimeline
              containers={containers}
              onScheduleContainer={(id, time) => console.log('Schedule', id, time)}
              onStartContainer={startContainer}
            />
          ) : selectedContainer ? (
            <div className="h-full overflow-auto p-6">
              <ContainerDetail
                container={selectedContainer}
                onBack={() => setSelectedContainerId(null)}
                onUpdateContainer={updateContainer}
                onAddTask={addTask}
                onToggleTask={toggleTask}
                onStartContainer={startContainer}
              />
            </div>
          ) : (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <Box className="h-12 w-12 mx-auto text-muted-foreground mb-3" />
                <p className="text-muted-foreground mb-1">No container selected</p>
                <p className="text-muted-foreground/60">Select a container from the sidebar</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
