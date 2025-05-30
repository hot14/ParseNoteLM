"""
사용자 정의 예외 클래스들
"""

from fastapi import HTTPException
from typing import Optional, Dict, Any


class ParseNoteLMException(HTTPException):
    """ParseNoteLM 기본 예외 클래스"""
    
    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.details = details or {}
        
        detail = {
            "message": message,
            "error_code": error_code,
            "details": self.details
        }
        
        super().__init__(status_code=status_code, detail=detail)


class DocumentNotFoundException(ParseNoteLMException):
    """문서를 찾을 수 없을 때 발생하는 예외"""
    
    def __init__(self, document_id: int):
        super().__init__(
            status_code=404,
            message="문서를 찾을 수 없습니다.",
            error_code="DOCUMENT_NOT_FOUND",
            details={"document_id": document_id}
        )


class ProjectNotFoundException(ParseNoteLMException):
    """프로젝트를 찾을 수 없을 때 발생하는 예외"""
    
    def __init__(self, project_id: int):
        super().__init__(
            status_code=404,
            message="프로젝트를 찾을 수 없습니다.",
            error_code="PROJECT_NOT_FOUND",
            details={"project_id": project_id}
        )


class FileUploadException(ParseNoteLMException):
    """파일 업로드 관련 예외"""
    
    def __init__(self, message: str, filename: Optional[str] = None):
        super().__init__(
            status_code=400,
            message=message,
            error_code="FILE_UPLOAD_ERROR",
            details={"filename": filename} if filename else {}
        )


class DocumentProcessingException(ParseNoteLMException):
    """문서 처리 관련 예외"""
    
    def __init__(self, message: str, document_id: Optional[int] = None):
        super().__init__(
            status_code=500,
            message=message,
            error_code="DOCUMENT_PROCESSING_ERROR",
            details={"document_id": document_id} if document_id else {}
        )


class AuthenticationException(ParseNoteLMException):
    """인증 관련 예외"""
    
    def __init__(self, message: str = "인증에 실패했습니다."):
        super().__init__(
            status_code=401,
            message=message,
            error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationException(ParseNoteLMException):
    """권한 관련 예외"""
    
    def __init__(self, message: str = "권한이 없습니다."):
        super().__init__(
            status_code=403,
            message=message,
            error_code="AUTHORIZATION_ERROR"
        )
