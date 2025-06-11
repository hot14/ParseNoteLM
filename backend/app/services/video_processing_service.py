"""
영상 처리 서비스 모듈
"""

import os
import logging
import subprocess
from typing import Optional, Dict, Any, List
from pathlib import Path
import tempfile
import json

logger = logging.getLogger(__name__)

class VideoProcessingService:
    """영상 처리 서비스 클래스"""
    
    def __init__(self, temp_dir: str = None):
        """
        영상 처리 서비스 초기화
        
        Args:
            temp_dir: 임시 파일 저장 디렉토리
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.ensure_dependencies()
    
    def ensure_dependencies(self):
        """필요한 의존성 확인 및 설치"""
        try:
            # yt-dlp 설치 확인
            subprocess.run(['yt-dlp', '--version'], 
                         capture_output=True, check=True)
            logger.info("yt-dlp 사용 가능")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.info("yt-dlp 설치 중...")
            subprocess.run(['pip', 'install', 'yt-dlp'], check=True)
        
        try:
            # ffmpeg 설치 확인
            subprocess.run(['ffmpeg', '-version'], 
                         capture_output=True, check=True)
            logger.info("ffmpeg 사용 가능")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("ffmpeg가 설치되지 않았습니다. 일부 기능이 제한될 수 있습니다.")
    
    def extract_audio_from_video(self, video_path: str, audio_path: str) -> bool:
        """
        비디오에서 오디오 추출
        
        Args:
            video_path: 비디오 파일 경로
            audio_path: 오디오 저장 경로
            
        Returns:
            추출 성공 여부
        """
        try:
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vn', '-acodec', 'libmp3lame',
                '-ab', '192k', '-ar', '44100',
                '-y', audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"오디오 추출 완료: {audio_path}")
                return True
            else:
                logger.error(f"오디오 추출 실패: {result.stderr}")
                return False
                
        except Exception as error:
            logger.error(f"오디오 추출 중 오류: {error}")
            return False
    
    def extract_video_metadata(self, video_path: str) -> Optional[Dict[str, Any]]:
        """
        비디오 메타데이터 추출
        
        Args:
            video_path: 비디오 파일 경로
            
        Returns:
            메타데이터 딕셔너리 또는 None
        """
        try:
            cmd = [
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_format', '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                metadata = json.loads(result.stdout)
                logger.info(f"메타데이터 추출 완료: {video_path}")
                return metadata
            else:
                logger.error(f"메타데이터 추출 실패: {result.stderr}")
                return None
                
        except Exception as error:
            logger.error(f"메타데이터 추출 중 오류: {error}")
            return None
    
    def extract_frames(self, video_path: str, output_dir: str, 
                      interval: int = 30) -> List[str]:
        """
        비디오에서 프레임 추출
        
        Args:
            video_path: 비디오 파일 경로
            output_dir: 프레임 저장 디렉토리
            interval: 프레임 추출 간격 (초)
            
        Returns:
            추출된 프레임 파일 경로 리스트
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vf', f'fps=1/{interval}',
                '-y', f'{output_dir}/frame_%04d.jpg'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # 생성된 프레임 파일 목록 반환
                frame_files = sorted([
                    os.path.join(output_dir, f) 
                    for f in os.listdir(output_dir) 
                    if f.startswith('frame_') and f.endswith('.jpg')
                ])
                logger.info(f"프레임 추출 완료: {len(frame_files)}개 프레임")
                return frame_files
            else:
                logger.error(f"프레임 추출 실패: {result.stderr}")
                return []
                
        except Exception as error:
            logger.error(f"프레임 추출 중 오류: {error}")
            return []
    
    def get_video_duration(self, video_path: str) -> Optional[float]:
        """
        비디오 길이 조회
        
        Args:
            video_path: 비디오 파일 경로
            
        Returns:
            비디오 길이 (초) 또는 None
        """
        try:
            cmd = [
                'ffprobe', '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'csv=p=0',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                logger.info(f"비디오 길이: {duration}초")
                return duration
            else:
                logger.error(f"비디오 길이 조회 실패: {result.stderr}")
                return None
                
        except Exception as error:
            logger.error(f"비디오 길이 조회 중 오류: {error}")
            return None
    
    def convert_video_format(self, input_path: str, output_path: str, 
                           format: str = 'mp4') -> bool:
        """
        비디오 포맷 변환
        
        Args:
            input_path: 입력 비디오 파일 경로
            output_path: 출력 비디오 파일 경로
            format: 출력 포맷
            
        Returns:
            변환 성공 여부
        """
        try:
            cmd = [
                'ffmpeg', '-i', input_path,
                '-c:v', 'libx264', '-c:a', 'aac',
                '-y', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"비디오 변환 완료: {output_path}")
                return True
            else:
                logger.error(f"비디오 변환 실패: {result.stderr}")
                return False
                
        except Exception as error:
            logger.error(f"비디오 변환 중 오류: {error}")
            return False
    
    def cleanup_temp_files(self, file_paths: List[str]):
        """
        임시 파일 정리
        
        Args:
            file_paths: 삭제할 파일 경로 리스트
        """
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"임시 파일 삭제: {file_path}")
            except Exception as error:
                logger.warning(f"임시 파일 삭제 실패: {file_path}, {error}")


def create_video_processing_service() -> VideoProcessingService:
    """
    비디오 처리 서비스 인스턴스 생성
    
    Returns:
        VideoProcessingService 인스턴스
    """
    return VideoProcessingService()

