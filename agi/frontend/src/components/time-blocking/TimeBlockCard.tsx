import React from 'react'
import { cn } from '@/lib/utils'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Clock, Edit, Trash2, Play, Pause } from 'lucide-react'

export interface TimeBlock {
  id: string
  title: string
  startTime: string
  endTime: string
  duration: number // en minutes
  priority: 'high' | 'medium' | 'low'
  category?: string
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  description?: string
  color?: string
}

interface TimeBlockCardProps {
  timeBlock: TimeBlock
  onEdit?: (timeBlock: TimeBlock) => void
  onDelete?: (id: string) => void
  onStart?: (id: string) => void
  onPause?: (id: string) => void
  onComplete?: (id: string) => void
  className?: string
  compact?: boolean
}

const priorityColors = {
  high: 'bg-destructive text-destructive-foreground',
  medium: 'bg-warning text-warning-foreground', 
  low: 'bg-muted text-muted-foreground'
}

const statusColors = {
  pending: 'border-muted',
  in_progress: 'border-primary bg-primary/5',
  completed: 'border-success bg-success/5',
  cancelled: 'border-muted bg-muted/5 opacity-60'
}

export function TimeBlockCard({
  timeBlock,
  onEdit,
  onDelete,
  onStart,
  onPause,
  onComplete,
  className,
  compact = false
}: TimeBlockCardProps) {
  const formatTime = (time: string) => {
    return new Date(`2000-01-01T${time}`).toLocaleTimeString('fr-FR', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    if (hours > 0) {
      return `${hours}h${mins > 0 ? ` ${mins}min` : ''}`
    }
    return `${mins}min`
  }

  const canStart = timeBlock.status === 'pending'
  const canPause = timeBlock.status === 'in_progress'
  const canComplete = timeBlock.status === 'in_progress'

  return (
    <Card className={cn(
      'transition-all duration-200 hover:shadow-md',
      statusColors[timeBlock.status],
      className
    )}>
      <CardHeader className={cn('pb-2', compact && 'pb-1')}>
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <h3 className={cn(
              'font-medium leading-tight',
              compact ? 'text-sm' : 'text-base'
            )}>
              {timeBlock.title}
            </h3>
            <div className="flex items-center gap-2 mt-1">
              <div className="flex items-center gap-1 text-muted-foreground">
                <Clock className="h-3 w-3" />
                <span className="text-xs">
                  {formatTime(timeBlock.startTime)} - {formatTime(timeBlock.endTime)}
                </span>
              </div>
              <Badge variant="outline" className="text-xs">
                {formatDuration(timeBlock.duration)}
              </Badge>
            </div>
          </div>

          <div className="flex items-center gap-1">
            <Badge 
              variant="secondary" 
              className={cn('text-xs', priorityColors[timeBlock.priority])}
            >
              {timeBlock.priority}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className={cn('pt-0', compact && 'pb-2')}>
        {timeBlock.description && !compact && (
          <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
            {timeBlock.description}
          </p>
        )}

        {timeBlock.category && (
          <Badge variant="outline" className="mb-3 text-xs">
            {timeBlock.category}
          </Badge>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1">
            {canStart && onStart && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => onStart(timeBlock.id)}
                className="h-7 px-2"
              >
                <Play className="h-3 w-3 mr-1" />
                Démarrer
              </Button>
            )}

            {canPause && onPause && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => onPause(timeBlock.id)}
                className="h-7 px-2"
              >
                <Pause className="h-3 w-3 mr-1" />
                Pause
              </Button>
            )}

            {canComplete && onComplete && (
              <Button
                size="sm"
                onClick={() => onComplete(timeBlock.id)}
                className="h-7 px-2"
              >
                Terminer
              </Button>
            )}
          </div>

          <div className="flex items-center gap-1">
            {onEdit && (
              <Button
                size="sm"
                variant="ghost"
                onClick={() => onEdit(timeBlock)}
                className="h-7 w-7 p-0"
              >
                <Edit className="h-3 w-3" />
              </Button>
            )}

            {onDelete && timeBlock.status !== 'in_progress' && (
              <Button
                size="sm"
                variant="ghost"
                onClick={() => onDelete(timeBlock.id)}
                className="h-7 w-7 p-0 text-destructive hover:text-destructive"
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}