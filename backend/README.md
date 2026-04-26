# 智能文档问答系统 - 后端 API

基于 RAG (Retrieval-Augmented Generation) 的企业级智能文档问答系统后端服务。

## 技术栈

- **Web 框架**: FastAPI 0.115+
- **LLM**: DeepSeek-chat (支持 OpenAI 兼容接口)
- **Embedding**: BGE-large-zh-v1.5 (中文优化)
- **向量数据库**: Chroma
- **文档处理**: PyPDF, python-docx
- **配置管理**: Pydantic Settings

## 快速开始

### 1. 环境要求

- Python 3.10+
- 8GB+ RAM (推荐)

### 2. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key
```

主要配置项：
- `DEEPSEEK_API_KEY`: DeepSeek API 密钥
- `LLM_MODEL`: LLM 模型名称 (默认: deepseek-chat)
- `EMBEDDING_MODEL`: Embedding 模型 (默认: BAAI/bge-large-zh-v1.5)

### 4. 启动服务

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 接口

### 文档管理

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/v1/documents/upload` | POST | 上传文档 |
| `/api/v1/documents` | GET | 获取文档列表 |
| `/api/v1/documents/{id}` | GET | 获取文档详情 |
| `/api/v1/documents/{id}` | DELETE | 删除文档 |

### 问答

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/v1/chat/chat` | POST | 问答 (非流式) |
| `/api/v1/chat/stream` | POST | 问答 (流式) |
| `/api/v1/chat/history/{session_id}` | GET | 获取对话历史 |
| `/api/v1/chat/history/{session_id}` | DELETE | 清除对话历史 |

### 知识库

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/v1/knowledge-bases` | POST | 创建知识库 |
| `/api/v1/knowledge-bases` | GET | 获取知识库列表 |
| `/api/v1/knowledge-bases/{id}` | GET | 获取知识库详情 |
| `/api/v1/knowledge-bases/{id}` | PUT | 更新知识库 |
| `/api/v1/knowledge-bases/{id}` | DELETE | 删除知识库 |

## 项目结构

```
backend/
├── app/
│   ├── api/              # API 接口层
│   │   ├── document.py   # 文档管理接口
│   │   ├── chat.py      # 问答接口
│   │   └── knowledge.py # 知识库接口
│   ├── core/            # 核心模块
│   │   ├── document_loader.py  # 文档加载
│   │   ├── text_splitter.py    # 文本分割
│   │   ├── embeddings.py       # 向量化
│   │   ├── vectorstore.py     # 向量存储
│   │   └── rag_chain.py       # RAG 链
│   ├── models/          # 数据模型
│   │   └── schemas.py    # Pydantic 模型
│   ├── services/        # 业务服务层
│   │   ├── document_service.py
│   │   └── chat_service.py
│   ├── middleware/       # 中间件
│   ├── config.py        # 配置管理
│   └── main.py          # 应用入口
├── tests/               # 测试目录
├── data/                # 数据存储 (自动创建)
├── requirements.txt     # Python 依赖
└── .env.example         # 环境变量示例
```

## 开发指南

### 运行测试

```bash
pytest tests/ -v
```

### 代码格式化

```bash
ruff format .
ruff check --fix .
```

### 类型检查

```bash
mypy app/
```

## License

MIT License
