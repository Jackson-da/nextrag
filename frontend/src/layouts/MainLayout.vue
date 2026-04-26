<template>
  <div class="app-container">
    <!-- 侧边栏 -->
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ChatDotRound, Document, Collection } from '@element-plus/icons-vue'
import request from '@/api/request'

const navItems = [
  { path: '/chat', label: '智能问答', icon: ChatDotRound },
  { path: '/documents', label: '文档管理', icon: Document },
  { path: '/knowledge-bases', label: '知识库', icon: Collection },
]

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

onMounted(() => {
  checkHealth()
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
  overflow: auto;
  background: #f5f7fa;
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

.system-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
}

.version {
  color: rgba(255, 255, 255, 0.5);
}
</style>
