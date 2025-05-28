"""
애플리케이션 설정
"""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""
    
    # JWT 설정
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 데이터베이스 설정
    DATABASE_URL: str = "sqlite:///./parsenotelm.db"
    
    # 파일 업로드 설정
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIRECTORY: str = "uploads"
    
    # 프로젝트 제한
    MAX_PROJECTS_PER_USER: int = 3
    MAX_DOCUMENTS_PER_PROJECT: int = 5
    
    # OpenAI 설정
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-ada-002"
    OPENAI_MAX_TOKENS: int = 1000
    OPENAI_TEMPERATURE: float = 0.1
    
    # CORS 설정
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    model_config = {
        "env_file": ".env",
        "extra": "allow"
    }

settings = Settings()
