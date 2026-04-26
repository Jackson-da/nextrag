"""文档管理 API 接口"""
from typing import Annotated
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query

from app.models.schemas import (
    DocumentResponse,
    DocumentListResponse,
    UploadResponse,
    DeleteResponse,
    ErrorResponse,
)
from app.services.document_service import get_document_service
from app.config import get_settings

router = APIRouter(prefix="/documents", tags=["文档管理"])


@router.post(
    "/upload",
    response_model=UploadResponse,
    responses={400: {"model": ErrorResponse}},
)
async def upload_document(
    file: Annotated[UploadFile, File(description="要上传的文档文件")],
    description: Annotated[str | None, Form(description="文档描述")] = None,
    knowledge_base_id: Annotated[str | None, Form(description="知识库 ID")] = None,
):
    """上传文档并自动处理"""
    settings = get_settings()
    
    # 检查文件扩展名
    if file.filename:
        ext = "." + file.filename.split(".")[-1].lower()
        if ext not in settings.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式。支持的格式: {', '.join(settings.allowed_extensions)}"
            )
    
    # 检查文件大小
    content = await file.read()
    if len(content) > settings.max_file_size:
        raise HTTPException(
            status_code=400,
            detail=f"文件过大。最大支持 {settings.max_file_size // (1024 * 1024)}MB"
        )
    
    # 上传处理
    doc_service = get_document_service()
    result = await doc_service.upload_document(
        file_content=content,
        filename=file.filename or "unknown",
        description=description,
        knowledge_base_id=knowledge_base_id,
    )
    
    if result["status"] == "failed":
        raise HTTPException(
            status_code=500,
            detail=f"文档处理失败: {result.get('error', '未知错误')}"
        )
    
    return UploadResponse(
        document_id=result["id"],
        filename=result["filename"],
        status=result["status"],
        message=f"文档上传成功，已分割为 {result['chunk_count']} 个片段",
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    knowledge_base_id: str | None = None,
):
    """获取文档列表"""
    doc_service = get_document_service()
    items, total = await doc_service.list_documents(
        skip=skip,
        limit=limit,
        knowledge_base_id=knowledge_base_id,
    )
    
    return DocumentListResponse(total=total, items=items)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """获取文档详情"""
    doc_service = get_document_service()
    doc = await doc_service.get_document(document_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return doc


@router.delete("/{document_id}", response_model=DeleteResponse)
async def delete_document(document_id: str):
    """删除文档"""
    doc_service = get_document_service()
    success = await doc_service.delete_document(document_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return DeleteResponse(success=True, message="文档删除成功")


@router.get("/vectorstore/info")
async def get_vectorstore_info():
    """获取向量库信息"""
    doc_service = get_document_service()
    info = await doc_service.get_vectorstore_info()
    return info
