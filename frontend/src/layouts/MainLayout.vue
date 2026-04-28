<template>
  <div class="app-container">
    <!-- 左侧导航栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="logo">
          <el-icon :size="24"><ChatDotRound /></el-icon>
          <span class="logo-text">智能问答</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          active-class="nav-item-active"
        >
          <el-icon :size="20"><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <!-- 用户信息 -->
        <div class="user-info">
          <el-dropdown @command="handleUserCommand">
            <span class="user-dropdown">
              <el-icon><User /></el-icon>
              <span class="username">{{ username }}</span>
              <el-icon class="arrow"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>

        <div class="system-info">
          <el-tag :type="healthStatus.type" size="small">
            {{ healthStatus.text }}
          </el-tag>
          <span class="version">v1.0.0</span>
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <router-view />
    </main>

    <!-- 聊天会话侧边栏 (仅在聊天页面显示，位于右侧) -->
    <ChatSidebar v-if="showChatSidebar" v-model:visible="chatSidebarVisible" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ChatDotRound, Document, Collection, User, ArrowDown, SwitchButton } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
import { tokenManager, authApi } from '@/api/auth'
import ChatSidebar from '@/components/ChatSidebar.vue'
import { useChatStore } from '@/store/chat'

const router = useRouter()
const route = useRoute()
const chatStore = useChatStore()

const navItems = [
  { path: '/chat', label: '智能问答', icon: ChatDotRound },
  { path: '/documents', label: '文档管理', icon: Document },
  { path: '/knowledge-bases', label: '知识库', icon: Collection },
]

// 是否显示聊天侧边栏
const showChatSidebar = computed(() => route.path === '/chat')
const chatSidebarVisible = ref(true)

const username = ref('用户')
const health = ref({
  status: 'checking',
  version: '',
  llm_connected: false,
  vectorstore_connected: false,
})

const healthStatus = computed(() => {
  if (health.value.status === 'checking') {
    return { type: 'info', text: '检测中...' }
  }
  if (health.value.llm_connected && health.value.vectorstore_connected) {
    return { type: 'success', text: '运行正常' }
  }
  return { type: 'warning', text: '部分异常' }
})

async function checkHealth() {
  try {
    const data = await request.get('/health')
    health.value = data
  } catch {
    health.value.status = 'error'
  }
}

async function fetchUserInfo() {
  try {
    const user = await authApi.getCurrentUser()
    username.value = user.username
  } catch {
    // 未登录时不显示用户名
  }
}

function handleUserCommand(command: string) {
  if (command === 'logout') {
    tokenManager.removeToken()
    chatStore.reset() // 清空会话历史
    ElMessage.success('已退出登录')
    router.push('/login')
  }
}

onMounted(() => {
  checkHealth()
  if (tokenManager.isLoggedIn()) {
    fetchUserInfo()
  }
})
</script>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.sidebar {
  width: 220px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%);
  color: white;
}

.main-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  min-width: 0;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
}

.sidebar-nav {
  flex: 1;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  transition: all 0.2s;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-item-active {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.user-info {
  margin-bottom: 12px;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.9);
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 8px;
  transition: background 0.2s;
}

.user-dropdown:hover {
  background: rgba(255, 255, 255, 0.1);
}

.username {
  flex: 1;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.arrow {
  font-size: 12px;
}

.system-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
}

.version {
  color: rgba(255, 255, 255, 0.5);
}

/* 聊天侧边栏样式 - 右侧显示 */
:deep(.chat-sidebar) {
  order: 2;
  border-right: none;
  border-left: 1px solid #e5e7eb;
}

:deep(.chat-sidebar.collapsed) {
  border-left: none;
}
</style>
