"""
사용자 서비스
"""
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password
from typing import Optional

class UserService:
    """사용자 관련 비즈니스 로직"""
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """사용자명으로 사용자 조회"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def create_user(db: Session, user: UserCreate) -> User:
        """새 사용자 생성"""
        hashed_password = get_password_hash(user.password)
        db_user = User(
            email=user.email,
            username=user.username,
            hashed_password=hashed_password,
            role=user.role
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """사용자 인증"""
        user = UserService.get_user_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    @staticmethod
    def is_email_taken(db: Session, email: str) -> bool:
        """이메일 중복 확인"""
        return UserService.get_user_by_email(db, email) is not None
    
    @staticmethod
    def is_username_taken(db: Session, username: str) -> bool:
        """사용자명 중복 확인"""
        return UserService.get_user_by_username(db, username) is not None
    
    @staticmethod
    def update_password(db: Session, email: str, new_password: str) -> bool:
        """사용자 비밀번호 업데이트"""
        user = UserService.get_user_by_email(db, email)
        if not user:
            return False
        
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        return True