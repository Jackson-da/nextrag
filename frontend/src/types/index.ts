// API 类型定义

// 文档相关
export interface Document {
  id: string
  filename: string
  description?: string
  file_path: string
  file_size: number
  file_type: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  chunk_count: number
  created_at: string
  updated_at: string
  metadata?: Record<string, unknown>
}

export interface DocumentListResponse {
  total: number
  items: Document[]
}

export interface UploadResponse {
  document_id: string
  filename: string
  status: string
  message: string
}

// 问答相关
export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at?: string
}

export interface ChatRequest {
  question: string
  session_id: string
  knowledge_base_id?: string
  stream?: boolean
}

export interface ChatResponse {
  answer: string
  session_id: string
  sources: Source[]
  tokens_used?: number
  latency: number
}

export interface Source {
  content: string
  metadata: Record<string, unknown>
}

// 知识库相关
export interface KnowledgeBase {
  id: string
  name: string
  description?: string
  document_count: number
  created_at: string
  updated_at: string
}

export interface KnowledgeBaseListResponse {
  total: number
  items: KnowledgeBase[]
}

// 健康检查
export interface HealthResponse {
  status: string
  version: string
  llm_connected: boolean
  vectorstore_connected: boolean
  document_count: number
}

// 通用响应
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

// 向量库信息
export interface VectorStoreInfo {
  name: string
  count: number
  metadata: Record<string, unknown>
}
