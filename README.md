# 智能文档问答系统 (NextRAG)

基于 RAG (Retrieval-Augmented Generation) 的智能文档问答系统，支持文档上传、向量检索和智能问答。

## 项目预览

```
┌─────────────────────────────────────────────────────────┐
│                    NextRAG 架构图                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐             │
│   │  前端   │───▶│ FastAPI │───▶│ LLM API │             │
│   │ (Vue3) │    │ Backend │    │(DeepSeek)│             │
│   └─────────┘    └────┬────┘    └─────────┘             │
│                       │                                  │
│         ┌─────────────┼─────────────┐                    │
│         │             │             │                    │
│   ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐             │
│   │  VectorDB │ │   Redis   │ │  SQLite   │             │
│   │ (Chroma)  │ │ (History) │ │ (Meta)    │             │
│   └───────────┘ └───────────┘ └───────────┘             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 技术栈

### 前端
- **框架**: Vue 3 + TypeScript
- **构建工具**: Vite
- **状态管理**: Pinia
- **HTTP 客户端**: Axios
- **样式**: SCSS + CSS Variables

### 后端
- **框架**: FastAPI
- **语言**: Python 3.11+
- **向量数据库**: ChromaDB
- **缓存**: Redis
- **数据库**: SQLite
- **LLM**: DeepSeek API

## 目录结构

```
智能问答系统/
├── backend/                    # 后端项目
│   ├── app/
│   │   ├── api/               # API 路由
│   │   │   ├── chat.py        # 对话 API
│   │   │   ├── chat_session.py # 会话管理 API
│   │   │   ├── document.py    # 文档 API
│   │   │   ├── knowledge.py    # 知识库 API
│   │   │   └── system.py      # 系统 API
│   │   ├── core/              # 核心模块
│   │   │   ├── rag_chain.py   # RAG 链
│   │   │   ├── embeddings.py   # 向量化
│   │   │   ├── vectorstore.py # 向量存储
│   │   │   └── document_loader.py
│   │   ├── models/           # 数据模型
│   │   ├── services/         # 业务服务
│   │   ├── config.py         # 配置管理
│   │   └── main.py           # 应用入口
│   ├── tests/                # 测试用例
│   ├── data/                 # 数据目录
│   ├── requirements.txt
│   └── README.md
│
├── frontend/                   # 前端项目
│   ├── src/
│   │   ├── api/              # API 调用
│   │   │   ├── chat.ts         # 对话 API
│   │   │   ├── chat-session.ts # 会话管理 API
│   │   ├── components/        # 公共组件
│   │   │   ├── ChatSidebar.vue # 聊天侧边栏
│   │   ├── layouts/          # 布局组件
│   │   ├── router/           # 路由配置
│   │   ├── store/            # 状态管理
│   │   ├── views/            # 页面视图
│   │   │   ├── ChatView.vue       # 对话页面
│   │   │   ├── DocumentsView.vue   # 文档管理
│   │   │   └── KnowledgeBasesView.vue
│   │   ├── App.vue
│   │   └── main.ts
│   └── package.json
│
└── README.md                  # 项目总览
```

## 快速开始

### 环境要求

- Node.js >= 18
- Python >= 3.11
- Redis (可选，用于对话历史)

### 1. 克隆项目

```bash
git clone https://github.com/Jackson-da/nextrag.git
cd nextrag
```

### 2. 后端配置

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的配置
```

#### 环境变量配置 (.env)

```env
# DeepSeek API 配置
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 向量数据库配置
EMBEDDING_MODEL=text-embedding-3-small
VECTORSTORE_PERSIST_DIR=./data/chroma_db

# Redis 配置 (可选)
REDIS_URL=redis://localhost:6379/0

# CORS 配置
CORS_ORIGINS=["http://localhost:5173","http://localhost:5174"]

# RAG 配置
RETRIEVAL_TOP_K=5
TEMPERATURE=0.4
MAX_TOKENS=2000
```

### 3. 前端配置

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env
```

### 4. 启动服务

#### 开发模式

```bash
# 终端 1 - 启动后端
cd backend
uvicorn app.main:app --reload --port 8000

