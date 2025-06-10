"""미디어 요약 API"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_user
from app.models.user import User
from app.services.openai_service import get_openai_service, OpenAIService
from app.services.youtube_service import YouTubeService
from app.schemas.media import YouTubeSummaryRequest, YouTubeSummaryResponse

router = APIRouter(prefix="/api/media", tags=["media"])
logger = logging.getLogger(__name__)

@router.post("/youtube/summary", response_model=YouTubeSummaryResponse)
async def youtube_summary(
    request: YouTubeSummaryRequest,
    current_user: User = Depends(get_current_user),
    openai_service: OpenAIService = Depends(get_openai_service),
):
    """YouTube 영상 요약 API"""
    transcript = await YouTubeService.get_transcript(request.url)
    if not transcript:
        raise HTTPException(status_code=400, detail="영상 트랜스크립트를 가져오지 못했습니다")
    summary = await openai_service.generate_summary(transcript, max_length=request.max_length)
    return YouTubeSummaryResponse(summary=summary, transcript_length=len(transcript))
