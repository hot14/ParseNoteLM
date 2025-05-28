"""
사용자 관련 스키마
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.user import UserRole

class UserBase(BaseModel):
    """사용자 기본 스키마"""
    email: EmailStr
    username: str

class UserCreate(UserBase):
    """사용자 생성 스키마"""
    password: str
    role: Optional[UserRole] = UserRole.USER

class UserUpdate(BaseModel):
    """사용자 업데이트 스키마"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None

class UserProfile(BaseModel):
    """사용자 프로필 스키마"""
    id: int
    email: EmailStr
    username: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    """사용자 로그인 스키마"""
    email: EmailStr
    password: str

class UserResponse(UserBase):
    """사용자 응답 스키마"""
    id: int
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    """토큰 스키마"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """토큰 데이터 스키마"""
    email: Optional[str] = None

class PasswordResetRequest(BaseModel):
    """비밀번호 재설정 요청 스키마"""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """비밀번호 재설정 확인 스키마"""
    token: str
    new_password: str

class MessageResponse(BaseModel):
    """메시지 응답 스키마"""
    message: str