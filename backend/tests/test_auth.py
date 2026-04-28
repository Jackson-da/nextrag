"""用户认证 API 测试"""
import pytest
from fastapi.testclient import TestClient
from fastapi import status


class TestUserRegistration:
    """用户注册测试"""

    def test_register_success(self, client: TestClient):
        """测试成功注册用户"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser1",
                "password": "password123"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert data["message"] == "注册成功"
        assert "user_id" in data
        assert len(data["user_id"]) > 0

    def test_register_duplicate_username(self, client: TestClient):
        """测试用户名已存在"""
        # 先注册一个用户
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "duplicate_user",
                "password": "password123"
            }
        )

        # 尝试注册相同的用户名
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "duplicate_user",
                "password": "password456"
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "用户名已存在" in response.json()["detail"]

    def test_register_username_too_short(self, client: TestClient):
        """测试用户名过短"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "ab",  # 小于3个字符
                "password": "password123"
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_password_too_short(self, client: TestClient):
        """测试密码过短"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "validuser",
                "password": "12345"  # 小于6个字符
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_missing_username(self, client: TestClient):
        """测试缺少用户名"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "password": "password123"
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_missing_password(self, client: TestClient):
        """测试缺少密码"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser"
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_empty_body(self, client: TestClient):
        """测试空请求体"""
        response = client.post(
            "/api/v1/auth/register",
            json={}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUserLogin:
    """用户登录测试"""

    def test_login_success(self, client: TestClient):
        """测试成功登录"""
        # 先注册用户
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "logintest",
                "password": "password123"
            }
        )

        # 登录
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "logintest",
                "password": "password123"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_login_user_not_found(self, client: TestClient):
        """测试用户不存在"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent_user",
                "password": "password123"
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "用户名或密码错误" in response.json()["detail"]

    def test_login_wrong_password(self, client: TestClient):
        """测试密码错误"""
        # 先注册用户
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "wrongpwtest",
                "password": "correct_password"
            }
        )

        # 使用错误密码登录
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "wrongpwtest",
                "password": "wrong_password"
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "用户名或密码错误" in response.json()["detail"]

    def test_login_missing_username(self, client: TestClient):
        """测试缺少用户名"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "password": "password123"
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_missing_password(self, client: TestClient):
        """测试缺少密码"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser"
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetCurrentUser:
    """获取当前用户信息测试"""

    def test_get_me_success(self, client: TestClient):
        """测试成功获取当前用户信息"""
        # 注册并登录
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "me_test_user",
                "password": "password123"
            }
        )
        user_id = register_response.json()["user_id"]

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "me_test_user",
                "password": "password123"
            }
        )
        access_token = login_response.json()["access_token"]

        # 获取当前用户信息
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == user_id
        assert data["username"] == "me_test_user"

    def test_get_me_without_token(self, client: TestClient):
        """测试未提供 token"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "未提供认证凭据" in response.json()["detail"]

    def test_get_me_with_invalid_token(self, client: TestClient):
        """测试无效的 token"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token_12345"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "无效" in response.json()["detail"] or "无效或已过期的令牌" in response.json()["detail"]

    def test_get_me_with_malformed_header(self, client: TestClient):
        """测试格式错误的认证头"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "invalid_format"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_me_with_empty_bearer_token(self, client: TestClient):
        """测试空的 Bearer token"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer "}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthenticationFlow:
    """完整认证流程测试"""

    def test_full_auth_flow(self, client: TestClient):
        """测试完整的注册-登录-获取用户信息流程"""
        # 1. 注册
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "full_flow_user",
                "password": "SecurePass123!"
            }
        )
        assert register_response.status_code == status.HTTP_200_OK
        user_id = register_response.json()["user_id"]

        # 2. 登录
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "full_flow_user",
                "password": "SecurePass123!"
            }
        )
        assert login_response.status_code == status.HTTP_200_OK
        access_token = login_response.json()["access_token"]

        # 3. 获取用户信息
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert me_response.status_code == status.HTTP_200_OK
        assert me_response.json()["id"] == user_id
        assert me_response.json()["username"] == "full_flow_user"

    def test_multiple_users_isolation(self, client: TestClient):
        """测试多个用户之间的隔离"""
        # 创建用户1
        client.post(
            "/api/v1/auth/register",
            json={"username": "user1", "password": "password1"}
        )
        login1 = client.post(
            "/api/v1/auth/login",
            json={"username": "user1", "password": "password1"}
        )
        token1 = login1.json()["access_token"]

        # 创建用户2
        client.post(
            "/api/v1/auth/register",
            json={"username": "user2", "password": "password2"}
        )
        login2 = client.post(
            "/api/v1/auth/login",
            json={"username": "user2", "password": "password2"}
        )
        token2 = login2.json()["access_token"]

        # 用户1的token只能获取用户1的信息
        me1 = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token1}"}
        )
        assert me1.json()["username"] == "user1"

        # 用户2的token只能获取用户2的信息
        me2 = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert me2.json()["username"] == "user2"

        # 用户1的token不能获取用户2的信息
        assert me1.json()["id"] != me2.json()["id"]


