import React, { useState, useMemo } from 'react'
import { cn } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { ChevronLeft, ChevronRight, Plus, Calendar as CalendarIcon } from 'lucide-react'
import { TimeBlock, TimeBlockCard } from './TimeBlockCard'

interface TimeBlockCalendarProps {
  timeBlocks: TimeBlock[]
  selectedDate: Date
  onDateChange: (date: Date) => void
  onCreateTimeBlock?: (date: Date, startTime?: string) => void
  onEditTimeBlock?: (timeBlock: TimeBlock) => void
  onDeleteTimeBlock?: (id: string) => void
  onStartTimeBlock?: (id: string) => void
  onPauseTimeBlock?: (id: string) => void
  onCompleteTimeBlock?: (id: string) => void
  className?: string
}

export function TimeBlockCalendar({
  timeBlocks,
  selectedDate,
  onDateChange,
  onCreateTimeBlock,
  onEditTimeBlock,
  onDeleteTimeBlock,
  onStartTimeBlock,
  onPauseTimeBlock,
  onCompleteTimeBlock,
  className
}: TimeBlockCalendarProps) {
  const [viewMode, setViewMode] = useState<'day' | 'week'>('day')

  // Génération des heures de la journée (6h - 23h)
  const timeSlots = useMemo(() => {
    const slots = []
    for (let hour = 6; hour <= 23; hour++) {
      slots.push({
        time: `${hour.toString().padStart(2, '0')}:00`,
        label: `${hour}:00`
      })
    }
    return slots
  }, [])

  // Filtrage des time blocks pour la date sélectionnée
  const dayTimeBlocks = useMemo(() => {
    const dateStr = selectedDate.toISOString().split('T')[0]
    return timeBlocks.filter(block => {
      // Supposons que les time blocks ont une date associée
      return block.startTime.includes(dateStr) || 
             new Date(block.startTime).toDateString() === selectedDate.toDateString()
    })
  }, [timeBlocks, selectedDate])

  // Navigation de date
  const navigateDate = (direction: 'prev' | 'next') => {
    const newDate = new Date(selectedDate)
    if (viewMode === 'day') {
      newDate.setDate(newDate.getDate() + (direction === 'next' ? 1 : -1))
    } else {
      newDate.setDate(newDate.getDate() + (direction === 'next' ? 7 : -7))
    }
    onDateChange(newDate)
  }

  // Formatage de la date
  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat('fr-FR', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    }).format(date)
  }

  // Calcul des statistiques du jour
  const dayStats = useMemo(() => {
    const total = dayTimeBlocks.length
    const completed = dayTimeBlocks.filter(b => b.status === 'completed').length
    const inProgress = dayTimeBlocks.filter(b => b.status === 'in_progress').length
    const totalDuration = dayTimeBlocks.reduce((sum, b) => sum + b.duration, 0)
    
    return { total, completed, inProgress, totalDuration }
  }, [dayTimeBlocks])

  // Trouver le time block à une heure donnée
  const getTimeBlockAtSlot = (timeSlot: string) => {
    return dayTimeBlocks.find(block => {
      const blockStart = block.startTime.split('T')[1]?.substring(0, 5) || block.startTime
      return blockStart === timeSlot
    })
  }

  return (
    <div className={cn('flex flex-col h-full', className)}>
      {/* En-tête avec navigation */}
      <Card className="mb-4">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CalendarIcon className="h-5 w-5" />
              <CardTitle className="text-lg">
                {formatDate(selectedDate)}
              </CardTitle>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setViewMode(viewMode === 'day' ? 'week' : 'day')}
              >
                {viewMode === 'day' ? 'Semaine' : 'Jour'}
              </Button>

              <div className="flex items-center gap-1">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigateDate('prev')}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onDateChange(new Date())}
                >
                  Aujourd'hui
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigateDate('next')}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          {/* Statistiques du jour */}
          <div className="flex items-center gap-4 mt-3">
            <Badge variant="outline">
              {dayStats.total} blocs
            </Badge>
            <Badge variant="outline" className="bg-success/10">
              {dayStats.completed} terminés
            </Badge>
            {dayStats.inProgress > 0 && (
              <Badge variant="outline" className="bg-primary/10">
                {dayStats.inProgress} en cours
              </Badge>
            )}
            <Badge variant="outline">
              {Math.floor(dayStats.totalDuration / 60)}h{dayStats.totalDuration % 60}min
            </Badge>
          </div>
        </CardHeader>
      </Card>

      {/* Vue calendrier */}
      <Card className="flex-1">
        <CardContent className="p-0">
          <ScrollArea className="h-[600px]">
            <div className="p-4">
              {/* Grille horaire */}
              <div className="space-y-1">
                {timeSlots.map((slot) => {
                  const existingBlock = getTimeBlockAtSlot(slot.time)
                  
                  return (
                    <div
                      key={slot.time}
                      className="flex items-center gap-3 min-h-[60px] border-b border-border/50 last:border-b-0"
                    >
                      {/* Heure */}
                      <div className="w-16 text-sm text-muted-foreground font-mono">
                        {slot.label}
                      </div>

                      {/* Contenu du slot */}
                      <div className="flex-1">
                        {existingBlock ? (
                          <TimeBlockCard
                            timeBlock={existingBlock}
                            onEdit={onEditTimeBlock}
                            onDelete={onDeleteTimeBlock}
                            onStart={onStartTimeBlock}
                            onPause={onPauseTimeBlock}
                            onComplete={onCompleteTimeBlock}
                            compact
                          />
                        ) : (
                          <Button
                            variant="ghost"
                            className="w-full h-12 border-2 border-dashed border-muted-foreground/20 hover:border-muted-foreground/40"
                            onClick={() => onCreateTimeBlock?.(selectedDate, slot.time)}
                          >
                            <Plus className="h-4 w-4 mr-2" />
                            Ajouter un bloc
                          </Button>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Actions rapides */}
      <div className="mt-4 flex gap-2">
        <Button
          onClick={() => onCreateTimeBlock?.(selectedDate)}
          className="flex-1"
        >
          <Plus className="h-4 w-4 mr-2" />
          Nouveau bloc de temps
        </Button>
      </div>
    </div>
  )
}