# 终端 2 - 启动前端
cd frontend
npm run dev
```

访问：
- 前端: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

#### 生产模式

```bash
# 构建前端
cd frontend
npm run build

# 后端使用 uvicorn
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 功能特性

### 1. 文档管理
- [x] 文档上传 (支持 PDF, TXT, Markdown)
- [x] 文档列表查看
- [x] 文档删除
- [x] 文件类型识别

### 2. 知识库管理
- [x] 创建知识库
- [x] 知识库列表
- [x] 关联文档管理
- [x] 知识库删除

### 3. 智能问答
- [x] 基于 RAG 的问答
- [x] 流式输出
- [x] 多轮对话支持
- [x] 历史对话记忆

### 4. 会话管理
- [x] 创建/删除会话
- [x] 会话列表查看
- [x] 会话重命名
- [x] 消息历史管理
- [x] 用户会话隔离
- [x] 关联知识库

## API 文档

### 对话 API

```
POST /api/v1/chat/stream
请求体:
{
    "message": "问题内容",
    "session_id": "会话ID"  // 可选
}

响应: SSE 流式输出
```

### 文档 API

```
GET    /api/v1/documents          # 获取文档列表
POST   /api/v1/documents/upload   # 上传文档
DELETE /api/v1/documents/{id}     # 删除文档
```

### 知识库 API

```
GET    /api/v1/knowledge-bases           # 获取知识库列表
POST   /api/v1/knowledge-bases            # 创建知识库
DELETE /api/v1/knowledge-bases/{id}       # 删除知识库
```

### 会话管理 API

```
GET    /api/v1/chat/sessions              # 获取会话列表
POST   /api/v1/chat/sessions              # 创建会话
GET    /api/v1/chat/sessions/{id}         # 获取会话详情
PATCH  /api/v1/chat/sessions/{id}         # 更新会话
DELETE /api/v1/chat/sessions/{id}         # 删除会话
GET    /api/v1/chat/sessions/{id}/messages # 获取会话消息
DELETE /api/v1/chat/sessions/{id}/messages # 清空会话消息
```

## 项目截图

| 对话页面 | 文档管理 | 知识库 |
|:--------:|:--------:|:------:|
| ![Chat] | ![Docs] | ![KB] |

## 开发指南

### 添加新的 API 路由

1. 在 `backend/app/api/` 创建新的路由文件
2. 注册到 `app/main.py` 的 `app.include_router()`

```python
# backend/app/api/new_route.py
from fastapi import APIRouter
router = APIRouter(prefix="/api/v1/new", tags=["new"])

@router.get("/items")
async def get_items():
    return {"items": []}
```

### 添加新的前端页面

1. 在 `frontend/src/views/` 创建 Vue 组件
2. 在 `frontend/src/router/index.ts` 添加路由

```typescript
// frontend/src/router/index.ts
{
    path: '/new-page',
    name: 'NewPage',
    component: () => import('@/views/NewPage.vue')
}
```

## 测试

```bash
cd backend

# 运行所有测试
pytest

# 运行指定测试
pytest tests/test_api.py

# 运行会话管理测试
pytest tests/test_chat_session.py -v

# 查看覆盖率
pytest --cov=app tests/
```

## 配置说明

### 提示词配置

可在 `.env` 中自定义 RAG 提示词：

```env
RAG_SYSTEM_PROMPT=你是一个专业的文档问答助手...
RAG_CONTEXTUALIZE_PROMPT=根据对话历史重写问题...
```

### 模型参数

```env
TEMPERATURE=0.4      # 创造性程度 (0-2)
MAX_TOKENS=2000      # 最大输出token数
RETRIEVAL_TOP_K=5    # 检索返回数量
```

## 常见问题

### Q: 向量数据库启动失败？
A: 确保 ChromaDB 数据目录存在且有写入权限。

### Q: API 调用失败？
A: 检查 `.env` 中的 `DEEPSEEK_API_KEY` 是否正确配置。

### Q: 前端无法连接后端？
A: 检查 CORS 配置是否包含前端地址。

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## License

本项目采用 MIT License - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- GitHub Issues: [Issues](https://github.com/Jackson-da/nextrag/issues)
- 作者: Jackson

---

<div align="center">

**如果这个项目对你有帮助，请给个 Star ⭐**

</div>
