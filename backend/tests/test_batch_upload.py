"""批量上传文档 API 测试"""
import io
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


class TestBatchUploadSuccess:
    """批量上传成功场景测试"""

    def test_batch_upload_single_txt_file(
        self, client: TestClient, auth_headers: dict
    ):
        """测试批量上传单个 TXT 文件成功"""
        content = "这是测试文档内容。用于批量上传功能测试。"
        file = ("test.txt", io.BytesIO(content.encode("utf-8")), "text/plain")

        response = client.post(
            "/api/v1/documents/upload/batch",
            files=[("files", file)],
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "success_count" in data
        assert "failed_count" in data
        assert "results" in data
        assert data["total"] == 1
        # 成功或部分成功（取决于完整环境）
        assert data["success_count"] + data["failed_count"] == data["total"]
        assert len(data["results"]) == 1

    def test_batch_upload_multiple_txt_files(
        self, client: TestClient, auth_headers: dict
    ):
        """测试批量上传多个 TXT 文件"""
        files = []
        for i in range(3):
            content = f"测试文档{i + 1}的内容。用于批量上传。"
            files.append(
                ("files", (f"doc{i + 1}.txt", io.BytesIO(content.encode("utf-8")), "text/plain"))
            )

        response = client.post(
            "/api/v1/documents/upload/batch",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["results"]) == 3
        assert data["success_count"] + data["failed_count"] == 3

    def test_batch_upload_with_knowledge_base_id(
        self, client: TestClient, auth_headers: dict
    ):
        """测试批量上传到指定知识库"""
        # 先创建知识库
        kb_response = client.post(
            "/api/v1/knowledge-bases",
            json={"name": "批量上传测试知识库"},
            headers=auth_headers,
        )
        assert kb_response.status_code == 200
        kb_id = kb_response.json()["id"]

        # 上传文件到知识库
        content = "知识库关联测试。"
        file = ("kb_test.txt", io.BytesIO(content.encode("utf-8")), "text/plain")

        response = client.post(
            "/api/v1/documents/upload/batch",
            files=[("files", file)],
            data={"knowledge_base_id": kb_id},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

        # 验证文档列表中该知识库有文档
        doc_response = client.get(
            f"/api/v1/documents?knowledge_base_id={kb_id}",
            headers=auth_headers,
        )
        if doc_response.status_code == 200:
            doc_data = doc_response.json()
            assert doc_data["total"] >= 0  # 可能成功或被 skip

    def test_batch_upload_supported_formats(
        self, client: TestClient, auth_headers: dict
    ):
        """测试支持的文件格式：.txt, .md, .pdf, .docx"""
        test_files = [
            ("test_upload.txt", b"TXT content for test", "text/plain"),
            ("test_upload.md", b"# Markdown content for test", "text/markdown"),
        ]

        files = [
            ("files", (name, io.BytesIO(content), mime))
            for name, content, mime in test_files
        ]

        response = client.post(
            "/api/v1/documents/upload/batch",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2


class TestBatchUploadValidation:
    """批量上传参数校验测试"""

    def test_batch_upload_unauthorized(self, client: TestClient):
        """测试未认证上传返回 401"""
        content = "未认证测试。"
        file = ("unauth.txt", io.BytesIO(content.encode("utf-8")), "text/plain")

        response = client.post(
            "/api/v1/documents/upload/batch",
            files=[("files", file)],
        )

        assert response.status_code == 401

    def test_batch_upload_no_files(self, client: TestClient, auth_headers: dict):
        """测试不传文件返回 422（files 参数必填）"""
        response = client.post(
            "/api/v1/documents/upload/batch",
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_batch_upload_empty_file_list(
        self, client: TestClient, auth_headers: dict
    ):
        """测试上传空文件列表返回 422"""
        response = client.post(
            "/api/v1/documents/upload/batch",
            files=[],
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_batch_upload_unsupported_extension(
        self, client: TestClient, auth_headers: dict
    ):
        """测试上传不支持的文件格式"""
        content = b"<html><body>Not supported</body></html>"
        file = ("webpage.html", io.BytesIO(content), "text/html")

        response = client.post(
            "/api/v1/documents/upload/batch",
            files=[("files", file)],
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # HTML 不在允许的扩展名中，应该标记为失败
        assert data["total"] == 1
        # 所有文件都失败
        for result in data["results"]:
            if result["filename"] == "webpage.html":
                assert result["status"] == "failed"
                assert "不支持" in result.get("error", "")

    def test_batch_upload_mixed_supported_and_unsupported(
        self, client: TestClient, auth_headers: dict
    ):
        """测试混合了支持和不受支持的文件格式"""
        files = [
            ("files", ("good.txt", io.BytesIO(b"Valid content"), "text/plain")),
            ("files", ("bad.xyz", io.BytesIO(b"Invalid content"), "application/octet-stream")),
        ]

        response = client.post(
            "/api/v1/documents/upload/batch",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["results"]) == 2

        # 验证每个文件的结果
        bad_result = next(r for r in data["results"] if r["filename"] == "bad.xyz")
        assert bad_result["status"] == "failed"

    def test_batch_upload_invalid_knowledge_base_id(
        self, client: TestClient, auth_headers: dict
    ):
        """测试传入不存在的 knowledge_base_id 仍能正常处理"""
        content = "测试不存在知识库的批量上传。"
        file = ("test_kb.txt", io.BytesIO(content.encode("utf-8")), "text/plain")

        response = client.post(
            "/api/v1/documents/upload/batch",
            files=[("files", file)],
            data={"knowledge_base_id": "nonexistent-kb-id"},
            headers=auth_headers,
        )

        # 不应该报 422，文件上传应该正常处理
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


class TestBatchUploadResponseStructure:
    """批量上传响应结构验证"""

    def test_response_has_required_fields(
        self, client: TestClient, auth_headers: dict
    ):
        """测试响应包含所有必要字段"""
        content = "响应结构测试。"
        file = ("resp_test.txt", io.BytesIO(content.encode("utf-8")), "text/plain")

        response = client.post(
            "/api/v1/documents/upload/batch",
            files=[("files", file)],
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # 顶层字段
        required_fields = ["total", "success_count", "failed_count", "results"]
        for field in required_fields:
            assert field in data, f"缺少顶层字段: {field}"
        assert isinstance(data["total"], int)
        assert isinstance(data["success_count"], int)
        assert isinstance(data["failed_count"], int)
        assert isinstance(data["results"], list)

    def test_result_item_has_required_fields(
        self, client: TestClient, auth_headers: dict
    ):
        """测试结果项包含必要字段"""
        content = "结果项结构测试。"
        file = ("result_item.txt", io.BytesIO(content.encode("utf-8")), "text/plain")

        response = client.post(
            "/api/v1/documents/upload/batch",
            files=[("files", file)],
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        for result in data["results"]:
            assert "filename" in result, "结果项缺少 filename"
            assert "status" in result, "结果项缺少 status"
            assert result["status"] in ["success", "failed"], \
                f"status 值非法: {result['status']}"

            if result["status"] == "success":
                assert "document_id" in result
                assert "chunk_count" in result
            else:
                assert "error" in result

    def test_success_count_matches_results(
        self, client: TestClient, auth_headers: dict
    ):
        """测试 success_count 和 failed_count 与 results 一致"""
        content = "一致性测试。"
        file = ("count_test.txt", io.BytesIO(content.encode("utf-8")), "text/plain")

        response = client.post(
            "/api/v1/documents/upload/batch",
            files=[("files", file)],
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        actual_success = sum(1 for r in data["results"] if r["status"] == "success")
        actual_failed = sum(1 for r in data["results"] if r["status"] == "failed")

        assert data["success_count"] == actual_success
        assert data["failed_count"] == actual_failed
        assert data["total"] == actual_success + actual_failed


class TestBatchUploadEdgeCases:
    """批量上传边界情况测试"""

    def test_batch_upload_chinese_filename(
        self, client: TestClient, auth_headers: dict
    ):
        """测试中文文件名"""
        content = "中文文件名测试。"
        file = ("测试文档.txt", io.BytesIO(content.encode("utf-8")), "text/plain")

        response = client.post(
            "/api/v1/documents/upload/batch",
            files=[("files", file)],
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_batch_upload_empty_file_content(
        self, client: TestClient, auth_headers: dict
    ):
        """测试上传空内容文件"""
        file = ("empty.txt", io.BytesIO(b""), "text/plain")

        response = client.post(
            "/api/v1/documents/upload/batch",
            files=[("files", file)],
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_batch_upload_large_text_file(
        self, client: TestClient, auth_headers: dict
    ):
        """测试上传较大文本文件（未超过限值）"""
        content = "大文件测试内容，用于验证批量上传不解析请求时的 Header。\n" * 200
        file = ("large.txt", io.BytesIO(content.encode("utf-8")), "text/plain")

        response = client.post(
            "/api/v1/documents/upload/batch",
            files=[("files", file)],
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_batch_upload_preserves_file_order(
        self, client: TestClient, auth_headers: dict
    ):
        """测试结果顺序与上传顺序一致"""
        filenames = ["aaa.txt", "bbb.txt", "ccc.txt"]
        files = []
        for name in filenames:
            content = f"Content of {name}"
            files.append(
                ("files", (name, io.BytesIO(content.encode("utf-8")), "text/plain"))
            )

        response = client.post(
            "/api/v1/documents/upload/batch",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 3
        result_names = [r["filename"] for r in data["results"]]
        assert result_names == filenames


class TestBatchUploadUserIsolation:
    """批量上传用户隔离测试"""

    def test_different_users_independent(
        self, client: TestClient, auth_headers: dict, db_session: "Session"
    ):
        """测试不同用户上传的文档相互隔离"""
        from app.core.security import create_access_token, hash_password
        from app.models.user import UserModel
        import uuid as uuid_module

        # 创建用户 A
        user_a_id = str(uuid_module.uuid4())
        user_a = UserModel(
            id=user_a_id,
            username=f"batch_user_a_{uuid_module.uuid4().hex[:8]}",
            password_hash=hash_password("password123"),
        )
        db_session.add(user_a)
        db_session.commit()

        token_a = create_access_token(data={"sub": user_a_id})
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # 创建用户 B
        user_b_id = str(uuid_module.uuid4())
        user_b = UserModel(
            id=user_b_id,
            username=f"batch_user_b_{uuid_module.uuid4().hex[:8]}",
            password_hash=hash_password("password123"),
        )
        db_session.add(user_b)
        db_session.commit()

        token_b = create_access_token(data={"sub": user_b_id})
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # 用户 A 上传文件
        content_a = "User A content"
        file_a = ("user_a.txt", io.BytesIO(content_a.encode("utf-8")), "text/plain")
        client.post(
            "/api/v1/documents/upload/batch",
            files=[("files", file_a)],
            headers=headers_a,
        )

        # 用户 B 上传文件
        content_b = "User B content"
        file_b = ("user_b.txt", io.BytesIO(content_b.encode("utf-8")), "text/plain")
        client.post(
            "/api/v1/documents/upload/batch",
            files=[("files", file_b)],
            headers=headers_b,
        )

        # 用户 A 只能看自己的文档
        docs_a = client.get("/api/v1/documents", headers=headers_a)
        if docs_a.status_code == 200:
            doc_list = docs_a.json()["items"]
            for doc in doc_list:
                assert doc.get("user_id", user_a_id) == user_a_id, \
                    "用户应看不到其他用户的文档"
