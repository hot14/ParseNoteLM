"""
채팅 히스토리 관련 스키마
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.chat_history import MessageRole, MessageType


class ChatMessageBase(BaseModel):
    """채팅 메시지 기본 스키마"""
    content: str = Field(..., min_length=1, max_length=10000, description="메시지 내용")
    role: MessageRole = Field(..., description="메시지 역할")
    message_type: MessageType = Field(default=MessageType.TEXT, description="메시지 타입")


class ChatMessageCreate(BaseModel):
    """채팅 메시지 생성 스키마"""
    project_id: int = Field(..., gt=0, description="프로젝트 ID")
    content: str = Field(..., min_length=1, max_length=10000, description="메시지 내용")
    session_id: Optional[str] = Field(None, max_length=100, description="세션 ID")
    parent_message_id: Optional[int] = Field(None, description="부모 메시지 ID")


class UserMessageCreate(ChatMessageCreate):
    """사용자 메시지 생성 스키마"""
    message_type: MessageType = Field(default=MessageType.QUERY, description="메시지 타입")


class AssistantMessageCreate(BaseModel):
    """AI 응답 메시지 생성 스키마"""
    project_id: int = Field(..., gt=0, description="프로젝트 ID")
    content: str = Field(..., min_length=1, description="응답 내용")
    session_id: Optional[str] = Field(None, description="세션 ID")
    parent_message_id: Optional[int] = Field(None, description="부모 메시지 ID")
    model_used: str = Field(default="gpt-3.5-turbo", description="사용된 AI 모델")
    input_tokens: int = Field(default=0, ge=0, description="입력 토큰 수")
    output_tokens: int = Field(default=0, ge=0, description="출력 토큰 수")
    response_time_ms: Optional[float] = Field(None, ge=0, description="응답 시간 (밀리초)")
    context_documents: Optional[List[Dict[str, Any]]] = Field(None, description="참조된 문서")
    similarity_scores: Optional[List[float]] = Field(None, description="유사도 점수")


class ChatMessageUpdate(BaseModel):
    """채팅 메시지 업데이트 스키마"""
    content: Optional[str] = Field(None, min_length=1, max_length=10000, description="메시지 내용")
    metadata: Optional[Dict[str, Any]] = Field(None, description="메타데이터")


class ChatMessageResponse(BaseModel):
    """채팅 메시지 응답 스키마"""
    id: int
    project_id: int
    role: MessageRole
    message_type: MessageType
    content: str
    content_preview: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model_used: Optional[str] = None
    response_time_ms: Optional[float] = None
    context_used: bool
    session_id: Optional[str] = None
    parent_message_id: Optional[int] = None
    user_feedback: Optional[str] = None
    token_cost_estimate: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ChatConversationResponse(BaseModel):
    """대화 내역 응답 스키마"""
    messages: List[ChatMessageResponse]
    total: int
    session_id: Optional[str] = None
    project_id: int


class ChatSessionRequest(BaseModel):
    """채팅 세션 요청 스키마"""
    project_id: int = Field(..., gt=0, description="프로젝트 ID")
    query: str = Field(..., min_length=1, max_length=1000, description="질의 내용")
    session_id: Optional[str] = Field(None, description="세션 ID (없으면 새 세션 생성)")
    include_context: bool = Field(default=True, description="RAG 컨텍스트 포함 여부")
    max_context_docs: int = Field(default=5, ge=1, le=10, description="최대 컨텍스트 문서 수")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="유사도 임계값")


class ChatSessionResponse(BaseModel):
    """채팅 세션 응답 스키마"""
    session_id: str
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
    context_documents: List[Dict[str, Any]]
    total_tokens: int
    response_time_ms: float
    cost_estimate: float


class MessageFeedbackRequest(BaseModel):
    """메시지 피드백 요청 스키마"""
    feedback: str = Field(..., pattern="^(thumbs_up|thumbs_down|neutral)$", description="피드백 타입")
    comment: Optional[str] = Field(None, max_length=500, description="피드백 코멘트")


class MessageFeedbackResponse(BaseModel):
    """메시지 피드백 응답 스키마"""
    message_id: int
    feedback: str
    comment: Optional[str] = None
    updated_at: datetime


class ChatHistoryListRequest(BaseModel):
    """채팅 히스토리 목록 요청 스키마"""
    project_id: Optional[int] = Field(None, description="프로젝트 ID")
    session_id: Optional[str] = Field(None, description="세션 ID")
    role: Optional[MessageRole] = Field(None, description="메시지 역할 필터")
    page: int = Field(default=1, ge=1, description="페이지 번호")
    limit: int = Field(default=20, ge=1, le=100, description="페이지당 항목 수")
    start_date: Optional[datetime] = Field(None, description="시작 날짜")
    end_date: Optional[datetime] = Field(None, description="종료 날짜")


class ChatStatisticsResponse(BaseModel):
    """채팅 통계 응답 스키마"""
    project_id: int
    total_messages: int
    user_messages: int
    assistant_messages: int
    total_tokens: int
    estimated_cost: float
    average_response_time: Optional[float] = None
    most_active_day: Optional[str] = None
    feedback_summary: Dict[str, int] = Field(default_factory=dict)


class ChatExportRequest(BaseModel):
    """채팅 내역 내보내기 요청 스키마"""
    project_id: int = Field(..., gt=0, description="프로젝트 ID")
    session_id: Optional[str] = Field(None, description="세션 ID")
    format: str = Field(default="json", pattern="^(json|csv|txt)$", description="내보내기 형식")
    include_metadata: bool = Field(default=False, description="메타데이터 포함 여부")
    start_date: Optional[datetime] = Field(None, description="시작 날짜")
    end_date: Optional[datetime] = Field(None, description="종료 날짜")


class ChatExportResponse(BaseModel):
    """채팅 내역 내보내기 응답 스키마"""
    download_url: str
    filename: str
    file_size: int
    total_messages: int
    expires_at: datetime
