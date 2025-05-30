"""
로깅 설정 모듈
상세한 로깅을 위한 설정과 유틸리티 함수들
"""
import logging
import sys
from pathlib import Path
from typing import Optional
import traceback
from datetime import datetime


class DetailedFormatter(logging.Formatter):
    """상세한 로그 포맷터"""
    
    def format(self, record):
        # 기본 포맷
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # ERROR 레벨일 경우 추가 정보 포함
        if record.levelno >= logging.ERROR:
            log_format += '\n  📍 파일: %(pathname)s:%(lineno)d'
            log_format += '\n  🔧 함수: %(funcName)s'
            
            # 예외 정보가 있을 경우 스택 트레이스 추가
            if record.exc_info:
                log_format += '\n  📋 스택 트레이스:\n%(exc_text)s'
        
        formatter = logging.Formatter(log_format)
        return formatter.format(record)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    app_name: str = "ParseNoteLM"
) -> None:
    """
    애플리케이션 로깅 설정
    
    Args:
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR)
        log_file: 로그 파일 경로 (None이면 콘솔만)
        app_name: 애플리케이션 이름
    """
    # 로그 레벨 설정
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 기존 핸들러 제거
    root_logger.handlers.clear()
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(DetailedFormatter())
    root_logger.addHandler(console_handler)
    
    # 파일 핸들러 (옵션)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(DetailedFormatter())
        root_logger.addHandler(file_handler)
    
    # 애플리케이션 시작 로그
    logger = logging.getLogger(__name__)
    logger.info(f"🚀 {app_name} 로깅 시스템 초기화 완료")
    logger.info(f"📊 로그 레벨: {level}")
    if log_file:
        logger.info(f"📁 로그 파일: {log_file}")


def log_function_call(func_name: str, args: dict = None, kwargs: dict = None):
    """함수 호출 로깅"""
    logger = logging.getLogger(__name__)
    
    log_msg = f"🔧 함수 호출: {func_name}"
    if args:
        log_msg += f"\n  📥 Args: {args}"
    if kwargs:
        log_msg += f"\n  📥 Kwargs: {kwargs}"
    
    logger.debug(log_msg)


def log_api_request(method: str, path: str, user_id: Optional[int] = None, 
                   body: Optional[dict] = None):
    """API 요청 로깅"""
    logger = logging.getLogger("api")
    
    log_msg = f"🌐 {method} {path}"
    if user_id:
        log_msg += f" (사용자 ID: {user_id})"
    if body and method in ['POST', 'PUT', 'PATCH']:
        # 민감한 정보 마스킹
        safe_body = mask_sensitive_data(body)
        log_msg += f"\n  📦 요청 본문: {safe_body}"
    
    logger.info(log_msg)


def log_api_response(status_code: int, response_time: float, 
                    error: Optional[str] = None):
    """API 응답 로깅"""
    logger = logging.getLogger("api")
    
    status_emoji = "✅" if status_code < 400 else "⚠️" if status_code < 500 else "❌"
    log_msg = f"{status_emoji} 응답: {status_code} ({response_time:.3f}s)"
    
    if error:
        log_msg += f"\n  ❌ 오류: {error}"
    
    if status_code >= 400:
        logger.warning(log_msg)
    else:
        logger.info(log_msg)


def log_database_operation(operation: str, table: str, record_id: Optional[int] = None,
                          duration: Optional[float] = None):
    """데이터베이스 작업 로깅"""
    logger = logging.getLogger("database")
    
    log_msg = f"🗄️ DB {operation}: {table}"
    if record_id:
        log_msg += f" (ID: {record_id})"
    if duration:
        log_msg += f" ({duration:.3f}s)"
    
    logger.info(log_msg)


def log_user_action(user_id: int, action: str, details: Optional[dict] = None):
    """사용자 액션 로깅"""
    logger = logging.getLogger("user_action")
    
    log_msg = f"👤 사용자 {user_id}: {action}"
    if details:
        safe_details = mask_sensitive_data(details)
        log_msg += f"\n  📋 상세: {safe_details}"
    
    logger.info(log_msg)


def mask_sensitive_data(data: dict) -> dict:
    """민감한 데이터 마스킹"""
    if not isinstance(data, dict):
        return data
    
    sensitive_keys = ['password', 'token', 'secret', 'key', 'api_key']
    masked_data = data.copy()
    
    for key in masked_data:
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            if isinstance(masked_data[key], str) and len(masked_data[key]) > 0:
                masked_data[key] = f"{masked_data[key][:3]}***"
    
    return masked_data


def log_error_with_context(logger: logging.Logger, error: Exception, 
                          context: dict = None):
    """컨텍스트와 함께 오류 로깅"""
    error_msg = f"❌ 오류 발생: {type(error).__name__}: {str(error)}"
    
    if context:
        error_msg += f"\n  🔍 컨텍스트: {context}"
    
    # 스택 트레이스 추가
    error_msg += f"\n  📋 상세 스택 트레이스:\n{traceback.format_exc()}"
    
    logger.error(error_msg)
