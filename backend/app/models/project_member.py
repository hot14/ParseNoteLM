"""
프로젝트 멤버 관리 모델
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class MemberRole(str, enum.Enum):
    """프로젝트 멤버 역할"""
    OWNER = "owner"      # 프로젝트 소유자
    ADMIN = "admin"      # 관리자 (모든 권한)
    EDITOR = "editor"    # 편집자 (문서 편집 가능)
    VIEWER = "viewer"    # 뷰어 (읽기 전용)


class ProjectMember(Base):
    """프로젝트 멤버 모델 - 프로젝트에 참여하는 사용자 정보"""
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    
    # 외래키
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 멤버 역할
    role = Column(Enum(MemberRole), nullable=False, default=MemberRole.VIEWER)
    
    # 초대 정보
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    invited_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    joined_at = Column(DateTime, nullable=True)  # 초대 수락 시간
    
    # 상태
    is_active = Column(Boolean, default=True, nullable=False)
    left_at = Column(DateTime, nullable=True)  # 프로젝트 탈퇴 시간
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 관계 설정
    project = relationship("Project", back_populates="members")
    user = relationship("User", foreign_keys=[user_id], back_populates="project_memberships")
    inviter = relationship("User", foreign_keys=[invited_by])

    def __repr__(self):
        return f"<ProjectMember(project_id={self.project_id}, user_id={self.user_id}, role={self.role})>"
    
    @property
    def is_owner(self):
        """소유자인지 확인"""
        return self.role == MemberRole.OWNER
    
    @property
    def can_manage_members(self):
        """멤버 관리 권한이 있는지 확인"""
        return self.role in [MemberRole.OWNER, MemberRole.ADMIN]
    
    @property
    def can_edit_documents(self):
        """문서 편집 권한이 있는지 확인"""
        return self.role in [MemberRole.OWNER, MemberRole.ADMIN, MemberRole.EDITOR]
    
    @property
    def can_view_documents(self):
        """문서 조회 권한이 있는지 확인"""
        return self.is_active  # 활성 멤버만 조회 가능
    
    def has_permission(self, action: str) -> bool:
        """특정 액션에 대한 권한 확인"""
        if not self.is_active:
            return False
            
        permissions = {
            MemberRole.OWNER: ["view", "edit", "delete", "manage_members", "manage_project"],
            MemberRole.ADMIN: ["view", "edit", "delete", "manage_members"],
            MemberRole.EDITOR: ["view", "edit"],
            MemberRole.VIEWER: ["view"]
        }
        
        return action in permissions.get(self.role, [])
