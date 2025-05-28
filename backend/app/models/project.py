from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship, validates
from app.core.database import Base


class Project(Base):
    """프로젝트 모델 - 사용자가 생성하는 프로젝트 정보"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # 소유자 정보
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 소프트 삭제
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # 통계 정보
    document_count = Column(Integer, default=0, nullable=False)  # 현재 문서 수
    
    # 관계 설정
    user = relationship("User", back_populates="projects")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    chat_histories = relationship("ChatHistory", back_populates="project", cascade="all, delete-orphan")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, title='{self.title}', user_id={self.user_id})>"

    @property
    def is_full(self):
        """프로젝트가 문서 제한(5개)에 도달했는지 확인"""
        return self.get_active_document_count() >= 5

    @property
    def active_documents(self):
        """삭제되지 않은 활성 문서 목록"""
        return [doc for doc in self.documents if not doc.is_deleted]

    def get_active_document_count(self):
        """활성 문서 수 계산"""
        return len(self.active_documents)

    def update_document_count(self):
        """문서 수 업데이트"""
        self.document_count = self.get_active_document_count()

    def can_add_document(self):
        """새 문서를 추가할 수 있는지 확인"""
        return not self.is_deleted and not self.is_full

    def soft_delete(self):
        """소프트 삭제 실행"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
