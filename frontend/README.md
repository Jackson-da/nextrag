# 智能文档问答系统 - 前端

基于 Vue 3 + TypeScript 的智能文档问答系统前端项目。

## 技术栈

- **框架**: Vue 3.5+ (Composition API + `<script setup>`)
- **构建工具**: Vite 6+
- **语言**: TypeScript 5.7+
- **状态管理**: Pinia 2.3+
- **路由**: Vue Router 4.5+
- **UI 组件**: Element Plus 2.9+
- **样式**: Tailwind CSS 3.4+
- **HTTP 客户端**: Axios

## 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件（可选，使用默认值即可）
```

### 3. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:5173 查看应用。

### 4. 构建生产版本

```bash
npm run build
```

## 项目结构

```
frontend/
├── src/
│   ├── api/              # API 接口层
│   │   ├── request.ts    # Axios 封装
│   │   ├── document.ts   # 文档 API
│   │   ├── chat.ts       # 问答 API
│   │   └── knowledge.ts  # 知识库 API
│   ├── components/       # 公共组件
│   ├── layouts/          # 布局组件
│   ├── router/           # 路由配置
│   ├── store/            # Pinia 状态管理
│   │   ├── document.ts   # 文档状态
│   │   ├── chat.ts       # 问答状态
│   │   └── knowledge.ts  # 知识库状态
│   ├── styles/           # 全局样式
│   ├── types/            # TypeScript 类型定义
│   ├── utils/            # 工具函数
│   ├── views/            # 页面组件
│   │   ├── ChatView.vue      # 问答页面
│   │   ├── DocumentsView.vue  # 文档管理页面
│   │   └── KnowledgeBasesView.vue  # 知识库页面
│   ├── App.vue           # 根组件
│   └── main.ts          # 应用入口
├── public/              # 静态资源
├── index.html           # HTML 入口
├── package.json
├── vite.config.ts      # Vite 配置
├── tsconfig.json        # TypeScript 配置
└── tailwind.config.js   # Tailwind CSS 配置
```

## 功能特性

- 📄 **文档管理**: 上传、查看、删除文档（支持 PDF、Word、TXT、Markdown）
- 💬 **智能问答**: 基于 RAG 的文档问答，支持流式输出
- 📚 **知识库管理**: 创建、管理多个知识库
- 💾 **对话历史**: 自动保存对话历史

## 开发指南

### 代码规范

```bash
# 代码格式化
npm run format

# 代码检查
npm run lint
```

### API 代理

开发环境下，Vite 会将 `/api` 请求代理到 `http://localhost:8000`（后端服务）。

如需修改，编辑 `vite.config.ts` 中的 `server.proxy` 配置。

## License

MIT License
