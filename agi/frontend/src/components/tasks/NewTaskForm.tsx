import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Plus, X } from 'lucide-react'
import { useTasksStore } from '@/stores/tasksStore'
import type { ProjectKey } from '@/types/tasks'

interface NewTaskFormProps {
  projectId: ProjectKey
  onCancel?: () => void
}

export function NewTaskForm({ projectId, onCancel }: NewTaskFormProps) {
  const [title, setTitle] = useState('')
  const [priority, setPriority] = useState<0 | 1 | 3 | 5>(0)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { createTask } = useTasksStore()

  const priorityOptions = [
    { value: 0 as const, label: 'None', color: 'bg-gray-200 text-gray-800' },
    { value: 1 as const, label: 'Low', color: 'bg-blue-200 text-blue-800' },
    { value: 3 as const, label: 'Medium', color: 'bg-orange-200 text-orange-800' },
    { value: 5 as const, label: 'High', color: 'bg-red-200 text-red-800' }
  ]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim() || isSubmitting) return

    setIsSubmitting(true)
    try {
      await createTask(projectId, { title: title.trim(), priority })
      setTitle('')
      setPriority(0)
      onCancel?.()
    } catch (error) {
      console.error('Failed to create task:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onCancel?.()
    }
  }

  return (
    <form onSubmit={handleSubmit} className="border rounded-lg p-3 mb-2 bg-gray-50">
      <div className="space-y-3">
        <Input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Task title..."
          autoFocus
          className="w-full"
        />

        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Priority:</span>
          {priorityOptions.map((option) => (
            <Badge
              key={option.value}
              className={`cursor-pointer transition-opacity ${
                priority === option.value 
                  ? option.color 
                  : 'bg-gray-100 text-gray-400 opacity-50'
              }`}
              onClick={() => setPriority(option.value)}
            >
              {option.label}
            </Badge>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <Button
            type="submit"
            size="sm"
            disabled={!title.trim() || isSubmitting}
            className="h-6"
          >
            <Plus className="h-3 w-3 mr-1" />
            {isSubmitting ? 'Adding...' : 'Add Task'}
          </Button>
          
          {onCancel && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={onCancel}
              className="h-6"
            >
              <X className="h-3 w-3 mr-1" />
              Cancel
            </Button>
          )}
        </div>
      </div>
    </form>
  )
}