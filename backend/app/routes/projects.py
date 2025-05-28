"""
프로젝트 관련 라우터
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def projects_root():
    """프로젝트 라우터 루트"""
    return {"message": "프로젝트 API"}