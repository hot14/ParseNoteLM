from pydantic import BaseModel

class VideoSummaryResponse(BaseModel):
    transcript: str
    summary: str
