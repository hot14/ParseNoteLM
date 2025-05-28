"""
관리자 전용 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.routes.auth import get_current_user
from app.core.security import require_role, has_permission
from app.models.user import User, UserRole
from app.schemas.user import UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """모든 사용자 조회 (관리자만 접근 가능)"""
    # 관리자 권한 확인
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    
    users = db.query(User).all()
    return users

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    new_role: UserRole,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """사용자 역할 변경 (관리자만 접근 가능)"""
    # 관리자 권한 확인
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    
    # 대상 사용자 조회
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    # 자기 자신의 역할은 변경할 수 없음
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자신의 역할은 변경할 수 없습니다"
        )
    
    # 역할 업데이트
    target_user.role = new_role
    db.commit()
    db.refresh(target_user)
    
    return {"message": f"사용자 {target_user.username}의 역할이 {new_role.value}로 변경되었습니다"}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """사용자 삭제 (관리자만 접근 가능)"""
    # 관리자 권한 확인
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    
    # 대상 사용자 조회
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    # 자기 자신은 삭제할 수 없음
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자신의 계정은 삭제할 수 없습니다"
        )
    
    # 사용자 삭제
    db.delete(target_user)
    db.commit()
    
    return {"message": f"사용자 {target_user.username}이 삭제되었습니다"}

@router.get("/stats")
async def get_system_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """시스템 통계 조회 (관리자만 접근 가능)"""
    # 관리자 권한 확인
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    
    # 통계 데이터 수집
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    verified_users = db.query(User).filter(User.is_verified == True).count()
    
    # 역할별 사용자 수
    user_count = db.query(User).filter(User.role == UserRole.USER).count()
    premium_count = db.query(User).filter(User.role == UserRole.PREMIUM).count()
    admin_count = db.query(User).filter(User.role == UserRole.ADMIN).count()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "verified_users": verified_users,
        "role_distribution": {
            "user": user_count,
            "premium": premium_count,
            "admin": admin_count
        }
    }
