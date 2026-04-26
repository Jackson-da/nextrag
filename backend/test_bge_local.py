"""测试 BGEEmbeddings 初始化"""
import sys
import os

# 添加 backend 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Starting BGEEmbeddings test...")

try:
    from app.core.embeddings import BGEEmbeddings
    
    print("Initializing BGEEmbeddings (this may take a while first time)...")
    print("Model: BAAI/bge-large-zh-v1.5")
    print("Device: cpu")
    
    embedding = BGEEmbeddings(
        model_name="BAAI/bge-large-zh-v1.5",
        device="cpu"
    )
    
    print("Initialization complete!")
    
    # 测试一下
    print("\nTesting embed_query...")
    result = embedding.embed_query("你好")
    print(f"Success! Embedding dimension: {len(result)}")
    
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
