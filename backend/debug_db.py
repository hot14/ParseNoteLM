#!/usr/bin/env python3
"""
데이터베이스 디버깅 스크립트
"""
import os
from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.database import Base
from app.models.user import User
from app.models.project import Project
from app.models.document import Document
from app.models.embedding import Embedding
from app.models.chat_history import ChatHistory

def debug_database():
    """데이터베이스 상태 디버깅"""
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    print(f"현재 작업 디렉토리: {os.getcwd()}")
    
    # 엔진 생성
    engine = create_engine(settings.DATABASE_URL, echo=True)
    
    print("\n=== 데이터베이스 파일 확인 ===")
    db_path = settings.DATABASE_URL.replace("sqlite:///./", "")
    if os.path.exists(db_path):
        print(f"✅ 데이터베이스 파일 존재: {db_path}")
        print(f"파일 크기: {os.path.getsize(db_path)} bytes")
    else:
        print(f"❌ 데이터베이스 파일 없음: {db_path}")
    
    print("\n=== 테이블 생성 시도 ===")
    try:
        Base.metadata.drop_all(bind=engine)  # 기존 테이블 삭제
        Base.metadata.create_all(bind=engine)  # 새로 생성
        print("✅ 테이블 생성 완료")
    except Exception as e:
        print(f"❌ 테이블 생성 실패: {e}")
        return
    
    print("\n=== 테이블 목록 확인 ===")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = result.fetchall()
            print(f"테이블 목록: {[table[0] for table in tables]}")
    except Exception as e:
        print(f"❌ 테이블 목록 조회 실패: {e}")

if __name__ == "__main__":
    debug_database()
