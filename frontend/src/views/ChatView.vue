<template>
  <div class="chat-view">
    <!-- 顶部栏 -->
    <header class="chat-header">
      <div class="header-left">
        <h1 class="page-title">智能问答</h1>
        <el-tag v-if="currentKnowledgeBaseName" type="success" size="small">
          当前知识库：{{ currentKnowledgeBaseName }}
        </el-tag>
        <el-tag v-else type="info" size="small">
          全局检索
        </el-tag>
      </div>
      <div class="header-actions">
        <el-button :icon="Plus" circle @click="handleNewChat" />
        <el-button
          :icon="Delete"
          :disabled="!chatStore.hasMessages"
          @click="handleClearChat"
        >
          清空对话
        </el-button>
      </div>
    </header>

    <!-- 对话区域 -->
    <div class="chat-container">
      <!-- 欢迎信息 -->
      <div v-if="!chatStore.hasMessages" class="welcome">
        <div class="welcome-icon">
          <el-icon :size="64"><ChatDotRound /></el-icon>
        </div>
        <h2>欢迎使用智能问答系统</h2>
        <p>我可以根据您上传的文档回答问题。请先在「文档管理」中上传文档。</p>
      </div>

      <!-- 消息列表 -->
      <div v-else ref="messagesContainer" class="messages">
        <div
          v-for="(message, index) in chatStore.messages"
          :key="index"
          class="message-item"
          :class="message.role"
        >
          <div class="message-avatar">
            <el-icon v-if="message.role === 'user'" :size="20"><User /></el-icon>
            <el-icon v-else :size="20"><ChatDotRound /></el-icon>
          </div>
          <div class="message-content">
            <div class="message-text">{{ message.content }}</div>
            <div
              v-if="message.created_at"
              class="message-time"
            >
              {{ formatTime(message.created_at) }}
            </div>
          </div>
        </div>

        <!-- 加载指示器 -->
        <div v-if="chatStore.loading" class="message-item assistant">
          <div class="message-avatar">
            <el-icon :size="20"><ChatDotRound /></el-icon>
          </div>
          <div class="message-content">
            <div class="message-text loading">
              <span class="loading-dot"></span>
              <span class="loading-dot"></span>
              <span class="loading-dot"></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <div class="input-container">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="2"
            :placeholder="inputPlaceholder"
            :disabled="chatStore.loading"
            resize="none"
            @keydown.enter.exact.prevent="handleSend"
          />
          <el-button
            type="primary"
            :icon="Promotion"
            :loading="chatStore.loading"
            :disabled="!inputText.trim()"
            class="send-button"
            @click="handleSend"
          >
            发送
          </el-button>
        </div>
        <div class="input-hint">
          按 Enter 发送，Shift + Enter 换行
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Plus, Delete, Promotion, User, ChatDotRound } from '@element-plus/icons-vue'
import { useChatStore, useKnowledgeBaseStore } from '@/store'

const route = useRoute()
const chatStore = useChatStore()
const knowledgeBaseStore = useKnowledgeBaseStore()

const inputText = ref('')
const messagesContainer = ref<HTMLElement | null>(null)

// 当前知识库名称
const currentKnowledgeBaseName = computed(() => {
  if (chatStore.currentKnowledgeBaseId) {
    const kb = knowledgeBaseStore.knowledgeBases.find(
      (kb) => kb.id === chatStore.currentKnowledgeBaseId
    )
    return kb?.name || ''
  }
  return ''
})

// 从路由参数获取知识库 ID
watch(
  () => route.query.knowledgeBaseId,
  (newKbId) => {
    if (newKbId && typeof newKbId === 'string') {
      chatStore.currentKnowledgeBaseId = newKbId
      // 如果还没加载知识库列表，先加载
      if (knowledgeBaseStore.knowledgeBases.length === 0) {
        knowledgeBaseStore.fetchKnowledgeBases()
      }
    }
  },
  { immediate: true }
)

const inputPlaceholder = computed(() => {
  return chatStore.hasMessages ? '输入问题...' : '请先上传文档，然后输入问题...'
})

function formatTime(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function handleSend() {
  const text = inputText.value.trim()
  if (!text || chatStore.loading) return

  inputText.value = ''
  await chatStore.sendMessage(text, chatStore.currentKnowledgeBaseId)

  // 滚动到底部
  await nextTick()
  scrollToBottom()
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

function handleNewChat() {
  chatStore.createSession()
  inputText.value = ''
}

async function handleClearChat() {
  try {
    await ElMessageBox.confirm('确定要清空当前对话吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    chatStore.clearCurrentSession()
    ElMessage.success('对话已清空')
  } catch {
    // 取消操作
  }
}

onMounted(() => {
  chatStore.init()
})
</script>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.welcome {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #6b7280;
}

.welcome-icon {
  margin-bottom: 24px;
  color: #3b82f6;
}

.welcome h2 {
  font-size: 24px;
  color: #1f2937;
  margin: 0 0 12px;
}

.welcome p {
  font-size: 14px;
  max-width: 400px;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user .message-avatar {
  background: #3b82f6;
  color: white;
}

.assistant .message-avatar {
  background: #f3f4f6;
  color: #6b7280;
}

.message-content {
  max-width: 70%;
}

.user .message-content {
  text-align: right;
}

.message-text {
  background: #f3f4f6;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.user .message-text {
  background: #3b82f6;
  color: white;
}

.message-time {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px;
}

.user .message-time {
  text-align: right;
}

.loading {
  display: flex;
  gap: 4px;
  padding: 16px 20px;
}

.loading-dot {
  width: 8px;
  height: 8px;
  background: #9ca3af;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dot:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%,
  80%,
  100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.input-area {
  padding: 16px 24px 24px;
  background: white;
  border-top: 1px solid #e5e7eb;
}

.input-container {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-container :deep(.el-textarea) {
  flex: 1;
}

.input-container :deep(.el-textarea__inner) {
  border-radius: 12px;
}

.send-button {
  height: 68px;
  width: 100px;
  border-radius: 12px;
}

.input-hint {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 8px;
  text-align: center;
}
</style>
