"""
파일 업로드 유효성 검사 모듈
"""
import os
import magic
from typing import Tuple, List, Optional
from fastapi import UploadFile, HTTPException
from app.models.document import DocumentType


class FileValidator:
    """파일 유효성 검사 클래스"""
    
    # 지원되는 파일 형식
    ALLOWED_EXTENSIONS = {'.pdf', '.txt'}
    
    # MIME 타입 매핑
    MIME_TYPE_MAPPING = {
        'application/pdf': DocumentType.PDF,
        'text/plain': DocumentType.TXT,
        'text/txt': DocumentType.TXT,
    }
    
    # 최대 파일 크기 (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
    
    # 파일명 제한
    MAX_FILENAME_LENGTH = 255
    MIN_FILENAME_LENGTH = 1
    
    @classmethod
    def validate_file_upload(cls, file: UploadFile) -> Tuple[bool, List[str]]:
        """
        파일 업로드 전체 유효성 검사
        
        Args:
            file: 업로드된 파일
            
        Returns:
            Tuple[bool, List[str]]: (유효성 여부, 에러 메시지 리스트)
        """
        errors = []
        
        # 파일명 검사
        filename_errors = cls.validate_filename(file.filename)
        errors.extend(filename_errors)
        
        # 파일 확장자 검사
        extension_errors = cls.validate_file_extension(file.filename)
        errors.extend(extension_errors)
        
        # 파일 크기 검사
        size_errors = cls.validate_file_size(file.size if file.size else 0)
        errors.extend(size_errors)
        
        # MIME 타입 검사 (파일 내용 기반)
        try:
            mime_errors = cls.validate_mime_type(file)
            errors.extend(mime_errors)
        except Exception as e:
            errors.append(f"MIME 타입 검사 중 오류 발생: {str(e)}")
        
        return len(errors) == 0, errors
    
    @classmethod
    def validate_filename(cls, filename: Optional[str]) -> List[str]:
        """파일명 유효성 검사"""
        errors = []
        
        if not filename:
            errors.append("파일명이 제공되지 않았습니다.")
            return errors
        
        # 길이 검사
        if len(filename) < cls.MIN_FILENAME_LENGTH:
            errors.append("파일명이 너무 짧습니다.")
        
        if len(filename) > cls.MAX_FILENAME_LENGTH:
            errors.append(f"파일명이 너무 깁니다. (최대 {cls.MAX_FILENAME_LENGTH}자)")
        
        # 금지된 문자 검사
        forbidden_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        for char in forbidden_chars:
            if char in filename:
                errors.append(f"파일명에 금지된 문자가 포함되어 있습니다: {char}")
        
        # 예약된 이름 검사 (Windows)
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 
                         'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 
                         'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 
                         'LPT7', 'LPT8', 'LPT9']
        
        name_without_ext = os.path.splitext(filename)[0].upper()
        if name_without_ext in reserved_names:
            errors.append("예약된 파일명은 사용할 수 없습니다.")
        
        return errors
    
    @classmethod
    def validate_file_extension(cls, filename: Optional[str]) -> List[str]:
        """파일 확장자 유효성 검사"""
        errors = []
        
        if not filename:
            errors.append("파일명이 제공되지 않았습니다.")
            return errors
        
        # 확장자 추출
        file_ext = os.path.splitext(filename)[1].lower()
        
        if not file_ext:
            errors.append("파일 확장자가 없습니다.")
            return errors
        
        if file_ext not in cls.ALLOWED_EXTENSIONS:
            allowed_list = ', '.join(cls.ALLOWED_EXTENSIONS)
            errors.append(f"지원되지 않는 파일 형식입니다. 지원 형식: {allowed_list}")
        
        return errors
    
    @classmethod
    def validate_file_size(cls, file_size: int) -> List[str]:
        """파일 크기 유효성 검사"""
        errors = []
        
        if file_size <= 0:
            errors.append("파일 크기가 유효하지 않습니다.")
            return errors
        
        if file_size > cls.MAX_FILE_SIZE:
            max_size_mb = cls.MAX_FILE_SIZE / (1024 * 1024)
            current_size_mb = file_size / (1024 * 1024)
            errors.append(
                f"파일 크기가 제한을 초과했습니다. "
                f"현재: {current_size_mb:.2f}MB, 최대: {max_size_mb:.0f}MB"
            )
        
        return errors
    
    @classmethod
    def validate_mime_type(cls, file: UploadFile) -> List[str]:
        """MIME 타입 유효성 검사 (실제 파일 내용 기반)"""
        errors = []
        
        try:
            # 파일 포인터를 처음으로 이동
            file.file.seek(0)
            
            # 파일의 처음 몇 바이트를 읽어 MIME 타입 확인
            file_header = file.file.read(1024)
            file.file.seek(0)  # 포인터를 다시 처음으로 이동
            
            # python-magic을 사용하여 실제 파일 타입 검사
            mime_type = magic.from_buffer(file_header, mime=True)
            
            if mime_type not in cls.MIME_TYPE_MAPPING:
                supported_types = ', '.join(cls.MIME_TYPE_MAPPING.keys())
                errors.append(
                    f"지원되지 않는 파일 형식입니다. "
                    f"감지된 타입: {mime_type}, 지원 타입: {supported_types}"
                )
        
        except Exception as e:
            errors.append(f"파일 타입 검사 실패: {str(e)}")
        
        return errors
    
    @classmethod
    def get_document_type(cls, file: UploadFile) -> DocumentType:
        """파일로부터 DocumentType 추출"""
        try:
            # 파일 포인터를 처음으로 이동
            file.file.seek(0)
            file_header = file.file.read(1024)
            file.file.seek(0)
            
            mime_type = magic.from_buffer(file_header, mime=True)
            
            return cls.MIME_TYPE_MAPPING.get(mime_type, DocumentType.TXT)
        
        except Exception:
            # 실패시 확장자로 추정
            file_ext = os.path.splitext(file.filename or '')[1].lower()
            if file_ext == '.pdf':
                return DocumentType.PDF
            else:
                return DocumentType.TXT
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """파일명 정리 (안전한 파일명으로 변환)"""
        if not filename:
            return "unknown_file"
        
        # 위험한 문자 제거/교체
        safe_chars = []
        for char in filename:
            if char.isalnum() or char in ['.', '-', '_', ' ']:
                safe_chars.append(char)
            else:
                safe_chars.append('_')
        
        sanitized = ''.join(safe_chars)
        
        # 연속된 공백이나 언더스코어 정리
        sanitized = ' '.join(sanitized.split())
        sanitized = '_'.join(sanitized.split('_'))
        
        # 길이 제한
        if len(sanitized) > cls.MAX_FILENAME_LENGTH:
            name, ext = os.path.splitext(sanitized)
            max_name_len = cls.MAX_FILENAME_LENGTH - len(ext)
            sanitized = name[:max_name_len] + ext
        
        return sanitized
    
    @classmethod
    def validate_project_document_limit(cls, current_count: int) -> List[str]:
        """프로젝트 문서 수 제한 검사"""
        errors = []
        
        MAX_DOCUMENTS_PER_PROJECT = 5
        
        if current_count >= MAX_DOCUMENTS_PER_PROJECT:
            errors.append(
                f"프로젝트당 최대 {MAX_DOCUMENTS_PER_PROJECT}개의 문서만 업로드할 수 있습니다. "
                f"현재: {current_count}개"
            )
        
        return errors


def validate_file_for_upload(file: UploadFile, current_document_count: int = 0) -> None:
    """
    파일 업로드 전 통합 유효성 검사
    
    Args:
        file: 업로드할 파일
        current_document_count: 현재 프로젝트의 문서 수
        
    Raises:
        HTTPException: 유효성 검사 실패 시
    """
    # 파일 자체 유효성 검사
    is_valid, file_errors = FileValidator.validate_file_upload(file)
    
    # 프로젝트 문서 수 제한 검사
    limit_errors = FileValidator.validate_project_document_limit(current_document_count)
    
    all_errors = file_errors + limit_errors
    
    if all_errors:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "파일 유효성 검사 실패",
                "errors": all_errors
            }
        )
