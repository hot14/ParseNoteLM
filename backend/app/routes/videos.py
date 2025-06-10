from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.core.auth import get_current_user
from app.models.user import User
from app.services.video_service import VideoService, get_video_service
from app.schemas.video import VideoSummaryResponse
import tempfile
import os

router = APIRouter(prefix="/api/videos", tags=["Videos"])

@router.post("/summary", response_model=VideoSummaryResponse)
async def summarize_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    video_service: VideoService = Depends(get_video_service),
):
    """비디오 요약 및 스크립트 추출"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        transcript, summary = await video_service.process_video(tmp_path)
        os.remove(tmp_path)
        return VideoSummaryResponse(transcript=transcript, summary=summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"비디오 처리 실패: {e}")
