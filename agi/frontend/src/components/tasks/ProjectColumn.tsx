import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Plus } from 'lucide-react'
import { useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import type { Project, ProjectKey } from '@/types/tasks'
import { TaskCard } from './TaskCard'
import { NewTaskForm } from './NewTaskForm'
import { SortableTaskCard } from './SortableTaskCard'

interface ProjectColumnProps {
  project: Project
  projectKey: ProjectKey
}

export function ProjectColumn({ project, projectKey }: ProjectColumnProps) {
  const [showNewTaskForm, setShowNewTaskForm] = useState(false)

  const { setNodeRef } = useDroppable({
    id: projectKey,
  })

  const taskIds = project.tasks.map(task => task.id)

  return (
    <div className="flex-1 min-w-0">
      <div
        className="rounded-lg border bg-white shadow-sm h-full flex flex-col"
        style={{ minHeight: '600px' }}
      >
        {/* Header */}
        <div
          className="p-4 border-b"
          style={{ backgroundColor: project.color + '20' }}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h2 className="font-semibold text-lg">{project.name}</h2>
              <span className="text-sm text-gray-500">
                ({project.tasks.length})
              </span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowNewTaskForm(true)}
              className="h-6 w-6 p-0"
            >
              <Plus className="h-4 w-4" />
            </Button>
          </div>
          
          <div className="mt-2 text-xs text-gray-600 capitalize">
            {project.view_mode} view
          </div>
        </div>

        {/* Content */}
        <div
          ref={setNodeRef}
          className="flex-1 p-4 overflow-y-auto"
          style={{ maxHeight: 'calc(100vh - 200px)' }}
        >
          {showNewTaskForm && (
            <NewTaskForm
              projectId={projectKey}
              onCancel={() => setShowNewTaskForm(false)}
            />
          )}

          <SortableContext items={taskIds} strategy={verticalListSortingStrategy}>
            {project.tasks.map((task) => (
              <SortableTaskCard
                key={task.id}
                task={task}
                projectId={projectKey}
              />
            ))}
          </SortableContext>

          {project.tasks.length === 0 && !showNewTaskForm && (
            <div className="text-center text-gray-400 mt-8">
              <p className="text-sm">No tasks yet</p>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowNewTaskForm(true)}
                className="mt-2 text-xs"
              >
                <Plus className="h-3 w-3 mr-1" />
                Add your first task
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}