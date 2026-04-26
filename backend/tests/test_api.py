"""API 接口测试"""
import pytest
from fastapi.testclient import TestClient


class TestRootAPI:
    """根路由测试"""
    
    def test_root_endpoint(self, client: TestClient):
        """测试根路径返回正确信息"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data
        assert data["name"] == "智能文档问答系统"


class TestHealthAPI:
    """健康检查 API 测试"""
    
    def test_health_check(self, client: TestClient):
        """测试健康检查端点"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证响应字段
        assert "status" in data
        assert "version" in data
        assert "llm_connected" in data
        assert "vectorstore_connected" in data
        assert "document_count" in data
        
        # status 应该是 healthy 或 degraded
        assert data["status"] in ["healthy", "degraded"]


class TestKnowledgeBaseAPI:
    """知识库 API 测试"""
    
    def test_create_knowledge_base(self, client: TestClient):
        """测试创建知识库"""
        response = client.post(
            "/api/v1/knowledge-bases",
            json={"name": "测试知识库", "description": "这是一个测试知识库"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["name"] == "测试知识库"
        assert data["description"] == "这是一个测试知识库"
        assert data["document_count"] == 0
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_knowledge_base_without_description(self, client: TestClient):
        """测试创建知识库（无描述）"""
        response = client.post(
            "/api/v1/knowledge-bases",
            json={"name": "测试知识库2"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "测试知识库2"
        assert data["description"] is None
    
    def test_create_knowledge_base_empty_name(self, client: TestClient):
        """测试创建知识库（空名称应失败）"""
        response = client.post(
            "/api/v1/knowledge-bases",
            json={"name": ""}
        )
        
        # Pydantic 验证应返回 422
        assert response.status_code == 422
    
    def test_list_knowledge_bases(self, client: TestClient):
        """测试列出知识库"""
        response = client.get("/api/v1/knowledge-bases")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)
    
    def test_list_knowledge_bases_pagination(self, client: TestClient):
        """测试知识库分页"""
        response = client.get("/api/v1/knowledge-bases?skip=0&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 0
        assert len(data["items"]) <= 10
    
    def test_get_knowledge_base_not_found(self, client: TestClient):
        """测试获取不存在的知识库"""
        response = client.get("/api/v1/knowledge-bases/nonexistent-id")
        
        assert response.status_code == 404
    
    def test_update_knowledge_base(self, client: TestClient):
        """测试更新知识库"""
        # 先创建
        create_response = client.post(
            "/api/v1/knowledge-bases",
            json={"name": "原始名称"}
        )
        kb_id = create_response.json()["id"]
        
        # 更新
        update_response = client.put(
            f"/api/v1/knowledge-bases/{kb_id}",
            json={"name": "新名称", "description": "新描述"}
        )
        
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["name"] == "新名称"
        assert data["description"] == "新描述"
    
    def test_delete_knowledge_base(self, client: TestClient):
        """测试删除知识库"""
        # 先创建
        create_response = client.post(
            "/api/v1/knowledge-bases",
            json={"name": "待删除知识库"}
        )
        kb_id = create_response.json()["id"]
        
        # 删除
        delete_response = client.delete(f"/api/v1/knowledge-bases/{kb_id}")
        
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert data["success"] is True
        
        # 确认已删除
        get_response = client.get(f"/api/v1/knowledge-bases/{kb_id}")
        assert get_response.status_code == 404


class TestDocumentAPI:
    """文档 API 测试"""
    
    def test_list_documents(self, client: TestClient):
        """测试列出文档"""
        response = client.get("/api/v1/documents")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)
    
    def test_list_documents_pagination(self, client: TestClient):
        """测试文档分页"""
        response = client.get("/api/v1/documents?skip=0&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 5
    
    def test_get_vectorstore_info(self, client: TestClient):
        """测试获取向量库信息"""
        response = client.get("/api/v1/documents/vectorstore/info")
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证向量库信息结构
        assert isinstance(data, dict)
    
    def test_get_document_not_found(self, client: TestClient):
        """测试获取不存在的文档"""
        response = client.get("/api/v1/documents/nonexistent-id")
        
        # 由于内存中没有这个文档，应该返回 404
        assert response.status_code == 404 or response.status_code == 500
    
    def test_delete_document_not_found(self, client: TestClient):
        """测试删除不存在的文档"""
        response = client.delete("/api/v1/documents/nonexistent-id")
        
        assert response.status_code == 404


class TestChatAPI:
    """聊天 API 测试"""
    
    def test_get_history_empty(self, client: TestClient):
        """测试获取空的对话历史"""
        response = client.get("/api/v1/chat/history/test-session-123")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "session_id" in data
        assert "messages" in data
        assert data["session_id"] == "test-session-123"
        assert data["messages"] == []
    
    def test_clear_history(self, client: TestClient):
        """测试清除对话历史"""
        response = client.delete("/api/v1/chat/history/test-session-456")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data
        assert "message" in data
    
    def test_chat_health_check(self, client: TestClient):
        """测试问答服务健康检查"""
        response = client.post("/api/v1/chat/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "llm_connected" in data


class TestCORS:
    """CORS 配置测试"""
    
    def test_cors_headers(self, client: TestClient):
        """测试 CORS 头"""
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )
        
        # CORS 预检请求应该成功
        assert response.status_code == 200
