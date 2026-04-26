import { defineStore } from 'pinia'
import { ref } from 'vue'
import { knowledgeBaseApi } from '@/api'
import type { KnowledgeBase } from '@/types'

export const useKnowledgeBaseStore = defineStore('knowledgeBase', () => {
  // 状态
  const knowledgeBases = ref<KnowledgeBase[]>([])
  const total = ref(0)
  const loading = ref(false)
  const currentKnowledgeBase = ref<KnowledgeBase | null>(null)

  // Actions
  async function fetchKnowledgeBases(params?: {
    skip?: number
    limit?: number
  }) {
    loading.value = true
    try {
      const response = await knowledgeBaseApi.list(params)
      knowledgeBases.value = response.items
      total.value = response.total
    } finally {
      loading.value = false
    }
  }

  async function createKnowledgeBase(data: {
    name: string
    description?: string
  }) {
    loading.value = true
    try {
      const kb = await knowledgeBaseApi.create(data)
      knowledgeBases.value.unshift(kb)
      total.value++
      return kb
    } finally {
      loading.value = false
    }
  }

  async function updateKnowledgeBase(
    id: string,
    data: { name?: string; description?: string }
  ) {
    loading.value = true
    try {
      const updated = await knowledgeBaseApi.update(id, data)
      const index = knowledgeBases.value.findIndex((kb) => kb.id === id)
      if (index !== -1) {
        knowledgeBases.value[index] = updated
      }
      return updated
    } finally {
      loading.value = false
    }
  }

  async function deleteKnowledgeBase(id: string) {
    loading.value = true
    try {
      await knowledgeBaseApi.delete(id)
      knowledgeBases.value = knowledgeBases.value.filter((kb) => kb.id !== id)
      total.value--
    } finally {
      loading.value = false
    }
  }

  return {
    // 状态
    knowledgeBases,
    total,
    loading,
    currentKnowledgeBase,
    // Actions
    fetchKnowledgeBases,
    createKnowledgeBase,
    updateKnowledgeBase,
    deleteKnowledgeBase,
  }
})
