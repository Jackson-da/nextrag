<template>
  <div class="knowledge-bases-view">
    <!-- 顶部栏 -->
    <header class="page-header">
      <h1 class="page-title">知识库管理</h1>
      <div class="header-actions">
        <el-button :icon="Refresh" @click="refresh">刷新</el-button>
        <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">
          创建知识库
        </el-button>
      </div>
    </header>

    <!-- 知识库列表 -->
    <div class="kb-grid">
      <el-card
        v-for="kb in knowledgeBaseStore.knowledgeBases"
        :key="kb.id"
        shadow="hover"
        class="kb-card"
      >
        <div class="kb-header">
          <div class="kb-icon">
            <el-icon :size="32"><Collection /></el-icon>
          </div>
          <div class="kb-info">
            <h3 class="kb-name">{{ kb.name }}</h3>
            <p v-if="kb.description" class="kb-description">
              {{ kb.description }}
            </p>
          </div>
        </div>

        <div class="kb-stats">
          <div class="kb-stat">
            <el-icon><Document /></el-icon>
            <span>{{ kb.document_count }} 个文档</span>
          </div>
          <div class="kb-stat">
            <el-icon><Clock /></el-icon>
            <span>{{ formatDate(kb.created_at) }}</span>
          </div>
        </div>

        <div class="kb-actions">
          <el-button
            type="primary"
            :icon="ChatLineRound"
            size="small"
            @click="goToChat(kb.id)"
          >
            问答
          </el-button>
          <el-button
            :icon="Edit"
            size="small"
            @click="handleEdit(kb)"
          >
            编辑
          </el-button>
          <el-button
            type="danger"
            :icon="Delete"
            size="small"
            @click="handleDelete(kb.id)"
          >
            删除
          </el-button>
        </div>
      </el-card>

      <!-- 创建知识库卡片 -->
      <el-card shadow="hover" class="kb-card create-card" @click="showCreateDialog = true">
        <div class="create-content">
          <el-icon :size="48"><Plus /></el-icon>
          <span>创建新知识库</span>
        </div>
      </el-card>
    </div>

    <!-- 空状态 -->
    <el-empty
      v-if="knowledgeBaseStore.knowledgeBases.length === 0 && !knowledgeBaseStore.loading"
      description="暂无知识库，请创建一个"
    >
      <el-button type="primary" @click="showCreateDialog = true">
        创建知识库
      </el-button>
    </el-empty>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingKb ? '编辑知识库' : '创建知识库'"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="80px"
      >
        <el-form-item label="名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="请输入知识库名称"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="可选：添加知识库描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="closeDialog">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  Plus,
  Refresh,
  Delete,
  Edit,
  Collection,
  Document,
  Clock,
  ChatLineRound,
} from '@element-plus/icons-vue'
import { useKnowledgeBaseStore } from '@/store'
import type { KnowledgeBase } from '@/types'

const router = useRouter()
const knowledgeBaseStore = useKnowledgeBaseStore()

const showCreateDialog = ref(false)
const editingKb = ref<KnowledgeBase | null>(null)
const loading = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  description: '',
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入知识库名称', trigger: 'blur' },
    { min: 1, max: 100, message: '名称长度为 1-100 个字符', trigger: 'blur' },
  ],
}

function formatDate(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleDateString('zh-CN')
}

function handleEdit(kb: KnowledgeBase) {
  editingKb.value = kb
  form.name = kb.name
  form.description = kb.description || ''
  showCreateDialog.value = true
}

async function handleSubmit() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      if (editingKb.value) {
        // 编辑
        await knowledgeBaseStore.updateKnowledgeBase(editingKb.value.id, {
          name: form.name,
          description: form.description,
        })
        ElMessage.success('更新成功')
      } else {
        // 创建
        await knowledgeBaseStore.createKnowledgeBase({
          name: form.name,
          description: form.description,
        })
        ElMessage.success('创建成功')
      }
      closeDialog()
    } catch {
      ElMessage.error('操作失败')
    } finally {
      loading.value = false
    }
  })
}

async function handleDelete(id: string) {
  try {
    await ElMessageBox.confirm('确定要删除这个知识库吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await knowledgeBaseStore.deleteKnowledgeBase(id)
    ElMessage.success('删除成功')
  } catch {
    // 取消操作
  }
}

function closeDialog() {
  showCreateDialog.value = false
  editingKb.value = null
  form.name = ''
  form.description = ''
  formRef.value?.resetFields()
}

function goToChat(kbId: string) {
  router.push({ path: '/chat', query: { knowledgeBaseId: kbId } })
}

async function refresh() {
  await knowledgeBaseStore.fetchKnowledgeBases()
}

onMounted(() => {
  knowledgeBaseStore.fetchKnowledgeBases()
})
</script>

<style scoped>
.knowledge-bases-view {
  height: 100%;
  padding: 24px;
  overflow: auto;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.kb-card {
  transition: transform 0.2s, box-shadow 0.2s;
}

.kb-card:hover {
  transform: translateY(-4px);
}

.kb-header {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.kb-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.kb-info {
  flex: 1;
  min-width: 0;
}

.kb-name {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 4px;
}

.kb-description {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.kb-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.kb-stat {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #6b7280;
}

.kb-actions {
  display: flex;
  gap: 8px;
}

.create-card {
  border: 2px dashed #d1d5db;
  background: #f9fafb;
  cursor: pointer;
  min-height: 200px;
}

.create-card:hover {
  border-color: #3b82f6;
  background: #eff6ff;
}

.create-content {
  height: 100%;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #6b7280;
}

.create-card:hover .create-content {
  color: #3b82f6;
}
</style>
