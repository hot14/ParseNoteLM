"""
파일 형식별 텍스트 추출 및 처리 모듈
"""
import os
import re
from abc import ABC, abstractmethod
from typing import Tuple, List, Dict, Optional
from pathlib import Path
import PyPDF2
from fastapi import HTTPException
from app.models.document import DocumentType


class BaseFileProcessor(ABC):
    """파일 처리기 기본 클래스"""
    
    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """파일에서 텍스트 추출"""
        pass
    
    @abstractmethod
    def get_metadata(self, file_path: str) -> Dict:
        """파일 메타데이터 추출"""
        pass
    
    def validate_file(self, file_path: str) -> bool:
        """파일 유효성 검사"""
        return os.path.exists(file_path) and os.path.getsize(file_path) > 0
    
    def clean_text(self, text: str) -> str:
        """텍스트 정리"""
        if not text:
            return ""
        
        # 여러 공백을 하나로 줄이기
        text = re.sub(r'\s+', ' ', text)
        
        # 줄바꿈 정리
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # 앞뒤 공백 제거
        text = text.strip()
        
        return text
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """텍스트를 청크 단위로 분할"""
        if not text:
            return []
        
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # 단어 경계에서 자르기
            if end < len(text):
                # 마지막 공백 찾기
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # 다음 시작점 설정 (겹치는 부분 고려)
            start = max(end - overlap, start + 1)
            
            # 무한 루프 방지
            if start >= len(text):
                break
        
        return chunks


class PDFProcessor(BaseFileProcessor):
    """PDF 파일 처리기"""
    
    def extract_text(self, file_path: str) -> str:
        """PDF에서 텍스트 추출"""
        try:
            if not self.validate_file(file_path):
                raise ValueError("유효하지 않은 PDF 파일")
            
            text_content = []
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # 암호화된 PDF 확인
                if pdf_reader.is_encrypted:
                    # 기본 패스워드로 시도
                    if not pdf_reader.decrypt(""):
                        raise ValueError("암호화된 PDF 파일은 지원되지 않습니다")
                
                # 각 페이지에서 텍스트 추출
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text_content.append(f"[페이지 {page_num + 1}]\n{page_text}")
                    except Exception as e:
                        # 특정 페이지 오류는 건너뛰고 계속 진행
                        text_content.append(f"[페이지 {page_num + 1}] - 텍스트 추출 실패: {str(e)}")
            
            if not text_content:
                raise ValueError("PDF에서 텍스트를 추출할 수 없습니다")
            
            full_text = "\n\n".join(text_content)
            return self.clean_text(full_text)
            
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"PDF 텍스트 추출 실패: {str(e)}"
            )
    
    def get_metadata(self, file_path: str) -> Dict:
        """PDF 메타데이터 추출"""
        try:
            metadata = {
                "pages": 0,
                "title": "",
                "author": "",
                "subject": "",
                "creator": "",
                "producer": "",
                "creation_date": None,
                "modification_date": None
            }
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # 페이지 수
                metadata["pages"] = len(pdf_reader.pages)
                
                # 문서 정보
                if pdf_reader.metadata:
                    doc_info = pdf_reader.metadata
                    metadata.update({
                        "title": doc_info.get("/Title", ""),
                        "author": doc_info.get("/Author", ""),
                        "subject": doc_info.get("/Subject", ""),
                        "creator": doc_info.get("/Creator", ""),
                        "producer": doc_info.get("/Producer", ""),
                        "creation_date": doc_info.get("/CreationDate"),
                        "modification_date": doc_info.get("/ModDate")
                    })
            
            return metadata
            
        except Exception as e:
            return {"error": f"메타데이터 추출 실패: {str(e)}"}


