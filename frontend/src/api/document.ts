import request from './request'
import type {
  Document,
  DocumentListResponse,
  UploadResponse,
  VectorStoreInfo,
  BatchUploadResponse,
} from '@/types'

export const documentApi = {
  // 上传文档
  upload(
    file: File,
    description?: string,
    knowledgeBaseId?: string
  ): Promise<UploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    if (description) {
      formData.append('description', description)
    }
    if (knowledgeBaseId) {
      formData.append('knowledge_base_id', knowledgeBaseId)
    }

    return request.upload<UploadResponse>('/documents/upload', formData, {
      timeout: 120000, // 上传文件需要更长的超时时间
    })
  },

  // 批量上传文档
  uploadBatch(
    files: File[],
    knowledgeBaseId?: string
  ): Promise<BatchUploadResponse> {
    const formData = new FormData()
    files.forEach((file) => {
      formData.append('files', file)
    })
    if (knowledgeBaseId) {
      formData.append('knowledge_base_id', knowledgeBaseId)
    }

    return request.upload<BatchUploadResponse>('/documents/upload/batch', formData, {
      timeout: 600000, // 批量上传需要更长的超时时间
    })
  },

  // 获取文档列表
  list(params?: {
    skip?: number
    limit?: number
    knowledge_base_id?: string
  }): Promise<DocumentListResponse> {
    return request.get<DocumentListResponse>('/documents', { params })
  },

  // 获取文档详情
  get(id: string): Promise<Document> {
    return request.get<Document>(`/documents/${id}`)
  },

  // 删除文档
  delete(id: string): Promise<{ success: boolean; message: string }> {
    return request.delete(`/documents/${id}`)
  },

  // 获取向量库信息
  getVectorStoreInfo(): Promise<VectorStoreInfo> {
    return request.get('/documents/vectorstore/info')
  },
}
