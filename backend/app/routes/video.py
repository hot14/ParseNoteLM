"""
비디오 처리 통합 API 엔드포인트
"""

import os
import logging
import tempfile
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.google_drive import create_google_drive_service
from app.services.video_processing import create_video_processing_service
from app.services.text_extraction import create_video_text_extraction_service
from app.services.summary import (
    create_summary_service, 
    create_markdown_generator, 
    create_document_sharing_service
)

router = APIRouter()
logger = logging.getLogger(__name__)

class VideoProcessRequest(BaseModel):
    """비디오 처리 요청 모델"""
    google_drive_url: Optional[str] = None
    project_name: str
    description: Optional[str] = None

class VideoProcessResponse(BaseModel):
    """비디오 처리 응답 모델"""
    success: bool
    message: str
    summary_id: Optional[str] = None
    share_link: Optional[str] = None
    markdown_path: Optional[str] = None

@router.post("/process-video", response_model=VideoProcessResponse)
async def process_video(
    request: VideoProcessRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    비디오 처리 및 요약 생성
    
    Args:
        request: 비디오 처리 요청
        current_user: 현재 사용자
        db: 데이터베이스 세션
        
    Returns:
        처리 결과
    """
    try:
        logger.info(f"비디오 처리 시작: 사용자 {current_user.id}")
        
        if not request.google_drive_url:
            raise HTTPException(
                status_code=400, 
                detail="Google Drive URL이 필요합니다."
            )
        
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            # Google Drive 서비스 초기화
            drive_service = create_google_drive_service()
            if not drive_service:
                raise HTTPException(
                    status_code=500,
                    detail="Google Drive 서비스 초기화 실패"
                )
            
            # 파일 ID 추출
            file_id = drive_service.extract_file_id_from_url(request.google_drive_url)
            if not file_id:
                raise HTTPException(
                    status_code=400,
                    detail="유효하지 않은 Google Drive URL입니다."
                )
            
            # 파일 정보 조회
            file_info = drive_service.get_file_info(file_id)
            if not file_info:
                raise HTTPException(
                    status_code=404,
                    detail="파일을 찾을 수 없습니다."
                )
            
            # 비디오 파일인지 확인
            if not drive_service.is_video_file(file_info):
                raise HTTPException(
                    status_code=400,
                    detail="비디오 파일이 아닙니다."
                )
            
            # 파일 다운로드
            video_filename = file_info.get('name', f'video_{file_id}.mp4')
            video_path = os.path.join(temp_dir, video_filename)
            
            if not drive_service.download_file(file_id, video_path):
                raise HTTPException(
                    status_code=500,
                    detail="파일 다운로드에 실패했습니다."
                )
            
            # 비디오 처리 서비스 초기화
            video_service = create_video_processing_service()
            
            # 오디오 추출
            audio_path = os.path.join(temp_dir, 'audio.mp3')
            if not video_service.extract_audio_from_video(video_path, audio_path):
                raise HTTPException(
                    status_code=500,
                    detail="오디오 추출에 실패했습니다."
                )
            
            # 프레임 추출
            frames_dir = os.path.join(temp_dir, 'frames')
            frame_paths = video_service.extract_frames(video_path, frames_dir, interval=30)
            
            # 텍스트 추출 서비스 초기화
            text_extraction_service = create_video_text_extraction_service()
            
            # 음성 및 화면 텍스트 추출
            extraction_result = text_extraction_service.extract_all_text_from_video(
                video_path, audio_path, frame_paths
            )
            
            # 요약 생성
            summary_service = create_summary_service()
            project_info = {
                "name": request.project_name,
                "description": request.description,
                "user_id": current_user.id,
                "original_filename": video_filename
            }
            
            summary_data = summary_service.create_video_summary(
                extraction_result, project_info
            )
            
            if not summary_data:
                raise HTTPException(
                    status_code=500,
                    detail="요약 생성에 실패했습니다."
                )
            
            # 마크다운 문서 생성
            markdown_generator = create_markdown_generator()
            markdown_path = markdown_generator.generate_video_summary_markdown(summary_data)
            
            if not markdown_path:
                raise HTTPException(
                    status_code=500,
                    detail="마크다운 문서 생성에 실패했습니다."
                )
            
            # 공유 링크 생성
            sharing_service = create_document_sharing_service()
            share_link = sharing_service.create_shareable_link(
                markdown_path, summary_data["id"]
            )
            
            # 메타데이터 저장
            sharing_service.save_summary_metadata(summary_data, markdown_path)
            
            logger.info(f"비디오 처리 완료: {summary_data['id']}")
            
            return VideoProcessResponse(
                success=True,
                message="비디오 처리가 완료되었습니다.",
                summary_id=summary_data["id"],
                share_link=share_link,
                markdown_path=markdown_path
            )
    
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"비디오 처리 중 오류: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"비디오 처리 중 오류가 발생했습니다: {str(error)}"
        )

@router.post("/upload-video", response_model=VideoProcessResponse)
async def upload_and_process_video(
    file: UploadFile = File(...),
    project_name: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    비디오 파일 업로드 및 처리
    
    Args:
        file: 업로드된 비디오 파일
        project_name: 프로젝트 이름
        description: 프로젝트 설명
        current_user: 현재 사용자
        db: 데이터베이스 세션
        
    Returns:
        처리 결과
    """
    try:
        logger.info(f"비디오 업로드 처리 시작: 사용자 {current_user.id}")
        
        # 파일 형식 확인
        if not file.content_type.startswith('video/'):
            raise HTTPException(
                status_code=400,
                detail="비디오 파일만 업로드 가능합니다."
            )
        
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            # 업로드된 파일 저장
            video_path = os.path.join(temp_dir, file.filename)
            with open(video_path, 'wb') as f:
                content = await file.read()
                f.write(content)
            
            # 비디오 처리 서비스 초기화
            video_service = create_video_processing_service()
            
            # 오디오 추출
            audio_path = os.path.join(temp_dir, 'audio.mp3')
            if not video_service.extract_audio_from_video(video_path, audio_path):
                raise HTTPException(
                    status_code=500,
                    detail="오디오 추출에 실패했습니다."
                )
            
            # 프레임 추출
            frames_dir = os.path.join(temp_dir, 'frames')
            frame_paths = video_service.extract_frames(video_path, frames_dir, interval=30)
            
            # 텍스트 추출 서비스 초기화
            text_extraction_service = create_video_text_extraction_service()
            
            # 음성 및 화면 텍스트 추출
            extraction_result = text_extraction_service.extract_all_text_from_video(
                video_path, audio_path, frame_paths
            )
            
            # 요약 생성
            summary_service = create_summary_service()
            project_info = {
                "name": project_name,
                "description": description,
                "user_id": current_user.id,
                "original_filename": file.filename
            }
            
            summary_data = summary_service.create_video_summary(
                extraction_result, project_info
            )
            
            if not summary_data:
                raise HTTPException(
                    status_code=500,
                    detail="요약 생성에 실패했습니다."
                )
            
            # 마크다운 문서 생성
            markdown_generator = create_markdown_generator()
            markdown_path = markdown_generator.generate_video_summary_markdown(summary_data)
            
            if not markdown_path:
                raise HTTPException(
                    status_code=500,
                    detail="마크다운 문서 생성에 실패했습니다."
                )
            
            # 공유 링크 생성
            sharing_service = create_document_sharing_service()
            share_link = sharing_service.create_shareable_link(
                markdown_path, summary_data["id"]
            )
            
            # 메타데이터 저장
            sharing_service.save_summary_metadata(summary_data, markdown_path)
            
            logger.info(f"비디오 업로드 처리 완료: {summary_data['id']}")
            
            return VideoProcessResponse(
                success=True,
                message="비디오 업로드 및 처리가 완료되었습니다.",
                summary_id=summary_data["id"],
                share_link=share_link,
                markdown_path=markdown_path
            )
    
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"비디오 업로드 처리 중 오류: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"비디오 업로드 처리 중 오류가 발생했습니다: {str(error)}"
        )

