"""
사용자 모델
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class UserRole(str, enum.Enum):
    """사용자 역할"""
    USER = "user"           # 일반 사용자
    PREMIUM = "premium"     # 프리미엄 사용자
    ADMIN = "admin"         # 관리자

class User(Base):
    """사용자 테이블"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    project_memberships = relationship("ProjectMember", foreign_keys="ProjectMember.user_id", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username}, role={self.role})>"

    @property
    def project_count(self):
        """사용자의 활성 프로젝트 수"""
        return len([p for p in self.projects if not p.is_deleted])

    @property
    def can_create_project(self):
        """새 프로젝트를 생성할 수 있는지 확인 (최대 3개)"""
        return self.project_count < 3