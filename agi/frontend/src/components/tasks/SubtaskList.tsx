import { useState } from 'react'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Plus, Trash2 } from 'lucide-react'
import { useTasksStore } from '@/stores/tasksStore'
import type { Subtask, ProjectKey } from '@/types/tasks'

interface SubtaskListProps {
  subtasks: Subtask[]
  projectId: ProjectKey
  taskId: string
}

export function SubtaskList({ subtasks, projectId, taskId }: SubtaskListProps) {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editingTitle, setEditingTitle] = useState('')
  const [newSubtaskTitle, setNewSubtaskTitle] = useState('')
  const [showNewForm, setShowNewForm] = useState(false)

  const { updateTask } = useTasksStore()

  const updateSubtasks = async (updatedSubtasks: Subtask[]) => {
    await updateTask(projectId, taskId, { subtasks: updatedSubtasks })
  }

  const toggleSubtaskCompleted = async (subtaskId: string) => {
    const updatedSubtasks = subtasks.map(subtask =>
      subtask.id === subtaskId
        ? { ...subtask, completed: !subtask.completed }
        : subtask
    )
    await updateSubtasks(updatedSubtasks)
  }

  const startEditing = (subtask: Subtask) => {
    setEditingId(subtask.id)
    setEditingTitle(subtask.title)
  }

  const saveEdit = async () => {
    if (editingId && editingTitle.trim()) {
      const updatedSubtasks = subtasks.map(subtask =>
        subtask.id === editingId
          ? { ...subtask, title: editingTitle.trim() }
          : subtask
      )
      await updateSubtasks(updatedSubtasks)
    }
    setEditingId(null)
    setEditingTitle('')
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditingTitle('')
  }

  const deleteSubtask = async (subtaskId: string) => {
    const updatedSubtasks = subtasks.filter(subtask => subtask.id !== subtaskId)
    await updateSubtasks(updatedSubtasks)
  }

  const addNewSubtask = async () => {
    if (newSubtaskTitle.trim()) {
      const newSubtask: Subtask = {
        id: crypto.randomUUID(),
        title: newSubtaskTitle.trim(),
        completed: false
      }
      const updatedSubtasks = [...subtasks, newSubtask]
      await updateSubtasks(updatedSubtasks)
      setNewSubtaskTitle('')
      setShowNewForm(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent, action: 'edit' | 'new') => {
    if (e.key === 'Enter') {
      if (action === 'edit') {
        saveEdit()
      } else {
        addNewSubtask()
      }
    }
    if (e.key === 'Escape') {
      if (action === 'edit') {
        cancelEdit()
      } else {
        setNewSubtaskTitle('')
        setShowNewForm(false)
      }
    }
  }

  return (
    <div className="ml-4 space-y-2">
      {subtasks.map((subtask) => (
        <div key={subtask.id} className="flex items-center gap-2 pl-4">
          <Checkbox
            checked={subtask.completed}
            onCheckedChange={() => toggleSubtaskCompleted(subtask.id)}
            className="h-4 w-4"
          />
          
          {editingId === subtask.id ? (
            <Input
              value={editingTitle}
              onChange={(e) => setEditingTitle(e.target.value)}
              onBlur={saveEdit}
              onKeyDown={(e) => handleKeyDown(e, 'edit')}
              autoFocus
              className="flex-1 h-6 text-sm"
            />
          ) : (
            <span
              onDoubleClick={() => startEditing(subtask)}
              className={`flex-1 text-sm cursor-pointer ${
                subtask.completed ? 'line-through text-gray-400' : ''
              }`}
            >
              {subtask.title}
            </span>
          )}

          <Button
            variant="ghost"
            size="sm"
            onClick={() => deleteSubtask(subtask.id)}
            className="h-6 w-6 p-0"
          >
            <Trash2 className="h-3 w-3 text-red-500" />
          </Button>
        </div>
      ))}

      {showNewForm ? (
        <div className="flex items-center gap-2 pl-4">
          <div className="h-4 w-4" /> {/* Spacer for checkbox alignment */}
          <Input
            value={newSubtaskTitle}
            onChange={(e) => setNewSubtaskTitle(e.target.value)}
            onKeyDown={(e) => handleKeyDown(e, 'new')}
            placeholder="New subtask..."
            autoFocus
            className="flex-1 h-6 text-sm"
          />
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setNewSubtaskTitle('')
              setShowNewForm(false)
            }}
            className="h-6 w-6 p-0"
          >
            ×
          </Button>
        </div>
      ) : (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowNewForm(true)}
          className="ml-4 h-6 px-2 text-xs text-gray-500"
        >
          <Plus className="h-3 w-3 mr-1" />
          Add subtask
        </Button>
      )}
    </div>
  )
}