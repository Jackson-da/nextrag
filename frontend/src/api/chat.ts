import request from './request'
import type { ChatRequest, ChatResponse, ChatMessage } from '@/types'

export const chatApi = {
  // 非流式问答
  chat(data: ChatRequest): Promise<ChatResponse> {
    return request.post<ChatResponse>('/chat/chat', data)
  },

  // 流式问答（使用 fetch 替代 EventSource 以支持认证）
  streamChat(
    data: ChatRequest,
    onMessage: (content: string) => void,
    onDone?: () => void,
    onError?: (error: string) => void
  ) {
    // 获取 token
    const token = localStorage.getItem('token')
    
    fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        question: data.question,
        session_id: data.session_id,
        knowledge_base_id: data.knowledge_base_id || undefined,
        stream: true,
      }),
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error('请求失败: ' + response.status)
        }
        
        const reader = response.body?.getReader()
        if (!reader) {
          throw new Error('无法读取响应流')
        }
        
        const decoder = new TextDecoder()
        let buffer = ''
        
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          
          buffer += decoder.decode(value, { stream: true })
          
          // 处理缓冲区，按行分割
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''
          
          for (const line of lines) {
            const trimmedLine = line.trim()
            if (!trimmedLine) continue
            
            // 解析 SSE data 行
            if (trimmedLine.startsWith('data:')) {
              const dataStr = trimmedLine.slice(5).trim()
              
              // 跳过 [DONE] 标记
              if (dataStr === '[DONE]') {
                onDone?.()
                return
              }
              
              // 尝试解析 JSON
              try {
                const parsed = JSON.parse(dataStr)
                if (parsed.content) {
                  onMessage(parsed.content)
                }
                if (parsed.error) {
                  throw new Error(parsed.error)
                }
              } catch (parseError) {
                // 如果不是 JSON，可能是纯文本内容
                if (dataStr) {
                  onMessage(dataStr)
                }
              }
            }
          }
        }
        
        onDone?.()
      })
      .catch((error) => {
        console.error('流式请求错误:', error)
        onError?.(error.message || '流式响应出错')
      })
    
    // 返回一个对象用于取消请求（如果需要）
    return {
      cancel: () => {
        // fetch 不支持取消，这里仅作接口占位
      }
    }
  },

  // 获取对话历史
  getHistory(
    sessionId: string
  ): Promise<{ session_id: string; messages: ChatMessage[] }> {
    return request.get(`/chat/history/${sessionId}`)
  },

  // 清除对话历史
  clearHistory(
    sessionId: string
  ): Promise<{ success: boolean; message: string }> {
    return request.delete(`/chat/history/${sessionId}`)
  },

  // 健康检查
  healthCheck(): Promise<{ status: string; llm_connected: boolean }> {
    return request.post('/chat/health')
  },
}

// 使用 fetch 实现流式请求（更可靠）
export async function* streamChatWithFetch(
  question: string,
  sessionId: string,
  knowledgeBaseId?: string
): AsyncGenerator<string> {
  // 获取 token
  const token = localStorage.getItem('token')
  
  const response = await fetch('/api/v1/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      question,
      session_id: sessionId,
      knowledge_base_id: knowledgeBaseId || undefined,
      stream: true,
    }),
  })

  if (!response.ok) {
    throw new Error('请求失败: ' + response.status)
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw new Error('无法读取响应流')
  }

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    
    // 处理缓冲区，按行分割
    const lines = buffer.split('\n')
    buffer = lines.pop() || '' // 保留最后一个不完整的行
    
    for (const line of lines) {
      const trimmedLine = line.trim()
      if (!trimmedLine) continue
      
      // 解析 SSE data 行
      if (trimmedLine.startsWith('data:')) {
        const dataStr = trimmedLine.slice(5).trim()
        
        // 跳过 [DONE] 标记
        if (dataStr === '[DONE]') {
          return
        }
        
        // 尝试解析 JSON
        try {
          const parsed = JSON.parse(dataStr)
          if (parsed.content) {
            yield parsed.content
          }
        } catch {
          // 如果不是 JSON，可能是纯文本内容
          if (dataStr) {
            yield dataStr
          }
        }
      }
    }
  }
}
