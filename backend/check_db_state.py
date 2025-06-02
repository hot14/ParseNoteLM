#!/usr/bin/env python3
"""
데이터베이스 상태 확인 스크립트
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

def check_database_state():
    """현재 데이터베이스 상태를 확인합니다."""
    
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as db:
        print("=== 데이터베이스 상태 확인 ===")
        
        # 사용자 확인
        users = db.query(User).all()
        print(f"\n📋 사용자 목록 ({len(users)}개):")
        for user in users:
            print(f"  - ID: {user.id}, Email: {user.email}")
        
        # 프로젝트 확인
        projects = db.query(Project).all()
        print(f"\n📁 프로젝트 목록 ({len(projects)}개):")
        for project in projects:
            print(f"  - ID: {project.id}, Title: {project.title}, Owner: {project.user_id}")
        
        # 문서 확인
        documents = db.query(Document).all()
        print(f"\n📄 문서 목록 ({len(documents)}개):")
        for doc in documents:
            print(f"  - ID: {doc.id}, Name: {doc.filename}, Project: {doc.project_id}")
            print(f"    Status: {doc.processing_status}, Chunks: {doc.chunk_count}")
            print(f"    Created: {doc.created_at}")
            print(f"    File Path: {doc.file_path}")
            print()

if __name__ == "__main__":
    check_database_state()