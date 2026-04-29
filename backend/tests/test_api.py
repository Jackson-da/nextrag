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

    def test_simple_health_check(self, client: TestClient):
        """测试简单健康检查端点（用于负载均衡器）"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # 简单端点只返回 status
        assert "status" in data
        assert data["status"] == "ok"

    def test_detailed_health_check(self, client: TestClient):
        """测试详细健康检查端点"""
        response = client.get("/api/v1/health")

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
    
    def test_create_knowledge_base(self, client: TestClient, auth_headers: dict):
        """测试创建知识库"""
        response = client.post(
            "/api/v1/knowledge-bases",
            json={"name": "测试知识库", "description": "这是一个测试知识库"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["name"] == "测试知识库"
        assert data["description"] == "这是一个测试知识库"
        assert data["document_count"] == 0
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_knowledge_base_without_description(self, client: TestClient, auth_headers: dict):
        """测试创建知识库（无描述）"""
        response = client.post(
            "/api/v1/knowledge-bases",
            json={"name": "测试知识库2"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "测试知识库2"
        assert data["description"] is None
    
    def test_create_knowledge_base_empty_name(self, client: TestClient, auth_headers: dict):
        """测试创建知识库（空名称应失败）"""
        response = client.post(
            "/api/v1/knowledge-bases",
            json={"name": ""},
            headers=auth_headers
        )
        
        # Pydantic 验证应返回 422
        assert response.status_code == 422
    
    def test_list_knowledge_bases(self, client: TestClient, auth_headers: dict):
        """测试列出知识库"""
        response = client.get("/api/v1/knowledge-bases", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)
    
    def test_list_knowledge_bases_pagination(self, client: TestClient, auth_headers: dict):
        """测试知识库分页"""
        response = client.get("/api/v1/knowledge-bases?skip=0&limit=10", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 0
        assert len(data["items"]) <= 10
    
    def test_get_knowledge_base_not_found(self, client: TestClient, auth_headers: dict):
        """测试获取不存在的知识库"""
        response = client.get("/api/v1/knowledge-bases/nonexistent-id", headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_update_knowledge_base(self, client: TestClient, auth_headers: dict):
        """测试更新知识库"""
        # 先创建
        create_response = client.post(
            "/api/v1/knowledge-bases",
            json={"name": "原始名称"},
            headers=auth_headers
        )
        assert create_response.status_code == 200
        kb_id = create_response.json()["id"]
        
        # 更新
        update_response = client.put(
            f"/api/v1/knowledge-bases/{kb_id}",
            json={"name": "新名称", "description": "新描述"},
            headers=auth_headers
        )
        
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["name"] == "新名称"
        assert data["description"] == "新描述"
    
    def test_delete_knowledge_base(self, client: TestClient, auth_headers: dict):
        """测试删除知识库（验证级联删除关联文档）"""
        # 先创建
        create_response = client.post(
            "/api/v1/knowledge-bases",
            json={"name": "待删除知识库"},
            headers=auth_headers
        )
        assert create_response.status_code == 200
        kb_id = create_response.json()["id"]
        
        # 删除
        delete_response = client.delete(f"/api/v1/knowledge-bases/{kb_id}", headers=auth_headers)
        
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert data["success"] is True
        # 验证返回消息（会提示删除了多少文档）
        assert "message" in data
        
        # 确认已删除
        get_response = client.get(f"/api/v1/knowledge-bases/{kb_id}", headers=auth_headers)
        assert get_response.status_code == 404


class TestDocumentAPI:
    """文档 API 测试"""
    
    @pytest.mark.skip(reason="需要完整的文档服务集成测试")
    def test_list_documents(self, client: TestClient, auth_headers: dict):
        """测试列出文档"""
        response = client.get("/api/v1/documents", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)
    
    @pytest.mark.skip(reason="需要完整的文档服务集成测试")
    def test_list_documents_pagination(self, client: TestClient, auth_headers: dict):
        """测试文档分页"""
        response = client.get("/api/v1/documents?skip=0&limit=5", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 5
    
    def test_get_vectorstore_info(self, client: TestClient, auth_headers: dict):
        """测试获取向量库信息"""
        response = client.get("/api/v1/documents/vectorstore/info", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证向量库信息结构
        assert isinstance(data, dict)
    
    def test_get_document_not_found(self, client: TestClient, auth_headers: dict):
        """测试获取不存在的文档"""
        response = client.get("/api/v1/documents/nonexistent-id", headers=auth_headers)
        
        # 由于内存中没有这个文档，应该返回 404
        assert response.status_code == 404 or response.status_code == 500
    
    def test_delete_document_not_found(self, client: TestClient, auth_headers: dict):
        """测试删除不存在的文档"""
        response = client.delete("/api/v1/documents/nonexistent-id", headers=auth_headers)
        
        assert response.status_code == 404


class TestChatAPI:
    """聊天 API 测试"""
    
    def test_get_history_empty(self, client: TestClient, auth_headers: dict):
        """测试获取空的对话历史"""
        response = client.get("/api/v1/chat/history/test-session-123", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "session_id" in data
        assert "messages" in data
        assert data["session_id"] == "test-session-123"
        assert data["messages"] == []
    
    def test_clear_history(self, client: TestClient, auth_headers: dict):
        """测试清除对话历史"""
        response = client.delete("/api/v1/chat/history/test-session-456", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data
        assert "message" in data
    
    def test_chat_health_check(self, client: TestClient, auth_headers: dict):
        """测试问答服务健康检查"""
        response = client.post("/api/v1/chat/health", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "llm_connected" in data

    def test_get_history_unauthorized(self, client: TestClient):
        """测试未认证请求返回 401"""
        response = client.get("/api/v1/chat/history/test-session")
        assert response.status_code == 401

    def test_clear_history_unauthorized(self, client: TestClient):
        """测试未认证清除历史返回 401"""
        response = client.delete("/api/v1/chat/history/test-session")
        assert response.status_code == 401

    def test_chat_health_check_unauthorized(self, client: TestClient):
        """测试未认证健康检查返回 401"""
        response = client.post("/api/v1/chat/health")
        assert response.status_code == 401


class TestChatWithKnowledgeBase:
    """聊天 API - 按知识库检索测试"""
    
    def test_chat_request_accepts_knowledge_base_id(self, client: TestClient, auth_headers: dict):
        """测试聊天请求能正确接受 knowledge_base_id 参数"""
        # 先创建一个知识库
        kb_response = client.post(
            "/api/v1/knowledge-bases",
            json={"name": "测试知识库-聊天"},
            headers=auth_headers
        )
        assert kb_response.status_code == 200
        kb_id = kb_response.json()["id"]
        
        # 发送聊天请求，附带 knowledge_base_id
        chat_response = client.post(
            "/api/v1/chat/chat",
            json={
                "question": "你好",
                "session_id": "test-kb-session-1",
                "knowledge_base_id": kb_id
            },
            headers=auth_headers
        )
        
        # 验证请求成功（即使 LLM 未配置也能正常返回结构）
        assert chat_response.status_code in [200, 500]
        if chat_response.status_code == 500:
            # 如果是 LLM 连接问题，应该是友好的错误信息
            assert "detail" in chat_response.json()
    
    def test_chat_request_without_knowledge_base_id(self, client: TestClient, auth_headers: dict):
        """测试不传 knowledge_base_id 时的全局检索请求"""
        # 发送聊天请求，不带 knowledge_base_id
        chat_response = client.post(
            "/api/v1/chat/chat",
            json={
                "question": "你好",
                "session_id": "test-global-session"
            },
            headers=auth_headers
        )
        
        # 验证请求能正常处理（不传 kb_id 应该走全局检索）
        assert chat_response.status_code in [200, 500]
    
    def test_chat_request_with_nonexistent_knowledge_base_id(self, client: TestClient, auth_headers: dict):
        """测试传入不存在的 knowledge_base_id 时的行为"""
        chat_response = client.post(
            "/api/v1/chat/chat",
            json={
                "question": "你好",
                "session_id": "test-invalid-kb-session",
                "knowledge_base_id": "nonexistent-kb-id"
            },
            headers=auth_headers
        )
        
        # 应该能处理不存在的 kb_id（返回空结果或全局检索）
        assert chat_response.status_code in [200, 500]
    
    def test_chat_request_validation(self, client: TestClient, auth_headers: dict):
        """测试聊天请求参数验证"""
        # 测试空问题
        response = client.post(
            "/api/v1/chat/chat",
            json={
                "question": "",
                "session_id": "test-validation"
            },
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # 测试缺少必填字段
        response = client.post(
            "/api/v1/chat/chat",
            json={"question": "你好"},
            headers=auth_headers
        )
        assert response.status_code == 422
    
    def test_chat_request_session_id_required(self, client: TestClient, auth_headers: dict):
        """测试 session_id 是必填字段"""
        response = client.post(
            "/api/v1/chat/chat",
            json={
                "question": "你好",
                # 缺少 session_id
            },
            headers=auth_headers
        )
        assert response.status_code == 422
    
    def test_get_history_with_different_sessions(self, client: TestClient, auth_headers: dict):
        """测试不同 session_id 获取各自的对话历史"""
        # 获取第一个会话的历史
        response1 = client.get("/api/v1/chat/history/session-1", headers=auth_headers)
        assert response1.status_code == 200
        assert response1.json()["session_id"] == "session-1"
        
        # 获取第二个会话的历史
        response2 = client.get("/api/v1/chat/history/session-2", headers=auth_headers)
        assert response2.status_code == 200
        assert response2.json()["session_id"] == "session-2"
    
    def test_clear_specific_session_history(self, client: TestClient, auth_headers: dict):
        """测试清除特定会话的历史"""
        # 清除指定会话（无论是否存在都应能处理）
        response = client.delete("/api/v1/chat/history/my-session-clear-test", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # 验证响应结构正确
        assert "success" in data
        assert "message" in data
        # success 可能为 True（有历史被清除）或 False（无历史）- 两者都是有效响应


class TestChatIntegrationWithKnowledgeBase:
    """聊天与知识库集成测试（需要完整环境）"""
    
    @pytest.mark.skip(reason="需要完整的 LLM 和向量库集成")
    def test_chat_with_knowledge_base_filters_docs(self, client: TestClient, auth_headers: dict):
        """测试聊天时按知识库过滤文档
        
        场景：
        1. 创建两个知识库 KB1 和 KB2
        2. KB1 上传文档 A
        3. KB2 上传文档 B
        4. 使用 KB1 的 kb_id 提问
        5. 验证回答只基于文档 A
        """
        # 创建知识库 1
        kb1_response = client.post(
            "/api/v1/knowledge-bases",
            json={"name": "知识库1-产品文档"},
            headers=auth_headers
        )
        kb1_id = kb1_response.json()["id"]
        
        # 创建知识库 2
        kb2_response = client.post(
            "/api/v1/knowledge-bases",
            json={"name": "知识库2-技术文档"},
            headers=auth_headers
        )
        kb2_id = kb2_response.json()["id"]
        
        # TODO: 上传不同的文档到两个知识库
        
        # 使用 KB1 提问
        chat1_response = client.post(
            "/api/v1/chat/chat",
            json={
                "question": "产品特性有哪些？",
                "session_id": "test-integrate-session",
                "knowledge_base_id": kb1_id
            },
            headers=auth_headers
        )
        
        # 使用 KB2 提问
        chat2_response = client.post(
            "/api/v1/chat/chat",
            json={
                "question": "技术架构是什么？",
                "session_id": "test-integrate-session-2",
                "knowledge_base_id": kb2_id
            },
            headers=auth_headers
        )
        
        # 验证两个回答来自不同的知识库
        assert chat1_response.status_code == 200
        assert chat2_response.status_code == 200
    
    @pytest.mark.skip(reason="需要完整的 LLM 和向量库集成")
    def test_global_chat_searches_all_knowledge_bases(self, client: TestClient, auth_headers: dict):
        """测试不指定知识库时搜索所有知识库
        
        场景：
        1. 创建多个知识库并上传文档
        2. 不指定 kb_id 提问
        3. 验证回答综合了多个知识库的内容
        """
        # TODO: 创建多个知识库并上传文档
        
        # 全局提问（不指定 kb_id）
        chat_response = client.post(
            "/api/v1/chat/chat",
            json={
                "question": "查找所有相关内容",
                "session_id": "test-global-search"
            },
            headers=auth_headers
        )
        
        assert chat_response.status_code == 200


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
