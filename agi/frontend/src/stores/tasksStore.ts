import { create } from 'zustand'
import * as api from '../api/tasks'
import type { TasksData, Task, TaskCreate, TaskUpdate, ProjectKey } from '../types/tasks'

interface TasksState {
  data: TasksData | null
  loading: boolean
  error: string | null

  // Actions
  fetchTasks: () => Promise<void>
  createTask: (projectId: ProjectKey, task: TaskCreate) => Promise<void>
  updateTask: (projectId: ProjectKey, taskId: string, updates: TaskUpdate) => Promise<void>
  deleteTask: (projectId: ProjectKey, taskId: string) => Promise<void>
  moveTask: (taskId: string, fromProject: ProjectKey, toProject: ProjectKey) => Promise<void>
  
  // UI state
  setError: (error: string | null) => void
  clearError: () => void
}

export const useTasksStore = create<TasksState>((set, get) => ({
  data: null,
  loading: false,
  error: null,

  fetchTasks: async () => {
    set({ loading: true, error: null })
    try {
      const data = await api.getTasks()
      set({ data, loading: false })
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch tasks', 
        loading: false 
      })
    }
  },

  createTask: async (projectId, task) => {
    set({ error: null })
    try {
      await api.createTask(projectId, task)
      await get().fetchTasks()
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to create task' })
    }
  },

  updateTask: async (projectId, taskId, updates) => {
    set({ error: null })
    try {
      await api.updateTask(projectId, taskId, updates)
      await get().fetchTasks()
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to update task' })
    }
  },

  deleteTask: async (projectId, taskId) => {
    set({ error: null })
    try {
      await api.deleteTask(projectId, taskId)
      await get().fetchTasks()
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to delete task' })
    }
  },

  moveTask: async (taskId, fromProject, toProject) => {
    set({ error: null })
    try {
      await api.moveTask(fromProject, taskId, toProject)
      await get().fetchTasks()
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to move task' })
    }
  },

  setError: (error) => set({ error }),
  clearError: () => set({ error: null })
}))