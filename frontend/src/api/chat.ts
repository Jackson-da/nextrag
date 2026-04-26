import request from './request'
import type { ChatRequest, ChatResponse, ChatMessage } from '@/types'

export const chatApi = {
  // 非流式问答
  chat(data: ChatRequest): Promise<ChatResponse> {
    return request.post<ChatResponse>('/chat/chat', data)
  },

  // 流式问答
  streamChat(
    data: ChatRequest,
    onMessage: (content: string) => void,
    onDone?: () => void,
    onError?: (error: string) => void
  ) {
    const eventSource = new EventSource(
      `/api/v1/chat/stream?question=${encodeURIComponent(data.question)}&session_id=${encodeURIComponent(data.session_id)}`
    )

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.content) {
          onMessage(data.content)
        }
      } catch {
        // 忽略解析错误
      }
    }

    eventSource.addEventListener('message', (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.content) {
          onMessage(data.content)
        }
      } catch {
        // 忽略解析错误
      }
    })

    eventSource.addEventListener('done', () => {
      eventSource.close()
      onDone?.()
    })

    eventSource.addEventListener('error', (event) => {
      eventSource.close()
      onError?.('流式响应出错')
    })

    return eventSource
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
  sessionId: string
): AsyncGenerator<string> {
  const response = await fetch('/api/v1/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question,
      session_id: sessionId,
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
