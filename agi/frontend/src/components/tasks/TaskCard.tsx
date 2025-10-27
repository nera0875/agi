import { useState, useEffect } from 'react'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Trash2, ChevronDown, ChevronRight } from 'lucide-react'
import { useTasksStore } from '@/stores/tasksStore'
import type { Task, ProjectKey } from '@/types/tasks'
import { SubtaskList } from './SubtaskList'
import { ItemChecklist } from './ItemChecklist'

interface TaskCardProps {
  task: Task
  projectId: ProjectKey
}

export function TaskCard({ task, projectId }: TaskCardProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [title, setTitle] = useState(task.title)
  const [showSubtasks, setShowSubtasks] = useState(false)
  const [showItems, setShowItems] = useState(false)

  const { updateTask, deleteTask } = useTasksStore()

  // Auto-save with debounce
  useEffect(() => {
    if (title !== task.title && title.trim()) {
      const timeoutId = setTimeout(() => {
        updateTask(projectId, task.id, { title })
      }, 2000)
      return () => clearTimeout(timeoutId)
    }
  }, [title, task.title, task.id, projectId, updateTask])

  const priorityColors = {
    0: 'bg-gray-200 text-gray-800',
    1: 'bg-blue-200 text-blue-800',
    3: 'bg-orange-200 text-orange-800',
    5: 'bg-red-200 text-red-800'
  }

  const handleSave = async () => {
    if (title !== task.title && title.trim()) {
      await updateTask(projectId, task.id, { title })
    }
    setIsEditing(false)
  }

  const toggleCompleted = async () => {
    await updateTask(projectId, task.id, { completed: !task.completed })
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSave()
    }
    if (e.key === 'Escape') {
      setTitle(task.title)
      setIsEditing(false)
    }
  }

  const completedSubtasks = task.subtasks.filter(s => s.completed).length
  const completedItems = task.items.filter(i => i.completed).length

  return (
    <div className="border rounded-lg p-3 mb-2 bg-white shadow-sm transition-opacity duration-150">
      <div className="flex items-start gap-2">
        <Checkbox
          checked={task.completed}
          onCheckedChange={toggleCompleted}
          className="mt-1"
        />

        <div className="flex-1">
          {isEditing ? (
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onBlur={handleSave}
              onKeyDown={handleKeyDown}
              autoFocus
              className="mb-2"
            />
          ) : (
            <p
              onDoubleClick={() => setIsEditing(true)}
              className={`cursor-pointer mb-2 ${
                task.completed ? 'line-through text-gray-400' : ''
              }`}
            >
              {task.title}
            </p>
          )}

          {task.subtasks.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowSubtasks(!showSubtasks)}
              className="mb-2 h-6 px-2 text-xs"
            >
              {showSubtasks ? (
                <ChevronDown className="h-3 w-3 mr-1" />
              ) : (
                <ChevronRight className="h-3 w-3 mr-1" />
              )}
              Subtasks ({completedSubtasks}/{task.subtasks.length})
            </Button>
          )}

          {showSubtasks && (
            <SubtaskList
              subtasks={task.subtasks}
              projectId={projectId}
              taskId={task.id}
            />
          )}

          {task.items.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowItems(!showItems)}
              className="h-6 px-2 text-xs"
            >
              {showItems ? (
                <ChevronDown className="h-3 w-3 mr-1" />
              ) : (
                <ChevronRight className="h-3 w-3 mr-1" />
              )}
              Items ({completedItems}/{task.items.length})
            </Button>
          )}

          {showItems && (
            <ItemChecklist
              items={task.items}
              projectId={projectId}
              taskId={task.id}
            />
          )}
        </div>

        <div className="flex items-center gap-2">
          {task.priority > 0 && (
            <Badge className={priorityColors[task.priority]}>
              P{task.priority}
            </Badge>
          )}

          <Button
            variant="ghost"
            size="sm"
            onClick={() => deleteTask(projectId, task.id)}
            className="h-6 w-6 p-0"
          >
            <Trash2 className="h-3 w-3 text-red-500" />
          </Button>
        </div>
      </div>
    </div>
  )
}