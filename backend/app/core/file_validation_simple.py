"""
간단한 파일 검증 유틸리티
"""
from typing import Tuple, Optional
import os


class SimpleFileValidator:
    """간단한 파일 검증 클래스"""
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'.pdf', '.txt'}
    
    @classmethod
    def validate_file(cls, filename: str, file_size: int) -> Tuple[bool, Optional[str]]:
        """
        파일 검증
        
        Args:
            filename: 파일명
            file_size: 파일 크기
            
        Returns:
            (검증 성공 여부, 오류 메시지)
        """
        # 파일 크기 검증
        if file_size > cls.MAX_FILE_SIZE:
            return False, f"파일 크기가 {cls.MAX_FILE_SIZE // 1024 // 1024}MB를 초과합니다"
        
        # 파일 확장자 검증
        _, ext = os.path.splitext(filename.lower())
        if ext not in cls.ALLOWED_EXTENSIONS:
            return False, f"지원하지 않는 파일 형식입니다. 허용된 형식: {', '.join(cls.ALLOWED_EXTENSIONS)}"
        
        return True, None
    
    @classmethod
    def get_file_type(cls, filename: str) -> str:
        """파일 확장자로부터 파일 타입 반환"""
        _, ext = os.path.splitext(filename.lower())
        return ext[1:] if ext else "unknown"
