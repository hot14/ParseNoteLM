"""
AI 요약 및 문서 생성 서비스 모듈
"""

import os
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import markdown
import json

logger = logging.getLogger(__name__)

class SummaryService:
    """AI 기반 요약 서비스"""
    
    def __init__(self, output_dir: str = None):
        """
        요약 서비스 초기화
        
        Args:
            output_dir: 출력 파일 저장 디렉토리
        """
        self.output_dir = output_dir or "/tmp/summaries"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def create_video_summary(self, video_data: Dict[str, Any], 
                           project_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        비디오 분석 결과를 기반으로 요약 생성
        
        Args:
            video_data: 비디오 텍스트 추출 결과
            project_info: 프로젝트 정보
            
        Returns:
            요약 결과 딕셔너리
        """
        try:
            logger.info("비디오 요약 생성 시작")
            
            # 고유 ID 생성
            summary_id = str(uuid.uuid4())
            timestamp = datetime.now()
            
            # 기본 정보 설정
            summary_data = {
                "id": summary_id,
                "created_at": timestamp.isoformat(),
                "video_path": video_data.get("video_path", ""),
                "project_info": project_info or {},
                "content": {
                    "speech_text": "",
                    "screen_text": "",
                    "combined_text": "",
                    "summary": "",
                    "key_points": [],
                    "timestamps": []
                },
                "metadata": {
                    "total_duration": 0,
                    "speech_segments": 0,
                    "screen_text_frames": 0,
                    "processing_time": 0
                }
            }
            
            # 텍스트 내용 추출
            if video_data.get("speech_transcription"):
                speech_data = video_data["speech_transcription"]
                summary_data["content"]["speech_text"] = speech_data.get("text", "")
                summary_data["metadata"]["speech_segments"] = len(speech_data.get("segments", []))
                
                # 타임스탬프 정보 추가
                for segment in speech_data.get("segments", []):
                    summary_data["content"]["timestamps"].append({
                        "start": segment.get("start", 0),
                        "end": segment.get("end", 0),
                        "text": segment.get("text", "")
                    })
            
            if video_data.get("screen_text_extraction"):
                screen_data = video_data["screen_text_extraction"]
                summary_data["content"]["screen_text"] = screen_data.get("combined_text", "")
                summary_data["metadata"]["screen_text_frames"] = screen_data.get("frames_with_text", 0)
            
            # 전체 텍스트 결합
            combined_content = video_data.get("combined_content", {})
            summary_data["content"]["combined_text"] = combined_content.get("total_content", "")
            
            # AI 요약 생성 (현재는 간단한 요약 로직 사용)
            summary_data["content"]["summary"] = self._generate_simple_summary(
                summary_data["content"]["combined_text"]
            )
            
            # 핵심 포인트 추출
            summary_data["content"]["key_points"] = self._extract_key_points(
                summary_data["content"]["combined_text"]
            )
            
            logger.info(f"비디오 요약 생성 완료: {summary_id}")
            return summary_data
            
        except Exception as error:
            logger.error(f"비디오 요약 생성 실패: {error}")
            return None
    
    def _generate_simple_summary(self, text: str) -> str:
        """
        간단한 요약 생성 (실제 환경에서는 AI 모델 사용)
        
        Args:
            text: 요약할 텍스트
            
        Returns:
            요약된 텍스트
        """
        if not text or len(text.strip()) < 50:
            return "내용이 충분하지 않아 요약을 생성할 수 없습니다."
        
        # 간단한 요약 로직 (실제로는 OpenAI API 등 사용)
        sentences = text.split('.')
        if len(sentences) <= 3:
            return text.strip()
        
        # 첫 번째와 마지막 문장, 그리고 중간 문장 하나 선택
        summary_sentences = [
            sentences[0].strip(),
            sentences[len(sentences)//2].strip() if len(sentences) > 2 else "",
            sentences[-2].strip() if len(sentences) > 1 else ""
        ]
        
        summary = '. '.join([s for s in summary_sentences if s])
        return summary + "." if summary and not summary.endswith('.') else summary
    
    def _extract_key_points(self, text: str) -> List[str]:
        """
        핵심 포인트 추출
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            핵심 포인트 리스트
        """
        if not text:
            return []
        
        # 간단한 키워드 추출 로직
        key_points = []
        
        # 문장 단위로 분할
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        # 길이가 적당한 문장들을 핵심 포인트로 선택
        for sentence in sentences[:5]:  # 최대 5개
            if 10 <= len(sentence) <= 100:
                key_points.append(sentence)
        
        return key_points


class MarkdownGenerator:
    """마크다운 문서 생성기"""
    
    def __init__(self, output_dir: str = None):
        """
        마크다운 생성기 초기화
        
        Args:
            output_dir: 출력 파일 저장 디렉토리
        """
        self.output_dir = output_dir or "/tmp/markdown"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_video_summary_markdown(self, summary_data: Dict[str, Any]) -> str:
        """
        비디오 요약 마크다운 문서 생성
        
        Args:
            summary_data: 요약 데이터
            
        Returns:
            생성된 마크다운 파일 경로
        """
        try:
            # 파일명 생성
            summary_id = summary_data.get("id", "unknown")
            filename = f"video_summary_{summary_id}.md"
            file_path = os.path.join(self.output_dir, filename)
            
            # 마크다운 내용 생성
            markdown_content = self._create_markdown_content(summary_data)
            
            # 파일 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            logger.info(f"마크다운 파일 생성 완료: {file_path}")
            return file_path
            
        except Exception as error:
            logger.error(f"마크다운 파일 생성 실패: {error}")
            return None
    
    def _create_markdown_content(self, summary_data: Dict[str, Any]) -> str:
        """마크다운 내용 생성"""
        content = summary_data.get("content", {})
        metadata = summary_data.get("metadata", {})
        project_info = summary_data.get("project_info", {})
        
        # 제목 및 기본 정보
        markdown = f"""# 영상 요약 보고서

## 기본 정보
- **생성일시**: {summary_data.get('created_at', 'Unknown')}
- **요약 ID**: {summary_data.get('id', 'Unknown')}
- **프로젝트**: {project_info.get('name', 'Unknown')}

## 영상 정보
- **파일 경로**: {summary_data.get('video_path', 'Unknown')}
- **음성 세그먼트 수**: {metadata.get('speech_segments', 0)}개
- **텍스트 포함 프레임 수**: {metadata.get('screen_text_frames', 0)}개

## 📝 요약

{content.get('summary', '요약 내용이 없습니다.')}

## 🔑 핵심 포인트

"""
        
        # 핵심 포인트 추가
        key_points = content.get('key_points', [])
        if key_points:
            for i, point in enumerate(key_points, 1):
                markdown += f"{i}. {point}\n"
        else:
            markdown += "핵심 포인트가 추출되지 않았습니다.\n"
        
        # 음성 내용 추가
        if content.get('speech_text'):
            markdown += f"""
## 🎤 음성 내용

{content['speech_text']}
"""
        
        # 화면 텍스트 추가
        if content.get('screen_text'):
            markdown += f"""
## 📺 화면 텍스트

{content['screen_text']}
"""
        
        # 타임스탬프 정보 추가
        timestamps = content.get('timestamps', [])
        if timestamps:
            markdown += "\n## ⏰ 타임스탬프\n\n"
            for ts in timestamps[:10]:  # 최대 10개만 표시
                start_time = self._format_timestamp(ts.get('start', 0))
                end_time = self._format_timestamp(ts.get('end', 0))
                text = ts.get('text', '').strip()
                if text:
                    markdown += f"- **{start_time} - {end_time}**: {text}\n"
        
        # 푸터 추가
        markdown += f"""
---
*이 보고서는 Lilys.ai 클론 시스템에 의해 자동 생성되었습니다.*  
*생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return markdown
    
    def _format_timestamp(self, seconds: float) -> str:
        """초를 MM:SS 형식으로 변환"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"


class DocumentSharingService:
    """문서 공유 서비스"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        문서 공유 서비스 초기화
        
        Args:
            base_url: 서비스 기본 URL
        """
        self.base_url = base_url.rstrip('/')
    
    def create_shareable_link(self, file_path: str, summary_id: str) -> str:
        """
        공유 가능한 링크 생성
        
        Args:
            file_path: 파일 경로
            summary_id: 요약 ID
            
        Returns:
            공유 링크
        """
        # 실제 환경에서는 파일을 웹 서버에서 접근 가능한 위치로 이동
        filename = os.path.basename(file_path)
        share_link = f"{self.base_url}/share/summary/{summary_id}"
        
        logger.info(f"공유 링크 생성: {share_link}")
        return share_link
    
    def save_summary_metadata(self, summary_data: Dict[str, Any], 
                            file_path: str) -> bool:
        """
        요약 메타데이터 저장
        
        Args:
            summary_data: 요약 데이터
            file_path: 마크다운 파일 경로
            
        Returns:
            저장 성공 여부
        """
        try:
            metadata_path = file_path.replace('.md', '_metadata.json')
            
            metadata = {
                "summary_id": summary_data.get("id"),
                "created_at": summary_data.get("created_at"),
                "file_path": file_path,
                "project_info": summary_data.get("project_info", {}),
                "metadata": summary_data.get("metadata", {})
            }
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"메타데이터 저장 완료: {metadata_path}")
            return True
            
        except Exception as error:
            logger.error(f"메타데이터 저장 실패: {error}")
            return False


def create_summary_service(output_dir: str = None) -> SummaryService:
    """요약 서비스 인스턴스 생성"""
    return SummaryService(output_dir)


def create_markdown_generator(output_dir: str = None) -> MarkdownGenerator:
    """마크다운 생성기 인스턴스 생성"""
    return MarkdownGenerator(output_dir)


def create_document_sharing_service(base_url: str = None) -> DocumentSharingService:
    """문서 공유 서비스 인스턴스 생성"""
    return DocumentSharingService(base_url)

