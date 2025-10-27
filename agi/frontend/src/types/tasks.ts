export interface ChecklistItem {
  id: string
  title: string
  completed: boolean
}

export interface Subtask {
  id: string
  title: string
  completed: boolean
}

export interface Task {
  id: string
  title: string
  completed: boolean
  priority: 0 | 1 | 3 | 5
  subtasks: Subtask[]
  items: ChecklistItem[]
}

export interface Project {
  id: string
  name: string
  color: string
  view_mode: 'list' | 'kanban'
  tasks: Task[]
}

export interface TasksData {
  version: string
  last_update: string
  projects: {
    GOALS: Project
    CODE: Project
    PENTEST: Project
    BRAIN: Project
  }
}

export type ProjectKey = 'GOALS' | 'CODE' | 'PENTEST' | 'BRAIN'

export interface TaskCreate {
  title: string
  priority: number
}

export interface TaskUpdate {
  title?: string
  completed?: boolean
  priority?: number
  subtasks?: Subtask[]
  items?: ChecklistItem[]
}