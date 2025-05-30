"""
사용자 인증 관련 API 엔드포인트
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, OAuth2PasswordRequestForm, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
    LoginRateLimiter,
    verify_token,
    create_password_reset_token,
)
from app.core.logging_config import (
    log_api_request,
    log_api_response,
    log_user_action,
    log_database_operation,
    log_error_with_context,
)
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserLogin,
    Token,
    UserUpdate,
    PasswordResetRequest,
    PasswordResetConfirm,
    MessageResponse,
)

# from app.utils.email import send_password_reset_email  # 임시 주석처리

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security), 
    db: Session = Depends(get_db)
):
    """현재 사용자 가져오기"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보를 확인할 수 없습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )

    email = verify_token(credentials.credentials)
    if email is None:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    사용자 등록

    Args:
        user_data: 사용자 등록 정보 (이메일, 비밀번호, 사용자명)
        db: 데이터베이스 세션

    Returns:
        UserResponse: 등록된 사용자 정보

    Raises:
        HTTPException: 이메일이 이미 사용 중인 경우
    """
    start_time = datetime.now()

    # API 요청 로깅
    log_api_request(
        method="POST",
        path="/auth/register",
        body={"email": user_data.email, "username": user_data.username},
    )

    try:
        logger.info(f"🆕 사용자 등록 시도: {user_data.email}")

        # 이메일 중복 검사
        logger.debug(f"🔍 이메일 중복 검사: {user_data.email}")
        log_database_operation("SELECT", "users")

        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            logger.warning(f"⚠️ 이미 존재하는 이메일: {user_data.email}")
            raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다")

        # 사용자 생성
        logger.debug(f"🔐 비밀번호 해싱 진행: {user_data.email}")
        hashed_password = get_password_hash(user_data.password)

        logger.debug(f"💾 새 사용자 데이터베이스 저장: {user_data.email}")
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            role="user",
            is_active=True,
            is_verified=False,
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # 성공 로깅
        response_time = (datetime.now() - start_time).total_seconds()
        log_database_operation(
            "INSERT", "users", record_id=db_user.id, duration=response_time
        )
        log_user_action(
            db_user.id,
            "회원가입",
            {"email": user_data.email, "username": user_data.username},
        )

        logger.info(f"✅ 사용자 등록 성공: {user_data.email} (ID: {db_user.id})")
        log_api_response(200, response_time)

        return db_user

    except HTTPException:
        response_time = (datetime.now() - start_time).total_seconds()
        log_api_response(400, response_time, "이메일 중복")
        raise
    except Exception as e:
        response_time = (datetime.now() - start_time).total_seconds()
        log_error_with_context(
            logger,
            e,
            context={
                "operation": "user_registration",
                "email": user_data.email,
                "username": user_data.username,
            },
        )
        log_api_response(500, response_time, str(e))
        raise HTTPException(
            status_code=500, detail="사용자 등록 중 오류가 발생했습니다"
        )


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    사용자 로그인

    Args:
        user_credentials: 로그인 정보 (이메일, 비밀번호)
        db: 데이터베이스 세션

    Returns:
        Token: JWT 액세스 토큰

    Raises:
        HTTPException: 인증 실패, 계정 비활성화, 로그인 시도 제한 등
    """
    start_time = datetime.now()

    # API 요청 로깅
    log_api_request(
        method="POST", path="/auth/login", body={"email": user_credentials.email}
    )

    try:
        logger.info(f"🔐 로그인 시도: {user_credentials.email}")

        # 로그인 시도 제한 확인
        logger.debug(f"🛡️ 로그인 시도 제한 확인: {user_credentials.email}")
        if LoginRateLimiter.is_blocked(user_credentials.email):
            logger.warning(f"🚫 로그인 시도 제한 적용: {user_credentials.email}")
            response_time = (datetime.now() - start_time).total_seconds()
            log_api_response(429, response_time, "로그인 시도 제한")
            raise HTTPException(
                status_code=429,
                detail="너무 많은 로그인 시도로 인해 일시적으로 차단되었습니다",
            )

        # 사용자 조회
        logger.debug(f"🔍 사용자 데이터베이스 조회: {user_credentials.email}")
        log_database_operation("SELECT", "users")

        user = db.query(User).filter(User.email == user_credentials.email).first()
        if not user:
            logger.warning(f"❌ 존재하지 않는 사용자: {user_credentials.email}")
            LoginRateLimiter.record_failed_attempt(user_credentials.email)
            response_time = (datetime.now() - start_time).total_seconds()
            log_api_response(401, response_time, "존재하지 않는 사용자")
            raise HTTPException(
                status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다"
            )

        # 비밀번호 검증
        logger.debug(f"🔑 비밀번호 검증: {user_credentials.email}")
        if not verify_password(user_credentials.password, user.hashed_password):
            logger.warning(f"❌ 비밀번호 불일치: {user_credentials.email}")
            LoginRateLimiter.record_failed_attempt(user_credentials.email)
            log_user_action(user.id, "로그인 실패", {"reason": "비밀번호 불일치"})
            response_time = (datetime.now() - start_time).total_seconds()
            log_api_response(401, response_time, "비밀번호 불일치")
            raise HTTPException(
                status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다"
            )

        # 계정 활성화 확인
        if not user.is_active:
            logger.warning(f"🚫 비활성화된 계정: {user_credentials.email}")
            response_time = (datetime.now() - start_time).total_seconds()
            log_api_response(401, response_time, "비활성화된 계정")
            raise HTTPException(status_code=401, detail="비활성화된 계정입니다")

        # 성공시 제한 해제
        logger.debug(f"🔓 로그인 시도 제한 해제: {user_credentials.email}")
        LoginRateLimiter.clear_attempts(user_credentials.email)

        # JWT 토큰 생성
        logger.debug(f"🎫 JWT 토큰 생성: {user_credentials.email}")
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )

        # 성공 로깅
        response_time = (datetime.now() - start_time).total_seconds()
        log_user_action(
            user.id,
            "로그인 성공",
            {
                "ip": "unknown",  # FastAPI Request에서 가져올 수 있음
                "user_agent": "unknown",  # FastAPI Request에서 가져올 수 있음
            },
        )

        logger.info(f"✅ 로그인 성공: {user_credentials.email} (ID: {user.id})")
        log_api_response(200, response_time)

        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception as e:
        response_time = (datetime.now() - start_time).total_seconds()
        log_error_with_context(
            logger,
            e,
            context={"operation": "user_login", "email": user_credentials.email},
        )
        log_api_response(500, response_time, str(e))
        raise HTTPException(
            status_code=500, detail="로그인 처리 중 오류가 발생했습니다"
        )


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """OAuth2 호환 토큰 엔드포인트"""
    # 로그인 시도 제한 확인 (username은 실제로는 email)
    if LoginRateLimiter.is_blocked(form_data.username):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="너무 많은 로그인 시도로 인해 계정이 일시적으로 잠겼습니다. 15분 후 다시 시도해주세요.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
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
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """현재 로그인한 사용자 정보 조회"""
    log_user_action(
        user_id=current_user.id,
        action="프로필 조회",
        details={}
    )
    return current_user


@router.post("/password-reset-request", response_model=MessageResponse)
async def request_password_reset(
    password_reset: PasswordResetRequest, db: Session = Depends(get_db)
):
    """비밀번호 재설정 요청"""
    # 사용자 존재 확인
    user = db.query(User).filter(User.email == password_reset.email).first()

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
    password_reset: PasswordResetConfirm, db: Session = Depends(get_db)
):
    """비밀번호 재설정 확인"""
    # 토큰 검증
    email = verify_password_reset_token(password_reset.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않거나 만료된 토큰입니다",
        )

    # 비밀번호 길이 검증 (최소 6자)
    if len(password_reset.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호는 최소 6자 이상이어야 합니다",
        )

    # 비밀번호 업데이트
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다"
        )

    user.hashed_password = get_password_hash(password_reset.new_password)
    db.commit()

    # 성공한 비밀번호 변경 후 해당 사용자의 로그인 시도 기록 초기화
    LoginRateLimiter.clear_attempts(email)

    return MessageResponse(message="비밀번호가 성공적으로 변경되었습니다")
