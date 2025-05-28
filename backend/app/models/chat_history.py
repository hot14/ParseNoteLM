from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Float, JSON, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class MessageRole(str, enum.Enum):
    """메시지 역할"""
    USER = "user"      # 사용자 메시지
    ASSISTANT = "assistant"  # AI 응답 메시지
    SYSTEM = "system"  # 시스템 메시지


class MessageType(str, enum.Enum):
    """메시지 타입"""
    TEXT = "text"         # 일반 텍스트
    QUERY = "query"       # 질의
    ANSWER = "answer"     # 답변
    ERROR = "error"       # 에러 메시지


class ChatHistory(Base):
    """채팅 히스토리 모델 - 사용자와 AI 간의 대화 내역"""
    __tablename__ = "chat_histories"

    id = Column(Integer, primary_key=True, index=True)
    
    # 프로젝트 관계
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    
    # 메시지 정보
    role = Column(Enum(MessageRole), nullable=False, index=True)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT, nullable=False)
    content = Column(Text, nullable=False)  # 메시지 내용
    
    # 토큰 사용량 정보
    input_tokens = Column(Integer, default=0, nullable=False)   # 입력 토큰 수
    output_tokens = Column(Integer, default=0, nullable=False)  # 출력 토큰 수
    total_tokens = Column(Integer, default=0, nullable=False)   # 총 토큰 수
    
    # AI 응답 관련 정보 (assistant role일 때)
    model_used = Column(String(100), nullable=True)  # 사용된 AI 모델
    response_time_ms = Column(Float, nullable=True)  # 응답 시간 (밀리초)
    
    # RAG 관련 정보
    context_documents = Column(JSON, nullable=True)  # 참조된 문서 정보
    similarity_scores = Column(JSON, nullable=True)  # 유사도 점수들
    context_used = Column(Boolean, default=False, nullable=False)  # 컨텍스트 사용 여부
    
    # 세션 정보
    session_id = Column(String(100), nullable=True, index=True)  # 대화 세션 ID
    parent_message_id = Column(Integer, ForeignKey("chat_histories.id"), nullable=True)  # 부모 메시지 (대화 연결)
    
    # 피드백 정보
    user_feedback = Column(String(20), nullable=True)  # thumbs_up, thumbs_down, neutral
    feedback_comment = Column(Text, nullable=True)     # 피드백 코멘트
    
    # 메타데이터
    document_metadata = Column(JSON, nullable=True)  # 추가 메타데이터
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 소프트 삭제
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # 관계 설정
    project = relationship("Project", back_populates="chat_histories")
    parent_message = relationship("ChatHistory", remote_side=[id], backref="child_messages")

    def __repr__(self):
        return (f"<ChatHistory(id={self.id}, project_id={self.project_id}, "
                f"role={self.role}, type={self.message_type})>")

    @property
    def content_preview(self):
        """메시지 내용 미리보기 (처음 100자)"""
        if not self.content:
            return ""
        return self.content[:100] + "..." if len(self.content) > 100 else self.content

    @property
    def is_user_message(self):
        """사용자 메시지인지 확인"""
        return self.role == MessageRole.USER

    @property
    def is_assistant_message(self):
        """AI 응답 메시지인지 확인"""
        return self.role == MessageRole.ASSISTANT

    @property
    def has_context(self):
        """컨텍스트를 사용했는지 확인"""
        return self.context_used and self.context_documents is not None

    @property
    def token_cost_estimate(self):
        """토큰 비용 추정 (간단한 계산)"""
        # OpenAI GPT-3.5-turbo 기준 대략적인 비용
        input_cost = (self.input_tokens / 1000) * 0.0015  # $0.0015 per 1K tokens
        output_cost = (self.output_tokens / 1000) * 0.002   # $0.002 per 1K tokens
        return round(input_cost + output_cost, 6)

    def set_tokens(self, input_tokens: int = 0, output_tokens: int = 0):
        """토큰 수 설정"""
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.total_tokens = input_tokens + output_tokens

    def set_ai_response_info(self, model: str, response_time_ms: float = None):
        """AI 응답 정보 설정"""
        self.model_used = model
        self.response_time_ms = response_time_ms

    def set_context_info(self, documents: list, similarity_scores: list = None):
        """RAG 컨텍스트 정보 설정"""
        self.context_documents = documents
        self.similarity_scores = similarity_scores or []
        self.context_used = len(documents) > 0 if documents else False

    def set_feedback(self, feedback: str, comment: str = None):
        """사용자 피드백 설정"""
        allowed_feedback = ["thumbs_up", "thumbs_down", "neutral"]
        if feedback in allowed_feedback:
            self.user_feedback = feedback
            self.feedback_comment = comment

    def set_metadata(self, **kwargs):
        """메타데이터 설정"""
        if self.document_metadata is None:
            self.document_metadata = {}
        self.document_metadata.update(kwargs)

    def get_metadata(self, key: str = None):
        """메타데이터 조회"""
        if self.document_metadata is None:
            return None if key else {}
        return self.document_metadata.get(key) if key else self.document_metadata

    def soft_delete(self):
        """소프트 삭제 실행"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    @classmethod
    def create_user_message(cls, project_id: int, content: str, session_id: str = None, 
                           parent_message_id: int = None):
        """사용자 메시지 생성"""
        return cls(
            project_id=project_id,
            role=MessageRole.USER,
            message_type=MessageType.QUERY,
            content=content,
            session_id=session_id,
            parent_message_id=parent_message_id
        )

    @classmethod
    def create_assistant_message(cls, project_id: int, content: str, session_id: str = None,
                                parent_message_id: int = None, model_used: str = None):
        """AI 응답 메시지 생성"""
        return cls(
            project_id=project_id,
            role=MessageRole.ASSISTANT,
            message_type=MessageType.ANSWER,
            content=content,
            session_id=session_id,
            parent_message_id=parent_message_id,
            model_used=model_used
        )

    @classmethod
    def get_conversation_history(cls, session, project_id: int, session_id: str = None, 
                               limit: int = 50, include_deleted: bool = False):
        """대화 히스토리 조회"""
        query = session.query(cls).filter(cls.project_id == project_id)
        
        if session_id:
            query = query.filter(cls.session_id == session_id)
            
        if not include_deleted:
            query = query.filter(cls.is_deleted == False)
            
        return query.order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def get_project_statistics(cls, session, project_id: int):
        """프로젝트별 채팅 통계"""
        total_messages = session.query(cls).filter(
            cls.project_id == project_id,
            cls.is_deleted == False
        ).count()
        
        user_messages = session.query(cls).filter(
            cls.project_id == project_id,
            cls.role == MessageRole.USER,
            cls.is_deleted == False
        ).count()
        
        assistant_messages = session.query(cls).filter(
            cls.project_id == project_id,
            cls.role == MessageRole.ASSISTANT,
            cls.is_deleted == False
        ).count()
        
        total_tokens = session.query(cls.total_tokens).filter(
            cls.project_id == project_id,
            cls.is_deleted == False
        ).scalar() or 0
        
        return {
            "total_messages": total_messages,
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "total_tokens": total_tokens,
            "estimated_cost": sum(msg.token_cost_estimate for msg in session.query(cls).filter(
                cls.project_id == project_id,
                cls.is_deleted == False
            ).all())
        }
