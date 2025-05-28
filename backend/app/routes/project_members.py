"""
프로젝트 멤버 관리 API 엔드포인트
"""
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.project_member import ProjectMember, MemberRole
from app.schemas.project_member import (
    ProjectMemberCreate, ProjectMemberUpdate, ProjectMemberResponse,
    ProjectMemberListResponse, MemberInvitationResponse, 
    MemberPermissions, ProjectMemberStats
)

router = APIRouter()


def get_project_with_permission(
    project_id: int, 
    user: User, 
    db: Session, 
    required_action: str = "view"
) -> Project:
    """프로젝트와 사용자 권한 확인"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.deleted_at.is_(None)
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=404,
            detail="프로젝트를 찾을 수 없습니다."
        )
    
    # 프로젝트 소유자인지 확인
    if project.user_id == user.id:
        return project
    
    # 프로젝트 멤버인지 확인
    member = db.query(ProjectMember).filter(
        and_(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
            ProjectMember.is_active == True
        )
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=403,
            detail="이 프로젝트에 접근할 권한이 없습니다."
        )
    
    # 권한 확인
    if not member.has_permission(required_action):
        raise HTTPException(
            status_code=403,
            detail=f"'{required_action}' 권한이 없습니다."
        )
    
    return project


@router.get("/{project_id}/members", response_model=ProjectMemberListResponse)
def get_project_members(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """프로젝트 멤버 목록 조회"""
    project = get_project_with_permission(project_id, current_user, db, "view")
    
    # 프로젝트 소유자를 자동으로 OWNER 멤버로 포함
    members = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id
    ).all()
    
    # 소유자가 멤버 테이블에 없으면 추가
    owner_member = next((m for m in members if m.user_id == project.user_id), None)
    if not owner_member:
        # 프로젝트 소유자를 OWNER로 자동 생성
        owner_member = ProjectMember(
            project_id=project_id,
            user_id=project.user_id,
            role=MemberRole.OWNER,
            is_active=True,
            joined_at=project.created_at
        )
        db.add(owner_member)
        db.commit()
        db.refresh(owner_member)
        members.append(owner_member)
    
    # 응답 데이터 생성
    member_responses = []
    for member in members:
        if member.is_active:
            member_responses.append(ProjectMemberResponse(
                id=member.id,
                project_id=member.project_id,
                user_id=member.user_id,
                user_email=member.user.email,
                user_username=member.user.username,
                role=member.role,
                invited_by=member.invited_by,
                invited_at=member.invited_at,
                joined_at=member.joined_at,
                is_active=member.is_active,
                left_at=member.left_at,
                created_at=member.created_at,
                updated_at=member.updated_at,
                can_manage_members=member.can_manage_members,
                can_edit_documents=member.can_edit_documents,
                can_view_documents=member.can_view_documents
            ))
    
    return ProjectMemberListResponse(
        members=member_responses,
        total=len(member_responses),
        project_id=project.id,
        project_title=project.title
    )


@router.post("/{project_id}/members", response_model=MemberInvitationResponse)
def invite_project_member(
    project_id: int,
    invitation_data: ProjectMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """프로젝트 멤버 초대"""
    project = get_project_with_permission(project_id, current_user, db, "manage_members")
    
    # 초대할 사용자 조회
    invited_user = db.query(User).filter(User.email == invitation_data.email).first()
    if not invited_user:
        raise HTTPException(
            status_code=404,
            detail="해당 이메일의 사용자를 찾을 수 없습니다."
        )
    
    # 이미 멤버인지 확인
    existing_member = db.query(ProjectMember).filter(
        and_(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == invited_user.id
        )
    ).first()
    
    if existing_member:
        if existing_member.is_active:
            raise HTTPException(
                status_code=400,
                detail="이미 프로젝트 멤버입니다."
            )
        else:
            # 비활성 멤버를 다시 활성화
            existing_member.is_active = True
            existing_member.role = invitation_data.role
            existing_member.invited_by = current_user.id
            existing_member.left_at = None
            db.commit()
            
            return MemberInvitationResponse(
                success=True,
                message="멤버가 성공적으로 재초대되었습니다.",
                member_id=existing_member.id,
                email=invitation_data.email
            )
    
    try:
        # 새 멤버 생성
        new_member = ProjectMember(
            project_id=project_id,
            user_id=invited_user.id,
            role=invitation_data.role,
            invited_by=current_user.id,
            is_active=True,
            joined_at=datetime.utcnow()
        )
        
        db.add(new_member)
        db.commit()
        db.refresh(new_member)
        
        return MemberInvitationResponse(
            success=True,
            message="멤버가 성공적으로 초대되었습니다.",
            member_id=new_member.id,
            email=invitation_data.email
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"멤버 초대 실패: {str(e)}"
        )


@router.put("/{project_id}/members/{member_id}", response_model=ProjectMemberResponse)
def update_project_member(
    project_id: int,
    member_id: int,
    update_data: ProjectMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """프로젝트 멤버 정보 업데이트"""
    project = get_project_with_permission(project_id, current_user, db, "manage_members")
    
    member = db.query(ProjectMember).filter(
        and_(
            ProjectMember.id == member_id,
            ProjectMember.project_id == project_id
        )
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=404,
            detail="멤버를 찾을 수 없습니다."
        )
    
    # 프로젝트 소유자의 역할은 변경할 수 없음
    if member.user_id == project.user_id and update_data.role != MemberRole.OWNER:
        raise HTTPException(
            status_code=400,
            detail="프로젝트 소유자의 역할은 변경할 수 없습니다."
        )
    
    try:
        if update_data.role:
            member.role = update_data.role
        
        db.commit()
        db.refresh(member)
        
        return ProjectMemberResponse(
            id=member.id,
            project_id=member.project_id,
            user_id=member.user_id,
            user_email=member.user.email,
            user_username=member.user.username,
            role=member.role,
            invited_by=member.invited_by,
            invited_at=member.invited_at,
            joined_at=member.joined_at,
            is_active=member.is_active,
            left_at=member.left_at,
            created_at=member.created_at,
            updated_at=member.updated_at,
            can_manage_members=member.can_manage_members,
            can_edit_documents=member.can_edit_documents,
            can_view_documents=member.can_view_documents
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"멤버 정보 업데이트 실패: {str(e)}"
        )


@router.delete("/{project_id}/members/{member_id}")
def remove_project_member(
    project_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """프로젝트 멤버 제거"""
    project = get_project_with_permission(project_id, current_user, db, "manage_members")
    
    member = db.query(ProjectMember).filter(
        and_(
            ProjectMember.id == member_id,
            ProjectMember.project_id == project_id
        )
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=404,
            detail="멤버를 찾을 수 없습니다."
        )
    
    # 프로젝트 소유자는 제거할 수 없음
    if member.user_id == project.user_id:
        raise HTTPException(
            status_code=400,
            detail="프로젝트 소유자는 제거할 수 없습니다."
        )
    
    try:
        member.is_active = False
        member.left_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "멤버가 성공적으로 제거되었습니다."}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"멤버 제거 실패: {str(e)}"
        )


@router.get("/{project_id}/members/{member_id}/permissions", response_model=MemberPermissions)
def get_member_permissions(
    project_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """멤버 권한 조회"""
    project = get_project_with_permission(project_id, current_user, db, "view")
    
    member = db.query(ProjectMember).filter(
        and_(
            ProjectMember.id == member_id,
            ProjectMember.project_id == project_id,
            ProjectMember.is_active == True
        )
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=404,
            detail="활성 멤버를 찾을 수 없습니다."
        )
    
    return MemberPermissions(
        can_view=member.has_permission("view"),
        can_edit=member.has_permission("edit"),
        can_delete=member.has_permission("delete"),
        can_manage_members=member.has_permission("manage_members"),
        can_manage_project=member.has_permission("manage_project")
    )


@router.get("/{project_id}/members/stats", response_model=ProjectMemberStats)
def get_project_member_statistics(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """프로젝트 멤버 통계 조회"""
    project = get_project_with_permission(project_id, current_user, db, "view")
    
    members = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id
    ).all()
    
    # 통계 계산
    total_members = len(members)
    active_members = len([m for m in members if m.is_active])
    
    role_counts = {role: 0 for role in MemberRole}
    for member in members:
        if member.is_active:
            role_counts[member.role] += 1
    
    # 소유자가 멤버 테이블에 없으면 카운트에 포함
    if not any(m.user_id == project.user_id for m in members):
        role_counts[MemberRole.OWNER] += 1
        active_members += 1
        total_members += 1
    
    pending_invitations = len([m for m in members if m.joined_at is None])
    
    return ProjectMemberStats(
        total_members=total_members,
        active_members=active_members,
        owners=role_counts[MemberRole.OWNER],
        admins=role_counts[MemberRole.ADMIN],
        editors=role_counts[MemberRole.EDITOR],
        viewers=role_counts[MemberRole.VIEWER],
        pending_invitations=pending_invitations
    )
