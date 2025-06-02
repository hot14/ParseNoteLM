#!/usr/bin/env python3
"""
프로젝트 13 상태 확인 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.models.user import User
from app.models.project import Project
from app.models.document import Document
from sqlalchemy.orm import sessionmaker

def check_project_13():
    """프로젝트 13의 상태를 확인합니다."""
    
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as db:
        print("=== 프로젝트 13 상태 확인 ===")
        
        # 프로젝트 13 정보
        project = db.query(Project).filter(Project.id == 13).first()
        if project:
            print(f"📁 프로젝트: {project.title} (ID: {project.id})")
            print(f"   소유자: {project.user_id}")
            
            # 해당 프로젝트의 문서들
            documents = db.query(Document).filter(Document.project_id == 13).all()
            print(f"\n📄 문서 목록 ({len(documents)}개):")
            for doc in documents:
                print(f"  - ID: {doc.id}, 파일명: {doc.filename}")
                print(f"    상태: {doc.processing_status}")
                print(f"    청크 수: {doc.chunk_count}")
                print(f"    파일 경로: {doc.file_path}")
                print(f"    생성시간: {doc.created_at}")
                print()
                
            # 벡터 스토어 폴더 확인
            vector_store_path = f"/Users/kelly/Desktop/Space/[2025]/ParseNoteLM/backend/data/vector_stores/project_13"
            if os.path.exists(vector_store_path):
                print(f"📊 벡터 스토어 존재: {vector_store_path}")
                files = os.listdir(vector_store_path)
                print(f"   파일들: {files}")
            else:
                print(f"❌ 벡터 스토어 없음: {vector_store_path}")
        else:
            print("❌ 프로젝트 13을 찾을 수 없습니다.")

if __name__ == "__main__":
    check_project_13()