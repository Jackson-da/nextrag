import request from './request'

// 类型定义
export interface ChatSession {
  id: string
  title: string
  knowledge_base_id: string | null
  message_count: number
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  id: string
  session_id: string
  role: 'user' | 'assistant'
  content: string
  sources: any[] | null
  created_at: string
}

export interface SessionListResponse {
  sessions: ChatSession[]
}

export interface MessageListResponse {
  session_id: string
  messages: ChatMessage[]
}

// API 函数

/**
 * 获取会话列表
 */
export async function getSessions(): Promise<SessionListResponse> {
  return request.get<SessionListResponse>('/chat/sessions')
}

/**
 * 创建新会话
 */
export async function createSession(
  data?: { title?: string; knowledge_base_id?: string }
): Promise<ChatSession> {
  return request.post<ChatSession>('/chat/sessions', data || {})
}

/**
 * 获取会话详情
 */
export async function getSession(sessionId: string): Promise<ChatSession> {
  return request.get<ChatSession>(`/chat/sessions/${sessionId}`)
}

/**
 * 更新会话（如重命名）
 */
export async function updateSession(
  sessionId: string,
  data: { title?: string }
): Promise<ChatSession> {
  return request.patch<ChatSession>(`/chat/sessions/${sessionId}`, data)
}

/**
 * 删除会话
 */
export async function deleteSession(sessionId: string): Promise<{ success: boolean }> {
  return request.delete<{ success: boolean }>(`/chat/sessions/${sessionId}`)
}

/**
 * 获取会话消息
 */
export async function getSessionMessages(sessionId: string): Promise<MessageListResponse> {
  return request.get<MessageListResponse>(`/chat/sessions/${sessionId}/messages`)
}

/**
 * 清空会话消息
 */
export async function clearSessionMessages(sessionId: string): Promise<{ success: boolean }> {
  return request.delete<{ success: boolean }>(`/chat/sessions/${sessionId}/messages`)
}
