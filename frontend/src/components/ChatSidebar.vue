<template>
  <div class="chat-sidebar" :class="{ collapsed: !visible }">
    <!-- 侧边栏头部 -->
    <div class="sidebar-header">
      <h3>历史对话</h3>
      <el-button :icon="Plus" circle size="small" @click="handleNewChat" />
    </div>

    <!-- 搜索框 -->
    <div class="sidebar-search">
      <el-input
        v-model="searchQuery"
        placeholder="搜索对话..."
        :prefix-icon="Search"
        clearable
        size="small"
      />
    </div>

    <!-- 会话列表 -->
    <div class="sidebar-content">
      <div v-if="filteredSessions.length === 0" class="empty-state">
        <el-icon :size="32"><ChatLineRound /></el-icon>
        <p>{{ searchQuery ? '没有找到匹配的对话' : '暂无历史对话' }}</p>
      </div>

      <div
        v-for="session in filteredSessions"
        :key="session.id"
        class="session-item"
        :class="{ active: session.id === chatStore.currentSessionId }"
        @click="handleSelectSession(session.id)"
      >
        <div class="session-info">
          <div class="session-title">{{ session.title }}</div>
          <div class="session-time">{{ formatTime(session.updatedAt) }}</div>
        </div>
        <el-dropdown
          trigger="click"
          @command="(cmd: string) => handleCommand(cmd, session.id)"
          @click.stop
        >
          <el-button :icon="More" text size="small" @click.stop />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="rename">
                <el-icon><Edit /></el-icon>
                重命名
              </el-dropdown-item>
              <el-dropdown-item command="delete" divided>
                <el-icon><Delete /></el-icon>
                删除
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 底部操作 -->
    <div class="sidebar-footer">
      <el-button type="primary" class="new-chat-btn" @click="handleNewChat">
        <el-icon><Plus /></el-icon>
        新建对话
      </el-button>
    </div>

    <!-- 重命名对话框 -->
    <el-dialog
      v-model="renameDialogVisible"
      title="重命名对话"
      width="400px"
    >
      <el-input v-model="newTitle" placeholder="输入新标题" />
      <template #footer>
        <el-button @click="renameDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleRename">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Plus, Search, More, Delete, Edit, ChatLineRound } from '@element-plus/icons-vue'
import { useChatStore } from '@/store'
import { updateSession } from '@/api/chat-session'

const props = defineProps<{
  visible: boolean
}>()

const chatStore = useChatStore()

const searchQuery = ref('')
const renameDialogVisible = ref(false)
const renameSessionId = ref('')
const newTitle = ref('')

// 过滤后的会话列表
const filteredSessions = computed(() => {
  if (!searchQuery.value.trim()) {
    return chatStore.sessions
  }
  const query = searchQuery.value.toLowerCase()
  return chatStore.sessions.filter((s) =>
    s.title.toLowerCase().includes(query)
  )
})

// 格式化时间
function formatTime(isoString: string): string {
  if (!isoString) return ''
  const date = new Date(isoString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  // 一天内显示时间
  if (diff < 24 * 60 * 60 * 1000) {
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  // 7天内显示星期
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
    return weekdays[date.getDay()]
  }

  // 更早显示日期
  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
  })
}

// 新建对话
function handleNewChat() {
  chatStore.createSession()
}

// 选择会话
async function handleSelectSession(sessionId: string) {
  await chatStore.switchSession(sessionId)
}

// 下拉菜单命令
function handleCommand(command: string, sessionId: string) {
  if (command === 'rename') {
    const session = chatStore.sessions.find((s) => s.id === sessionId)
    if (session) {
      renameSessionId.value = sessionId
      newTitle.value = session.title
      renameDialogVisible.value = true
    }
  } else if (command === 'delete') {
    handleDelete(sessionId)
  }
}

// 重命名
async function handleRename() {
  if (!newTitle.value.trim()) {
    ElMessage.warning('标题不能为空')
    return
  }

  try {
    await updateSession(renameSessionId.value, { title: newTitle.value.trim() })

    // 更新本地状态
    const session = chatStore.sessions.find(
      (s) => s.id === renameSessionId.value
    )
    if (session) {
      session.title = newTitle.value.trim()
    }

    renameDialogVisible.value = false
    ElMessage.success('重命名成功')
  } catch (error) {
    console.error('Failed to rename session:', error)
    ElMessage.error('重命名失败')
  }
}

// 删除会话
async function handleDelete(sessionId: string) {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个对话吗？删除后无法恢复。',
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await chatStore.deleteSession(sessionId)
    ElMessage.success('删除成功')
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
.chat-sidebar {
  width: 280px;
  height: 100%;
  background: #f7f8fa;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  overflow: hidden;
}

.chat-sidebar.collapsed {
  width: 0;
  border-right: none;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.sidebar-search {
  padding: 12px 16px;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #9ca3af;
  text-align: center;
}

.empty-state p {
  margin: 12px 0 0;
  font-size: 14px;
}

.session-item {
  display: flex;
  align-items: center;
  padding: 12px;
  margin-bottom: 4px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.session-item:hover {
  background: #e5e7eb;
}

.session-item.active {
  background: #3b82f6;
  color: white;
}

.session-item.active .session-time {
  color: rgba(255, 255, 255, 0.7);
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-title {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-time {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #e5e7eb;
}

.new-chat-btn {
  width: 100%;
}
</style>
