import { useState } from 'react';
import { Calendar, Plus, X, Play, Trash2 } from 'lucide-react';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { toast } from 'sonner';
import type { BlockContainer } from '../types/timeblock';
import { formatDuration } from '../types/timeblock';

interface DailyTimelineProps {
  containers: BlockContainer[];
  onScheduleContainer: (containerId: string, startTime: string) => void;
  onStartContainer: (containerId: string) => void;
}

interface ScheduledSlot {
  id: string;
  startHour: number;
  startMinute: number;
  endHour: number;
  endMinute: number;
  container: BlockContainer;
}

export function DailyTimeline({ containers, onScheduleContainer, onStartContainer }: DailyTimelineProps) {
  const [scheduledSlots, setScheduledSlots] = useState<ScheduledSlot[]>([]);
  const [scheduleDialogOpen, setScheduleDialogOpen] = useState(false);
  const [selectedContainer, setSelectedContainer] = useState<string>('');
  const [startTime, setStartTime] = useState('09:00');

  // Generate time options (every 15min from 6h to 23h45)
  const timeOptions: string[] = [];
  for (let h = 6; h < 24; h++) {
    for (let m = 0; m < 60; m += 15) {
      timeOptions.push(`${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`);
    }
  }

  const handleSchedule = () => {
    if (!selectedContainer) return;
    const container = containers.find(c => c.id === selectedContainer);
    if (!container) return;

    const [startH, startM] = startTime.split(':').map(Number);
    const durationMinutes = container.totalDuration + container.pauseAfter;
    const endMinutes = startH * 60 + startM + durationMinutes;
    const endH = Math.floor(endMinutes / 60);
    const endM = endMinutes % 60;

    // Backend offline check - log to console for demo mode
    if (endH > 24) {
      toast.warning('Schedule extends past midnight - adjusting...');
    }

    const newSlot: ScheduledSlot = {
      id: crypto.randomUUID(),
      startHour: startH,
      startMinute: startM,
      endHour: Math.min(endH, 24),
      endMinute: endH > 24 ? 0 : endM,
      container,
    };

    setScheduledSlots([...scheduledSlots, newSlot]);
    onScheduleContainer(selectedContainer, startTime);
    setScheduleDialogOpen(false);
    setSelectedContainer('');
    toast.success('Container scheduled');
  };

  const handleRemoveSlot = (slotId: string) => {
    setScheduledSlots(scheduledSlots.filter(s => s.id !== slotId));
    toast.success('Slot removed');
  };

  const currentHour = new Date().getHours();
  const currentMinute = new Date().getMinutes();
  const currentTimePercent = ((currentHour - 6) * 60 + currentMinute) / (18 * 60) * 100;

  // Calculate position for each slot (6h = 0%, 24h = 100%)
  const getSlotPosition = (slot: ScheduledSlot) => {
    const startMinutes = (slot.startHour - 6) * 60 + slot.startMinute;
    const endMinutes = (slot.endHour - 6) * 60 + slot.endMinute;
    const totalMinutes = 18 * 60; // 6h to 24h

    return {
      top: `${(startMinutes / totalMinutes) * 100}%`,
      height: `${((endMinutes - startMinutes) / totalMinutes) * 100}%`,
    };
  };

  return (
    <div className="h-full flex flex-col bg-card">
      {/* HEADER */}
      <div className="px-4 py-3 border-b border-border flex items-center justify-between flex-shrink-0">
        <div>
          <div className="flex items-center gap-2 mb-0.5">
            <Calendar className="h-4 w-4 text-foreground" />
            <h2>
              {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
            </h2>
          </div>
          <p className="text-muted-foreground">
            {scheduledSlots.length} scheduled • {scheduledSlots.reduce((sum, s) => sum + (s.container?.totalDuration || 0), 0)}min planned
          </p>
        </div>

        {/* Schedule Dialog */}
        <Dialog open={scheduleDialogOpen} onOpenChange={setScheduleDialogOpen}>
          <DialogTrigger asChild>
            <Button size="sm" className="bg-primary text-primary-foreground hover:bg-primary/90 h-7">
              <Plus className="h-3 w-3 mr-1" />
              Add
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-sm bg-card border-border">
            <DialogHeader>
              <DialogTitle>Schedule Container</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Container</Label>
                <Select value={selectedContainer} onValueChange={setSelectedContainer}>
                  <SelectTrigger className="h-8">
                    <SelectValue placeholder="Select a container" />
                  </SelectTrigger>
                  <SelectContent>
                    {containers.filter(c => !c.locked).map(c => (
                      <SelectItem key={c.id} value={c.id}>
                        {c.name} ({formatDuration(c.totalDuration)})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Start Time</Label>
                <Select value={startTime} onValueChange={setStartTime}>
                  <SelectTrigger className="h-8">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="max-h-48">
                    {timeOptions.map(time => (
                      <SelectItem key={time} value={time}>
                        {time}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {selectedContainer && (
                <div className="bg-muted border border-border rounded-md p-2">
                  <p className="text-muted-foreground">
                    Duration: <span className="text-foreground">{formatDuration(containers.find(c => c.id === selectedContainer)?.totalDuration || 0)}</span>
                  </p>
                  <p className="text-muted-foreground">
                    Ends at: <span className="text-foreground">
                      {(() => {
                        const container = containers.find(c => c.id === selectedContainer);
                        if (!container) return '';
                        const [h, m] = startTime.split(':').map(Number);
                        const endMinutes = h * 60 + m + container.totalDuration + container.pauseAfter;
                        const endH = Math.floor(endMinutes / 60);
                        const endM = endMinutes % 60;
                        return `${endH.toString().padStart(2, '0')}:${endM.toString().padStart(2, '0')}`;
                      })()}
                    </span>
                  </p>
                </div>
              )}
            </div>
            <Button onClick={handleSchedule} disabled={!selectedContainer} className="w-full bg-primary text-primary-foreground hover:bg-primary/90 h-8">
              Schedule
            </Button>
          </DialogContent>
        </Dialog>
      </div>

      {/* COMPACT TIMELINE - Entire day visible */}
      <div className="flex-1 flex overflow-hidden">
        {/* Time Labels (LEFT) */}
        <div className="w-12 flex-shrink-0 border-r border-border bg-muted">
          <div className="relative h-full">
            {Array.from({ length: 19 }, (_, i) => i + 6).map((hour) => (
              <div
                key={hour}
                className="absolute left-0 right-0 flex items-start justify-center"
                style={{
                  top: `${((hour - 6) / 18) * 100}%`,
                  height: `${(1 / 18) * 100}%`,
                }}
              >
                <span className={hour === currentHour ? 'text-foreground' : 'text-muted-foreground'}>
                  {hour.toString().padStart(2, '0')}:00
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Timeline Grid (CENTER) */}
        <div className="flex-1 relative bg-card">
          {/* Hour Lines */}
          <div className="absolute inset-0">
            {Array.from({ length: 18 }, (_, i) => i).map((i) => (
              <div
                key={i}
                className="absolute left-0 right-0 border-t border-border"
                style={{ top: `${(i / 18) * 100}%` }}
              />
            ))}
          </div>

          {/* Current Time Indicator */}
          {currentHour >= 6 && currentHour < 24 && (
            <div
              className="absolute left-0 right-0 z-10 border-t-2 border-foreground"
              style={{ top: `${currentTimePercent}%` }}
            >
              <div className="absolute -left-1 -top-1 w-2 h-2 bg-foreground rounded-full" />
            </div>
          )}

          {/* Scheduled Slots */}
          {scheduledSlots.map((slot) => {
            const pos = getSlotPosition(slot);
            return (
              <div
                key={slot.id}
                className="absolute left-2 right-2 bg-chart-2 border-l-4 border-foreground rounded-md shadow-sm group hover:shadow-md transition-all"
                style={pos}
              >
                <div className="h-full flex flex-col justify-between p-2">
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <div className="flex-1 min-w-0">
                      <p className="text-primary-foreground truncate">{slot.container.name}</p>
                      <p className="text-primary-foreground/70">
                        {slot.startHour.toString().padStart(2, '0')}:{slot.startMinute.toString().padStart(2, '0')} - {slot.endHour.toString().padStart(2, '0')}:{slot.endMinute.toString().padStart(2, '0')}
                      </p>
                    </div>
                    <button
                      onClick={() => handleRemoveSlot(slot.id)}
                      className="opacity-0 group-hover:opacity-100 transition-opacity h-4 w-4 flex items-center justify-center rounded hover:bg-chart-3"
                    >
                      <X className="h-3 w-3 text-primary-foreground/50 hover:text-primary-foreground" />
                    </button>
                  </div>

                  {/* Quick Start Button */}
                  <Button
                    size="sm"
                    onClick={() => onStartContainer?.(slot.container.id)}
                    className="h-5 px-2 bg-primary text-primary-foreground hover:bg-primary/90 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <Play className="h-2.5 w-2.5 mr-1" />
                    Start
                  </Button>
                </div>
              </div>
            );
          })}

          {/* Empty State */}
          {scheduledSlots.length === 0 && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <p className="text-muted-foreground mb-2">No containers scheduled</p>
                <Button
                  size="sm"
                  onClick={() => setScheduleDialogOpen(true)}
                  variant="outline"
                  className="h-7 border-border"
                >
                  <Plus className="h-3 w-3 mr-1" />
                  Add Container
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Quick Stats (RIGHT) */}
        <div className="w-48 flex-shrink-0 border-l border-border bg-muted p-3 overflow-y-auto">
          <h3 className="text-foreground mb-2 uppercase tracking-wide">Scheduled</h3>
          {scheduledSlots.length === 0 ? (
            <p className="text-muted-foreground">Nothing yet</p>
          ) : (
            <div className="space-y-1.5">
              {scheduledSlots.map((slot) => (
                <div key={slot.id} className="bg-card border border-border rounded-md p-2 group hover:border-accent transition-colors">
                  <div className="flex items-start justify-between gap-1 mb-1">
                    <p className="text-foreground truncate flex-1">{slot.container.name}</p>
                    <button
                      onClick={() => handleRemoveSlot(slot.id)}
                      className="opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <Trash2 className="h-3 w-3 text-muted-foreground hover:text-foreground" />
                    </button>
                  </div>
                  <p className="text-muted-foreground">
                    {slot.startHour.toString().padStart(2, '0')}:{slot.startMinute.toString().padStart(2, '0')} - {slot.endHour.toString().padStart(2, '0')}:{slot.endMinute.toString().padStart(2, '0')}
                  </p>
                  <p className="text-muted-foreground mt-0.5">
                    {slot.container.blocks.length} blocks • {formatDuration(slot.container.totalDuration)}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
