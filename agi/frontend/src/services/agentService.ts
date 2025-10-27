// Service pour l'intégration avec les agents LangGraph
export interface AgentExecutionRequest {
  agent_type: 'consolidator' | 'time_blocking' | 'task_manager' | 'memory_manager'
  input_data: any
  stream?: boolean
  user_id?: string
}

export interface AgentExecutionResponse {
  success: boolean
  data?: any
  error?: string
  stream_id?: string
}

export interface TimeBlockRequest {
  date: string
  tasks: Array<{
    title: string
    duration: number
    priority: 'high' | 'medium' | 'low'
    category?: string
  }>
  preferences?: {
    work_hours_start: string
    work_hours_end: string
    break_duration: number
    focus_blocks: boolean
  }
}

export interface MemoryOperation {
  operation: 'load' | 'save' | 'clear' | 'absorb'
  level: 'L1' | 'L2' | 'L3'
  data?: any
  user_id: string
}

class AgentService {
  private baseUrl: string

  constructor() {
    this.baseUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'
  }

  // Exécution générique d'agent
  async executeAgent(request: AgentExecutionRequest): Promise<AgentExecutionResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/agents/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request)
      })

      if (!response.ok) {
        throw new Error(`Agent execution failed: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Agent execution error:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    }
  }

  // Agent Consolidator pour le chat
  async chatWithConsolidator(
    messages: any[], 
    memoryContext?: any, 
    userId?: string
  ): Promise<AgentExecutionResponse> {
    return this.executeAgent({
      agent_type: 'consolidator',
      input_data: {
        messages,
        memory_context: memoryContext,
        user_id: userId
      },
      stream: false,
      user_id: userId
    })
  }

  // Agent Time Blocking
  async generateTimeBlocks(request: TimeBlockRequest, userId?: string): Promise<AgentExecutionResponse> {
    return this.executeAgent({
      agent_type: 'time_blocking',
      input_data: request,
      user_id: userId
    })
  }

  // Agent Task Manager
  async manageTasks(
    operation: 'create' | 'update' | 'delete' | 'list',
    taskData?: any,
    userId?: string
  ): Promise<AgentExecutionResponse> {
    return this.executeAgent({
      agent_type: 'task_manager',
      input_data: {
        operation,
        task_data: taskData
      },
      user_id: userId
    })
  }

  // Agent Memory Manager
  async manageMemory(operation: MemoryOperation): Promise<AgentExecutionResponse> {
    return this.executeAgent({
      agent_type: 'memory_manager',
      input_data: operation,
      user_id: operation.user_id
    })
  }

  // Stream chat avec Server-Sent Events
  async streamChat(
    messages: any[],
    memoryContext?: any,
    userId?: string,
    onMessage?: (chunk: string) => void,
    onError?: (error: Error) => void,
    onComplete?: () => void
  ): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/agents/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agent_type: 'consolidator',
          input_data: {
            messages,
            memory_context: memoryContext,
            user_id: userId
          },
          stream: true
        })
      })

      if (!response.ok) {
        throw new Error(`Stream failed: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No response body reader available')
      }

      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          onComplete?.()
          break
        }

        const chunk = decoder.decode(value, { stream: true })
        onMessage?.(chunk)
      }

    } catch (error) {
      console.error('Stream chat error:', error)
      onError?.(error instanceof Error ? error : new Error('Unknown streaming error'))
    }
  }

  // Vérification de la santé du backend
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`)
      return response.ok
    } catch {
      return false
    }
  }

  // Récupération des agents disponibles
  async getAvailableAgents(): Promise<string[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/agents/list`)
      if (!response.ok) return []
      
      const data = await response.json()
      return data.agents || []
    } catch {
      return []
    }
  }
}

export const agentService = new AgentService()
export default agentService