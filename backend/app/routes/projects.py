"""
프로젝트 관리 API 엔드포인트
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.core.auth import get_current_user
from app.core.exceptions import ProjectNotFoundException
from app.models.user import User
from app.models.project import Project
from app.models.document import Document
from app.schemas.project import (
    ProjectCreate, ProjectResponse, ProjectUpdate, 
    ProjectListResponse, ProjectStatistics
)
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=ProjectResponse)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    새 프로젝트 생성
    """
    logger.info(f"사용자 {current_user.username}이 프로젝트 생성을 시도합니다: {project_data.title}")
    
    try:
        # 사용자 프로젝트 수 제한 확인
        current_project_count = db.query(Project).filter(
            Project.user_id == current_user.id,
            Project.deleted_at.is_(None)
        ).count()
        
        logger.info(f"현재 프로젝트 수: {current_project_count}")
        
        if current_project_count >= settings.MAX_PROJECTS_PER_USER:
            raise HTTPException(
                status_code=400,
                detail=f"최대 {settings.MAX_PROJECTS_PER_USER}개의 프로젝트만 생성할 수 있습니다."
            )
        
        # 프로젝트명 중복 확인 (사용자별)
        existing_project = db.query(Project).filter(
            Project.user_id == current_user.id,
            Project.title == project_data.title,
            Project.deleted_at.is_(None)
        ).first()
        
        if existing_project:
            raise HTTPException(
                status_code=400,
                detail="이미 같은 이름의 프로젝트가 존재합니다."
            )
        
        # 프로젝트 생성
        project = Project(
            user_id=current_user.id,
            title=project_data.title,
            description=project_data.description
        )
        
        logger.info("프로젝트 객체 생성 완료, 데이터베이스에 저장 시도")
        db.add(project)
        db.commit()
        db.refresh(project)
        
        logger.info(f"프로젝트 생성 성공: ID={project.id}")
        return ProjectResponse.model_validate(project)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"프로젝트 생성 중 오류 발생: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"프로젝트 생성 실패: {str(e)}"
        )


@router.get("/", response_model=ProjectListResponse)
def get_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    사용자의 프로젝트 목록 조회
    """
    query = db.query(Project).filter(
        Project.user_id == current_user.id,
        Project.deleted_at.is_(None)
    )
    
    total = query.count()
    projects = query.order_by(Project.created_at.desc()).offset(skip).limit(limit).all()
    
    # 사용자가 더 많은 프로젝트를 생성할 수 있는지 확인
    can_create_more = total < settings.MAX_PROJECTS_PER_USER
    
    return ProjectListResponse(
        projects=[ProjectResponse.model_validate(project) for project in projects],
        total=total,
        skip=skip,
        limit=limit,
        can_create_more=can_create_more
    )


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    특정 프로젝트 조회
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id,
        Project.deleted_at.is_(None)
    ).first()
    
    if not project:
        raise ProjectNotFoundException
    
    return ProjectResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    update_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    프로젝트 정보 업데이트
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id,
        Project.deleted_at.is_(None)
    ).first()
    
    if not project:
        raise ProjectNotFoundException
    
    # 프로젝트명 중복 확인 (자신 제외)
    if update_data.title and update_data.title != project.title:
        existing_project = db.query(Project).filter(
            Project.user_id == current_user.id,
            Project.title == update_data.title,
            Project.id != project_id,
            Project.deleted_at.is_(None)
        ).first()
        
        if existing_project:
            raise HTTPException(
                status_code=400,
                detail="이미 같은 이름의 프로젝트가 존재합니다."
            )
    
    try:
        # 업데이트 가능한 필드만 수정
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            if hasattr(project, field):
                setattr(project, field, value)
        
        db.commit()
        return ProjectResponse.model_validate(project)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"프로젝트 업데이트 실패: {str(e)}"
        )


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    프로젝트 삭제 (소프트 삭제)
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id,
        Project.deleted_at.is_(None)
    ).first()
    
    if not project:
        raise ProjectNotFoundException
    
    try:
        # 소프트 삭제
        from datetime import datetime
        project.deleted_at = datetime.utcnow()
        
        # 프로젝트 내 모든 문서도 소프트 삭제
        documents = db.query(Document).filter(
            Document.project_id == project_id,
            Document.deleted_at.is_(None)
        ).all()
        
        for document in documents:
            document.deleted_at = datetime.utcnow()
        
        db.commit()
        
        # 파일 시스템에서 프로젝트 폴더 삭제 (백그라운드에서)
        try:
            # 간단한 파일 정리 (나중에 구현)
            pass
        except Exception as e:
            # 파일 삭제 실패해도 DB는 이미 커밋됨
            print(f"파일 정리 실패: {e}")
        
        return {"message": "프로젝트가 성공적으로 삭제되었습니다."}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"프로젝트 삭제 실패: {str(e)}"
        )


@router.get("/{project_id}/statistics", response_model=ProjectStatistics)
def get_project_statistics(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    프로젝트 통계 조회
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id,
        Project.deleted_at.is_(None)
    ).first()
    
    if not project:
        raise ProjectNotFoundException
    
    try:
        # 문서 통계
        total_documents = db.query(Document).filter(
            Document.project_id == project_id,
            Document.deleted_at.is_(None)
        ).count()
        
        completed_documents = db.query(Document).filter(
            Document.project_id == project_id,
            Document.status == "completed",
            Document.deleted_at.is_(None)
        ).count()
        
        processing_documents = db.query(Document).filter(
            Document.project_id == project_id,
            Document.status == "processing",
            Document.deleted_at.is_(None)
        ).count()
        
        failed_documents = db.query(Document).filter(
            Document.project_id == project_id,
            Document.status == "failed",
            Document.deleted_at.is_(None)
        ).count()
        
        # 저장소 통계 (간단하게 계산)
        documents_in_project = total_documents
        total_size_bytes = db.query(func.sum(Document.file_size)).filter(
            Document.project_id == project_id,
            Document.is_deleted == False
        ).scalar() or 0
        
        # 임베딩 개수 (나중에 구현)
        total_embeddings = 0
        
        return ProjectStatistics(
            id=project.id,
            title=project.title,
            description=project.description,
            total_documents=documents_in_project,
            total_storage_mb=round(total_size_bytes / (1024 * 1024), 2),
            total_embeddings=total_embeddings,
            created_at=project.created_at,
            last_activity=project.updated_at,
            can_upload_more=documents_in_project < 5
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"통계 조회 실패: {str(e)}"
        )