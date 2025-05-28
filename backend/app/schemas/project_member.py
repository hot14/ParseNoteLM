"""
프로젝트 멤버 관련 Pydantic 스키마
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from app.models.project_member import MemberRole


class ProjectMemberBase(BaseModel):
    """프로젝트 멤버 기본 스키마"""
    role: MemberRole = Field(..., description="멤버 역할")


class ProjectMemberCreate(BaseModel):
    """프로젝트 멤버 초대 요청 스키마"""
    email: EmailStr = Field(..., description="초대할 사용자 이메일")
    role: MemberRole = Field(MemberRole.VIEWER, description="초대할 역할")
    message: Optional[str] = Field(None, description="초대 메시지", max_length=500)


class ProjectMemberUpdate(BaseModel):
    """프로젝트 멤버 정보 업데이트 스키마"""
    role: Optional[MemberRole] = Field(None, description="변경할 역할")


class ProjectMemberResponse(ProjectMemberBase):
    """프로젝트 멤버 응답 스키마"""
    id: int = Field(..., description="멤버 ID")
    project_id: int = Field(..., description="프로젝트 ID")
    user_id: int = Field(..., description="사용자 ID")
    user_email: str = Field(..., description="사용자 이메일")
    user_username: str = Field(..., description="사용자명")
    
    invited_by: Optional[int] = Field(None, description="초대한 사용자 ID")
    invited_at: datetime = Field(..., description="초대 시간")
    joined_at: Optional[datetime] = Field(None, description="참여 시간")
    
    is_active: bool = Field(..., description="활성 상태")
    left_at: Optional[datetime] = Field(None, description="탈퇴 시간")
    
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")
    
    # 권한 정보
    can_manage_members: bool = Field(..., description="멤버 관리 권한")
    can_edit_documents: bool = Field(..., description="문서 편집 권한")
    can_view_documents: bool = Field(..., description="문서 조회 권한")

    class Config:
        from_attributes = True


class ProjectMemberListResponse(BaseModel):
    """프로젝트 멤버 목록 응답 스키마"""
    members: List[ProjectMemberResponse] = Field(..., description="멤버 목록")
    total: int = Field(..., description="전체 멤버 수")
    project_id: int = Field(..., description="프로젝트 ID")
    project_title: str = Field(..., description="프로젝트 제목")


class MemberInvitationResponse(BaseModel):
    """멤버 초대 응답 스키마"""
    success: bool = Field(..., description="초대 성공 여부")
    message: str = Field(..., description="응답 메시지")
    member_id: Optional[int] = Field(None, description="멤버 ID (성공시)")
    email: str = Field(..., description="초대된 이메일")


class MemberPermissions(BaseModel):
    """멤버 권한 정보 스키마"""
    can_view: bool = Field(..., description="조회 권한")
    can_edit: bool = Field(..., description="편집 권한") 
    can_delete: bool = Field(..., description="삭제 권한")
    can_manage_members: bool = Field(..., description="멤버 관리 권한")
    can_manage_project: bool = Field(..., description="프로젝트 관리 권한")


class ProjectMemberStats(BaseModel):
    """프로젝트 멤버 통계 스키마"""
    total_members: int = Field(..., description="전체 멤버 수")
    active_members: int = Field(..., description="활성 멤버 수")
    owners: int = Field(..., description="소유자 수")
    admins: int = Field(..., description="관리자 수")
    editors: int = Field(..., description="편집자 수")
    viewers: int = Field(..., description="뷰어 수")
    pending_invitations: int = Field(..., description="대기 중인 초대 수")
