import asyncio
from typing import Optional
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi

class YouTubeService:
    """간단한 YouTube 트랜스크립트 서비스"""

    @staticmethod
    async def get_transcript(video_url: str) -> Optional[str]:
        """영상 URL에서 트랜스크립트를 가져온다"""
        def _fetch(video_id: str):
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["ko", "en"])
                return " ".join([x['text'] for x in transcript])
            except Exception:
                return None
        video_id = YouTubeService.extract_video_id(video_url)
        if not video_id:
            return None
        return await asyncio.to_thread(_fetch, video_id)

    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        parsed = urlparse(url)
        if parsed.hostname in ['www.youtube.com', 'youtube.com']:
            qs = parse_qs(parsed.query)
            return qs.get('v', [None])[0]
        if parsed.hostname == 'youtu.be':
            return parsed.path.lstrip('/')
        return None
