# ShadCN Chatbot Kit - Module de Chat Streaming pour AGI-v2

## 1. Vue d'ensemble

Ce document présente la recommandation technique pour l'intégration du module de chat streaming dans l'interface AGI-v2, basé sur `shadcn-chatbot-kit` - une solution production-ready optimisée pour les interfaces LLM modernes.

### 1.1 Contexte
L'interface AGI-v2 nécessite un composant de chat en temps réel similaire à ChatGPT, capable de :
- Streaming fluide des réponses IA
- Intégration avec le système de mémoire existant (L1/L2/L3)
- Compatibilité avec l'architecture LangChain/LangGraph
- Interface utilisateur moderne et accessible

## 2. Analyse Comparative des Solutions

### 2.1 Comparaison shadcn-chatbot-kit vs shadcn-chat

| Critère | shadcn-chatbot-kit | shadcn-chat |
|---------|-------------------|-------------|
| **Maintenance** | ✅ Active (Oct 2025) | ⚠️ Limitée |
| **Support Officiel** | ✅ Template ShadCN.io | ❌ Non officiel |
| **Streaming Natif** | ✅ Vercel AI SDK intégré | ⚠️ Configuration manuelle |
| **TypeScript** | ✅ 82.6% de couverture | ⚠️ Support partiel |
| **Fonctionnalités** | ✅ Complètes (upload, markdown, syntax) | ⚠️ Basiques |
| **Support Entreprise** | ✅ Blazity | ❌ Communauté |
| **Documentation** | ✅ Complète | ⚠️ Limitée |
| **Production Ready** | ✅ Oui | ⚠️ Développement requis |

### 2.2 Justification Technique

**shadcn-chatbot-kit** est recommandé pour les raisons suivantes :

1. **Streaming Ultra-Fluide** : Intégration native avec Vercel AI SDK pour un streaming word-by-word optimisé
2. **Zero-Configuration** : Prêt à l'emploi avec notre stack React + Vite + ShadCN/UI + Tailwind
3. **Maintenance Active** : Développement continu et support des dernières versions
4. **Type-Safety** : Couverture TypeScript élevée pour une meilleure DX
5. **Composants Complets** : Tous les éléments nécessaires pour une interface chat moderne

## 3. Architecture des Composants

### 3.1 Composants Disponibles

```typescript
// Composants principaux
import {
  Chat,              // Container principal du chat
  ChatMessage,       // Affichage des messages
  MessageInput,      // Saisie utilisateur
  MarkdownRenderer,  // Rendu markdown des réponses
  AudioVisualizer,   // Visualisation audio (optionnel)
  FilePreview,       // Prévisualisation fichiers
  PromptSuggestions  // Suggestions de prompts
} from 'shadcn-chatbot-kit'
```

### 3.2 Intégration avec Notre Stack

```typescript
// Configuration type-safe avec notre architecture
interface AGIChatConfig {
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
  theme: 'dark' | 'light'
  animations: boolean
  fileUpload: boolean
}
```

## 4. Plan d'Installation

### 4.1 Dépendances Requises

```bash
# AI SDK pour le streaming
npm install ai @ai-sdk/openai @ai-sdk/anthropic

# ShadCN Chatbot Kit
npm install shadcn-chatbot-kit

# Dépendances additionnelles
npm install @radix-ui/react-scroll-area
npm install lucide-react
```

### 4.2 Configuration ShadCN/UI

```bash
# Ajouter les composants base si pas déjà fait
npx shadcn-ui@latest add button
npx shadcn-ui@latest add input
npx shadcn-ui@latest add scroll-area
npx shadcn-ui@latest add avatar
```

## 5. Implémentation

### 5.1 Interface Chat Basique

```typescript
// src/components/AGIChat.tsx
import React from 'react'
import { Chat, ChatMessage, MessageInput } from 'shadcn-chatbot-kit'
import { useChat } from 'ai/react'

interface AGIChatProps {
  memoryContext?: {
    L1: any[]  // Contexte immédiat
    L2: any[]  // Mémoire étendue  
    L3: any[]  // Mémoire long terme
  }
}

export function AGIChat({ memoryContext }: AGIChatProps) {
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat({
    api: '/api/chat',
    initialMessages: [],
    body: {
      memoryContext // Envoi du contexte mémoire
    }
  })

  return (
    <div className="h-screen flex flex-col">
      <Chat className="flex-1">
        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            message={message}
            isLoading={isLoading && message.role === 'assistant'}
          />
        ))}
      </Chat>
      
      <MessageInput
        input={input}
        handleInputChange={handleInputChange}
        handleSubmit={handleSubmit}
        isLoading={isLoading}
        placeholder="Posez votre question à l'AGI..."
      />
    </div>
  )
}
```

### 5.2 Intégration Backend LangChain/LangGraph

```typescript
// backend/api/chat/route.ts
import { LangChainStream, StreamingTextResponse } from 'ai'
import { ChatOpenAI } from 'langchain/chat_models/openai'
import { MemoryManager } from '../services/memory'

export async function POST(req: Request) {
  const { messages, memoryContext } = await req.json()
  
  // Initialisation du modèle avec streaming
  const model = new ChatOpenAI({
    modelName: 'gpt-4',
    streaming: true,
    temperature: 0.7
  })
  
  // Gestion de la mémoire L1/L2/L3
  const memoryManager = new MemoryManager()
  const enrichedContext = await memoryManager.enrichContext({
    messages,
    L1: memoryContext?.L1 || [],
    L2: memoryContext?.L2 || [],
    L3: memoryContext?.L3 || []
  })
  
  // Configuration du streaming
  const { stream, handlers } = LangChainStream()
  
  // Exécution avec LangGraph
  model.call(enrichedContext, {}, [handlers]).catch(console.error)
  
  return new StreamingTextResponse(stream)
}
```

