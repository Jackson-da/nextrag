"""聊天会话 API 测试"""
import uuid
import pytest
from fastapi.testclient import TestClient
from fastapi import status


class TestSessionCreation:
    """会话创建测试"""

    def test_create_session_success(self, client: TestClient, auth_headers: dict):
        """测试成功创建会话"""
        response = client.post(
            "/api/v1/chat/sessions",
            headers=auth_headers,
            json={"title": "测试对话"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert data["title"] == "测试对话"
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_session_without_title(self, client: TestClient, auth_headers: dict):
        """测试不提供标题时使用默认值"""
        response = client.post(
            "/api/v1/chat/sessions",
            headers=auth_headers,
            json={}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "新对话"

    def test_create_session_with_knowledge_base(
        self, client: TestClient, auth_headers: dict
    ):
        """测试关联知识库创建会话"""
        kb_id = str(uuid.uuid4())
        response = client.post(
            "/api/v1/chat/sessions",
            headers=auth_headers,
            json={
                "title": "知识库对话",
                "knowledge_base_id": kb_id
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["knowledge_base_id"] == kb_id

    def test_create_session_unauthorized(self, client: TestClient):
        """测试未认证创建会话"""
        response = client.post(
            "/api/v1/chat/sessions",
            json={"title": "测试"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_multiple_sessions(self, client: TestClient, auth_headers: dict):
        """测试创建多个会话"""
        for i in range(3):
            response = client.post(
                "/api/v1/chat/sessions",
                headers=auth_headers,
                json={"title": f"对话 {i + 1}"}
            )
            assert response.status_code == status.HTTP_200_OK


class TestSessionList:
    """会话列表测试"""

    def test_list_sessions_empty(self, client: TestClient, auth_headers: dict):
        """测试空会话列表"""
        response = client.get(
            "/api/v1/chat/sessions",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "sessions" in data
        assert isinstance(data["sessions"], list)

    def test_list_sessions_with_data(self, client: TestClient, auth_headers: dict):
        """测试获取包含会话的列表"""
        # 先创建几个会话
        for title in ["会话1", "会话2", "会话3"]:
            client.post(
                "/api/v1/chat/sessions",
                headers=auth_headers,
                json={"title": title}
            )

        response = client.get(
            "/api/v1/chat/sessions",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["sessions"]) >= 3

    def test_list_sessions_unauthorized(self, client: TestClient):
        """测试未认证获取会话列表"""
        response = client.get("/api/v1/chat/sessions")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestSessionUpdate:
    """会话更新测试"""

    def test_update_session_title(self, client: TestClient, auth_headers: dict):
        """测试更新会话标题"""
        # 创建会话
        create_response = client.post(
            "/api/v1/chat/sessions",
            headers=auth_headers,
            json={"title": "原始标题"}
        )
        session_id = create_response.json()["id"]

        # 更新标题
        response = client.patch(
            f"/api/v1/chat/sessions/{session_id}",
            headers=auth_headers,
            json={"title": "新标题"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["title"] == "新标题"

    def test_update_nonexistent_session(self, client: TestClient, auth_headers: dict):
        """测试更新不存在的会话"""
        fake_id = str(uuid.uuid4())
        response = client.patch(
            f"/api/v1/chat/sessions/{fake_id}",
            headers=auth_headers,
            json={"title": "新标题"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_other_user_session(
        self, client: TestClient, test_user: "UserModel", auth_headers: dict, db_session: "Session"
    ):
        """测试不能更新其他用户的会话"""
        from app.core.security import create_access_token

        # 创建另一个用户（使用测试数据库会话）
        from app.models.user import UserModel
        from app.core.security import hash_password
        import uuid as uuid_module

        other_user_id = str(uuid_module.uuid4())
        other_user = UserModel(
            id=other_user_id,
            username=f"other_user_{uuid_module.uuid4().hex[:8]}",
            password_hash=hash_password("password123")
        )
        db_session.add(other_user)
        db_session.commit()

        other_token = create_access_token(data={"sub": other_user_id})
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # 用用户1创建会话
        create_response = client.post(
            "/api/v1/chat/sessions",
            headers=auth_headers,
            json={"title": "用户1的会话"}
        )
        session_id = create_response.json()["id"]

        # 用户2尝试更新用户1的会话
        response = client.patch(
            f"/api/v1/chat/sessions/{session_id}",
            headers=other_headers,
            json={"title": "被劫持的标题"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestSessionDelete:
    """会话删除测试"""

    def test_delete_session_success(self, client: TestClient, auth_headers: dict):
        """测试成功删除会话"""
        # 创建会话
        create_response = client.post(
            "/api/v1/chat/sessions",
            headers=auth_headers,
            json={"title": "待删除会话"}
        )
        session_id = create_response.json()["id"]

        # 删除会话
        response = client.delete(
            f"/api/v1/chat/sessions/{session_id}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["success"] is True

        # 验证会话已删除
        get_response = client.get(
            f"/api/v1/chat/sessions/{session_id}",
            headers=auth_headers
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_nonexistent_session(self, client: TestClient, auth_headers: dict):
        """测试删除不存在的会话"""
        fake_id = str(uuid.uuid4())
        response = client.delete(
            f"/api/v1/chat/sessions/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_other_user_session(
        self, client: TestClient, auth_headers: dict, db_session: "Session"
    ):
        """测试不能删除其他用户的会话"""
        from app.core.security import create_access_token

        # 创建另一个用户（使用测试数据库会话）
        from app.models.user import UserModel
        from app.core.security import hash_password
        import uuid as uuid_module

        other_user_id = str(uuid_module.uuid4())
        other_user = UserModel(
            id=other_user_id,
            username=f"delete_test_{uuid_module.uuid4().hex[:8]}",
            password_hash=hash_password("password123")
        )
        db_session.add(other_user)
        db_session.commit()

        other_token = create_access_token(data={"sub": other_user_id})
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # 用户1创建会话
        create_response = client.post(
            "/api/v1/chat/sessions",
            headers=auth_headers,
            json={"title": "用户1的会话"}
        )
        session_id = create_response.json()["id"]

        # 用户2尝试删除
        response = client.delete(
            f"/api/v1/chat/sessions/{session_id}",
            headers=other_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

        # 验证会话仍然存在
        get_response = client.get(
            f"/api/v1/chat/sessions/{session_id}",
            headers=auth_headers
        )
        assert get_response.status_code == status.HTTP_200_OK


class TestSessionMessages:
    """会话消息测试"""

    def test_get_session_messages_empty(
        self, client: TestClient, auth_headers: dict
    ):
        """测试获取空消息列表"""
        # 创建会话
        create_response = client.post(
            "/api/v1/chat/sessions",
            headers=auth_headers,
            json={"title": "消息测试会话"}
        )
        session_id = create_response.json()["id"]

        # 获取消息
        response = client.get(
            f"/api/v1/chat/sessions/{session_id}/messages",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["session_id"] == session_id
        assert data["messages"] == []

    def test_get_nonexistent_session_messages(
        self, client: TestClient, auth_headers: dict
    ):
        """测试获取不存在会话的消息"""
        fake_id = str(uuid.uuid4())
        response = client.get(
            f"/api/v1/chat/sessions/{fake_id}/messages",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_clear_session_messages(
        self, client: TestClient, auth_headers: dict
    ):
        """测试清空会话消息"""
        # 创建会话
        create_response = client.post(
            "/api/v1/chat/sessions",
            headers=auth_headers,
            json={"title": "清空消息测试"}
        )
        session_id = create_response.json()["id"]

        # 清空消息
        response = client.delete(
            f"/api/v1/chat/sessions/{session_id}/messages",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["success"] is True

    def test_clear_messages_nonexistent_session(
        self, client: TestClient, auth_headers: dict
    ):
        """测试清空不存在会话的消息"""
        fake_id = str(uuid.uuid4())
        response = client.delete(
            f"/api/v1/chat/sessions/{fake_id}/messages",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestSessionIsolation:
    """会话隔离测试"""

    def test_users_cannot_see_others_sessions(
        self, client: TestClient, auth_headers: dict, db_session: "Session"
    ):
        """测试用户看不到其他用户的会话"""
        from app.core.security import create_access_token

        # 创建另一个用户（使用测试数据库会话）
        from app.models.user import UserModel
        from app.core.security import hash_password
        import uuid as uuid_module

        other_user_id = str(uuid_module.uuid4())
        other_user = UserModel(
            id=other_user_id,
            username=f"isolation_{uuid_module.uuid4().hex[:8]}",
            password_hash=hash_password("password123")
        )
        db_session.add(other_user)
        db_session.commit()

        other_token = create_access_token(data={"sub": other_user_id})
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # 用户1创建会话
        client.post(
            "/api/v1/chat/sessions",
            headers=auth_headers,
            json={"title": "用户1的私密会话"}
        )

        # 用户2获取会话列表
        response = client.get(
            "/api/v1/chat/sessions",
            headers=other_headers
        )

        assert response.status_code == status.HTTP_200_OK
        sessions = response.json()["sessions"]
        # 用户2不应该看到用户1的会话
        user1_sessions = [s for s in sessions if s["title"] == "用户1的私密会话"]
        assert len(user1_sessions) == 0


class TestSessionGet:
    """获取单个会话详情测试"""

    def test_get_session_success(self, client: TestClient, auth_headers: dict):
        """测试成功获取会话详情"""
        # 创建会话
        create_response = client.post(
            "/api/v1/chat/sessions",
            headers=auth_headers,
            json={"title": "详情测试会话"}
        )
        session_id = create_response.json()["id"]

        # 获取会话
        response = client.get(
            f"/api/v1/chat/sessions/{session_id}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == session_id
        assert data["title"] == "详情测试会话"

    def test_get_nonexistent_session(self, client: TestClient, auth_headers: dict):
        """测试获取不存在的会话"""
        fake_id = str(uuid.uuid4())
        response = client.get(
            f"/api/v1/chat/sessions/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
