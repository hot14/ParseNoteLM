"""
ParseNoteLM FastAPI 메인 애플리케이션
"""
import logging
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import time
from app.routes import (
    auth,
    admin,
    documents,
    projects,
    openai_api,
    rag,
    project_members,
    media,
    videos,
    video,
    monitoring,
)
from app.core.config import settings
from app.core.database import engine, Base
from app.core.logging_config import setup_logging, log_api_request, log_api_response

# 로깅 시스템 초기화
setup_logging(
    level="DEBUG",  # 개발 환경에서는 DEBUG 레벨
    log_file=f"{settings.PROJECT_ROOT}/logs/parsenotelm.log",
    app_name="ParseNoteLM"
)

logger = logging.getLogger(__name__)

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ParseNoteLM API",
    description="AI 기반 문서 분석 및 질의응답 서비스",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(admin.router, prefix="/api", tags=["admin"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(project_members.router, prefix="/api/projects", tags=["project-members"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(openai_api.router, tags=["openai"])
app.include_router(rag.router, tags=["rag"])
app.include_router(media.router, tags=["media"])
app.include_router(videos.router, tags=["videos"])
app.include_router(video.router)
app.include_router(monitoring.router)

@app.get("/")
async def root():
    """루트 엔드포인트"""
    logger.info("루트 엔드포인트에 접근했습니다.")
    return {"message": "ParseNoteLM API가 정상적으로 작동 중입니다"}

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    logger.info("ParseNoteLM API 서버가 시작되었습니다.")
    logger.info(f"프로젝트 루트: {settings.PROJECT_ROOT}")
    logger.info(f"데이터베이스 URL: {settings.DATABASE_URL}")

@app.on_event("shutdown") 
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    logger.info("ParseNoteLM API 서버가 종료됩니다.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)