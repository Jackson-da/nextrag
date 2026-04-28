import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { streamChatWithFetch } from '@/api'
import {
  getSessions,
  createSession as apiCreateSession,
  deleteSession as apiDeleteSession,
  getSessionMessages,
  clearSessionMessages as apiClearSessionMessages,
} from '@/api/chat-session'
import type { ChatMessage, Source } from '@/types'

interface ChatSession {
  id: string
  title: string
  messages: ChatMessage[]
  sources: Source[]
  createdAt: string
  updatedAt: string
  knowledgeBaseId?: string
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

  // 初始化状态（是否已加载会话列表）
  const initialized = ref(false)

  // 计算属性
  const currentSession = computed(() =>
    sessions.value.find((s) => s.id === currentSessionId.value)
  )

  const hasMessages = computed(() => messages.value.length > 0)

  // Actions

  /**
   * 从后端加载会话列表
   */
  async function fetchSessions(): Promise<void> {
    try {
      const response = await getSessions()
      sessions.value = response.sessions.map((s) => ({
        id: s.id,
        title: s.title,
        messages: [],
        sources: [],
        createdAt: s.created_at,
        updatedAt: s.updated_at,
        knowledgeBaseId: s.knowledge_base_id || undefined,
      }))
    } catch (error) {
      console.error('Failed to fetch sessions:', error)
    }
  }

  /**
   * 从后端加载会话消息
   */
  async function fetchMessages(sessionId: string): Promise<void> {
    try {
      const response = await getSessionMessages(sessionId)
      const session = sessions.value.find((s) => s.id === sessionId)
      if (session) {
        session.messages = response.messages.map((m) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          created_at: m.created_at || new Date().toISOString(),
        }))
        session.sources = []
      }
      messages.value = session?.messages || []
    } catch (error) {
      console.error('Failed to fetch messages:', error)
    }
  }

  /**
   * 创建新会话（后端）
   */
  async function createSession(): Promise<ChatSession> {
    const response = await apiCreateSession({
      knowledge_base_id: currentKnowledgeBaseId.value || undefined,
    })

    const session: ChatSession = {
      id: response.id,
      title: response.title,
      messages: [],
      sources: [],
      createdAt: response.created_at,
      updatedAt: response.updated_at,
      knowledgeBaseId: response.knowledge_base_id || undefined,
    }

    sessions.value.unshift(session)
    currentSessionId.value = session.id
    messages.value = []
    sources.value = []

    return session
  }

  /**
   * 切换会话
   */
  async function switchSession(sessionId: string): Promise<void> {
    const session = sessions.value.find((s) => s.id === sessionId)
    if (session) {
      currentSessionId.value = sessionId
      // 如果没有消息，从后端加载
      if (session.messages.length === 0) {
        await fetchMessages(sessionId)
      } else {
        messages.value = session.messages
        sources.value = session.sources
      }
    }
  }

  /**
   * 清空当前会话
   */
  async function clearCurrentSession(): Promise<void> {
    if (!currentSessionId.value) return

    try {
      await apiClearSessionMessages(currentSessionId.value)
    } catch (error) {
      console.error('Failed to clear session:', error)
    }

    const session = sessions.value.find((s) => s.id === currentSessionId.value)
    if (session) {
      session.messages = []
      session.sources = []
    }
    messages.value = []
    sources.value = []
  }

  /**
   * 发送消息
   */
  async function sendMessage(
    question: string,
    knowledgeBaseId?: string
  ): Promise<void> {
    if (!question.trim() || loading.value) return

    // 更新当前知识库 ID
    if (knowledgeBaseId) {
      currentKnowledgeBaseId.value = knowledgeBaseId
    }

    // 如果没有当前会话，创建一个新会话
    if (!currentSessionId.value) {
      await createSession()
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

      // 保存到当前会话
      const session = sessions.value.find(
        (s) => s.id === currentSessionId.value
      )
      if (session) {
        session.messages = [...messages.value]
        session.updatedAt = new Date().toISOString()
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

  /**
   * 删除会话（后端）
   */
  async function deleteSession(sessionId: string): Promise<void> {
    try {
      await apiDeleteSession(sessionId)
    } catch (error) {
      console.error('Failed to delete session:', error)
    }

    const index = sessions.value.findIndex((s) => s.id === sessionId)
    if (index !== -1) {
      sessions.value.splice(index, 1)

      // 如果删除的是当前会话，切换到第一个或创建新会话
      if (currentSessionId.value === sessionId) {
        if (sessions.value.length > 0) {
          await switchSession(sessions.value[0].id)
        } else {
          await createSession()
        }
      }
    }
  }

  /**
   * 初始化（从后端加载会话列表）
   */
  async function init(): Promise<void> {
    if (initialized.value) return

    try {
      await fetchSessions()

      // 如果有会话，加载最新一个的消息
      if (sessions.value.length > 0) {
        await switchSession(sessions.value[0].id)
      } else {
        // 没有会话则创建一个
        await createSession()
      }

      initialized.value = true
    } catch (error) {
      console.error('Failed to initialize chat:', error)
      // 即使失败也创建一个本地会话
      if (sessions.value.length === 0) {
        await createSession()
      }
    }
  }

  /**
   * 设置当前知识库
   */
  function setKnowledgeBase(kbId: string | null): void {
    currentKnowledgeBaseId.value = kbId
  }

  /**
   * 重置所有状态（退出登录时调用）
   */
  function reset(): void {
    currentSessionId.value = ''
    currentKnowledgeBaseId.value = null
    sessions.value = []
    messages.value = []
    sources.value = []
    loading.value = false
    streaming.value = false
    initialized.value = false
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
    initialized,
    // 计算属性
    currentSession,
    hasMessages,
    // Actions
    fetchSessions,
    fetchMessages,
    createSession,
    switchSession,
    clearCurrentSession,
    sendMessage,
    deleteSession,
    init,
    setKnowledgeBase,
    reset,
  }
})
