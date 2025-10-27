/**
 * Types TypeScript pour le système de chat AGI et la gestion mémoire
 */

// Types de base pour les messages
export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
  metadata?: Record<string, any>
}

// Types pour le système de mémoire L1/L2/L3
export interface MemoryLevels {
  L1: MemoryContext[]  // Contexte conversation actuelle
  L2: MemoryContext[]  // Historique session étendue
  L3: MemoryContext[]  // Mémoire persistante utilisateur
}

export interface MemoryContext {
  messages: Message[]
  metadata?: Record<string, any>
  timestamp: number
  userId?: string
  sessionId?: string
  conversationId?: string
}

// Configuration du chat AGI
export interface AGIChatConfig {
  // Intégration LangChain/LangGraph
  backendEndpoint: string
  streamingEnabled: boolean
  
  // Système de mémoire
  memoryLevels: {
    L1: 'immediate'    // Contexte immédiat
    L2: 'extended'     // Mémoire étendue
    L3: 'long_term'    // Mémoire long terme
  }
  
  // Configuration UI
  theme: 'dark' | 'light' | 'system'
  animations: boolean
  fileUpload: boolean
  voiceInput: boolean
  
  // Limites et performance
  maxL1Messages: number
  maxL2Contexts: number
  maxL3Contexts: number
  memoryCleanupThreshold: number // en KB
}

// Types pour les hooks de mémoire
export interface UseAGIMemoryReturn {
  memory: MemoryLevels
  updateL1: (newContext: Message[]) => void
  absorbToL2: (contextData: MemoryContext) => void
  loadLongTermMemory: (userId: string) => Promise<void>
  clearMemory: (level?: 'L1' | 'L2' | 'L3') => void
  getMemoryStats: () => MemoryStats
}

export interface MemoryStats {
  L1Count: number
  L2Count: number
  L3Count: number
  totalSize: number
  lastUpdate: number
}

// Types pour les composants de chat
export interface ChatProps {
  messages: Message[]
  input: string
  handleInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  handleSubmit: (e: React.FormEvent<HTMLFormElement>) => void
  isGenerating?: boolean
  stop?: () => void
  className?: string
}

export interface ChatMessageProps {
  message: Message
  isLoading?: boolean
  className?: string
  showActions?: boolean
  onCopy?: (content: string) => void
  onRate?: (messageId: string, rating: 'positive' | 'negative') => void
}

export interface MessageInputProps {
  input: string
  handleInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  handleSubmit: (e: React.FormEvent<HTMLFormElement>) => void
  isLoading?: boolean
  placeholder?: string
  className?: string
  maxLength?: number
  showFileUpload?: boolean
  showVoiceInput?: boolean
}

// Types pour les suggestions de prompts
export interface PromptSuggestion {
  id: string
  text: string
  category?: string
  icon?: string
}

export interface PromptSuggestionsProps {
  suggestions: PromptSuggestion[] | string[]
  onSuggestionClick: (suggestion: string) => void
  className?: string
  maxVisible?: number
}

// Types pour le conteneur de chat
export interface AGIChatContainerProps {
  userId?: string
  className?: string
  showMemoryStats?: boolean
  showControls?: boolean
  apiEndpoint?: string
  config?: Partial<AGIChatConfig>
}

// Types pour la session utilisateur
export interface UserSession {
  id: string
  name?: string
  avatar?: string
  preferences?: UserPreferences
  memorySettings?: MemorySettings
}

export interface UserPreferences {
  theme: 'dark' | 'light' | 'system'
  language: string
  notifications: boolean
  autoSave: boolean
  streamingSpeed: 'slow' | 'normal' | 'fast'
}

export interface MemorySettings {
  enableL1: boolean
  enableL2: boolean
  enableL3: boolean
  autoCleanup: boolean
  retentionDays: number
  maxStorageSize: number // en MB
}

// Types pour les événements de chat
export interface ChatEvent {
  type: 'message_sent' | 'message_received' | 'memory_updated' | 'error'
  timestamp: number
  data: any
  userId?: string
  sessionId?: string
}

// Types pour les erreurs
export interface ChatError {
  code: string
  message: string
  details?: any
  timestamp: number
  recoverable: boolean
}

// Types pour l'API backend
export interface ChatRequest {
  messages: Message[]
  memoryContext?: {
    L1: MemoryContext[]
    L2: MemoryContext[]
    L3: MemoryContext[]
  }
  config?: Partial<AGIChatConfig>
  userId?: string
  sessionId?: string
}

export interface ChatResponse {
  message: Message
  memoryUpdates?: Partial<MemoryLevels>
  suggestions?: PromptSuggestion[]
  metadata?: Record<string, any>
}

// Types pour le streaming
export interface StreamingResponse {
  id: string
  content: string
  isComplete: boolean
  metadata?: Record<string, any>
}

// Types pour les outils et intégrations
export interface ToolCall {
  id: string
  name: string
  parameters: Record<string, any>
  status: 'pending' | 'running' | 'completed' | 'failed'
  result?: any
  error?: string
}

export interface ToolCallVisualization {
  toolCall: ToolCall
  showProgress: boolean
  allowCancel: boolean
  onCancel?: (toolCallId: string) => void
}

// Types pour les attachements
export interface Attachment {
  id: string
  name: string
  type: string
  size: number
  url?: string
  content?: string
  preview?: string
}

export interface FileUploadProps {
  onFileSelect: (files: File[]) => void
  acceptedTypes?: string[]
  maxSize?: number
  maxFiles?: number
  className?: string
}

// Types pour l'export/import de conversations
export interface ConversationExport {
  id: string
  title: string
  messages: Message[]
  memory: MemoryLevels
  metadata: {
    createdAt: number
    updatedAt: number
    userId: string
    version: string
  }
}

// Types pour les métriques et analytics
export interface ChatMetrics {
  messagesCount: number
  averageResponseTime: number
  memoryUsage: number
  errorRate: number
  userSatisfaction?: number
  sessionDuration: number
}

// Types pour les thèmes personnalisés
export interface ChatTheme {
  name: string
  colors: {
    primary: string
    secondary: string
    background: string
    foreground: string
    muted: string
    accent: string
    destructive: string
  }
  fonts: {
    sans: string
    mono: string
  }
  spacing: Record<string, string>
  borderRadius: Record<string, string>
}

// Constantes par défaut
export const DEFAULT_AGI_CONFIG: AGIChatConfig = {
  backendEndpoint: '/api/chat',
  streamingEnabled: true,
  memoryLevels: {
    L1: 'immediate',
    L2: 'extended',
    L3: 'long_term'
  },
  theme: 'system',
  animations: true,
  fileUpload: true,
  voiceInput: false,
  maxL1Messages: 20,
  maxL2Contexts: 50,
  maxL3Contexts: 100,
  memoryCleanupThreshold: 500 // 500KB
}

export const DEFAULT_PROMPT_SUGGESTIONS: string[] = [
  "Explique-moi ce concept simplement",
  "Aide-moi à résoudre ce problème",
  "Quelles sont les meilleures pratiques ?",
  "Peux-tu me donner des exemples ?",
  "Comment puis-je améliorer cela ?"
]