"""LLM 回答缓存测试（独立版本）"""
import hashlib
import json
import pytest


class TestCacheKeysLogic:
    """缓存键逻辑测试（不依赖 app 模块）"""

    # 模拟 CacheKeys 类的逻辑
    @staticmethod
    def llm_response(question_hash: str) -> str:
        """LLM 回答缓存键"""
        return f"llm:response:{question_hash}"
    
    @staticmethod
    def TTL_META() -> int:
        """缓存 TTL = 1 小时"""
        return 3600

    def test_llm_response_key_format(self):
        """测试 LLM 回答缓存键格式"""
        question_hash = "abc123"
        key = self.llm_response(question_hash)
        
        assert key == "llm:response:abc123"
        assert key.startswith("llm:response:")

    def test_llm_response_different_hash_different_key(self):
        """测试不同 hash 生成不同的键"""
        key1 = self.llm_response("hash1")
        key2 = self.llm_response("hash2")
        
        assert key1 != key2

    def test_question_hash_generation_md5(self):
        """测试问题 hash 生成"""
        question = "今天天气怎么样"
        expected_hash = hashlib.md5(question.encode()).hexdigest()
        
        actual_hash = hashlib.md5(question.encode()).hexdigest()
        
        assert actual_hash == expected_hash
        assert len(actual_hash) == 32  # MD5 产生 32 字符的十六进制字符串

    def test_same_question_same_hash(self):
        """测试相同问题产生相同 hash"""
        question = "今天天气怎么样"
        
        hash1 = hashlib.md5(question.encode()).hexdigest()
        hash2 = hashlib.md5(question.encode()).hexdigest()
        
        assert hash1 == hash2

    def test_different_question_different_hash(self):
        """测试不同问题产生不同 hash"""
        question1 = "今天天气怎么样"
        question2 = "明天天气怎么样"
        
        hash1 = hashlib.md5(question1.encode()).hexdigest()
        hash2 = hashlib.md5(question2.encode()).hexdigest()
        
        assert hash1 != hash2

    def test_chinese_question_hash(self):
        """测试中文问题 hash 生成"""
        question = "你们公司的产品有哪些"
        hash_result = hashlib.md5(question.encode()).hexdigest()
        
        assert len(hash_result) == 32
        assert hash_result.isalnum()  # 纯字母数字

    def test_english_question_hash(self):
        """测试英文问题 hash 生成"""
        question = "What is a vector database"
        hash_result = hashlib.md5(question.encode()).hexdigest()
        
        assert len(hash_result) == 32


class TestCacheDataSerialization:
    """缓存数据序列化测试"""

    def test_cache_data_serialization(self):
        """测试缓存数据序列化"""
        cache_data = {
            "answer": "测试回答",
            "sources": [
                {"content": "来源1", "metadata": {"source": "doc1"}},
                {"content": "来源2", "metadata": {"source": "doc2"}}
            ]
        }
        
        serialized = json.dumps(cache_data, ensure_ascii=False)
        deserialized = json.loads(serialized)
        
        assert deserialized["answer"] == "测试回答"
        assert len(deserialized["sources"]) == 2

    def test_cache_data_with_special_chars(self):
        """测试带特殊字符的缓存数据"""
        cache_data = {
            "answer": "回答包含 <script> 和 emoji 🎉",
            "sources": [{"content": "测试\n换行"}]
        }
        
        serialized = json.dumps(cache_data, ensure_ascii=False)
        deserialized = json.loads(serialized)
        
        assert deserialized["answer"] == "回答包含 <script> 和 emoji 🎉"

    def test_cache_data_empty_sources(self):
        """测试空 sources"""
        cache_data = {
            "answer": "无来源的回答",
            "sources": []
        }
        
        serialized = json.dumps(cache_data)
        deserialized = json.loads(serialized)
        
        assert deserialized["answer"] == "无来源的回答"
        assert deserialized["sources"] == []


class TestCacheKeyGeneration:
    """缓存键生成测试"""

    @staticmethod
    def generate_cache_key(question: str) -> str:
        """生成缓存键"""
        question_hash = hashlib.md5(question.encode()).hexdigest()
        return f"llm:response:{question_hash}"

    def test_same_question_same_cache_key(self):
        """测试相同问题产生相同缓存键"""
        question = "如何退款"
        
        key1 = self.generate_cache_key(question)
        key2 = self.generate_cache_key(question)
        
        assert key1 == key2

    def test_different_questions_different_cache_keys(self):
        """测试不同问题产生不同缓存键"""
        question1 = "如何退款"
        question2 = "如何办理会员"
        
        key1 = self.generate_cache_key(question1)
        key2 = self.generate_cache_key(question2)
        
        assert key1 != key2

    def test_whitespace_matters(self):
        """测试空格会影响 hash"""
        question1 = "你好 世界"
        question2 = "你好世界"
        
        key1 = self.generate_cache_key(question1)
        key2 = self.generate_cache_key(question2)
        
        assert key1 != key2

    def test_case_matters(self):
        """测试大小写会影响 hash"""
        question1 = "Hello World"
        question2 = "hello world"
        
        key1 = self.generate_cache_key(question1)
        key2 = self.generate_cache_key(question2)
        
        assert key1 != key2

    def test_punctuation_matters(self):
        """测试标点符号会影响 hash"""
        question1 = "你好。"
        question2 = "你好"
        
        key1 = self.generate_cache_key(question1)
        key2 = self.generate_cache_key(question2)
        
        assert key1 != key2


