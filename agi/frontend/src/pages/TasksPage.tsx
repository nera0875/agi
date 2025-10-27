import { useEffect, useState } from 'react'
import { DndContext, DragEndEvent, DragOverEvent, closestCenter } from '@dnd-kit/core'
import { arrayMove } from '@dnd-kit/sortable'
import { useTasksStore } from '@/stores/tasksStore'
import { ProjectColumn } from '@/components/tasks/ProjectColumn'
import type { ProjectKey } from '@/types/tasks'
import { toast } from 'sonner'

export function TasksPage() {
  const { data, loading, error, fetchTasks, moveTask } = useTasksStore()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    fetchTasks()
  }, [fetchTasks])

  useEffect(() => {
    if (error) {
      toast.error(error)
    }
  }, [error])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Only handle shortcuts when not in an input field
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return
      }

      switch (e.key.toLowerCase()) {
        case 'n':
          // Focus on first "Add Task" button
          const addButton = document.querySelector('[data-add-task]') as HTMLButtonElement
          addButton?.click()
          break
        case 'r':
          // Refresh tasks
          fetchTasks()
          toast.success('Tasks refreshed')
          break
      }
    }

    if (mounted) {
      document.addEventListener('keydown', handleKeyDown)
      return () => document.removeEventListener('keydown', handleKeyDown)
    }
  }, [mounted, fetchTasks])

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event

    if (!over || !data) return

    const taskId = active.id as string
    const targetProjectKey = over.id as ProjectKey

    // Find the task and its current project
    let sourceProjectKey: ProjectKey | null = null
    let task = null

    for (const [projectKey, project] of Object.entries(data.projects)) {
      const foundTask = project.tasks.find(t => t.id === taskId)
      if (foundTask) {
        sourceProjectKey = projectKey as ProjectKey
        task = foundTask
        break
      }
    }

    if (!sourceProjectKey || !task) return

    // If moving to a different project
    if (sourceProjectKey !== targetProjectKey) {
      try {
        await moveTask(taskId, sourceProjectKey, targetProjectKey)
        toast.success(`Task moved to ${data.projects[targetProjectKey].name}`)
      } catch (error) {
        toast.error('Failed to move task')
      }
    }
  }

  if (!mounted) {
    return null // Prevent hydration mismatch
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading tasks...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 mb-4">Error: {error}</p>
          <button
            onClick={fetchTasks}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-600">No data available</p>
      </div>
    )
  }

  const projectKeys: ProjectKey[] = ['GOALS', 'CODE', 'PENTEST', 'BRAIN']

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Task Manager AGI
          </h1>
          <p className="text-gray-600">
            Manage your tasks across GOALS, CODE, PENTEST, and BRAIN projects
          </p>
          <div className="mt-4 text-sm text-gray-500">
            <p>Keyboard shortcuts: <kbd className="px-1 py-0.5 bg-gray-200 rounded">N</kbd> - New task, <kbd className="px-1 py-0.5 bg-gray-200 rounded">R</kbd> - Refresh</p>
          </div>
        </div>

        {/* Task Columns */}
        <DndContext
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {projectKeys.map((projectKey) => (
              <ProjectColumn
                key={projectKey}
                project={data.projects[projectKey]}
                projectKey={projectKey}
              />
            ))}
          </div>
        </DndContext>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>Last updated: {new Date(data.last_update).toLocaleString()}</p>
        </div>
      </div>
    </div>
  )
}