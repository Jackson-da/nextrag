"""文档管理 API 接口"""
from typing import Annotated
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Depends
import structlog

from app.models.schemas import (
    DocumentResponse,
    DocumentListResponse,
    UploadResponse,
    DeleteResponse,
    ErrorResponse,
    BatchUploadResponse,
    UploadResultItem,
)
from app.services.document_service import get_document_service
from app.config import get_settings
from app.api.auth import get_current_user
from app.models.user import UserModel

router = APIRouter(prefix="/documents", tags=["文档管理"])
logger = structlog.get_logger()


@router.post(
    "/upload",
    response_model=UploadResponse,
    responses={400: {"model": ErrorResponse}},
)
async def upload_document(
    file: Annotated[UploadFile, File(description="要上传的文档文件")],
    description: Annotated[str | None, Form(description="文档描述")] = None,
    knowledge_base_id: Annotated[str | None, Form(description="知识库 ID")] = None,
    current_user: UserModel = Depends(get_current_user),
):
    """上传文档并自动处理（需要登录）"""
    logger.info("文档上传请求", user_id=current_user.id, filename=file.filename, kb_id=knowledge_base_id)
    
    settings = get_settings()
    
    # 检查文件扩展名
    if file.filename:
        ext = "." + file.filename.split(".")[-1].lower()
        if ext not in settings.allowed_extensions:
            logger.warning("不支持的文件格式", filename=file.filename, ext=ext)
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式。支持的格式: {', '.join(settings.allowed_extensions)}"
            )
    
    # 检查文件大小
    content = await file.read()
    if len(content) > settings.max_file_size:
        logger.warning("文件过大", filename=file.filename, size=len(content))
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
        user_id=current_user.id,  # 关联用户
    )
    
    if result["status"] == "failed":
        logger.error("文档处理失败", filename=file.filename, error=result.get("error"))
        raise HTTPException(
            status_code=500,
            detail=f"文档处理失败: {result.get('error', '未知错误')}"
        )
    
    logger.info("文档上传成功", user_id=current_user.id, doc_id=result["id"], chunk_count=result["chunk_count"])
    
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
    current_user: UserModel = Depends(get_current_user),
):
    """获取当前用户的文档列表"""
    doc_service = get_document_service()
    items, total = await doc_service.list_documents(
        skip=skip,
        limit=limit,
        knowledge_base_id=knowledge_base_id,
        user_id=current_user.id,  # 只返回当前用户的文档
    )
    
    logger.info("获取文档列表", user_id=current_user.id, skip=skip, limit=limit, total=total, kb_id=knowledge_base_id)
    
    return DocumentListResponse(total=total, items=items)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: UserModel = Depends(get_current_user),
):
    """获取文档详情（需要登录，只能查看自己的文档）"""
    logger.info("获取文档详情", doc_id=document_id, user_id=current_user.id)
    
    doc_service = get_document_service()
    doc = await doc_service.get_document(document_id)
    
    if not doc:
        logger.warning("文档不存在", doc_id=document_id)
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 验证文档属于当前用户
    if doc.get("user_id") != current_user.id:
        logger.warning("无权访问文档", doc_id=document_id, user_id=current_user.id)
        raise HTTPException(status_code=403, detail="无权访问该文档")
    
    return doc


@router.delete("/{document_id}", response_model=DeleteResponse)
async def delete_document(
    document_id: str,
    current_user: UserModel = Depends(get_current_user),
):
    """删除文档（需要登录，只能删除自己的文档）"""
    logger.info("删除文档", doc_id=document_id, user_id=current_user.id)
    
    doc_service = get_document_service()
    
    # 先检查文档是否存在且属于当前用户
    doc = await doc_service.get_document(document_id)
    if not doc:
        logger.warning("文档不存在，无法删除", doc_id=document_id)
        raise HTTPException(status_code=404, detail="文档不存在")
    
    if doc.get("user_id") != current_user.id:
        logger.warning("无权删除文档", doc_id=document_id, user_id=current_user.id)
        raise HTTPException(status_code=403, detail="无权删除该文档")
    
    success = await doc_service.delete_document(document_id)
    
    if not success:
        logger.warning("文档删除失败", doc_id=document_id)
        raise HTTPException(status_code=500, detail="文档删除失败")
    
    logger.info("文档删除成功", doc_id=document_id, user_id=current_user.id)
    
    return DeleteResponse(success=True, message="文档删除成功")


