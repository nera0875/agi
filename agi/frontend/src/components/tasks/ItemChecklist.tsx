import { useState } from 'react'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Plus, Trash2 } from 'lucide-react'
import { useTasksStore } from '@/stores/tasksStore'
import type { ChecklistItem, ProjectKey } from '@/types/tasks'

interface ItemChecklistProps {
  items: ChecklistItem[]
  projectId: ProjectKey
  taskId: string
}

export function ItemChecklist({ items, projectId, taskId }: ItemChecklistProps) {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editingTitle, setEditingTitle] = useState('')
  const [newItemTitle, setNewItemTitle] = useState('')
  const [showNewForm, setShowNewForm] = useState(false)

  const { updateTask } = useTasksStore()

  const updateItems = async (updatedItems: ChecklistItem[]) => {
    await updateTask(projectId, taskId, { items: updatedItems })
  }

  const toggleItemCompleted = async (itemId: string) => {
    const updatedItems = items.map(item =>
      item.id === itemId
        ? { ...item, completed: !item.completed }
        : item
    )
    await updateItems(updatedItems)
  }

  const startEditing = (item: ChecklistItem) => {
    setEditingId(item.id)
    setEditingTitle(item.title)
  }

  const saveEdit = async () => {
    if (editingId && editingTitle.trim()) {
      const updatedItems = items.map(item =>
        item.id === editingId
          ? { ...item, title: editingTitle.trim() }
          : item
      )
      await updateItems(updatedItems)
    }
    setEditingId(null)
    setEditingTitle('')
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditingTitle('')
  }

  const deleteItem = async (itemId: string) => {
    const updatedItems = items.filter(item => item.id !== itemId)
    await updateItems(updatedItems)
  }

  const addNewItem = async () => {
    if (newItemTitle.trim()) {
      const newItem: ChecklistItem = {
        id: crypto.randomUUID(),
        title: newItemTitle.trim(),
        completed: false
      }
      const updatedItems = [...items, newItem]
      await updateItems(updatedItems)
      setNewItemTitle('')
      setShowNewForm(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent, action: 'edit' | 'new') => {
    if (e.key === 'Enter') {
      if (action === 'edit') {
        saveEdit()
      } else {
        addNewItem()
      }
    }
    if (e.key === 'Escape') {
      if (action === 'edit') {
        cancelEdit()
      } else {
        setNewItemTitle('')
        setShowNewForm(false)
      }
    }
  }

  return (
    <div className="ml-4 space-y-1">
      {items.map((item) => (
        <div key={item.id} className="flex items-center gap-2 pl-4">
          <Checkbox
            checked={item.completed}
            onCheckedChange={() => toggleItemCompleted(item.id)}
            className="h-3 w-3"
          />
          
          {editingId === item.id ? (
            <Input
              value={editingTitle}
              onChange={(e) => setEditingTitle(e.target.value)}
              onBlur={saveEdit}
              onKeyDown={(e) => handleKeyDown(e, 'edit')}
              autoFocus
              className="flex-1 h-5 text-xs"
            />
          ) : (
            <span
              onDoubleClick={() => startEditing(item)}
              className={`flex-1 text-xs cursor-pointer ${
                item.completed ? 'line-through text-gray-400' : ''
              }`}
            >
              {item.title}
            </span>
          )}

          <Button
            variant="ghost"
            size="sm"
            onClick={() => deleteItem(item.id)}
            className="h-5 w-5 p-0"
          >
            <Trash2 className="h-2 w-2 text-red-500" />
          </Button>
        </div>
      ))}

      {showNewForm ? (
        <div className="flex items-center gap-2 pl-4">
          <div className="h-3 w-3" /> {/* Spacer for checkbox alignment */}
          <Input
            value={newItemTitle}
            onChange={(e) => setNewItemTitle(e.target.value)}
            onKeyDown={(e) => handleKeyDown(e, 'new')}
            placeholder="New item..."
            autoFocus
            className="flex-1 h-5 text-xs"
          />
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setNewItemTitle('')
              setShowNewForm(false)
            }}
            className="h-5 w-5 p-0"
          >
            ×
          </Button>
        </div>
      ) : (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowNewForm(true)}
          className="ml-4 h-5 px-2 text-xs text-gray-500"
        >
          <Plus className="h-2 w-2 mr-1" />
          Add item
        </Button>
      )}
    </div>
  )
}