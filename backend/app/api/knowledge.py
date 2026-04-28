"""知识库 API 接口"""
import uuid
from typing import Annotated
from fastapi import APIRouter, HTTPException, Query, Depends
import structlog

from app.models.schemas import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    KnowledgeBaseListResponse,
    DocumentListResponse,
    DeleteResponse,
)
from app.services.document_service import get_document_service
from app.models.database import KnowledgeBaseModel, init_db, SessionLocal
from app.api.auth import get_current_user
from app.models.user import UserModel

router = APIRouter(prefix="/knowledge-bases", tags=["知识库"])
logger = structlog.get_logger()

# 初始化数据库
init_db()


def get_db():
    """获取数据库会话"""
    return SessionLocal()


@router.post("", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(
    request: KnowledgeBaseCreate,
    current_user: UserModel = Depends(get_current_user),
):
    """创建知识库（需要登录）"""
    logger.info("创建知识库", user_id=current_user.id, name=request.name)
    
    db = get_db()
    try:
        kb_id = str(uuid.uuid4())

        kb = KnowledgeBaseModel(
            id=kb_id,
            user_id=current_user.id,  # 关联用户
            name=request.name,
            description=request.description,
        )
        db.add(kb)
        db.commit()
        db.refresh(kb)

        logger.info("知识库创建成功", kb_id=kb_id, name=request.name, user_id=current_user.id)
        
        return kb.to_dict()
    finally:
        db.close()


@router.get("", response_model=KnowledgeBaseListResponse)
async def list_knowledge_bases(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    current_user: UserModel = Depends(get_current_user),
):
    """获取当前用户的知识库列表"""
    db = get_db()
    try:
        doc_service = get_document_service()

        # 只查询当前用户创建的知识库
        query = db.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.user_id == current_user.id)
        total = query.count()
        items = query.order_by(KnowledgeBaseModel.created_at.desc()).offset(skip).limit(limit).all()

        # 动态计算每个知识库的文档数量
        result = []
        for kb in items:
            kb_dict = kb.to_dict()
            _, doc_count = await doc_service.list_documents(
                skip=0,
                limit=1,
                knowledge_base_id=kb.id,
                user_id=current_user.id,  # 只统计当前用户的文档
            )
            kb_dict["document_count"] = doc_count
            result.append(kb_dict)

        logger.info("获取知识库列表", user_id=current_user.id, skip=skip, limit=limit, total=total)
        
        return KnowledgeBaseListResponse(total=total, items=result)
    finally:
        db.close()


@router.get("/{kb_id}/documents", response_model=DocumentListResponse)
async def get_knowledge_base_documents(
    kb_id: str,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    current_user: UserModel = Depends(get_current_user),
):
    """获取知识库关联的文档列表（需要登录，且只能查看自己的知识库）"""
    db = get_db()
    try:
        kb = db.query(KnowledgeBaseModel).filter(
            KnowledgeBaseModel.id == kb_id,
            KnowledgeBaseModel.user_id == current_user.id  # 验证知识库属于当前用户
        ).first()
        if not kb:
            logger.warning("知识库不存在或无权访问", kb_id=kb_id, user_id=current_user.id)
            raise HTTPException(status_code=404, detail="知识库不存在")

        doc_service = get_document_service()
        items, total = await doc_service.list_documents(
            skip=skip,
            limit=limit,
            knowledge_base_id=kb_id,
            user_id=current_user.id,
        )

        logger.info("获取知识库文档列表", kb_id=kb_id, user_id=current_user.id, skip=skip, limit=limit, total=total)
        
        return DocumentListResponse(total=total, items=items)
    finally:
        db.close()


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: str,
    current_user: UserModel = Depends(get_current_user),
):
    """获取知识库详情（需要登录，且只能查看自己的知识库）"""
    logger.info("获取知识库详情", kb_id=kb_id, user_id=current_user.id)
    
    db = get_db()
    try:
        kb = db.query(KnowledgeBaseModel).filter(
            KnowledgeBaseModel.id == kb_id,
            KnowledgeBaseModel.user_id == current_user.id  # 验证知识库属于当前用户
        ).first()
        if not kb:
            logger.warning("知识库不存在或无权访问", kb_id=kb_id, user_id=current_user.id)
            raise HTTPException(status_code=404, detail="知识库不存在")

        kb_dict = kb.to_dict()

        # 动态计算关联文档数量
        doc_service = get_document_service()
        _, doc_count = await doc_service.list_documents(
            skip=0,
            limit=1,
            knowledge_base_id=kb_id,
            user_id=current_user.id,
        )
        kb_dict["document_count"] = doc_count

        return kb_dict
    finally:
        db.close()


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: str,
    request: KnowledgeBaseUpdate,
    current_user: UserModel = Depends(get_current_user),
):
    """更新知识库（需要登录，且只能更新自己的知识库）"""
    logger.info("更新知识库", kb_id=kb_id, user_id=current_user.id, name=request.name, description=request.description)
    
    db = get_db()
    try:
        kb = db.query(KnowledgeBaseModel).filter(
            KnowledgeBaseModel.id == kb_id,
            KnowledgeBaseModel.user_id == current_user.id  # 验证知识库属于当前用户
        ).first()
        if not kb:
            logger.warning("知识库不存在或无权访问", kb_id=kb_id, user_id=current_user.id)
            raise HTTPException(status_code=404, detail="知识库不存在")

        if request.name is not None:
            kb.name = request.name
        if request.description is not None:
            kb.description = request.description

        db.commit()
        db.refresh(kb)

        logger.info("知识库更新成功", kb_id=kb_id, user_id=current_user.id)
        
        return kb.to_dict()
    finally:
        db.close()


@router.delete("/{kb_id}", response_model=DeleteResponse)
async def delete_knowledge_base(
    kb_id: str,
    current_user: UserModel = Depends(get_current_user),
):
    """删除知识库（需要登录，只能删除自己的知识库，同时删除关联的文档）"""
    logger.info("删除知识库", kb_id=kb_id, user_id=current_user.id)
    
    db = get_db()
    try:
        kb = db.query(KnowledgeBaseModel).filter(
            KnowledgeBaseModel.id == kb_id,
            KnowledgeBaseModel.user_id == current_user.id  # 验证知识库属于当前用户
        ).first()
        if not kb:
            logger.warning("知识库不存在或无权访问", kb_id=kb_id, user_id=current_user.id)
            raise HTTPException(status_code=404, detail="知识库不存在")

        # 查询并删除关联的文档
        doc_service = get_document_service()
        documents, _ = await doc_service.list_documents(
            skip=0,
            limit=1000,  # 获取所有文档
            knowledge_base_id=kb_id,
            user_id=current_user.id,
        )

        # 删除每个关联的文档
        deleted_doc_count = 0
        for doc in documents:
            await doc_service.delete_document(doc["id"])
            deleted_doc_count += 1

        # 删除知识库记录
        db.delete(kb)
        db.commit()

        logger.info("知识库删除成功", kb_id=kb_id, user_id=current_user.id, deleted_doc_count=deleted_doc_count)
        
        return DeleteResponse(
            success=True,
            message=f"知识库删除成功，同时删除了 {deleted_doc_count} 个关联文档"
        )
    finally:
        db.close()
