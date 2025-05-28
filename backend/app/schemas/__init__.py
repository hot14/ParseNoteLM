"""
스키마 패키지 - 모든 Pydantic 스키마를 import
"""

# User 스키마
from .user import (
    UserCreate, UserUpdate, UserResponse, UserLogin, UserProfile,
    PasswordResetRequest, PasswordResetConfirm, MessageResponse
)

# Project 스키마
from .project import (
    ProjectCreate, ProjectUpdate, ProjectResponse, 
    ProjectListResponse, ProjectStatsResponse, ProjectStatistics
)

# Document 스키마
from .document import (
    DocumentCreate, DocumentUploadResponse, DocumentResponse,
    DocumentListResponse, DocumentProcessingUpdate, DocumentStatsResponse,
    DocumentValidationResponse, FileValidationError
)

# Embedding 스키마
from .embedding import (
    EmbeddingCreate, EmbeddingUpdate, EmbeddingResponse,
    EmbeddingListResponse, EmbeddingSearchRequest, EmbeddingSearchResult,
    EmbeddingSearchResponse, EmbeddingBatchCreate, EmbeddingBatchResponse,
    EmbeddingStatsResponse, VectorSimilarityRequest, VectorSimilarityResponse
)

# ChatHistory 스키마
from .chat_history import (
    ChatMessageCreate, UserMessageCreate, AssistantMessageCreate,
    ChatMessageUpdate, ChatMessageResponse, ChatConversationResponse,
    ChatSessionRequest, ChatSessionResponse, MessageFeedbackRequest,
    MessageFeedbackResponse, ChatHistoryListRequest, ChatStatisticsResponse,
    ChatExportRequest, ChatExportResponse
)

# OpenAI 스키마
from .openai import (
    DocumentAnalysisRequest, DocumentAnalysisResponse,
    EmbeddingRequest, EmbeddingResponse,
    BatchEmbeddingRequest, BatchEmbeddingResponse,
    SummaryRequest, SummaryResponse,
    QuestionAnswerRequest, QuestionAnswerResponse,
    OpenAIUsageStats, APIErrorResponse
)

# 모든 스키마를 외부에서 사용할 수 있도록 export
__all__ = [
    # User 스키마
    "UserCreate", "UserUpdate", "UserResponse", "UserLogin", "UserProfile",
    "PasswordResetRequest", "PasswordResetConfirm", "MessageResponse",
    
    # Project 스키마
    "ProjectCreate", "ProjectUpdate", "ProjectResponse", 
    "ProjectListResponse", "ProjectStatsResponse", "ProjectStatistics",
    
    # Document 스키마
    "DocumentCreate", "DocumentUploadResponse", "DocumentResponse",
    "DocumentListResponse", "DocumentProcessingUpdate", "DocumentStatsResponse",
    "DocumentValidationResponse", "FileValidationError",
    
    # Embedding 스키마
    "EmbeddingCreate", "EmbeddingUpdate", "EmbeddingResponse",
    "EmbeddingListResponse", "EmbeddingSearchRequest", "EmbeddingSearchResult",
    "EmbeddingSearchResponse", "EmbeddingBatchCreate", "EmbeddingBatchResponse",
    "EmbeddingStatsResponse", "VectorSimilarityRequest", "VectorSimilarityResponse",
    
    # ChatHistory 스키마
    "ChatMessageCreate", "UserMessageCreate", "AssistantMessageCreate",
    "ChatMessageUpdate", "ChatMessageResponse", "ChatConversationResponse",
    "ChatSessionRequest", "ChatSessionResponse", "MessageFeedbackRequest",
    "MessageFeedbackResponse", "ChatHistoryListRequest", "ChatStatisticsResponse",
    "ChatExportRequest", "ChatExportResponse",
    
    # OpenAI 스키마
    "DocumentAnalysisRequest", "DocumentAnalysisResponse",
    "EmbeddingRequest", "EmbeddingResponse",
    "BatchEmbeddingRequest", "BatchEmbeddingResponse",
    "SummaryRequest", "SummaryResponse",
    "QuestionAnswerRequest", "QuestionAnswerResponse",
    "OpenAIUsageStats", "APIErrorResponse",
]