import os
from typing import List

import gdown
from moviepy.editor import VideoFileClip
import whisper
import cv2
import pytesseract
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


def summarize_text(text: str, max_length: int = 200) -> str:
    """Summarize text with OpenAI GPT model."""
    openai.api_key = os.getenv('OPENAI_API_KEY')
    if not openai.api_key:
        raise RuntimeError('OPENAI_API_KEY not set')
    prompt = f"다음 내용을 {max_length}자 이내로 한국어로 요약해 주세요.\n{text}"
    resp = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content.strip()


def create_markdown(summary: str, transcript: str, ocr_texts: List[str], path: str) -> str:
    """Write summary, transcript, and extracted texts to markdown file."""
    with open(path, 'w', encoding='utf-8') as f:
        f.write('# Video Summary\n\n')
        f.write('## 요약\n')
        f.write(summary + '\n\n')
        f.write('## 스크립트\n')
        f.write(transcript + '\n\n')
        f.write('## 추출된 텍스트\n')
        for t in ocr_texts:
            f.write(f'- {t}\n')
    return path


def process_video(source: str, model_name: str = 'base') -> str:
    """Full pipeline from source to markdown summary."""
    video_path = download_video(source)
    audio_path = os.path.join('downloads', 'audio.wav')
    extract_audio(video_path, audio_path)
    transcript = transcribe_audio(audio_path, model_name)
    texts = extract_text_from_video(video_path)
    summary = summarize_text(transcript + '\n'.join(texts))
    md_path = os.path.join('downloads', 'summary.md')
    create_markdown(summary, transcript, texts, md_path)
    return md_path


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Process a video and generate summary markdown.')
    parser.add_argument('source', help='Local video path or Google Drive share link')
    parser.add_argument('--model', default='base', help='Whisper model size (tiny, base, small, medium, large)')
    args = parser.parse_args()
    md = process_video(args.source, args.model)
    print('Markdown saved to', md)