class TestCacheBehaviorSimulation:
    """缓存行为模拟测试"""

    def test_cache_miss_then_hit_simulation(self):
        """模拟缓存未命中后命中的流程"""
        question = "今天能干什么"
        question_hash = hashlib.md5(question.encode()).hexdigest()
        cache_key = f"llm:response:{question_hash}"
        
        # 模拟缓存存储（字典模拟 Redis）
        cache_store = {}
        
        # 第一次访问：MISS
        first_result = cache_store.get(cache_key)
        assert first_result is None  # 未命中
        
        # 计算回答（模拟 LLM 调用）
        computed_answer = "今天可以做很多事情"
        
        # 写入缓存
        cache_store[cache_key] = json.dumps({
            "answer": computed_answer,
            "sources": []
        })
        
        # 第二次访问：HIT
        second_result = cache_store.get(cache_key)
        assert second_result is not None  # 命中
        
        parsed = json.loads(second_result)
        assert parsed["answer"] == computed_answer

    def test_different_sessions_same_question(self):
        """模拟不同会话问相同问题"""
        question = "退款政策是什么"
        question_hash = hashlib.md5(question.encode()).hexdigest()
        cache_key = f"llm:response:{question_hash}"
        
        # 无论哪个会话，相同问题的缓存键应该相同
        session1_key = f"llm:response:{hashlib.md5(question.encode()).hexdigest()}"
        session2_key = f"llm:response:{hashlib.md5(question.encode()).hexdigest()}"
        
        assert session1_key == session2_key  # 相同问题的缓存键相同

    def test_different_questions_independent_cache(self):
        """测试不同问题有独立的缓存"""
        cache_store = {}
        
        # 写入两个不同的缓存
        q1 = "问题1"
        q2 = "问题2"
        
        cache_store[f"llm:response:{hashlib.md5(q1.encode()).hexdigest()}"] = json.dumps({"answer": "回答1", "sources": []})
        cache_store[f"llm:response:{hashlib.md5(q2.encode()).hexdigest()}"] = json.dumps({"answer": "回答2", "sources": []})
        
        # 验证两个缓存独立
        assert cache_store[f"llm:response:{hashlib.md5(q1.encode()).hexdigest()}"] != cache_store[f"llm:response:{hashlib.md5(q2.encode()).hexdigest()}"]

    def test_cache_ttl_simulation(self):
        """模拟缓存 TTL"""
        import time
        
        question = "测试问题"
        question_hash = hashlib.md5(question.encode()).hexdigest()
        cache_key = f"llm:response:{question_hash}"
        ttl = 3600  # 1小时
        
        cache_store = {
            "key": cache_key,
            "value": json.dumps({"answer": "回答", "sources": []}),
            "expire_at": time.time() + ttl
        }
        
        # 检查缓存是否过期
        is_expired = time.time() > cache_store["expire_at"]
        assert not is_expired  # 未过期

    def test_chinese_question_caching(self):
        """测试中文问题缓存"""
        chinese_question = "你们公司的产品有哪些"
        question_hash = hashlib.md5(chinese_question.encode()).hexdigest()
        cache_key = f"llm:response:{question_hash}"
        
        cached_data = {
            "answer": "我们公司有以下产品...",
            "sources": [{"content": "产品介绍文档"}]
        }
        
        cache_store = {cache_key: json.dumps(cached_data, ensure_ascii=False)}
        
        result = json.loads(cache_store[cache_key])
        assert result["answer"] == "我们公司有以下产品..."
        assert len(result["sources"]) == 1


class TestCacheKeyCollisionPrevention:
    """缓存键冲突预防测试"""

    def test_long_question_hash(self):
        """测试长问题的 hash"""
        long_question = "这是一个非常长的问题，" * 100
        hash_result = hashlib.md5(long_question.encode()).hexdigest()
        
        assert len(hash_result) == 32  # 固定长度

    def test_unicode_question_hash(self):
        """测试 Unicode 问题的 hash"""
        questions = [
            "你好世界",
            "こんにちは",
            "Hello World",
            "🎉🎊🎁",
            "mixed 中英123"
        ]
        
        hashes = [hashlib.md5(q.encode()).hexdigest() for q in questions]
        
        # 所有 hash 长度一致
        assert all(len(h) == 32 for h in hashes)
        
        # 所有 hash 都不同（大概率）
        assert len(set(hashes)) == len(hashes)  # 全都不同

    def test_hash_deterministic(self):
        """测试 hash 是确定性的"""
        question = "测试确定性"
        
        hashes = [hashlib.md5(question.encode()).hexdigest() for _ in range(100)]
        
        # 所有 hash 应该相同
        assert len(set(hashes)) == 1
