"""
ParseNoteLM 백엔드 서버
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, admin, documents, projects, openai_api, rag, project_members

app = FastAPI(
    title="ParseNoteLM API",
    description="AI 기반 문서 분석 및 질의응답 서비스",
    version="1.0.0"
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

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {"message": "ParseNoteLM API가 정상적으로 작동 중입니다"}

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)