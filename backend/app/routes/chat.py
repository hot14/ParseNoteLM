"""
채팅 관련 라우터
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def chat_root():
    """채팅 라우터 루트"""
    return {"message": "채팅 API"}