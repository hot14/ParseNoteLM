#!/usr/bin/env python3
"""
데이터베이스 테이블 생성 스크립트
"""
from app.core.database import engine, Base
from app.models.user import User
from app.models.project import Project
from app.models.document import Document
from app.models.embedding import Embedding
from app.models.chat_history import ChatHistory

def create_tables():
    """모든 테이블 생성"""
    try:
        print("데이터베이스 테이블 생성 중...")
        Base.metadata.create_all(bind=engine)
        print("✅ 모든 테이블이 성공적으로 생성되었습니다!")
    except Exception as e:
        print(f"❌ 테이블 생성 중 오류 발생: {e}")

if __name__ == "__main__":
    create_tables()
