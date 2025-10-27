import React, { useRef, useEffect } from 'react'
import { cn } from '../../lib/utils'
import { Button } from './button'
import { Input } from './input'
import { ScrollArea } from './scroll-area'
import { Avatar, AvatarFallback } from './avatar'
import { Send, Copy, ThumbsUp, ThumbsDown, User, Bot } from 'lucide-react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp?: number
}

interface ChatProps {
  messages: Message[]
  input: string
  handleInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  handleSubmit: (e: React.FormEvent<HTMLFormElement>) => void
  isGenerating?: boolean
  stop?: () => void
  className?: string
}

interface ChatMessageProps {
  message: Message
  isLoading?: boolean
  className?: string
}

interface MessageInputProps {
  input: string
  handleInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  handleSubmit: (e: React.FormEvent<HTMLFormElement>) => void
  isLoading?: boolean
  placeholder?: string
  className?: string
}

// Composant principal Chat
export function Chat({
  messages,
  input,
  handleInputChange,
  handleSubmit,
  isGenerating = false,
  stop,
  className
}: ChatProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  return (
    <div className={cn('flex flex-col h-full', className)}>
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((message) => (
            <ChatMessage
              key={message.id}
              message={message}
              isLoading={isGenerating && message.role === 'assistant' && message === messages[messages.length - 1]}
            />
          ))}
          {isGenerating && messages[messages.length - 1]?.role === 'assistant' && (
            <div className="flex justify-center">
              <Button
                variant="outline"
                size="sm"
                onClick={stop}
                className="text-xs"
              >
                Arrêter la génération
              </Button>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>
      
      <div className="border-t p-4">
        <MessageInput
          input={input}
          handleInputChange={handleInputChange}
          handleSubmit={handleSubmit}
          isLoading={isGenerating}
          placeholder="Posez votre question à l'AGI..."
        />
      </div>
    </div>
  )
}

// Composant ChatMessage
export function ChatMessage({ message, isLoading = false, className }: ChatMessageProps) {
  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
    } catch (err) {
      console.error('Erreur lors de la copie:', err)
    }
  }

  return (
    <div className={cn('group flex gap-3 p-4 rounded-lg', className, {
      'bg-muted/50': message.role === 'assistant',
      'bg-primary/5': message.role === 'user'
    })}>
      <Avatar className="h-8 w-8 shrink-0">
        <AvatarFallback>
          {message.role === 'user' ? (
            <User className="h-4 w-4" />
          ) : (
            <Bot className="h-4 w-4" />
          )}
        </AvatarFallback>
      </Avatar>
      
      <div className="flex-1 space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">
            {message.role === 'user' ? 'Vous' : 'AGI Assistant'}
          </span>
          {message.timestamp && (
            <span className="text-xs text-muted-foreground">
              {new Date(message.timestamp).toLocaleTimeString()}
            </span>
          )}
        </div>
        
        <div className="prose prose-sm max-w-none dark:prose-invert">
          {isLoading ? (
            <div className="flex items-center gap-2">
              <div className="animate-pulse">Génération en cours...</div>
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-current rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
              </div>
            </div>
          ) : (
            <div className="whitespace-pre-wrap">{message.content}</div>
          )}
        </div>
        
        {!isLoading && message.role === 'assistant' && (
          <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => copyToClipboard(message.content)}
              className="h-6 px-2 text-xs"
            >
              <Copy className="h-3 w-3 mr-1" />
              Copier
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 px-2 text-xs"
            >
              <ThumbsUp className="h-3 w-3" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 px-2 text-xs"
            >
              <ThumbsDown className="h-3 w-3" />
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

// Composant MessageInput
export function MessageInput({
  input,
  handleInputChange,
  handleSubmit,
  isLoading = false,
  placeholder = "Tapez votre message...",
  className
}: MessageInputProps) {
  const inputRef = useRef<HTMLInputElement>(null)

  const onSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (input.trim() && !isLoading) {
      handleSubmit(e)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (input.trim() && !isLoading) {
        const form = e.currentTarget.form
        if (form) {
          handleSubmit(e as any)
        }
      }
    }
  }

  return (
    <form onSubmit={onSubmit} className={cn('flex gap-2', className)}>
      <div className="flex-1 relative">
        <Input
          ref={inputRef}
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={isLoading}
          className="pr-12"
        />
      </div>
      <Button
        type="submit"
        disabled={!input.trim() || isLoading}
        size="sm"
        className="px-3"
      >
        {isLoading ? (
          <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
        ) : (
          <Send className="h-4 w-4" />
        )}
      </Button>
    </form>
  )
}

// Composant PromptSuggestions
interface PromptSuggestionsProps {
  suggestions: string[]
  onSuggestionClick: (suggestion: string) => void
  className?: string
}

export function PromptSuggestions({ suggestions, onSuggestionClick, className }: PromptSuggestionsProps) {
  return (
    <div className={cn('flex flex-wrap gap-2 p-4', className)}>
      {suggestions.map((suggestion, index) => (
        <Button
          key={index}
          variant="outline"
          size="sm"
          onClick={() => onSuggestionClick(suggestion)}
          className="text-xs h-8"
        >
          {suggestion}
        </Button>
      ))}
    </div>
  )
}