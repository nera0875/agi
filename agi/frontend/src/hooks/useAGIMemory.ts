import { useState, useEffect, useCallback } from 'react'

interface MemoryLevels {
  L1: any[]  // Contexte conversation actuelle
  L2: any[]  // Historique session étendue
  L3: any[]  // Mémoire persistante utilisateur
}

interface MemoryStats {
  L1Count: number
  L2Count: number
  L3Count: number
  totalSize: number
}

export function useAGIMemory(userId?: string) {
  const [memory, setMemory] = useState<MemoryLevels>({
    L1: [],
    L2: [],
    L3: []
  })

  // Chargement mémoire L3 (PostgreSQL/Neo4j)
  const loadLongTermMemory = useCallback(async (userId: string) => {
    try {
      const response = await fetch(`/api/memory/L3/${userId}`)
      
      // Vérifier si la réponse est du JSON valide
      const contentType = response.headers.get('content-type')
      if (!contentType || !contentType.includes('application/json')) {
        console.warn('API backend non disponible, utilisation de données mock pour L3')
        // Mock data temporaire en attendant le backend
        setMemory(prev => ({ ...prev, L3: [] }))
        return
      }
      
      if (response.ok) {
        const data = await response.json()
        setMemory(prev => ({ ...prev, L3: data }))
      } else {
        console.warn(`Erreur API L3: ${response.status} - ${response.statusText}`)
        setMemory(prev => ({ ...prev, L3: [] }))
      }
    } catch (error) {
      console.warn('Backend non disponible, utilisation de données mock pour L3:', error)
      // Utiliser des données mock en cas d'erreur
      setMemory(prev => ({ ...prev, L3: [] }))
    }
  }, [])

  useEffect(() => {
    if (userId) {
      loadLongTermMemory(userId)
    }
  }, [userId, loadLongTermMemory])

  // Mise à jour mémoire L1 (contexte immédiat)
  const updateL1 = useCallback((newContext: any[]) => {
    setMemory(prev => ({ ...prev, L1: newContext }))
  }, [])

  // Absorption vers L2 (mémoire étendue)
  const absorbToL2 = useCallback((contextData: any) => {
    setMemory(prev => ({
      ...prev,
      L2: [...prev.L2, contextData].slice(-50) // Limite 50 éléments
    }))
  }, [])

  // Nettoyage de la mémoire
  const clearMemory = useCallback((level?: 'L1' | 'L2' | 'L3') => {
    if (level) {
      setMemory(prev => ({ ...prev, [level]: [] }))
    } else {
      setMemory({ L1: [], L2: [], L3: [] })
    }
  }, [])

  // Statistiques de mémoire
  const getMemoryStats = useCallback((): MemoryStats => {
    const totalSize = JSON.stringify(memory).length
    return {
      L1Count: memory.L1.length,
      L2Count: memory.L2.length,
      L3Count: memory.L3.length,
      totalSize
    }
  }, [memory])

  return { 
    memory, 
    updateL1, 
    absorbToL2, 
    clearMemory, 
    getMemoryStats,
    loadLongTermMemory 
  }
}