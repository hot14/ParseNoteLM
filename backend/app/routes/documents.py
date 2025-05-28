"""
문서 관련 라우터
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def documents_root():
    """문서 라우터 루트"""
    return {"message": "문서 API"}