"""知识库 API 接口"""
from typing import Annotated
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

from app.models.schemas import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    KnowledgeBaseListResponse,
    DocumentListResponse,
    DeleteResponse,
)
from app.services.document_service import get_document_service

router = APIRouter(prefix="/knowledge-bases", tags=["知识库"])

# 内存存储（生产环境应使用数据库）
_knowledge_bases: dict[str, dict] = {}


@router.post("", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(request: KnowledgeBaseCreate):
    """创建知识库"""
    import uuid
    
    kb_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    kb = {
        "id": kb_id,
        "name": request.name,
        "description": request.description,
        "document_count": 0,
        "created_at": now,
        "updated_at": now,
    }
    
    _knowledge_bases[kb_id] = kb
    
    return kb


@router.get("", response_model=KnowledgeBaseListResponse)
async def list_knowledge_bases(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """获取知识库列表"""
    doc_service = get_document_service()
    
    items = list(_knowledge_bases.values())
    # 动态计算每个知识库的文档数量
    for kb in items:
        _, doc_count = await doc_service.list_documents(
            skip=0,
            limit=1,
            knowledge_base_id=kb["id"],
        )
        kb["document_count"] = doc_count
    
    items.sort(key=lambda x: x["created_at"], reverse=True)
    
    total = len(items)
    paginated_items = items[skip:skip + limit]
    
    return KnowledgeBaseListResponse(total=total, items=paginated_items)


@router.get("/{kb_id}/documents", response_model=DocumentListResponse)
async def get_knowledge_base_documents(
    kb_id: str,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """获取知识库关联的文档列表"""
    if kb_id not in _knowledge_bases:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    doc_service = get_document_service()
    items, total = await doc_service.list_documents(
        skip=skip,
        limit=limit,
        knowledge_base_id=kb_id,
    )
    
    return DocumentListResponse(total=total, items=items)


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(kb_id: str):
    """获取知识库详情"""
    if kb_id not in _knowledge_bases:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    kb = _knowledge_bases[kb_id]
    
    # 动态计算关联文档数量
    doc_service = get_document_service()
    _, doc_count = await doc_service.list_documents(
        skip=0,
        limit=1,
        knowledge_base_id=kb_id,
    )
    kb["document_count"] = doc_count
    
    return kb


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: str,
    request: KnowledgeBaseUpdate,
):
    """更新知识库"""
    if kb_id not in _knowledge_bases:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    kb = _knowledge_bases[kb_id]
    
    if request.name is not None:
        kb["name"] = request.name
    if request.description is not None:
        kb["description"] = request.description
    
    kb["updated_at"] = datetime.now().isoformat()
    
    return kb


@router.delete("/{kb_id}", response_model=DeleteResponse)
async def delete_knowledge_base(kb_id: str):
    """删除知识库"""
    if kb_id not in _knowledge_bases:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    del _knowledge_bases[kb_id]
    
    return DeleteResponse(success=True, message="知识库删除成功")
