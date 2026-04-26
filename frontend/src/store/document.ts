import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { documentApi } from '@/api'
import type { Document, VectorStoreInfo } from '@/types'

export const useDocumentStore = defineStore('document', () => {
  // 状态
  const documents = ref<Document[]>([])
  const total = ref(0)
  const loading = ref(false)
  const currentDocument = ref<Document | null>(null)
  const vectorStoreInfo = ref<VectorStoreInfo | null>(null)

  // 计算属性
  const completedDocuments = computed(() =>
    documents.value.filter((doc) => doc.status === 'completed')
  )

  const failedDocuments = computed(() =>
    documents.value.filter((doc) => doc.status === 'failed')
  )

  // Actions
  async function fetchDocuments(params?: {
    skip?: number
    limit?: number
    knowledge_base_id?: string
  }) {
    loading.value = true
    try {
      const response = await documentApi.list(params)
      documents.value = response.items
      total.value = response.total
    } finally {
      loading.value = false
    }
  }

  async function fetchDocument(id: string) {
    loading.value = true
    try {
      currentDocument.value = await documentApi.get(id)
      return currentDocument.value
    } finally {
      loading.value = false
    }
  }

  async function uploadDocument(
    file: File,
    description?: string,
    knowledgeBaseId?: string
  ) {
    loading.value = true
    try {
      const response = await documentApi.upload(
        file,
        description,
        knowledgeBaseId
      )
      // 刷新列表
      await fetchDocuments()
      return response
    } finally {
      loading.value = false
    }
  }

  async function deleteDocument(id: string) {
    loading.value = true
    try {
      await documentApi.delete(id)
      // 从列表中移除
      documents.value = documents.value.filter((doc) => doc.id !== id)
      total.value--
    } finally {
      loading.value = false
    }
  }

  async function fetchVectorStoreInfo() {
    try {
      vectorStoreInfo.value = await documentApi.getVectorStoreInfo()
    } catch {
      vectorStoreInfo.value = null
    }
  }

  return {
    // 状态
    documents,
    total,
    loading,
    currentDocument,
    vectorStoreInfo,
    // 计算属性
    completedDocuments,
    failedDocuments,
    // Actions
    fetchDocuments,
    fetchDocument,
    uploadDocument,
    deleteDocument,
    fetchVectorStoreInfo,
  }
})
