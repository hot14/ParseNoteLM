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
    """
    비디오에서 일정 간격마다 화면의 텍스트를 OCR로 추출합니다.
    
    Args:
        video_path: 처리할 비디오 파일 경로.
        interval: 텍스트 추출 간격(초)입니다.
    
    Returns:
        추출된 화면 텍스트 문자열의 리스트를 반환합니다.
    """
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
    """
    OpenAI GPT 모델을 사용하여 주어진 텍스트와 참고 자료를 한국어로 요약합니다.
    
    텍스트와 선택적으로 제공된 참고 자료를 결합하여, 지정된 최대 길이 이내로 핵심 내용을 요약합니다. OpenAI API 키가 환경 변수에 설정되어 있어야 하며, 설정되지 않은 경우 예외가 발생합니다.
    
    Args:
        text: 요약할 주요 텍스트(예: 영상 스크립트).
        supplement: 요약에 참고할 추가 자료(예: 슬라이드, 스크립트 등). 기본값은 빈 문자열입니다.
        max_length: 요약문의 최대 문자 수. 기본값은 200입니다.
    
    Returns:
        요약된 한국어 텍스트 문자열.
    """
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
    """
    요약, 스크립트, OCR 텍스트, 참고 자료, 캡처 이미지를 포함한 마크다운 파일을 생성합니다.
    
    summary, transcript, supplement, OCR로 추출된 텍스트, 캡처된 프레임 이미지를 지정된 경로의 마크다운 파일로 저장합니다.
    
    Args:
        summary: 비디오 및 보조 자료의 요약문.
        transcript: 음성 인식으로 추출된 전체 스크립트.
        ocr_texts: 비디오 프레임에서 OCR로 추출된 텍스트 목록.
        frames: 저장된 주요 캡처 이미지 파일 경로 목록.
        supplement: PDF 슬라이드 또는 스크립트 등 추가 참고 자료의 텍스트.
        path: 생성할 마크다운 파일의 경로.
    
    Returns:
        생성된 마크다운 파일의 경로.
    """
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
    """
    PDF 슬라이드 파일에서 모든 페이지의 텍스트를 추출하여 하나의 문자열로 반환합니다.
    
    Args:
        slides_path: 텍스트를 추출할 PDF 파일 경로.
    
    Returns:
        PDF의 모든 페이지에서 추출한 텍스트를 개행 문자로 연결한 문자열.
    """
    texts = []
    with pdfplumber.open(slides_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                texts.append(t)
    return "\n".join(texts)


def read_script(script_path: str) -> str:
    """
    텍스트 스크립트 파일의 전체 내용을 읽어 반환합니다.
    
    Args:
        script_path: 읽을 텍스트 파일의 경로.
    
    Returns:
        파일의 전체 텍스트 내용.
    """
    with open(script_path, "r", encoding="utf-8") as f:
        return f.read()


def capture_frames(video_path: str, output_dir: str = "downloads/frames", interval: int = 10) -> List[str]:
    """
    비디오 파일에서 지정된 간격(초)마다 프레임을 캡처하여 이미지 파일로 저장하고, 저장된 이미지 경로 목록을 반환합니다.
    
    Args:
        video_path: 프레임을 추출할 비디오 파일 경로.
        output_dir: 캡처된 프레임 이미지를 저장할 디렉터리 경로. 기본값은 "downloads/frames"입니다.
        interval: 프레임을 캡처할 시간 간격(초). 기본값은 10초입니다.
    
    Returns:
        저장된 프레임 이미지 파일의 경로 리스트.
    """
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
    """
    비디오 파일 또는 Google Drive 링크에서 오디오, 자막, OCR 텍스트, 보조 자료(슬라이드, 스크립트)를 추출하여 요약 마크다운 파일을 생성합니다.
    
    비디오 다운로드, 오디오 추출, 음성 인식, 화면 텍스트 추출, 프레임 캡처, 보조 자료 통합, 요약 생성, 마크다운 파일 저장까지 전체 파이프라인을 실행합니다.
    
    Args:
        source: 비디오 파일 경로 또는 Google Drive 링크.
        model_name: Whisper 음성 인식 모델 이름(기본값: 'base').
        slides: PDF 슬라이드 파일 경로(선택).
        script: 텍스트 스크립트 파일 경로(선택).
    
    Returns:
        생성된 마크다운 요약 파일의 경로.
    """
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
