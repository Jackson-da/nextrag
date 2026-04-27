import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { streamChatWithFetch } from '@/api'
import type { ChatMessage, Source } from '@/types'

interface ChatSession {
  id: string
  title: string
  messages: ChatMessage[]
  sources: Source[]
  createdAt: Date
}

export const useChatStore = defineStore('chat', () => {
  // 当前会话 ID
  const currentSessionId = ref<string>('')

  // 当前知识库 ID（null 表示全局检索）
  const currentKnowledgeBaseId = ref<string | null>(null)

  // 所有会话
  const sessions = ref<ChatSession[]>([])

  // 当前会话的消息
  const messages = ref<ChatMessage[]>([])

  // 当前会话的引用来源
  const sources = ref<Source[]>([])

  // 加载状态
  const loading = ref(false)

  // 流式输出状态
  const streaming = ref(false)

  // 计算属性
  const currentSession = computed(() =>
    sessions.value.find((s) => s.id === currentSessionId.value)
  )

  const hasMessages = computed(() => messages.value.length > 0)

  // 生成新会话 ID
  function generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
  }

  // Actions
  function createSession(): ChatSession {
    const session: ChatSession = {
      id: generateSessionId(),
      title: '新对话',
      messages: [],
      sources: [],
      createdAt: new Date(),
    }
    sessions.value.unshift(session)
    currentSessionId.value = session.id
    return session
  }

  function switchSession(sessionId: string) {
    const session = sessions.value.find((s) => s.id === sessionId)
    if (session) {
      currentSessionId.value = sessionId
      messages.value = session.messages
      sources.value = session.sources
    }
  }

  function clearCurrentSession() {
    const session = sessions.value.find((s) => s.id === currentSessionId.value)
    if (session) {
      session.messages = []
      session.sources = []
    }
    messages.value = []
    sources.value = []
  }

  async function sendMessage(
    question: string,
    knowledgeBaseId?: string
  ): Promise<void> {
    if (!question.trim() || loading.value) return

    // 如果没有当前会话，创建一个新会话
    if (!currentSessionId.value) {
      createSession()
    }

    // 更新当前知识库 ID
    if (knowledgeBaseId) {
      currentKnowledgeBaseId.value = knowledgeBaseId
    }

    loading.value = true
    streaming.value = true

    // 添加用户消息
    const userMessage: ChatMessage = {
      role: 'user',
      content: question,
      created_at: new Date().toISOString(),
    }
    messages.value.push(userMessage)

    // 添加占位的助手消息
    const assistantMessage: ChatMessage = {
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
    }
    messages.value.push(assistantMessage)

    try {
      // 使用 fetch 进行流式请求
      let fullContent = ''

      for await (const chunk of streamChatWithFetch(
        question,
        currentSessionId.value,
        knowledgeBaseId || currentKnowledgeBaseId.value
      )) {
        fullContent += chunk
        // 更新助手消息内容
        assistantMessage.content = fullContent
        // 触发响应式更新
        messages.value = [...messages.value]
      }

      // 保存到会话
      const session = sessions.value.find(
        (s) => s.id === currentSessionId.value
      )
      if (session) {
        session.messages = [...messages.value]
        // 如果是第一条消息，更新会话标题
        if (session.messages.length === 2) {
          session.title =
            question.substring(0, 30) + (question.length > 30 ? '...' : '')
        }
      }
    } catch (error) {
      // 更新失败消息
      assistantMessage.content = '抱歉，发生了错误，请稍后重试。'
      messages.value = [...messages.value]
      console.error('Chat error:', error)
    } finally {
      loading.value = false
      streaming.value = false
    }
  }

  function deleteSession(sessionId: string) {
    const index = sessions.value.findIndex((s) => s.id === sessionId)
    if (index !== -1) {
      sessions.value.splice(index, 1)
      // 如果删除的是当前会话，切换到第一个或创建新会话
      if (currentSessionId.value === sessionId) {
        if (sessions.value.length > 0) {
          switchSession(sessions.value[0].id)
        } else {
          createSession()
        }
      }
    }
  }

  // 初始化
  function init() {
    if (sessions.value.length === 0) {
      createSession()
    }
  }

  // 设置当前知识库
  function setKnowledgeBase(kbId: string | null) {
    currentKnowledgeBaseId.value = kbId
  }

  return {
    // 状态
    currentSessionId,
    currentKnowledgeBaseId,
    sessions,
    messages,
    sources,
    loading,
    streaming,
    // 计算属性
    currentSession,
    hasMessages,
    // Actions
    createSession,
    switchSession,
    clearCurrentSession,
    sendMessage,
    deleteSession,
    init,
    setKnowledgeBase,
  }
})
