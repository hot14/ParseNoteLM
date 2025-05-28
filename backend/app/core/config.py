"""
ParseNoteLM 설정 관리
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 데이터베이스 설정
    DATABASE_URL: str = "sqlite:///./parsenotelm.db"
    
    # JWT 설정
    SECRET_KEY: str = "parsenotelm-super-secret-key-change-in-production-2025"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI API 설정
    OPENAI_API_KEY: Optional[str] = "sk-your-openai-api-key-here"
    
    # 파일 업로드 설정
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # 사용량 제한
    MAX_PROJECTS_PER_USER: int = 3
    MAX_DOCUMENTS_PER_PROJECT: int = 5
    
    class Config:
        env_file = ".env"
        extra = "allow"  # 추가 필드 허용

settings = Settings()