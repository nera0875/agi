// API route pour le chat streaming avec intégration LangGraph
import { NextRequest } from 'next/server'

export async function POST(req: NextRequest) {
  try {
    const { messages, memoryContext, userId } = await req.json()
    
    // Configuration du streaming vers le backend FastAPI
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
    
    const response = await fetch(`${backendUrl}/api/agents/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        agent_type: 'consolidator',  // Agent par défaut pour le chat
        input_data: {
          messages,
          memory_context: memoryContext,
          user_id: userId
        },
        stream: true
      })
    })

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`)
    }

    // Retourner le stream directement
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Transfer-Encoding': 'chunked'
      }
    })

  } catch (error) {
    console.error('Chat API error:', error)
    return new Response(
      JSON.stringify({ error: 'Internal server error' }), 
      { 
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    )
  }
}