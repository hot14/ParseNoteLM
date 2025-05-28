"""
프로젝트 관련 스키마
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    """프로젝트 기본 스키마"""
    name: str = Field(..., min_length=1, max_length=255, description="프로젝트 이름")
    description: Optional[str] = Field(None, max_length=1000, description="프로젝트 설명")


class ProjectCreate(ProjectBase):
    """프로젝트 생성 스키마"""
    pass


class ProjectUpdate(BaseModel):
    """프로젝트 업데이트 스키마"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="프로젝트 이름")
    description: Optional[str] = Field(None, max_length=1000, description="프로젝트 설명")


class ProjectResponse(ProjectBase):
    """프로젝트 응답 스키마"""
    id: int
    user_id: int
    document_count: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False
    
    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """프로젝트 목록 응답 스키마"""
    projects: List[ProjectResponse]
    total: int
    can_create_more: bool = Field(description="더 많은 프로젝트를 생성할 수 있는지 여부")


class ProjectStatsResponse(BaseModel):
    """프로젝트 통계 응답 스키마"""
    id: int
    name: str
    document_count: int
    total_embeddings: int = 0
    total_chats: int = 0
    last_activity: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ProjectStatistics(BaseModel):
    """프로젝트 상세 통계 스키마"""
    project_id: int
    total_documents: int
    completed_documents: int
    processing_documents: int
    failed_documents: int
    total_storage_mb: float
    created_at: datetime
    updated_at: datetime
