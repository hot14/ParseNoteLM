"""
데이터베이스 연결 및 설정
"""
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 로거 설정
logger = logging.getLogger(__name__)

# 설정값 로깅
logger.info(f"데이터베이스 URL: {settings.DATABASE_URL}")
logger.info(f"프로젝트 루트: {settings.PROJECT_ROOT}")

# SQLAlchemy 엔진 생성
try:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False}  # SQLite용
    )
    logger.info("데이터베이스 엔진이 성공적으로 생성되었습니다.")
except Exception as e:
    logger.error(f"데이터베이스 엔진 생성 실패: {e}")
    raise

# 세션 로컬 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성
Base = declarative_base()

def get_db():
    """데이터베이스 세션 의존성"""
    logger.debug("데이터베이스 세션을 생성합니다.")
    db = SessionLocal()
    try:
        # 연결 테스트
        db.execute(text("SELECT 1"))
        logger.debug("데이터베이스 연결이 성공했습니다.")
        yield db
    except Exception as e:
        logger.error(f"데이터베이스 세션 오류: {e}")
        raise
    finally:
        db.close()
        logger.debug("데이터베이스 세션을 닫았습니다.")