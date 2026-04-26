import request from './request'
import type { KnowledgeBase, KnowledgeBaseListResponse } from '@/types'

export const knowledgeBaseApi = {
  // 创建知识库
  create(data: {
    name: string
    description?: string
  }): Promise<KnowledgeBase> {
    return request.post<KnowledgeBase>('/knowledge-bases', data)
  },

  // 获取知识库列表
  list(params?: {
    skip?: number
    limit?: number
  }): Promise<KnowledgeBaseListResponse> {
    return request.get<KnowledgeBaseListResponse>('/knowledge-bases', { params })
  },

  // 获取知识库详情
  get(id: string): Promise<KnowledgeBase> {
    return request.get<KnowledgeBase>(`/knowledge-bases/${id}`)
  },

  // 更新知识库
  update(
    id: string,
    data: { name?: string; description?: string }
  ): Promise<KnowledgeBase> {
    return request.put<KnowledgeBase>(`/knowledge-bases/${id}`, data)
  },

  // 删除知识库
  delete(id: string): Promise<{ success: boolean; message: string }> {
    return request.delete(`/knowledge-bases/${id}`)
  },
}
