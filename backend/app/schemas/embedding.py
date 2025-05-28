"""
임베딩 관련 스키마
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class EmbeddingBase(BaseModel):
    """임베딩 기본 스키마"""
    chunk_index: int = Field(..., ge=0, description="청크 인덱스")
    chunk_text: str = Field(..., min_length=1, description="청크 텍스트")
    chunk_size: int = Field(..., gt=0, description="청크 크기")


class EmbeddingCreate(EmbeddingBase):
    """임베딩 생성 스키마"""
    document_id: int = Field(..., gt=0, description="문서 ID")
    embedding_vector: Optional[List[float]] = Field(None, description="임베딩 벡터")
    embedding_model: str = Field(default="text-embedding-ada-002", description="임베딩 모델")
    metadata: Optional[Dict[str, Any]] = Field(None, description="메타데이터")
    tokens: int = Field(default=0, ge=0, description="토큰 수")


class EmbeddingUpdate(BaseModel):
    """임베딩 업데이트 스키마"""
    embedding_vector: Optional[List[float]] = Field(None, description="임베딩 벡터")
    embedding_model: Optional[str] = Field(None, description="임베딩 모델")
    metadata: Optional[Dict[str, Any]] = Field(None, description="메타데이터")


class EmbeddingResponse(BaseModel):
    """임베딩 응답 스키마"""
    id: int
    document_id: int
    chunk_index: int
    chunk_text: str
    chunk_preview: str
    chunk_size: int
    embedding_model: str
    vector_dimension: int
    has_vector: bool
    tokens: int
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EmbeddingListResponse(BaseModel):
    """임베딩 목록 응답 스키마"""
    embeddings: List[EmbeddingResponse]
    total: int
    document_id: int


class EmbeddingSearchRequest(BaseModel):
    """임베딩 검색 요청 스키마"""
    query: str = Field(..., min_length=1, max_length=1000, description="검색 쿼리")
    project_id: Optional[int] = Field(None, description="프로젝트 ID (특정 프로젝트 내 검색)")
    document_id: Optional[int] = Field(None, description="문서 ID (특정 문서 내 검색)")
    limit: int = Field(default=5, ge=1, le=20, description="반환할 결과 수")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="유사도 임계값")


class EmbeddingSearchResult(BaseModel):
    """임베딩 검색 결과"""
    id: int
    document_id: int
    document_title: str
    chunk_index: int
    chunk_text: str
    chunk_preview: str
    similarity_score: float
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class EmbeddingSearchResponse(BaseModel):
    """임베딩 검색 응답 스키마"""
    query: str
    results: List[EmbeddingSearchResult]
    total: int
    search_time_ms: float
    max_similarity: float
    min_similarity: float


class EmbeddingBatchCreate(BaseModel):
    """임베딩 배치 생성 스키마"""
    document_id: int = Field(..., gt=0, description="문서 ID")
    chunks: List[Dict[str, Any]] = Field(..., description="청크 리스트")
    embedding_model: str = Field(default="text-embedding-ada-002", description="임베딩 모델")


class EmbeddingBatchResponse(BaseModel):
    """임베딩 배치 응답 스키마"""
    document_id: int
    created_count: int
    failed_count: int
    total_chunks: int
    embeddings: List[EmbeddingResponse]


class EmbeddingStatsResponse(BaseModel):
    """임베딩 통계 응답 스키마"""
    document_id: int
    document_title: str
    total_embeddings: int
    total_tokens: int
    average_chunk_size: float
    embedding_model: str
    vector_dimension: int
    created_at: datetime
    last_updated: datetime
    
    class Config:
        from_attributes = True


class VectorSimilarityRequest(BaseModel):
    """벡터 유사도 계산 요청"""
    vector1: List[float] = Field(..., description="첫 번째 벡터")
    vector2: List[float] = Field(..., description="두 번째 벡터")


class VectorSimilarityResponse(BaseModel):
    """벡터 유사도 계산 응답"""
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="코사인 유사도 점수")
    vector1_dimension: int
    vector2_dimension: int
