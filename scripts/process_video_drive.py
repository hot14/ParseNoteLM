#!/usr/bin/env python3
"""Google Drive 동영상 처리 스크립트

사용법:
    python process_video_drive.py --drive-url <공유링크>
    python process_video_drive.py --local-file <로컬 경로>

기능:
    1. Google Drive에서 동영상을 다운로드하거나 로컬 파일 사용
    2. ffmpeg으로 오디오 추출
    3. Whisper 모델을 이용해 스크립트(자막) 추출
    4. 프레임을 추출하여 pytesseract로 화면 텍스트 추출
    5. (선택) lilys.ai API를 호출해 요약 생성 (예시는 목업)
    6. 결과를 마크다운 파일로 저장
"""

import argparse
import os
import subprocess
import tempfile
import time
from pathlib import Path

import gdown
from whisper import load_model
import pytesseract
from PIL import Image

# 성능 측정을 위한 간단한 데코레이터

def timing(fn):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = fn(*args, **kwargs)
        elapsed = time.time() - start
        print(f"⏱️ {fn.__name__} 완료 - {elapsed:.2f}s")
        return result
    return wrapper

@timing
def download_drive_file(url: str, output: str) -> str:
    """Google Drive 파일 다운로드"""
    gdown.download(url, output, quiet=False)
    return output

@timing
def extract_audio(video_path: str, audio_path: str) -> str:
    """ffmpeg을 이용해 오디오 추출"""
    cmd = [
        "ffmpeg",
        "-i",
        video_path,
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        audio_path,
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return audio_path

@timing
def transcribe_audio(audio_path: str) -> str:
    """Whisper 모델로 오디오 전사"""
    model = load_model("base")
    result = model.transcribe(audio_path, language="ko")
    return result.get("text", "")

@timing
def extract_frame_text(video_path: str, interval: int = 5) -> str:
    """프레임을 주기적으로 추출해 화면 텍스트 OCR"""
    temp_dir = tempfile.mkdtemp()
    frame_pattern = os.path.join(temp_dir, "frame_%04d.png")
    # 매 interval 초마다 프레임 저장
    cmd = [
        "ffmpeg",
        "-i",
        video_path,
        "-vf",
        f"fps=1/{interval}",
        frame_pattern,
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    texts = []
    for frame_file in sorted(Path(temp_dir).glob("frame_*.png")):
        text = pytesseract.image_to_string(Image.open(frame_file), lang="kor+eng")
        if text.strip():
            texts.append(text.strip())
    return "\n".join(texts)

@timing
def summarize_with_lilys(text: str) -> str:
    """lilys.ai API를 이용한 요약 (목업)"""
    # 실제 구현에서는 requests.post 등으로 API 호출
    # 여기서는 간단히 텍스트 앞부분을 반환
    return text[:200] + "..."

@timing
def save_markdown(transcript: str, screen_text: str, summary: str, output: str) -> str:
    """결과를 마크다운 파일로 저장"""
    md = f"""# 동영상 처리 결과

## 추출된 스크립트

```
{transcript}
```

## 화면 텍스트

```
{screen_text}
```

## 요약 (lilys.ai)

{summary}
"""
    with open(output, "w", encoding="utf-8") as f:
        f.write(md)
    return output

def main():
    parser = argparse.ArgumentParser(description="Google Drive 동영상 처리")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--drive-url", help="Google Drive 공유 링크")
    group.add_argument("--local-file", help="로컬 비디오 파일 경로")
    parser.add_argument("--output", default="video_summary.md", help="출력 MD 파일")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp_dir:
        if args.drive_url:
            video_path = Path(tmp_dir) / "video.mp4"
            download_drive_file(args.drive_url, str(video_path))
        else:
            video_path = Path(args.local_file)

        audio_path = Path(tmp_dir) / "audio.wav"
        extract_audio(str(video_path), str(audio_path))

        transcript = transcribe_audio(str(audio_path))
        screen_text = extract_frame_text(str(video_path))
        summary = summarize_with_lilys(transcript + "\n" + screen_text)
        save_markdown(transcript, screen_text, summary, args.output)

    print(f"✅ 결과 저장: {args.output}")

if __name__ == "__main__":
    main()
