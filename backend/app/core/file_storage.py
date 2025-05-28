"""
파일 저장 및 관리 시스템
"""
import os
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException
from app.core.config import settings
from app.core.file_validation import FileValidator


class FileStorageManager:
    """파일 저장 관리 클래스"""
    
    def __init__(self):
        self.base_upload_dir = Path(settings.UPLOAD_DIR)
        self.ensure_upload_directories()
    
    def ensure_upload_directories(self):
        """업로드 디렉토리 구조 생성"""
        # 기본 업로드 디렉토리
        self.base_upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 사용자별 디렉토리 구조: uploads/users/{user_id}/projects/{project_id}/
        # 임시 파일 디렉토리
        (self.base_upload_dir / "temp").mkdir(exist_ok=True)
        
        # 사용자 디렉토리
        (self.base_upload_dir / "users").mkdir(exist_ok=True)
    
    def get_user_project_dir(self, user_id: int, project_id: int) -> Path:
        """사용자 프로젝트 디렉토리 경로 반환"""
        return self.base_upload_dir / "users" / str(user_id) / "projects" / str(project_id)
    
    def get_document_file_path(self, user_id: int, project_id: int, document_id: int, filename: str) -> Path:
        """문서 파일 전체 경로 반환"""
        project_dir = self.get_user_project_dir(user_id, project_id)
        # 파일명에 document_id 추가하여 고유성 보장
        safe_filename = FileValidator.sanitize_filename(filename)
        name, ext = os.path.splitext(safe_filename)
        unique_filename = f"{document_id}_{name}{ext}"
        return project_dir / unique_filename
    
    def save_uploaded_file(
        self, 
        file: UploadFile, 
        user_id: int, 
        project_id: int, 
        document_id: int
    ) -> Tuple[str, str, int]:
        """
        업로드된 파일을 저장
        
        Args:
            file: 업로드 파일
            user_id: 사용자 ID
            project_id: 프로젝트 ID
            document_id: 문서 ID
            
        Returns:
            Tuple[str, str, int]: (저장된 파일 경로, 원본 파일명, 파일 크기)
        """
        try:
            # 프로젝트 디렉토리 생성
            project_dir = self.get_user_project_dir(user_id, project_id)
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # 파일 경로 생성
            file_path = self.get_document_file_path(user_id, project_id, document_id, file.filename or "unknown")
            
            # 파일 저장
            file_size = 0
            with open(file_path, "wb") as buffer:
                # 파일을 청크 단위로 읽어서 저장
                file.file.seek(0)  # 파일 포인터를 처음으로 이동
                while chunk := file.file.read(8192):  # 8KB 청크
                    buffer.write(chunk)
                    file_size += len(chunk)
            
            return str(file_path), file.filename or "unknown", file_size
            
        except Exception as e:
            # 저장 실패 시 부분적으로 생성된 파일 삭제
            if 'file_path' in locals() and file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=500,
                detail=f"파일 저장 실패: {str(e)}"
            )
    
    def delete_document_file(self, user_id: int, project_id: int, document_id: int, filename: str) -> bool:
        """문서 파일 삭제"""
        try:
            file_path = self.get_document_file_path(user_id, project_id, document_id, filename)
            
            if file_path.exists():
                file_path.unlink()
                return True
            return False
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"파일 삭제 실패: {str(e)}"
            )
    
    def move_temp_file_to_permanent(
        self, 
        temp_file_path: str, 
        user_id: int, 
        project_id: int, 
        document_id: int,
        filename: str
    ) -> str:
        """임시 파일을 영구 저장소로 이동"""
        try:
            temp_path = Path(temp_file_path)
            if not temp_path.exists():
                raise FileNotFoundError("임시 파일을 찾을 수 없습니다.")
            
            # 최종 저장 경로
            final_path = self.get_document_file_path(user_id, project_id, document_id, filename)
            final_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 파일 이동
            shutil.move(str(temp_path), str(final_path))
            
            return str(final_path)
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"파일 이동 실패: {str(e)}"
            )
    
    def get_file_info(self, file_path: str) -> dict:
        """파일 정보 반환"""
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError("파일을 찾을 수 없습니다.")
            
            stat = path.stat()
            return {
                "file_path": str(path),
                "file_size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime),
                "modified_at": datetime.fromtimestamp(stat.st_mtime),
                "exists": True
            }
            
        except Exception as e:
            return {
                "file_path": file_path,
                "file_size": 0,
                "created_at": None,
                "modified_at": None,
                "exists": False,
                "error": str(e)
            }
    
    def cleanup_project_files(self, user_id: int, project_id: int) -> bool:
        """프로젝트의 모든 파일 삭제"""
        try:
            project_dir = self.get_user_project_dir(user_id, project_id)
            
            if project_dir.exists():
                shutil.rmtree(project_dir)
                return True
            return False
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"프로젝트 파일 정리 실패: {str(e)}"
            )
    
    def cleanup_user_files(self, user_id: int) -> bool:
        """사용자의 모든 파일 삭제"""
        try:
            user_dir = self.base_upload_dir / "users" / str(user_id)
            
            if user_dir.exists():
                shutil.rmtree(user_dir)
                return True
            return False
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"사용자 파일 정리 실패: {str(e)}"
            )
    
    def get_storage_stats(self, user_id: Optional[int] = None, project_id: Optional[int] = None) -> dict:
        """저장소 사용량 통계"""
        try:
            if user_id and project_id:
                # 특정 프로젝트 통계
                target_dir = self.get_user_project_dir(user_id, project_id)
            elif user_id:
                # 특정 사용자 통계
                target_dir = self.base_upload_dir / "users" / str(user_id)
            else:
                # 전체 통계
                target_dir = self.base_upload_dir
            
            if not target_dir.exists():
                return {
                    "total_size": 0,
                    "file_count": 0,
                    "directory_count": 0
                }
            
            total_size = 0
            file_count = 0
            directory_count = 0
            
            for item in target_dir.rglob("*"):
                if item.is_file():
                    total_size += item.stat().st_size
                    file_count += 1
                elif item.is_dir():
                    directory_count += 1
            
            return {
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_count": file_count,
                "directory_count": directory_count
            }
            
        except Exception as e:
            return {
                "total_size": 0,
                "file_count": 0,
                "directory_count": 0,
                "error": str(e)
            }
    
    def create_temp_file(self, file: UploadFile) -> Tuple[str, int]:
        """임시 파일 생성"""
        try:
            # 고유한 임시 파일명 생성
            temp_filename = f"temp_{uuid.uuid4().hex}_{file.filename}"
            temp_path = self.base_upload_dir / "temp" / temp_filename
            
            # 임시 파일 저장
            file_size = 0
            with open(temp_path, "wb") as buffer:
                file.file.seek(0)
                while chunk := file.file.read(8192):
                    buffer.write(chunk)
                    file_size += len(chunk)
            
            return str(temp_path), file_size
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"임시 파일 생성 실패: {str(e)}"
            )
    
    def cleanup_temp_files(self, older_than_hours: int = 24) -> int:
        """오래된 임시 파일 정리"""
        try:
            temp_dir = self.base_upload_dir / "temp"
            if not temp_dir.exists():
                return 0
            
            cutoff_time = datetime.now().timestamp() - (older_than_hours * 3600)
            cleaned_count = 0
            
            for temp_file in temp_dir.iterdir():
                if temp_file.is_file() and temp_file.stat().st_ctime < cutoff_time:
                    temp_file.unlink()
                    cleaned_count += 1
            
            return cleaned_count
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"임시 파일 정리 실패: {str(e)}"
            )


# 글로벌 파일 저장소 매니저 인스턴스
file_storage = FileStorageManager()