@router.get("/vectorstore/info")
async def get_vectorstore_info(
    current_user: UserModel = Depends(get_current_user),
):
    """获取向量库信息（按当前用户过滤）"""
    logger.info("获取向量库信息", user_id=current_user.id)
    
    doc_service = get_document_service()
    info = await doc_service.get_vectorstore_info(user_id=current_user.id)
    
    return info


@router.post("/upload/batch", response_model=BatchUploadResponse)
async def batch_upload_documents(
    files: Annotated[list[UploadFile], File(description="多个文档文件")],
    knowledge_base_id: Annotated[str | None, Form(description="知识库 ID")] = None,
    current_user: UserModel = Depends(get_current_user),
):
    """批量上传文档并自动处理（需要登录）"""
    settings = get_settings()
    
    # 校验文件数量
    if len(files) > settings.batch_max_files:
        logger.warning("批量上传文件数量超限", count=len(files), max=settings.batch_max_files)
        raise HTTPException(
            status_code=400,
            detail=f"单次最多上传 {settings.batch_max_files} 个文件"
        )
    
    # 校验总大小
    total_size = 0
    for f in files:
        if f.size:
            total_size += f.size
    
    if total_size > settings.batch_max_total_size:
        logger.warning("批量上传总大小超限", total_size=total_size, max=settings.batch_max_total_size)
        raise HTTPException(
            status_code=400,
            detail=f"批量上传总大小不能超过 {settings.batch_max_total_size // (1024 * 1024)}MB"
        )
    
    logger.info("批量上传请求", user_id=current_user.id, file_count=len(files), kb_id=knowledge_base_id)
    
    doc_service = get_document_service()
    results: list[UploadResultItem] = []
    success_count = 0
    failed_count = 0
    
    for file in files:
        filename = file.filename or "unknown"
        
        # 检查文件扩展名
        ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
        if ext not in settings.allowed_extensions:
            logger.warning("不支持的文件格式", filename=filename, ext=ext)
            results.append(UploadResultItem(
                filename=filename,
                status="failed",
                error=f"不支持的文件格式：{ext}"
            ))
            failed_count += 1
            continue
        
        try:
            # 读取文件内容
            content = await file.read()
            
            # 检查单文件大小
            if len(content) > settings.max_file_size:
                results.append(UploadResultItem(
                    filename=filename,
                    status="failed",
                    error=f"文件过大，最大支持 {settings.max_file_size // (1024 * 1024)}MB"
                ))
                failed_count += 1
                continue
            
            # 上传处理（复用现有逻辑）
            result = await doc_service.upload_document(
                file_content=content,
                filename=filename,
                description=None,
                knowledge_base_id=knowledge_base_id,
                user_id=current_user.id,
            )
            
            if result["status"] == "failed":
                results.append(UploadResultItem(
                    filename=filename,
                    status="failed",
                    error=result.get("error", "未知错误")
                ))
                failed_count += 1
            else:
                results.append(UploadResultItem(
                    filename=filename,
                    status="success",
                    document_id=result["id"],
                    chunk_count=result["chunk_count"]
                ))
                success_count += 1
                
        except Exception as e:
            logger.error("文件处理异常", filename=filename, error=str(e))
            results.append(UploadResultItem(
                filename=filename,
                status="failed",
                error=f"处理异常：{str(e)}"
            ))
            failed_count += 1
    
    logger.info("批量上传完成", user_id=current_user.id, success=success_count, failed=failed_count)
    
    return BatchUploadResponse(
        total=len(files),
        success_count=success_count,
        failed_count=failed_count,
        results=results
    )
