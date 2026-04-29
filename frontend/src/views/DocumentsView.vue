<template>
  <div class="documents-view">
    <!-- 顶部栏 -->
    <header class="page-header">
      <h1 class="page-title">文档管理</h1>
      <div class="header-actions">
        <el-button :icon="Refresh" @click="refresh">刷新</el-button>
        <el-button type="primary" :icon="UploadFilled" @click="showUploadDialog = true">
          上传文档
        </el-button>
        <el-button type="success" :icon="Upload" @click="showBatchUploadDialog = true">
          批量上传
        </el-button>
      </div>
    </header>

    <!-- 知识库筛选 -->
    <div class="filter-bar">
      <el-select
        v-model="selectedKnowledgeBase"
        placeholder="全部知识库"
        clearable
        @change="handleKnowledgeBaseChange"
      >
        <el-option label="全部知识库" value="" />
        <el-option
          v-for="kb in knowledgeBaseStore.knowledgeBases"
          :key="kb.id"
          :label="kb.name"
          :value="kb.id"
        />
      </el-select>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-card shadow="hover">
        <div class="stat-item">
          <div class="stat-icon blue">
            <el-icon :size="24"><Document /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ documentStore.total }}</div>
            <div class="stat-label">文档总数</div>
          </div>
        </div>
      </el-card>

      <el-card shadow="hover">
        <div class="stat-item">
          <div class="stat-icon green">
            <el-icon :size="24"><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ documentStore.completedDocuments.length }}</div>
            <div class="stat-label">已完成</div>
          </div>
        </div>
      </el-card>

      <el-card shadow="hover">
        <div class="stat-item">
          <div class="stat-icon purple">
            <el-icon :size="24"><Connection /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ vectorInfo?.count || 0 }}</div>
            <div class="stat-label">向量片段</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 文档列表 -->
    <div class="documents-list card">
      <div class="card-header">
        <span>文档列表</span>
      </div>
      <div class="card-body">
        <el-table
          v-loading="documentStore.loading"
          :data="documentStore.documents"
          stripe
          style="width: 100%"
        >
          <el-table-column prop="filename" label="文件名" min-width="200">
            <template #default="{ row }">
              <div class="file-name">
                <el-icon :size="20">
                  <Document v-if="row.file_type === 'pdf'" />
                  <Document v-else-if="row.file_type === 'docx'" />
                  <Document v-else />
                </el-icon>
                <span>{{ row.filename }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="file_type" label="类型" width="100">
            <template #default="{ row }">
              <el-tag type="info" size="small">
                {{ row.file_type.toUpperCase() }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="chunk_count" label="分块数" width="100" align="center" />

          <el-table-column label="知识库" width="150">
            <template #default="{ row }">
              <template v-if="getKnowledgeBaseName(row.knowledge_base_id)">
                {{ getKnowledgeBaseName(row.knowledge_base_id) }}
              </template>
              <span v-else class="text-muted">-</span>
            </template>
          </el-table-column>

          <el-table-column prop="status" label="状态" width="120" align="center">
            <template #default="{ row }">
              <el-tag
                :type="
                  row.status === 'completed'
                    ? 'success'
                    : row.status === 'failed'
                      ? 'danger'
                      : row.status === 'processing'
                        ? 'warning'
                        : 'info'
                "
                size="small"
              >
                {{ statusText[row.status] }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="created_at" label="上传时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>

          <el-table-column label="操作" width="120" align="center" fixed="right">
            <template #default="{ row }">
              <el-button
                type="danger"
                :icon="Delete"
                size="small"
                link
                @click="handleDelete(row.id)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 空状态 -->
        <el-empty
          v-if="!documentStore.loading && documentStore.documents.length === 0"
          description="暂无文档，请上传文档"
        >
          <el-button type="primary" @click="showUploadDialog = true">
            上传文档
          </el-button>
        </el-empty>

        <!-- 分页 -->
        <div v-if="documentStore.total > 0" class="pagination">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :total="documentStore.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next"
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </div>

    <!-- 上传对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传文档"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="uploadForm" label-width="80px">
        <el-form-item label="选择文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :file-list="fileList"
            accept=".pdf,.docx,.doc,.txt,.md"
            class="upload-component"
          >
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">
                支持 PDF、Word、TXT、Markdown 格式，单文件不超过 50MB
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item label="知识库">
          <el-select
            v-model="uploadForm.knowledge_base_id"
            placeholder="选择知识库（可选）"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="kb in knowledgeBaseStore.knowledgeBases"
              :key="kb.id"
              :label="kb.name"
              :value="kb.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="文档描述">
          <el-input
            v-model="uploadForm.description"
            type="textarea"
            :rows="3"
            placeholder="可选：添加文档描述"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="uploading"
          :disabled="!selectedFile"
          @click="handleUpload"
        >
          上传
        </el-button>
      </template>
    </el-dialog>

    <!-- 批量上传对话框 -->
    <el-dialog
      v-model="showBatchUploadDialog"
      title="批量上传文档"
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="batch-upload-area" @dragover.prevent @drop.prevent="handleBatchDrop">
        <el-upload
          ref="batchUploadRef"
          :auto-upload="false"
          :limit="20"
          multiple
          :on-change="handleBatchFileChange"
          :file-list="batchFileList"
          accept=".pdf,.docx,.doc,.txt,.md"
          class="batch-upload-component"
        >
          <div class="upload-placeholder">
            <el-icon :size="48"><Upload /></el-icon>
            <p>拖拽文件到此处，或<em>点击选择</em></p>
            <p class="upload-tip">支持 PDF、Word、TXT、Markdown 格式，最多 20 个文件</p>
          </div>
        </el-upload>
      </div>

      <!-- 已选文件列表 -->
      <div v-if="batchFileList.length > 0" class="batch-file-list">
        <div class="batch-file-header">
          <span>已选择 {{ batchFileList.length }} 个文件</span>
          <el-button type="danger" size="small" link @click="clearBatchFiles">清空</el-button>
        </div>
        <el-table :data="batchFileList" size="small" max-height="200">
          <el-table-column prop="name" label="文件名" />
          <el-table-column label="大小" width="100">
            <template #default="{ row }">
              {{ formatFileSize(row.size) }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag v-if="batchResults[row.name]" :type="batchResults[row.name].status === 'success' ? 'success' : 'danger'" size="small">
                {{ batchResults[row.name].status === 'success' ? '成功' : '失败' }}
              </el-tag>
              <span v-else class="text-muted">等待上传</span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <el-form :model="batchUploadForm" label-width="80px" class="batch-form">
        <el-form-item label="知识库">
          <el-select
            v-model="batchUploadForm.knowledge_base_id"
            placeholder="选择知识库（可选）"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="kb in knowledgeBaseStore.knowledgeBases"
              :key="kb.id"
              :label="kb.name"
              :value="kb.id"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showBatchUploadDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="batchUploading"
          :disabled="batchFileList.length === 0"
          @click="handleBatchUpload"
        >
          开始上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Upload,
  UploadFilled,
  Refresh,
  Delete,
  Document,
  CircleCheck,
  Connection,
} from '@element-plus/icons-vue'
import { useDocumentStore, useKnowledgeBaseStore } from '@/store'
import { documentApi } from '@/api'
import type { UploadInstance, UploadRawFile } from 'element-plus'

const documentStore = useDocumentStore()
const knowledgeBaseStore = useKnowledgeBaseStore()

const showUploadDialog = ref(false)
const uploading = ref(false)
const uploadRef = ref<UploadInstance>()
const selectedFile = ref<File | null>(null)
const fileList = ref<{ name: string }[]>([])

// 批量上传
const showBatchUploadDialog = ref(false)
const batchUploadRef = ref<UploadInstance>()
const batchUploading = ref(false)
type BatchFileItem = { name: string; size: number; raw?: File; status?: string }
const batchFileList = ref<BatchFileItem[]>([])
const batchResults = ref<Record<string, { status: string; message?: string }>>({})

const uploadForm = reactive({
  description: '',
  knowledge_base_id: '',
})

const batchUploadForm = reactive({
  knowledge_base_id: '',
})

const currentPage = ref(1)
const pageSize = ref(20)
const selectedKnowledgeBase = ref('')

const statusText: Record<string, string> = {
  pending: '待处理',
  processing: '处理中',
  completed: '已完成',
  failed: '失败',
}

const vectorInfo = computed(() => documentStore.vectorStoreInfo)

function formatDate(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN')
}

function getKnowledgeBaseName(kbId: string | null | undefined): string {
  if (!kbId) return ''
  const kb = knowledgeBaseStore.knowledgeBases.find((k) => k.id === kbId)
  return kb?.name || ''
}

function handleFileChange(file: { raw: UploadRawFile }) {
  selectedFile.value = file.raw
  fileList.value = [{ name: file.raw.name }]
}

async function handleUpload() {
  if (!selectedFile.value) {
    ElMessage.warning('请选择文件')
    return
  }

  uploading.value = true
  try {
    await documentStore.uploadDocument(
      selectedFile.value,
      uploadForm.description,
      uploadForm.knowledge_base_id || undefined
    )
    ElMessage.success('文档上传成功')
    showUploadDialog.value = false
    selectedFile.value = null
    fileList.value = []
    uploadForm.description = ''
    uploadForm.knowledge_base_id = ''

    // 刷新向量库信息
    documentStore.fetchVectorStoreInfo()
  } catch (error) {
    ElMessage.error('上传失败，请重试')
  } finally {
    uploading.value = false
  }
}

async function handleDelete(id: string) {
  try {
    await ElMessageBox.confirm('确定要删除这个文档吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await documentStore.deleteDocument(id)
    ElMessage.success('删除成功')
    documentStore.fetchVectorStoreInfo()
  } catch {
    // 取消操作
  }
}

function handleSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  refresh()
}

function handlePageChange(page: number) {
  currentPage.value = page
  refresh()
}

async function refresh() {
  await documentStore.fetchDocuments({
    skip: (currentPage.value - 1) * pageSize.value,
    limit: pageSize.value,
    knowledge_base_id: selectedKnowledgeBase.value || undefined,
  })
}

function handleKnowledgeBaseChange() {
  currentPage.value = 1
  refresh()
}

// 批量上传相关
function handleBatchFileChange(uploadFile: { name: string; size?: number; raw?: UploadRawFile }) {
  const exists = batchFileList.value.some((f) => f.name === uploadFile.name)
  if (!exists) {
    batchFileList.value.push({
      name: uploadFile.name,
      size: uploadFile.size ?? 0,
      raw: uploadFile.raw as File | undefined,
    })
  }
}

function handleBatchDrop(e: DragEvent) {
  const files = e.dataTransfer?.files
  if (files) {
    for (const file of Array.from(files)) {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase()
      if (['.pdf', '.docx', '.doc', '.txt', '.md'].includes(ext)) {
        const exists = batchFileList.value.some((f) => f.name === file.name)
        if (!exists) {
          batchFileList.value.push({ name: file.name, size: file.size, raw: file })
        }
      }
    }
  }
}

function clearBatchFiles() {
  batchFileList.value = []
  batchResults.value = {}
  batchUploadRef.value?.clearFiles()
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

async function handleBatchUpload() {
  if (batchFileList.value.length === 0) {
    ElMessage.warning('请选择文件')
    return
  }

  batchUploading.value = true
  batchResults.value = {}

  try {
    const files = batchFileList.value
      .map((f) => f.raw)
      .filter((f): f is File => f instanceof File)

    if (files.length === 0) {
      ElMessage.error('没有有效的文件，请重新选择')
      return
    }

    const response = await documentApi.uploadBatch(
      files,
      batchUploadForm.knowledge_base_id || undefined
    )

    // 更新结果状态
    response.results.forEach((result) => {
      batchResults.value[result.filename] = {
        status: result.status,
        message: result.error || result.chunk_count ? `分块数: ${result.chunk_count}` : undefined,
      }
    })

    // 显示汇总消息
    if (response.failed_count === 0) {
      ElMessage.success(`批量上传成功！${response.success_count} 个文件已处理`)
    } else {
      ElMessage.warning(
        `上传完成：成功 ${response.success_count} 个，失败 ${response.failed_count} 个`
      )
    }

    // 成功后关闭对话框并刷新
    if (response.success_count > 0) {
      showBatchUploadDialog.value = false
      clearBatchFiles()
      batchUploadForm.knowledge_base_id = ''
      refresh()
      documentStore.fetchVectorStoreInfo()
    }
  } catch (error) {
    ElMessage.error('批量上传失败，请重试')
  } finally {
    batchUploading.value = false
  }
}

onMounted(() => {
  refresh()
  documentStore.fetchVectorStoreInfo()
  knowledgeBaseStore.fetchKnowledgeBases()
})
</script>

<style scoped>
.documents-view {
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

.filter-bar {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-bar .el-select {
  width: 200px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon.blue {
  background: #eff6ff;
  color: #3b82f6;
}

.stat-icon.green {
  background: #ecfdf5;
  color: #10b981;
}

.stat-icon.purple {
  background: #f5f3ff;
  color: #8b5cf6;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
}

.documents-list {
  background: white;
}

.file-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.upload-component {
  width: 100%;
}

.text-muted {
  color: #9ca3af;
}

.batch-upload-area {
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  transition: border-color 0.3s;
}

.batch-upload-area:hover {
  border-color: #409eff;
}

.batch-upload-component {
  width: 100%;
}

.batch-upload-component :deep(.el-upload) {
  width: 100%;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px 0;
  color: #909399;
}

.upload-placeholder p {
  margin: 8px 0 0;
  font-size: 14px;
}

.upload-placeholder em {
  color: #409eff;
  font-style: normal;
}

.upload-tip {
  font-size: 12px !important;
  color: #c0c4cc !important;
}

.batch-file-list {
  margin-bottom: 16px;
}

.batch-file-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
}

.batch-form {
  margin-top: 16px;
}
</style>
