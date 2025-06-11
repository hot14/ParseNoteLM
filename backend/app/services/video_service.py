import asyncio
import subprocess
from pathlib import Path
import speech_recognition as sr
import tempfile

class VideoService:
    async def process_video(self, path: str):
        audio_path = await self._extract_audio(path)
        transcript = await self._transcribe_audio(audio_path)
        summary = self._summarize_text(transcript)
        Path(audio_path).unlink(missing_ok=True)
        return transcript, summary

    async def _extract_audio(self, path: str) -> str:
        out_fd, out_path = tempfile.mkstemp(suffix='.wav')
        cmd = [
            'ffmpeg', '-y', '-i', path,
            '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', out_path
        ]
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError('ffmpeg 변환 실패')
        return out_path

    async def _transcribe_audio(self, path: str) -> str:
        r = sr.Recognizer()
        with sr.AudioFile(path) as source:
            audio_data = r.record(source)
        try:
            text = r.recognize_google(audio_data, language='ko-KR')
        except Exception:
            text = ""
        return text

    def _summarize_text(self, text: str) -> str:
        sentences = text.split('.')
        summary = '.'.join(sentences[:3]).strip()
        return summary if summary else text[:200]

def get_video_service():
    return VideoService()
