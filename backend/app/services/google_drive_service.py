"""
Google Drive API 연동 모듈
"""

import os
import io
import logging
from typing import Optional, List, Dict, Any
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Google Drive API 스코프
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

class GoogleDriveService:
    """Google Drive API 서비스 클래스"""
    
    def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.json"):
        """
        Google Drive 서비스 초기화
        
        Args:
            credentials_path: OAuth2 credentials JSON 파일 경로
            token_path: 토큰 저장 파일 경로
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Google Drive API 인증"""
        creds = None
        
        # 기존 토큰 파일이 있으면 로드
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        
        # 유효한 자격 증명이 없으면 새로 인증
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    logger.error(f"Credentials file not found: {self.credentials_path}")
                    raise FileNotFoundError(f"Credentials file not found: {self.credentials_path}")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # 토큰 저장
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        # Drive API 서비스 빌드
        self.service = build('drive', 'v3', credentials=creds)
        logger.info("Google Drive API 인증 완료")
    
    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        파일 정보 조회
        
        Args:
            file_id: Google Drive 파일 ID
            
        Returns:
            파일 정보 딕셔너리 또는 None
        """
        try:
            file_info = self.service.files().get(fileId=file_id).execute()
            logger.info(f"파일 정보 조회 성공: {file_info.get('name')}")
            return file_info
        except HttpError as error:
            logger.error(f"파일 정보 조회 실패: {error}")
            return None
    
    def download_file(self, file_id: str, local_path: str) -> bool:
        """
        파일 다운로드
        
        Args:
            file_id: Google Drive 파일 ID
            local_path: 로컬 저장 경로
            
        Returns:
            다운로드 성공 여부
        """
        try:
            # 파일 정보 조회
            file_info = self.get_file_info(file_id)
            if not file_info:
                return False
            
            # 파일 다운로드
            request = self.service.files().get_media(fileId=file_id)
            file_io = io.BytesIO()
            downloader = MediaIoBaseDownload(file_io, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                logger.debug(f"다운로드 진행률: {int(status.progress() * 100)}%")
            
            # 로컬 파일로 저장
            with open(local_path, 'wb') as f:
                f.write(file_io.getvalue())
            
            logger.info(f"파일 다운로드 완료: {file_info.get('name')} -> {local_path}")
            return True
            
        except HttpError as error:
            logger.error(f"파일 다운로드 실패: {error}")
            return False
        except Exception as error:
            logger.error(f"파일 다운로드 중 오류: {error}")
            return False
    
    def extract_file_id_from_url(self, url: str) -> Optional[str]:
        """
        Google Drive URL에서 파일 ID 추출
        
        Args:
            url: Google Drive 공유 URL
            
        Returns:
            파일 ID 또는 None
        """
        try:
            # 다양한 Google Drive URL 형식 지원
            if '/file/d/' in url:
                # https://drive.google.com/file/d/FILE_ID/view?usp=sharing
                file_id = url.split('/file/d/')[1].split('/')[0]
            elif 'id=' in url:
                # https://drive.google.com/open?id=FILE_ID
                file_id = url.split('id=')[1].split('&')[0]
            else:
                logger.error(f"지원하지 않는 URL 형식: {url}")
                return None
            
            logger.info(f"파일 ID 추출 성공: {file_id}")
            return file_id
            
        except Exception as error:
            logger.error(f"파일 ID 추출 실패: {error}")
            return None
    
    def is_video_file(self, file_info: Dict[str, Any]) -> bool:
        """
        비디오 파일 여부 확인
        
        Args:
            file_info: 파일 정보 딕셔너리
            
        Returns:
            비디오 파일 여부
        """
        mime_type = file_info.get('mimeType', '')
        return mime_type.startswith('video/')
    
    def get_shareable_link(self, file_id: str) -> Optional[str]:
        """
        파일의 공유 가능한 링크 생성
        
        Args:
            file_id: Google Drive 파일 ID
            
        Returns:
            공유 링크 또는 None
        """
        try:
            # 파일을 공개적으로 읽기 가능하게 설정
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            self.service.permissions().create(
                fileId=file_id,
                body=permission
            ).execute()
            
            # 공유 링크 반환
            link = f"https://drive.google.com/file/d/{file_id}/view"
            logger.info(f"공유 링크 생성 완료: {link}")
            return link
            
        except HttpError as error:
            logger.error(f"공유 링크 생성 실패: {error}")
            return None


def create_google_drive_service() -> Optional[GoogleDriveService]:
    """
    Google Drive 서비스 인스턴스 생성
    
    Returns:
        GoogleDriveService 인스턴스 또는 None
    """
    try:
        return GoogleDriveService()
    except Exception as error:
        logger.error(f"Google Drive 서비스 생성 실패: {error}")
        return None

