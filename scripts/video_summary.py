import os
from typing import List, Optional

import gdown
from moviepy.editor import VideoFileClip
import whisper
import cv2
import pytesseract
import pdfplumber
import openai


def download_video(gdrive_url: str, output_dir: str = "downloads") -> str:
    """Download a video from Google Drive link and return local path."""
    os.makedirs(output_dir, exist_ok=True)
    if 'drive.google.com' in gdrive_url:
        try:
            file_id = gdrive_url.split('/d/')[1].split('/')[0]
        except IndexError:
            raise ValueError('Invalid Google Drive URL')
        output_path = os.path.join(output_dir, f"{file_id}.mp4")
        gdown.download(id=file_id, output=output_path, quiet=False)
        return output_path
    if os.path.exists(gdrive_url):
        return gdrive_url
    raise FileNotFoundError('Provided path does not exist')


def extract_audio(video_path: str, output_path: str) -> str:
    """Extract audio track from video using moviepy."""
    clip = VideoFileClip(video_path)
    clip.audio.write_audiofile(output_path, logger=None)
    return output_path


def transcribe_audio(audio_path: str, model_name: str = "base") -> str:
    """Transcribe audio using whisper."""
    model = whisper.load_model(model_name)
    result = model.transcribe(audio_path)
    return result.get("text", "")


def extract_text_from_video(video_path: str, interval: int = 1) -> List[str]:
    """Extract on-screen text every `interval` seconds using OCR."""
    texts = []
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame = 0
    while True:
        ret, img = cap.read()
        if not ret:
            break
        if int(frame % (fps * interval)) == 0:
            text = pytesseract.image_to_string(img).strip()
            if text:
                texts.append(text)
        frame += 1
    cap.release()
    return texts


def summarize_text(text: str, supplement: str = "", max_length: int = 200) -> str:
    """Summarize text with OpenAI GPT model, using supplemental material."""
    openai.api_key = os.getenv('OPENAI_API_KEY')
    if not openai.api_key:
        raise RuntimeError('OPENAI_API_KEY not set')
    prompt = (
        f"다음 영상 스크립트와 참고 자료를 바탕으로 핵심 내용을 {max_length}자 이내로 한국어로 요약해 주세요.\n"
        f"[스크립트]\n{text}\n"
        f"[참고 자료]\n{supplement}"
    )
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content.strip()


def create_markdown(summary: str, transcript: str, ocr_texts: List[str], frames: List[str], supplement: str, path: str) -> str:
    """Write summary, transcript and optional materials to markdown file."""
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Video Summary\n\n")
        f.write("## 요약\n")
        f.write(summary + "\n\n")

        if supplement:
            f.write("## 참고 자료\n")
            f.write(supplement + "\n\n")

        f.write("## 스크립트\n")
        f.write(transcript + "\n\n")

        if ocr_texts:
            f.write("## 추출된 텍스트 (OCR)\n")
            for t in ocr_texts:
                f.write(f"- {t}\n")
            f.write("\n")

        if frames:
            f.write("## 주요 캡처 이미지\n")
            for img_path in frames:
                f.write(f"![frame]({img_path})\n")
            f.write("\n")
    return path


def read_slides(slides_path: str) -> str:
    """Extract text from pdf slides."""
    texts = []
    with pdfplumber.open(slides_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                texts.append(t)
    return "\n".join(texts)


def read_script(script_path: str) -> str:
    with open(script_path, "r", encoding="utf-8") as f:
        return f.read()


def capture_frames(video_path: str, output_dir: str = "downloads/frames", interval: int = 10) -> List[str]:
    """Capture frames every `interval` seconds and return image paths."""
    os.makedirs(output_dir, exist_ok=True)
    frames = []
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame = 0
    idx = 0
    while True:
        ret, img = cap.read()
        if not ret:
            break
        if int(frame % (fps * interval)) == 0:
            img_path = os.path.join(output_dir, f"frame_{idx:03d}.png")
            cv2.imwrite(img_path, img)
            frames.append(img_path)
            idx += 1
        frame += 1
    cap.release()
    return frames


def process_video(source: str, model_name: str = 'base', slides: Optional[str] = None, script: Optional[str] = None) -> str:
    """Full pipeline from source to markdown summary."""
    video_path = download_video(source)
    audio_path = os.path.join('downloads', 'audio.wav')
    extract_audio(video_path, audio_path)
    transcript = transcribe_audio(audio_path, model_name)
    ocr_texts = extract_text_from_video(video_path)
    frames = capture_frames(video_path)

    supplement_text = ""
    if slides:
        supplement_text += read_slides(slides)
    if script:
        supplement_text += "\n" + read_script(script)

    summary = summarize_text(transcript + "\n".join(ocr_texts), supplement_text)
    md_path = os.path.join('downloads', 'summary.md')
    create_markdown(summary, transcript, ocr_texts, frames, supplement_text, md_path)
    return md_path


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Process a video and generate summary markdown.')
    parser.add_argument('source', help='Local video path or Google Drive share link')
    parser.add_argument('--model', default='base', help='Whisper model size (tiny, base, small, medium, large)')
    parser.add_argument('--slides', help='PDF slides to supplement the video', default=None)
    parser.add_argument('--script', help='Text script file for the video', default=None)
    args = parser.parse_args()
    md = process_video(args.source, args.model, slides=args.slides, script=args.script)
    print('Markdown saved to', md)
