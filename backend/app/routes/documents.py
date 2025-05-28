"""
문서 관리 API 엔드포인트
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.document import Document, DocumentStatus
from app.schemas.document import (
    DocumentCreate, DocumentResponse, DocumentUpdate, 
    DocumentListResponse, DocumentProcessingStatus
)
from app.schemas.project import ProjectResponse
import os
import pathlib
from app.config import settings
from app.core.file_validation_simple import SimpleFileValidator
from app.services.document_service import get_document_service

router = APIRouter()

# 간단한 파일 검증 함수
def validate_uploaded_file(file: UploadFile, file_size: int) -> None:
    """간단한 파일 검증"""
    is_valid, error_msg = SimpleFileValidator.validate_file(file.filename, file_size)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    project_id: int = Form(...),
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    문서 업로드
    """
    # 프로젝트 존재 및 권한 확인
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id,
        Project.deleted_at.is_(None)
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=404,
            detail="프로젝트를 찾을 수 없거나 접근 권한이 없습니다."
        )
    
    # 현재 프로젝트의 문서 수 확인
    current_doc_count = db.query(Document).filter(
        Document.project_id == project_id,
        Document.deleted_at.is_(None)
    ).count()
    
    # 파일 유효성 검사
    validate_uploaded_file(file, file.size)
    
    try:
        # 데이터베이스에 문서 레코드 생성
        document = Document(
            filename=file.filename,
            original_filename=file.filename,
            project_id=project_id,
            user_id=current_user.id,
            file_type=SimpleFileValidator.get_file_type(file.filename),
            file_size=file.size or 0,
            description=description,
            status=DocumentStatus.UPLOADING
        )
        
        db.add(document)
        db.flush()  # ID를 얻기 위해 flush
        
        # 파일 저장 (간단한 구현)
        upload_dir = pathlib.Path(settings.UPLOAD_DIRECTORY)
        upload_dir.mkdir(exist_ok=True)
        
        # 사용자별/프로젝트별 디렉토리 생성
        user_dir = upload_dir / str(current_user.id) / str(project_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일 저장
        file_path = user_dir / f"{document.id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 문서 정보 업데이트
        document.file_path = str(file_path)
        document.file_size = len(content)
        document.status = DocumentStatus.COMPLETED  # 일단 완료로 처리
        
        # 간단한 텍스트 추출 (PDF는 나중에 구현)
        if file.filename.endswith('.txt'):
            try:
                document.content = content.decode('utf-8')
            except:
                document.content = content.decode('utf-8', errors='ignore')
        
        db.commit()
        
        return DocumentResponse.model_validate(document)
        
    except Exception as e:
        db.rollback()
        # 저장된 파일 삭제
        if 'file_path' in locals() and os.path.exists(str(file_path)):
            try:
                os.remove(str(file_path))
            except:
                pass
        
        raise HTTPException(
            status_code=500,
            detail=f"문서 업로드 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/", response_model=DocumentListResponse)
def get_documents(
    project_id: Optional[int] = None,
    status: Optional[DocumentStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    사용자의 문서 목록 조회
    """
    query = db.query(Document).join(Project).filter(
        Project.user_id == current_user.id,
        Document.deleted_at.is_(None)
    )
    
    if project_id:
        query = query.filter(Document.project_id == project_id)
    
    if status:
        query = query.filter(Document.status == status)
    
    total = query.count()
    documents = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(doc) for doc in documents],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    특정 문서 조회
    """
    document = db.query(Document).join(Project).filter(
        Document.id == document_id,
        Project.user_id == current_user.id,
        Document.deleted_at.is_(None)
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=404,
            detail="문서를 찾을 수 없습니다."
        )
    
    return DocumentResponse.model_validate(document)


@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: int,
    update_data: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    문서 정보 업데이트
    """
    document = db.query(Document).join(Project).filter(
        Document.id == document_id,
        Project.user_id == current_user.id,
        Document.deleted_at.is_(None)
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=404,
            detail="문서를 찾을 수 없습니다."
        )
    
    # 업데이트 가능한 필드만 수정
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if hasattr(document, field):
            setattr(document, field, value)
    
    db.commit()
    return DocumentResponse.model_validate(document)


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    문서 삭제 (소프트 삭제)
    """
    document = db.query(Document).join(Project).filter(
        Document.id == document_id,
        Project.user_id == current_user.id,
        Document.deleted_at.is_(None)
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=404,
            detail="문서를 찾을 수 없습니다."
        )
    
    try:
        # 소프트 삭제 실행
        document.is_deleted = True
        document.deleted_at = datetime.utcnow()
        
        # 파일 시스템에서 실제 파일 삭제
        if document.file_path and os.path.exists(document.file_path):
            try:
                os.remove(document.file_path)
            except Exception:
                pass  # 파일 삭제 실패해도 DB 삭제는 진행
        
        db.commit()
        
        return {"message": "문서가 성공적으로 삭제되었습니다."}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"문서 삭제 실패: {str(e)}"
        )


@router.get("/{document_id}/status", response_model=DocumentProcessingStatus)
def get_document_processing_status(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    문서 처리 상태 조회
    """
    document = db.query(Document).join(Project).filter(
        Document.id == document_id,
        Project.user_id == current_user.id,
        Document.deleted_at.is_(None)
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=404,
            detail="문서를 찾을 수 없습니다."
        )
    
    # 진행률 계산
    progress = 0
    if document.status == DocumentStatus.UPLOADING:
        progress = 25
    elif document.status == DocumentStatus.PROCESSING:
        progress = 50
    elif document.status == DocumentStatus.COMPLETED:
        progress = 100
    elif document.status == DocumentStatus.FAILED:
        progress = 0
    
    return DocumentProcessingStatus(
        document_id=document.id,
        status=document.status,
        progress=progress,
        error_message=document.error_message,
        created_at=document.created_at,
        updated_at=document.updated_at
    )


@router.post("/{document_id}/reprocess")
async def reprocess_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    문서 재처리 (OpenAI 분석 포함)
    """
    document = db.query(Document).join(Project).filter(
        Document.id == document_id,
        Project.user_id == current_user.id,
        Document.deleted_at.is_(None)
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=404,
            detail="문서를 찾을 수 없습니다."
        )
    
    if document.status == DocumentStatus.PROCESSING:
        raise HTTPException(
            status_code=400,
            detail="문서가 이미 처리 중입니다."
        )
    
    try:
        # 문서 처리 서비스를 통해 재처리
        document_service = get_document_service()
        success = await document_service.reprocess_document(document, db)
        
        if success:
            return {"message": "문서 재처리가 성공적으로 완료되었습니다."}
        else:
            raise HTTPException(
                status_code=500,
                detail="문서 재처리 중 오류가 발생했습니다."
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"문서 재처리 실패: {str(e)}"
        )