class TXTProcessor(BaseFileProcessor):
    """TXT 파일 처리기"""
    
    def extract_text(self, file_path: str) -> str:
        """TXT 파일에서 텍스트 추출"""
        try:
            if not self.validate_file(file_path):
                raise ValueError("유효하지 않은 텍스트 파일")
            
            # 여러 인코딩으로 시도
            encodings = ['utf-8', 'cp949', 'euc-kr', 'latin-1']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        text = file.read()
                        return self.clean_text(text)
                except UnicodeDecodeError:
                    continue
            
            # 모든 인코딩 실패시 바이너리로 읽어서 오류 문자 무시
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                text = file.read()
                return self.clean_text(text)
                
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"텍스트 파일 읽기 실패: {str(e)}"
            )
    
    def get_metadata(self, file_path: str) -> Dict:
        """TXT 파일 메타데이터 추출"""
        try:
            # 파일 정보
            file_stat = os.stat(file_path)
            
            # 텍스트 내용 분석
            text_content = self.extract_text(file_path)
            
            return {
                "encoding": self._detect_encoding(file_path),
                "line_count": text_content.count('\n') + 1 if text_content else 0,
                "character_count": len(text_content),
                "word_count": len(text_content.split()) if text_content else 0,
                "file_size": file_stat.st_size
            }
            
        except Exception as e:
            return {"error": f"메타데이터 추출 실패: {str(e)}"}
    
    def _detect_encoding(self, file_path: str) -> str:
        """파일 인코딩 감지"""
        encodings = ['utf-8', 'cp949', 'euc-kr', 'latin-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    file.read(1024)  # 일부만 읽어서 테스트
                    return encoding
            except UnicodeDecodeError:
                continue
        
        return "unknown"


class FileProcessorFactory:
    """파일 처리기 팩토리"""
    
    _processors = {
        DocumentType.PDF: PDFProcessor,
        DocumentType.TXT: TXTProcessor
    }
    
    @classmethod
    def get_processor(cls, document_type: DocumentType) -> BaseFileProcessor:
        """문서 타입에 따른 처리기 반환"""
        processor_class = cls._processors.get(document_type)
        
        if not processor_class:
            raise HTTPException(
                status_code=400,
                detail=f"지원되지 않는 문서 타입: {document_type}"
            )
        
        return processor_class()
    
    @classmethod
    def process_document(
        cls, 
        file_path: str, 
        document_type: DocumentType,
        extract_chunks: bool = True,
        chunk_size: int = 1000
    ) -> Tuple[str, List[str], Dict]:
        """
        문서 처리 통합 함수
        
        Args:
            file_path: 파일 경로
            document_type: 문서 타입
            extract_chunks: 청크 추출 여부
            chunk_size: 청크 크기
            
        Returns:
            Tuple[str, List[str], Dict]: (전체 텍스트, 청크 리스트, 메타데이터)
        """
        try:
            processor = cls.get_processor(document_type)
            
            # 텍스트 추출
            full_text = processor.extract_text(file_path)
            
            # 청크 분할
            chunks = []
            if extract_chunks and full_text:
                chunks = processor.chunk_text(full_text, chunk_size)
            
            # 메타데이터 추출
            metadata = processor.get_metadata(file_path)
            
            # 처리 결과 추가 정보
            metadata.update({
                "full_text_length": len(full_text),
                "chunk_count": len(chunks),
                "processing_success": True
            })
            
            return full_text, chunks, metadata
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"문서 처리 실패: {str(e)}"
            )


def validate_and_process_document(
    file_path: str,
    document_type: DocumentType,
    chunk_size: int = 1000
) -> Dict:
    """
    문서 유효성 검사 및 처리
    
    Args:
        file_path: 파일 경로
        document_type: 문서 타입
        chunk_size: 청크 크기
        
    Returns:
        Dict: 처리 결과
    """
    try:
        # 파일 존재 확인
        if not os.path.exists(file_path):
            raise FileNotFoundError("파일을 찾을 수 없습니다")
        
        # 파일 크기 확인
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise ValueError("빈 파일입니다")
        
        # 문서 처리
        full_text, chunks, metadata = FileProcessorFactory.process_document(
            file_path, document_type, extract_chunks=True, chunk_size=chunk_size
        )
        
        if not full_text.strip():
            raise ValueError("파일에서 텍스트를 추출할 수 없습니다")
        
        return {
            "success": True,
            "full_text": full_text,
            "chunks": chunks,
            "metadata": metadata,
            "file_size": file_size,
            "chunk_count": len(chunks)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "full_text": "",
            "chunks": [],
            "metadata": {},
            "file_size": 0,
            "chunk_count": 0
        }
