"""
보안 관련 유틸리티
"""
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# 비밀번호 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 로그인 시도 추적을 위한 메모리 저장소
login_attempts: Dict[str, list] = {}

class LoginRateLimiter:
    """로그인 시도 제한 클래스"""
    
    @staticmethod
    def is_blocked(email: str, max_attempts: int = 5, window_minutes: int = 15) -> bool:
        """사용자가 로그인 시도 제한에 걸렸는지 확인"""
        if email not in login_attempts:
            return False
        
        now = datetime.utcnow()
        cutoff_time = now - timedelta(minutes=window_minutes)
        
        # 시간 윈도우 내의 시도만 필터링
        recent_attempts = [
            attempt for attempt in login_attempts[email]
            if attempt > cutoff_time
        ]
        
        # 정리된 시도 목록으로 업데이트
        login_attempts[email] = recent_attempts
        
        return len(recent_attempts) >= max_attempts
    
    @staticmethod
    def record_failed_attempt(email: str):
        """실패한 로그인 시도 기록"""
        now = datetime.utcnow()
        if email not in login_attempts:
            login_attempts[email] = []
        login_attempts[email].append(now)
    
    @staticmethod
    def clear_attempts(email: str):
        """성공한 로그인 후 시도 기록 초기화"""
        if email in login_attempts:
            del login_attempts[email]

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """액세스 토큰 생성"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[str]:
    """토큰 검증 및 사용자 이메일 반환"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None

def create_password_reset_token(email: str) -> str:
    """비밀번호 재설정 토큰 생성 (30분 유효)"""
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode = {"sub": email, "exp": expire, "type": "password_reset"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_password_reset_token(token: str) -> Optional[str]:
    """비밀번호 재설정 토큰 검증"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if email is None or token_type != "password_reset":
            return None
        return email
    except JWTError:
        return None

# 권한 관리 함수들
def require_role(required_role: str):
    """역할 기반 권한 검사 데코레이터"""
    from functools import wraps
    from fastapi import HTTPException, status
    from app.models.user import UserRole
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 현재 사용자 정보 가져오기
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="인증이 필요합니다"
                )
            
            # 관리자는 모든 권한을 가짐
            if current_user.role == UserRole.ADMIN:
                return await func(*args, **kwargs)
            
            # 요구되는 역할 검사
            if required_role == "admin" and current_user.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="관리자 권한이 필요합니다"
                )
            elif required_role == "premium" and current_user.role not in [UserRole.PREMIUM, UserRole.ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="프리미엄 사용자 권한이 필요합니다"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def has_permission(user_role: str, required_permission: str) -> bool:
    """사용자 역할별 권한 확인"""
    from app.models.user import UserRole
    
    # 권한 매트릭스
    permissions = {
        UserRole.USER: [
            "read_own_projects",
            "create_project",
            "upload_file",
            "query_documents"
        ],
        UserRole.PREMIUM: [
            "read_own_projects",
            "create_project",
            "upload_file", 
            "query_documents",
            "advanced_search",
            "export_data",
            "priority_support"
        ],
        UserRole.ADMIN: [
            "read_all_projects",
            "manage_users",
            "system_settings",
            "view_analytics",
            "moderate_content"
        ]
    }
    
    # 관리자는 모든 권한을 가짐
    if user_role == UserRole.ADMIN:
        return True
    
    # 사용자 역할에 따른 권한 확인
    user_permissions = permissions.get(user_role, [])
    return required_permission in user_permissions