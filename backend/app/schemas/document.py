"""
문서 관련 스키마
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.document import DocumentType, ProcessingStatus


class DocumentBase(BaseModel):
    """문서 기본 스키마"""
    filename: str = Field(..., min_length=1, max_length=255, description="파일명")
    original_filename: str = Field(..., min_length=1, max_length=255, description="원본 파일명")


class DocumentCreate(BaseModel):
    """문서 생성 스키마"""
    original_filename: str = Field(..., min_length=1, max_length=255, description="원본 파일명")
    file_size: int = Field(..., gt=0, description="파일 크기 (바이트)")
    file_type: DocumentType = Field(..., description="파일 타입")
    mime_type: Optional[str] = Field(None, max_length=100, description="MIME 타입")


class DocumentUpdate(BaseModel):
    """문서 업데이트 스키마"""
    filename: Optional[str] = Field(None, min_length=1, max_length=255, description="파일명")
    original_filename: Optional[str] = Field(None, min_length=1, max_length=255, description="원본 파일명")


class DocumentUploadResponse(BaseModel):
    """문서 업로드 응답 스키마"""
    id: int
    filename: str
    original_filename: str
    file_size: int
    file_size_mb: float
    file_type: DocumentType
    processing_status: ProcessingStatus
    project_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """문서 응답 스키마"""
    id: int
    filename: str
    original_filename: str
    file_size: int
    file_size_mb: float
    file_type: DocumentType
    processing_status: ProcessingStatus
    content_length: int
    chunk_count: int
    project_id: int
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None
    processing_error: Optional[str] = None
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """문서 목록 응답 스키마"""
    documents: List[DocumentResponse]
    total: int
    project_can_add_more: bool = Field(description="프로젝트에 더 많은 문서를 추가할 수 있는지 여부")


class DocumentProcessingUpdate(BaseModel):
    """문서 처리 상태 업데이트 스키마"""
    processing_status: ProcessingStatus
    content: Optional[str] = None
    chunk_count: Optional[int] = 0
    processing_error: Optional[str] = None


class DocumentProcessingStatus(BaseModel):
    """문서 처리 상태 스키마"""
    id: int
    processing_status: ProcessingStatus
    processing_error: Optional[str] = None
    chunk_count: int = 0
    updated_at: datetime


class DocumentStatsResponse(BaseModel):
    """문서 통계 응답 스키마"""
    id: int
    filename: str
    original_filename: str
    file_size_mb: float
    processing_status: ProcessingStatus
    content_length: int
    chunk_count: int
    embedding_count: int = 0
    created_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class FileValidationError(BaseModel):
    """파일 검증 에러"""
    field: str
    message: str
    
    
class DocumentValidationResponse(BaseModel):
    """문서 검증 응답"""
    is_valid: bool
    errors: List[FileValidationError] = []
    max_file_size_mb: float = 10.0
    allowed_types: List[str] = ["pdf", "txt"]
