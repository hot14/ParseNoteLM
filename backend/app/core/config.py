"""
ParseNoteLM 설정 관리
"""

import os
from dotenv import load_dotenv
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


# .env 파일 로드
load_dotenv()

class Settings(BaseSettings):
    """애플리케이션 설정"""

    # 프로젝트 경로 설정
    PROJECT_ROOT: str = "/Users/kelly/Desktop/Space/[2025]/ParseNoteLM"

    # 데이터베이스 설정 - 절대경로로 강제 변환
    _DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./parsenotelm.db")
    
    @property
    def DATABASE_URL(self) -> str:
        """데이터베이스 URL을 절대경로로 변환"""
        if self._DATABASE_URL.startswith("sqlite:///./backend/"):
            # sqlite:///./backend/parsenotelm.db -> 절대경로로 변환
            db_path = self._DATABASE_URL.replace("sqlite:///./backend/", "")
            abs_path = f"/Users/kelly/Desktop/Space/[2025]/ParseNoteLM/backend/{db_path}"
            return f"sqlite:///{abs_path}"
        elif self._DATABASE_URL.startswith("sqlite:///./"):
            # 상대경로를 절대경로로 변환
            db_path = self._DATABASE_URL.replace("sqlite:///./", "")
            abs_path = f"/Users/kelly/Desktop/Space/[2025]/ParseNoteLM/backend/{db_path}"
            return f"sqlite:///{abs_path}"
        elif self._DATABASE_URL.startswith("sqlite:///") and not self._DATABASE_URL.startswith("sqlite:////"):
            # sqlite:///parsenotelm.db -> 절대경로로 변환
            db_path = self._DATABASE_URL.replace("sqlite:///", "")
            abs_path = f"/Users/kelly/Desktop/Space/[2025]/ParseNoteLM/backend/{db_path}"
            return f"sqlite:///{abs_path}"
        return self._DATABASE_URL
    
    DATABASE_DIR: str = "backend/data"

    # JWT 설정
    SECRET_KEY: str = "parsenotelm-super-secret-key-change-in-production-2025"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # OpenAI API 설정
    OPENAI_API_KEY: Optional[str] = "sk-your-openai-api-key-here"

    # 파일 및 디렉토리 경로 설정
    UPLOAD_DIR: str = "backend/uploads"
    VECTOR_STORE_DIR: str = "backend/data/vector_stores"
    DATA_DIR: str = "backend/data"
    TEMP_DIR: str = "backend/temp"

    # 파일 업로드 설정
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    # 사용량 제한
    MAX_PROJECTS_PER_USER: int = 10
    MAX_DOCUMENTS_PER_PROJECT: int = 50

    # RAG 설정
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    SIMILARITY_THRESHOLD: float = 0.7

    @property
    def get_absolute_upload_dir(self) -> str:
        """업로드 디렉토리의 절대 경로 반환"""
        return os.path.join(self.PROJECT_ROOT, self.UPLOAD_DIR)

    @property
    def get_absolute_vector_store_dir(self) -> str:
        """벡터 스토어 디렉토리의 절대 경로 반환"""
        return os.path.join(self.PROJECT_ROOT, self.VECTOR_STORE_DIR)

    @property
    def get_absolute_data_dir(self) -> str:
        """데이터 디렉토리의 절대 경로 반환"""
        return os.path.join(self.PROJECT_ROOT, self.DATA_DIR)

    @property
    def get_absolute_temp_dir(self) -> str:
        """임시 디렉토리의 절대 경로 반환"""
        return os.path.join(self.PROJECT_ROOT, self.TEMP_DIR)

    def ensure_directories(self):
        """필요한 디렉토리들이 존재하는지 확인하고 생성"""
        directories = [
            self.get_absolute_upload_dir,
            self.get_absolute_vector_store_dir,
            self.get_absolute_data_dir,
            self.get_absolute_temp_dir,
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    class Config:
        env_file = ".env"
        extra = "allow"  # 추가 필드 허용


settings = Settings()

# 애플리케이션 시작 시 필요한 디렉토리 생성
settings.ensure_directories()
