import React, { useState, useCallback, useRef, useEffect } from 'react'
import { useChat } from 'ai/react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Card, CardContent } from '@/components/ui/card'
import { Send, Bot, User, Loader2 } from 'lucide-react'

interface AGIChatProps {
  userId?: string
  memoryContext?: {
    L1: any[]  // Contexte immédiat
    L2: any[]  // Mémoire étendue  
    L3: any[]  // Mémoire long terme
  }
  onContextUpdate?: (context: any[]) => void
  onMemoryAbsorption?: (data: any) => void
  apiEndpoint?: string
  className?: string
}

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export function AGIChat({ 
  userId = 'default-user',
  memoryContext,
  onContextUpdate,
  onMemoryAbsorption,
  apiEndpoint = '/api/chat',
  className 
}: AGIChatProps) {
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const [isTyping, setIsTyping] = useState(false)

  const { messages, input, handleInputChange, handleSubmit, isLoading, error } = useChat({
    api: apiEndpoint,
    initialMessages: [],
    body: {
      memoryContext,
      userId
    },
    onResponse: (response) => {
      setIsTyping(false)
    },
    onFinish: (message) => {
      // Absorption vers L2 après chaque réponse
      if (onMemoryAbsorption) {
        onMemoryAbsorption({
          type: 'conversation',
          content: message.content,
          timestamp: new Date(),
          userId
        })
      }
    }
  })

  // Auto-scroll vers le bas
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]')
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight
      }
    }
  }, [messages])

  // Mise à jour du contexte L1 à chaque nouveau message
  useEffect(() => {
    if (onContextUpdate && messages.length > 0) {
      const recentMessages = messages.slice(-5) // Garder les 5 derniers messages
      onContextUpdate(recentMessages)
    }
  }, [messages, onContextUpdate])

  const onSubmit = useCallback((e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (input.trim()) {
      setIsTyping(true)
      handleSubmit(e)
    }
  }, [input, handleSubmit])

  const formatTimestamp = (timestamp: Date) => {
    return new Intl.DateTimeFormat('fr-FR', {
      hour: '2-digit',
      minute: '2-digit'
    }).format(timestamp)
  }

  return (
    <div className={cn('flex flex-col h-full bg-background', className)}>
      {/* Zone de messages */}
      <ScrollArea ref={scrollAreaRef} className="flex-1 p-4">
        <div className="space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-64 text-center">
              <Bot className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">Bienvenue dans AGI Chat</h3>
              <p className="text-muted-foreground max-w-md">
                Posez vos questions à l'AGI. Je peux vous aider avec la planification, 
                l'organisation et l'optimisation de votre temps.
              </p>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                'flex gap-3 max-w-4xl',
                message.role === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'
              )}
            >
              <Avatar className="h-8 w-8 shrink-0">
                <AvatarFallback>
                  {message.role === 'user' ? (
                    <User className="h-4 w-4" />
                  ) : (
                    <Bot className="h-4 w-4" />
                  )}
                </AvatarFallback>
              </Avatar>

              <Card className={cn(
                'max-w-[80%]',
                message.role === 'user' 
                  ? 'bg-primary text-primary-foreground' 
                  : 'bg-muted'
              )}>
                <CardContent className="p-3">
                  <div className="prose prose-sm max-w-none">
                    <p className="whitespace-pre-wrap break-words m-0">
                      {message.content}
                    </p>
                  </div>
                  <div className={cn(
                    'text-xs mt-2 opacity-70',
                    message.role === 'user' 
                      ? 'text-primary-foreground' 
                      : 'text-muted-foreground'
                  )}>
                    {formatTimestamp(new Date(message.createdAt || Date.now()))}
                  </div>
                </CardContent>
              </Card>
            </div>
          ))}

          {/* Indicateur de frappe */}
          {(isLoading || isTyping) && (
            <div className="flex gap-3 max-w-4xl mr-auto">
              <Avatar className="h-8 w-8 shrink-0">
                <AvatarFallback>
                  <Bot className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
              <Card className="bg-muted">
                <CardContent className="p-3">
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm text-muted-foreground">
                      L'AGI réfléchit...
                    </span>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Zone de saisie */}
      <div className="border-t bg-muted/30 p-4">
        <form onSubmit={onSubmit} className="flex gap-2">
          <Input
            value={input}
            onChange={handleInputChange}
            placeholder="Posez votre question à l'AGI..."
            disabled={isLoading}
            className="flex-1"
            autoFocus
          />
          <Button 
            type="submit" 
            disabled={isLoading || !input.trim()}
            size="icon"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>

        {/* Affichage des erreurs */}
        {error && (
          <div className="mt-2 p-2 bg-destructive/10 border border-destructive/20 rounded text-sm text-destructive">
            Erreur: {error.message}
          </div>
        )}

        {/* Statistiques de mémoire (mode développement) */}
        {process.env.NODE_ENV === 'development' && memoryContext && (
          <div className="mt-2 text-xs text-muted-foreground">
            Contexte: L1({memoryContext.L1.length}) L2({memoryContext.L2.length}) L3({memoryContext.L3.length})
          </div>
        )}
      </div>
    </div>
  )
}