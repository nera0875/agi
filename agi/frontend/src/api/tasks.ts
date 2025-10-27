import type { TasksData, TaskCreate, TaskUpdate, ProjectKey } from '@/types/tasks'

const API_BASE_URL = 'http://localhost:8001/api'

export async function getTasks(): Promise<TasksData> {
  const response = await fetch(`${API_BASE_URL}/tasks`)
  if (!response.ok) {
    throw new Error(`Failed to fetch tasks: ${response.statusText}`)
  }
  return response.json()
}

export async function createTask(projectKey: ProjectKey, task: TaskCreate): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/tasks/${projectKey}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(task),
  })
  if (!response.ok) {
    throw new Error(`Failed to create task: ${response.statusText}`)
  }
  return response.json()
}

export async function updateTask(taskId: string, updates: TaskUpdate): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(updates),
  })
  if (!response.ok) {
    throw new Error(`Failed to update task: ${response.statusText}`)
  }
  return response.json()
}

export async function deleteTask(taskId: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    throw new Error(`Failed to delete task: ${response.statusText}`)
  }
  return response.json()
}

export async function moveTask(
  taskId: string,
  sourceProject: ProjectKey,
  targetProject: ProjectKey
): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/move`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      source_project: sourceProject,
      target_project: targetProject,
    }),
  })
  if (!response.ok) {
    throw new Error(`Failed to move task: ${response.statusText}`)
  }
  return response.json()
}