from pydantic import BaseModel, Field

class YouTubeSummaryRequest(BaseModel):
    url: str = Field(..., description="YouTube 영상 URL")
    max_length: int = Field(default=200, description="요약 최대 길이", ge=50, le=500)

class YouTubeSummaryResponse(BaseModel):
    summary: str = Field(..., description="생성된 요약")
    transcript_length: int = Field(..., description="트랜스크립트 길이")
