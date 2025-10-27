import React, { useState, useCallback, useEffect } from 'react'
import { AGIChat } from './AGIChat'
import { useAGIMemory } from '@/hooks/useAGIMemory'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Settings, RotateCcw, Database, User } from 'lucide-react'

interface AGIChatContainerProps {
  userId?: string
  className?: string
  showMemoryStats?: boolean
  showControls?: boolean
  apiEndpoint?: string
}

interface UserSession {
  id: string
  name?: string
  avatar?: string
}

export function AGIChatContainer({
  userId = 'default-user',
  className,
  showMemoryStats = false,
  showControls = true,
  apiEndpoint = '/api/chat'
}: AGIChatContainerProps) {
  const [currentUser] = useState<UserSession>({
    id: userId,
    name: 'Utilisateur AGI',
    avatar: undefined
  })

  const { 
    memory, 
    updateL1, 
    absorbToL2, 
    clearMemory, 
    getMemoryStats,
    loadLongTermMemory 
  } = useAGIMemory(currentUser.id)

  const [isMemoryLoading, setIsMemoryLoading] = useState(false)

  // Gestion de la mise à jour du contexte L1
  const handleContextUpdate = useCallback((newContext: any[]) => {
    updateL1(newContext)
  }, [updateL1])

  // Gestion de l'absorption vers L2
  const handleMemoryAbsorption = useCallback((contextData: any) => {
    absorbToL2(contextData)
  }, [absorbToL2])

  // Rechargement de la mémoire L3
  const handleReloadLongTermMemory = useCallback(async () => {
    setIsMemoryLoading(true)
    try {
      await loadLongTermMemory(currentUser.id)
    } catch (error) {
      console.error('Erreur lors du rechargement de la mémoire L3:', error)
    } finally {
      setIsMemoryLoading(false)
    }
  }, [loadLongTermMemory, currentUser.id])

  // Nettoyage de la mémoire avec confirmation
  const handleClearMemory = useCallback((level?: 'L1' | 'L2' | 'L3') => {
    const confirmMessage = level 
      ? `Êtes-vous sûr de vouloir effacer la mémoire ${level} ?`
      : 'Êtes-vous sûr de vouloir effacer toute la mémoire ?'
    
    if (window.confirm(confirmMessage)) {
      clearMemory(level)
    }
  }, [clearMemory])

  // Statistiques de mémoire
  const memoryStats = getMemoryStats()

  return (
    <div className={cn('flex flex-col h-full bg-background', className)}>
      {/* En-tête avec informations utilisateur et contrôles */}
      {showControls && (
        <div className="border-b bg-muted/30 p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <User className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">{currentUser.name}</span>
              </div>
              {showMemoryStats && (
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Database className="h-3 w-3" />
                  <span>
                    L1: {memoryStats.L1Count} | L2: {memoryStats.L2Count} | L3: {memoryStats.L3Count}
                  </span>
                  <span className="text-xs">
                    ({Math.round(memoryStats.totalSize / 1024)}KB)
                  </span>
                </div>
              )}
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleReloadLongTermMemory}
                disabled={isMemoryLoading}
                className="h-8 px-2"
              >
                <RotateCcw className={cn('h-3 w-3', isMemoryLoading && 'animate-spin')} />
              </Button>
              
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleClearMemory()}
                className="h-8 px-2"
              >
                <Settings className="h-3 w-3" />
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Panneau de statistiques détaillées (mode développement) */}
      {showMemoryStats && process.env.NODE_ENV === 'development' && (
        <div className="border-b bg-muted/20 p-2">
          <div className="grid grid-cols-3 gap-4 text-xs">
            <div className="space-y-1">
              <div className="font-medium text-muted-foreground">Mémoire L1 (Immédiate)</div>
              <div className="flex justify-between">
                <span>Éléments:</span>
                <span>{memoryStats.L1Count}</span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleClearMemory('L1')}
                className="h-6 w-full text-xs"
              >
                Effacer L1
              </Button>
            </div>
            
            <div className="space-y-1">
              <div className="font-medium text-muted-foreground">Mémoire L2 (Session)</div>
              <div className="flex justify-between">
                <span>Éléments:</span>
                <span>{memoryStats.L2Count}</span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleClearMemory('L2')}
                className="h-6 w-full text-xs"
              >
                Effacer L2
              </Button>
            </div>
            
            <div className="space-y-1">
              <div className="font-medium text-muted-foreground">Mémoire L3 (Long terme)</div>
              <div className="flex justify-between">
                <span>Éléments:</span>
                <span>{memoryStats.L3Count}</span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleClearMemory('L3')}
                className="h-6 w-full text-xs"
              >
                Effacer L3
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Interface de chat principale */}
      <div className="flex-1">
        <AGIChat
          userId={currentUser.id}
          memoryContext={memory}
          onContextUpdate={handleContextUpdate}
          onMemoryAbsorption={handleMemoryAbsorption}
          apiEndpoint={apiEndpoint}
          className="h-full"
        />
      </div>

      {/* Indicateur de statut de la mémoire */}
      {isMemoryLoading && (
        <div className="border-t bg-muted/30 p-2">
          <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
            <div className="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
            <span>Synchronisation de la mémoire long terme...</span>
          </div>
        </div>
      )}
    </div>
  )
}

// Composant wrapper avec gestion d'erreur et fallback
interface AGIChatContainerWrapperProps extends AGIChatContainerProps {
  fallback?: React.ReactNode
  onError?: (error: Error) => void
}

export function AGIChatContainerWrapper({ 
  fallback, 
  onError,
  ...props 
}: AGIChatContainerWrapperProps) {
  const [hasError, setHasError] = useState(false)

  useEffect(() => {
    const handleError = (error: ErrorEvent) => {
      setHasError(true)
      if (onError) {
        onError(new Error(error.message))
      }
    }

    window.addEventListener('error', handleError)
    return () => window.removeEventListener('error', handleError)
  }, [onError])

  if (hasError) {
    return (
      <div className="flex items-center justify-center h-full p-8">
        <div className="text-center space-y-4">
          <div className="text-lg font-medium text-destructive">
            Erreur lors du chargement du chat
          </div>
          <Button
            variant="outline"
            onClick={() => {
              setHasError(false)
              window.location.reload()
            }}
          >
            Recharger
          </Button>
        </div>
      </div>
    )
  }

  return (
    <React.Suspense 
      fallback={
        fallback || (
          <div className="flex items-center justify-center h-full">
            <div className="text-center space-y-4">
              <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
              <div className="text-sm text-muted-foreground">
                Initialisation du chat AGI...
              </div>
            </div>
          </div>
        )
      }
    >
      <AGIChatContainer {...props} />
    </React.Suspense>
  )
}

export default AGIChatContainer