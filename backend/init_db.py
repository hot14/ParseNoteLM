#!/usr/bin/env python3
"""
데이터베이스 초기화 스크립트
"""
import os
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, Base
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from sqlalchemy.orm import sessionmaker

def init_database():
    """데이터베이스 초기화"""
    print("데이터베이스 테이블 생성 중...")
    
    # 모든 테이블 생성
    Base.metadata.create_all(bind=engine)
    print("✅ 데이터베이스 테이블이 생성되었습니다.")
    
    # 세션 생성
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 기본 관리자 계정 생성 (이미 존재하지 않는 경우)
        admin_email = "admin@parsenotelm.com"
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        
        if not existing_admin:
            admin_user = User(
                email=admin_email,
                username="admin",
                hashed_password=get_password_hash("admin123!"),
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True
            )
            db.add(admin_user)
            db.commit()
            print(f"✅ 관리자 계정이 생성되었습니다: {admin_email}")
            print("   비밀번호: admin123!")
        else:
            print(f"ℹ️  관리자 계정이 이미 존재합니다: {admin_email}")
            
    except Exception as e:
        print(f"❌ 초기 데이터 생성 중 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
    print("🎉 데이터베이스 초기화가 완료되었습니다!")
