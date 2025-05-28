"""
OpenAI 관련 Pydantic 스키마
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class DocumentAnalysisRequest(BaseModel):
    """문서 분석 요청 스키마"""
    content: str = Field(..., description="분석할 문서 내용", min_length=1, max_length=10000)

class DocumentAnalysisResponse(BaseModel):
    """문서 분석 응답 스키마"""
    summary: str = Field(..., description="문서 요약")
    keywords: List[str] = Field(..., description="주요 키워드 목록")
    category: str = Field(..., description="문서 카테고리")
    topic: str = Field(..., description="주제 분야")
    difficulty: str = Field(..., description="난이도")

class EmbeddingRequest(BaseModel):
    """임베딩 생성 요청 스키마"""
    text: str = Field(..., description="임베딩을 생성할 텍스트", min_length=1, max_length=8000)

class EmbeddingResponse(BaseModel):
    """임베딩 생성 응답 스키마"""
    embedding: List[float] = Field(..., description="생성된 임베딩 벡터")
    dimension: int = Field(..., description="임베딩 차원")

class BatchEmbeddingRequest(BaseModel):
    """배치 임베딩 생성 요청 스키마"""
    texts: List[str] = Field(..., description="임베딩을 생성할 텍스트 목록", max_items=100)

class BatchEmbeddingResponse(BaseModel):
    """배치 임베딩 생성 응답 스키마"""
    embeddings: List[List[float]] = Field(..., description="생성된 임베딩 벡터 목록")
    count: int = Field(..., description="생성된 임베딩 수")

class SummaryRequest(BaseModel):
    """텍스트 요약 요청 스키마"""
    text: str = Field(..., description="요약할 텍스트", min_length=1, max_length=15000)
    max_length: Optional[int] = Field(200, description="최대 요약 길이", ge=50, le=500)

class SummaryResponse(BaseModel):
    """텍스트 요약 응답 스키마"""
    summary: str = Field(..., description="생성된 요약")
    original_length: int = Field(..., description="원본 텍스트 길이")
    summary_length: int = Field(..., description="요약 텍스트 길이")

class QuestionAnswerRequest(BaseModel):
    """질의응답 요청 스키마"""
    question: str = Field(..., description="사용자 질문", min_length=1, max_length=1000)
    context: str = Field(..., description="검색된 컨텍스트", min_length=1, max_length=8000)

class QuestionAnswerResponse(BaseModel):
    """질의응답 응답 스키마"""
    answer: str = Field(..., description="생성된 답변")
    context_used: bool = Field(..., description="컨텍스트 사용 여부")

class OpenAIUsageStats(BaseModel):
    """OpenAI 사용 통계 스키마"""
    total_requests: int = Field(..., description="총 요청 수")
    total_tokens: int = Field(..., description="총 토큰 사용량")
    embedding_requests: int = Field(..., description="임베딩 요청 수")
    chat_requests: int = Field(..., description="채팅 요청 수")
    last_request_time: Optional[str] = Field(None, description="마지막 요청 시간")

class APIErrorResponse(BaseModel):
    """API 오류 응답 스키마"""
    error: str = Field(..., description="오류 메시지")
    error_type: str = Field(..., description="오류 유형")
    details: Optional[Dict[str, Any]] = Field(None, description="추가 오류 세부사항")