## 6. Configuration Système de Mémoire

### 6.1 Hooks de Mémoire Personnalisés

```typescript
// src/hooks/useAGIMemory.ts
import { useState, useEffect } from 'react'

interface MemoryLevels {
  L1: any[]  // Contexte conversation actuelle
  L2: any[]  // Historique session étendue
  L3: any[]  // Mémoire persistante utilisateur
}

export function useAGIMemory(userId?: string) {
  const [memory, setMemory] = useState<MemoryLevels>({
    L1: [],
    L2: [],
    L3: []
  })
  
  // Chargement mémoire L3 (PostgreSQL/Neo4j)
  useEffect(() => {
    if (userId) {
      loadLongTermMemory(userId).then(data => {
        setMemory(prev => ({ ...prev, L3: data }))
      })
    }
  }, [userId])
  
  // Mise à jour mémoire L1 (contexte immédiat)
  const updateL1 = (newContext: any[]) => {
    setMemory(prev => ({ ...prev, L1: newContext }))
  }
  
  // Absorption vers L2 (mémoire étendue)
  const absorbToL2 = (contextData: any) => {
    setMemory(prev => ({
      ...prev,
      L2: [...prev.L2, contextData].slice(-50) // Limite 50 éléments
    }))
  }
  
  return { memory, updateL1, absorbToL2 }
}
```

### 6.2 Intégration Complète

```typescript
// src/components/AGIChatContainer.tsx
import { AGIChat } from './AGIChat'
import { useAGIMemory } from '../hooks/useAGIMemory'
import { useAuth } from '../hooks/useAuth'

export function AGIChatContainer() {
  const { user } = useAuth()
  const { memory, updateL1, absorbToL2 } = useAGIMemory(user?.id)
  
  return (
    <div className="w-full h-full">
      <AGIChat 
        memoryContext={memory}
        onContextUpdate={updateL1}
        onMemoryAbsorption={absorbToL2}
      />
    </div>
  )
}
```

## 7. Configuration Avancée

### 7.1 Thématisation

```typescript
// src/styles/chat-theme.css
.chat-container {
  @apply bg-background text-foreground;
}

.chat-message-user {
  @apply bg-primary text-primary-foreground;
}

.chat-message-assistant {
  @apply bg-muted text-muted-foreground;
}

.chat-input {
  @apply border-input bg-background;
}
```

### 7.2 Animations Framer Motion

```typescript
// Configuration animations pour les messages
const messageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 }
}
```

## 8. Tests et Validation

### 8.1 Tests de Streaming

```typescript
// tests/chat-streaming.test.ts
describe('AGI Chat Streaming', () => {
  test('should stream responses word by word', async () => {
    // Test du streaming en temps réel
  })
  
  test('should maintain memory context', async () => {
    // Test de la persistance mémoire
  })
})
```

### 8.2 Tests d'Intégration

```typescript
// tests/memory-integration.test.ts
describe('Memory System Integration', () => {
  test('should load L3 memory on user login', async () => {
    // Test chargement mémoire long terme
  })
  
  test('should absorb L1 to L2 correctly', async () => {
    // Test absorption mémoire
  })
})
```

## 9. Déploiement et Performance

### 9.1 Optimisations

- **Code Splitting** : Chargement lazy des composants chat
- **Memoization** : React.memo pour les messages
- **Virtualization** : Liste virtualisée pour l'historique long
- **Debouncing** : Optimisation des appels API

### 9.2 Monitoring

```typescript
// Métriques de performance
const chatMetrics = {
  streamingLatency: 'ms',
  memoryLoadTime: 'ms',
  messageRenderTime: 'ms',
  errorRate: '%'
}
```

## 10. Roadmap d'Implémentation

### Phase 1 : Installation et Configuration (1-2 jours)
- [ ] Installation des dépendances
- [ ] Configuration ShadCN/UI
- [ ] Setup composants de base

### Phase 2 : Interface Chat (2-3 jours)
- [ ] Implémentation AGIChat component
- [ ] Configuration streaming Vercel AI SDK
- [ ] Tests interface utilisateur

### Phase 3 : Intégration Backend (3-4 jours)
- [ ] API route pour streaming
- [ ] Connexion LangChain/LangGraph
- [ ] Tests end-to-end

### Phase 4 : Système Mémoire (2-3 jours)
- [ ] Hooks mémoire personnalisés
- [ ] Intégration PostgreSQL/Neo4j
- [ ] Tests de persistance

### Phase 5 : Optimisation et Tests (2-3 jours)
- [ ] Performance tuning
- [ ] Tests complets
- [ ] Documentation utilisateur

## 11. Conclusion

Le module `shadcn-chatbot-kit` représente la solution optimale pour l'interface de chat streaming de l'AGI-v2. Sa compatibilité native avec notre stack technique, son support du streaming avancé, et son intégration seamless avec le système de mémoire en font le choix technique idéal pour une implémentation rapide et robuste.

**Prochaines étapes** : Validation de l'architecture proposée et début de l'implémentation selon le roadmap défini.