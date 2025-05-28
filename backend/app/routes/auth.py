"""
인증 관련 라우터
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import (
    create_access_token, 
    verify_token, 
    LoginRateLimiter,
    create_password_reset_token,
    verify_password_reset_token
)
from app.core.config import settings
from app.schemas.user import (
    UserCreate, 
    UserResponse, 
    Token, 
    UserLogin,
    PasswordResetRequest,
    PasswordResetConfirm,
    MessageResponse
)
from app.services.user_service import UserService
from app.models.user import User

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """현재 사용자 가져오기"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보를 확인할 수 없습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    email = verify_token(token)
    if email is None:
        raise credentials_exception
    
    user = UserService.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """사용자 등록"""
    # 이메일 중복 확인
    if UserService.is_email_taken(db, user.email):
        raise HTTPException(
            status_code=400,
            detail="이미 등록된 이메일입니다"
        )
    
    # 사용자명 중복 확인
    if UserService.is_username_taken(db, user.username):
        raise HTTPException(
            status_code=400,
            detail="이미 사용 중인 사용자명입니다"
        )
    
    return UserService.create_user(db=db, user=user)

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """사용자 로그인"""
    # 로그인 시도 제한 확인
    if LoginRateLimiter.is_blocked(user_credentials.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="너무 많은 로그인 시도로 인해 계정이 일시적으로 잠겼습니다. 15분 후 다시 시도해주세요.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = UserService.authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        # 실패한 로그인 시도 기록
        LoginRateLimiter.record_failed_attempt(user_credentials.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 성공한 로그인 시도 기록 초기화
    LoginRateLimiter.clear_attempts(user_credentials.email)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 호환 토큰 엔드포인트"""
    # 로그인 시도 제한 확인 (username은 실제로는 email)
    if LoginRateLimiter.is_blocked(form_data.username):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="너무 많은 로그인 시도로 인해 계정이 일시적으로 잠겼습니다. 15분 후 다시 시도해주세요.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = UserService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        # 실패한 로그인 시도 기록
        LoginRateLimiter.record_failed_attempt(form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 성공한 로그인 시도 기록 초기화
    LoginRateLimiter.clear_attempts(form_data.username)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """현재 사용자 정보 조회"""
    return current_user

@router.post("/password-reset-request", response_model=MessageResponse)
async def request_password_reset(
    password_reset: PasswordResetRequest, 
    db: Session = Depends(get_db)
):
    """비밀번호 재설정 요청"""
    # 사용자 존재 확인
    user = UserService.get_user_by_email(db, password_reset.email)
    
    # 보안상 이유로 사용자가 존재하지 않아도 성공 메시지를 반환
    # 실제 운영 환경에서는 이메일 발송 서비스와 연동
    if user:
        # 재설정 토큰 생성
        reset_token = create_password_reset_token(user.email)
        
        # TODO: 실제 운영 환경에서는 이메일로 reset_token을 전송
        print(f"Password reset token for {user.email}: {reset_token}")
        print(f"Reset URL: http://localhost:3000/reset-password?token={reset_token}")
    
    return MessageResponse(
        message="비밀번호 재설정 링크가 이메일로 전송되었습니다. (개발 환경에서는 콘솔을 확인하세요)"
    )

@router.post("/password-reset-confirm", response_model=MessageResponse)
async def confirm_password_reset(
    password_reset: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """비밀번호 재설정 확인"""
    # 토큰 검증
    email = verify_password_reset_token(password_reset.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않거나 만료된 토큰입니다"
        )
    
    # 비밀번호 길이 검증 (최소 6자)
    if len(password_reset.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호는 최소 6자 이상이어야 합니다"
        )
    
    # 비밀번호 업데이트
    success = UserService.update_password(db, email, password_reset.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    # 성공한 비밀번호 변경 후 해당 사용자의 로그인 시도 기록 초기화
    LoginRateLimiter.clear_attempts(email)
    
    return MessageResponse(message="비밀번호가 성공적으로 변경되었습니다")