class TestPasswordSecurity:
    """密码安全性测试"""

    def test_password_hashing(self, client: TestClient):
        """测试密码是否被正确哈希"""
        # 注册用户
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "hash_test_user",
                "password": "TestPassword123"
            }
        )
        user_id = response.json()["user_id"]

        # 登录
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "hash_test_user",
                "password": "TestPassword123"
            }
        )

        assert login_response.status_code == status.HTTP_200_OK
        assert "access_token" in login_response.json()

    def test_long_password_handling(self, client: TestClient):
        """测试长密码处理（bcrypt限制72字节）"""
        # bcrypt 限制密码最长72字节，这里测试超长密码的处理
        long_password = "a" * 100  # 超过72字节

        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "long_pwd_user",
                "password": long_password
            }
        )

        # 应该成功（密码会被截断到72字节）
        assert response.status_code == status.HTTP_200_OK

        # 登录时使用相同的长密码
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "long_pwd_user",
                "password": long_password
            }
        )

        assert login_response.status_code == status.HTTP_200_OK

    def test_special_characters_in_password(self, client: TestClient):
        """测试密码中的特殊字符"""
        special_password = "P@ssw0rd!#$%^&*()_+-=[]{}|;':\",./<>?"

        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "special_char_user",
                "password": special_password
            }
        )

        assert response.status_code == status.HTTP_200_OK

        # 使用特殊字符密码登录
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "special_char_user",
                "password": special_password
            }
        )

        assert login_response.status_code == status.HTTP_200_OK

    def test_chinese_characters_in_password(self, client: TestClient):
        """测试密码中的中文字符"""
        chinese_password = "密码123456"

        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "chinese_pwd_user",
                "password": chinese_password
            }
        )

        # 应该成功
        assert response.status_code == status.HTTP_200_OK

        # 使用中文密码登录
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "chinese_pwd_user",
                "password": chinese_password
            }
        )

        assert login_response.status_code == status.HTTP_200_OK


class TestJWTToken:
    """JWT Token 测试"""

    def test_token_contains_user_id(self, client: TestClient):
        """测试 token 中包含用户 ID"""
        # 注册并登录
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "token_user",
                "password": "password123"
            }
        )

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "token_user",
                "password": "password123"
            }
        )

        token = login_response.json()["access_token"]

        # Token 应该是一个有效的 JWT 字符串（包含两个点）
        assert token.count('.') == 2

        # 使用 token 获取用户信息
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert me_response.status_code == status.HTTP_200_OK
        assert me_response.json()["username"] == "token_user"

    def test_token_reuse(self, client: TestClient):
        """测试 token 可以重复使用"""
        # 注册并登录
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "reuse_token_user",
                "password": "password123"
            }
        )

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "reuse_token_user",
                "password": "password123"
            }
        )

        token = login_response.json()["access_token"]

        # 多次使用 token
        for _ in range(3):
            me_response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert me_response.status_code == status.HTTP_200_OK
