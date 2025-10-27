import { create } from 'zustand'
import { TimeBlock } from '@/components/time-blocking/TimeBlockCard'

interface TimeBlockState {
  // État des time blocks
  timeBlocks: TimeBlock[]
  selectedDate: Date
  selectedTimeBlock: TimeBlock | null
  isCreating: boolean
  isEditing: boolean
  
  // Actions
  setTimeBlocks: (blocks: TimeBlock[]) => void
  addTimeBlock: (block: TimeBlock) => void
  updateTimeBlock: (id: string, updates: Partial<TimeBlock>) => void
  deleteTimeBlock: (id: string) => void
  setSelectedDate: (date: Date) => void
  setSelectedTimeBlock: (block: TimeBlock | null) => void
  setIsCreating: (creating: boolean) => void
  setIsEditing: (editing: boolean) => void
  
  // Actions métier
  startTimeBlock: (id: string) => void
  pauseTimeBlock: (id: string) => void
  completeTimeBlock: (id: string) => void
  
  // Utilitaires
  getTimeBlocksForDate: (date: Date) => TimeBlock[]
  getTodayStats: () => {
    total: number
    completed: number
    inProgress: number
    totalDuration: number
  }
}

export const useTimeBlockStore = create<TimeBlockState>((set, get) => ({
  // État initial
  timeBlocks: [],
  selectedDate: new Date(),
  selectedTimeBlock: null,
  isCreating: false,
  isEditing: false,

  // Actions de base
  setTimeBlocks: (blocks) => set({ timeBlocks: blocks }),
  
  addTimeBlock: (block) => set((state) => ({
    timeBlocks: [...state.timeBlocks, block]
  })),
  
  updateTimeBlock: (id, updates) => set((state) => ({
    timeBlocks: state.timeBlocks.map(block =>
      block.id === id ? { ...block, ...updates } : block
    )
  })),
  
  deleteTimeBlock: (id) => set((state) => ({
    timeBlocks: state.timeBlocks.filter(block => block.id !== id),
    selectedTimeBlock: state.selectedTimeBlock?.id === id ? null : state.selectedTimeBlock
  })),
  
  setSelectedDate: (date) => set({ selectedDate: date }),
  setSelectedTimeBlock: (block) => set({ selectedTimeBlock: block }),
  setIsCreating: (creating) => set({ isCreating: creating }),
  setIsEditing: (editing) => set({ isEditing: editing }),

  // Actions métier
  startTimeBlock: (id) => {
    const { updateTimeBlock } = get()
    updateTimeBlock(id, { status: 'in_progress' })
  },
  
  pauseTimeBlock: (id) => {
    const { updateTimeBlock } = get()
    updateTimeBlock(id, { status: 'pending' })
  },
  
  completeTimeBlock: (id) => {
    const { updateTimeBlock } = get()
    updateTimeBlock(id, { status: 'completed' })
  },

  // Utilitaires
  getTimeBlocksForDate: (date) => {
    const { timeBlocks } = get()
    const dateStr = date.toISOString().split('T')[0]
    
    return timeBlocks.filter(block => {
      // Supposons que startTime contient la date
      return block.startTime.includes(dateStr)
    })
  },
  
  getTodayStats: () => {
    const { getTimeBlocksForDate } = get()
    const today = new Date()
    const todayBlocks = getTimeBlocksForDate(today)
    
    return {
      total: todayBlocks.length,
      completed: todayBlocks.filter(b => b.status === 'completed').length,
      inProgress: todayBlocks.filter(b => b.status === 'in_progress').length,
      totalDuration: todayBlocks.reduce((sum, b) => sum + b.duration, 0)
    }
  }
}))

// Hook pour les actions fréquentes
export const useTimeBlockActions = () => {
  const store = useTimeBlockStore()
  
  return {
    createTimeBlock: (data: Omit<TimeBlock, 'id'>) => {
      const newBlock: TimeBlock = {
        ...data,
        id: `tb_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      }
      store.addTimeBlock(newBlock)
      return newBlock
    },
    
    duplicateTimeBlock: (id: string) => {
      const block = store.timeBlocks.find(b => b.id === id)
      if (!block) return null
      
      const duplicated: TimeBlock = {
        ...block,
        id: `tb_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        title: `${block.title} (copie)`,
        status: 'pending'
      }
      
      store.addTimeBlock(duplicated)
      return duplicated
    },
    
    moveTimeBlock: (id: string, newStartTime: string, newEndTime: string) => {
      const duration = new Date(`2000-01-01T${newEndTime}`).getTime() - 
                      new Date(`2000-01-01T${newStartTime}`).getTime()
      
      store.updateTimeBlock(id, {
        startTime: newStartTime,
        endTime: newEndTime,
        duration: Math.floor(duration / (1000 * 60)) // en minutes
      })
    }
  }
}