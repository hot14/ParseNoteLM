from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, BigInteger, Enum
from sqlalchemy.orm import relationship
from app.db.session import Base
import enum


class DocumentType(str, enum.Enum):
    """문서 타입"""
    PDF = "pdf"
    TXT = "txt"


class ProcessingStatus(str, enum.Enum):
    """문서 처리 상태"""
    PENDING = "pending"          # 업로드 대기
    UPLOADING = "uploading"      # 업로드 중
    PROCESSING = "processing"    # 처리 중
    COMPLETED = "completed"      # 처리 완료
    FAILED = "failed"           # 처리 실패


# alias 추가
DocumentStatus = ProcessingStatus


class Document(Base):
    """문서 모델 - 프로젝트에 업로드된 문서 정보"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)  # 사용자가 업로드한 원본 파일명
    file_path = Column(String(500), nullable=False)  # 서버에 저장된 파일 경로
    
    # 파일 정보
    file_size = Column(BigInteger, nullable=False)  # 바이트 단위
    file_type = Column(Enum(DocumentType), nullable=False)
    mime_type = Column(String(100), nullable=True)
    
    # 프로젝트 관계
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    
    # 처리 상태
    processing_status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING, nullable=False)
    processing_error = Column(Text, nullable=True)  # 처리 실패 시 에러 메시지
    
    # 문서 내용 정보
    content = Column(Text, nullable=True)  # 추출된 텍스트 내용
    content_length = Column(Integer, default=0, nullable=False)  # 문자 수
    chunk_count = Column(Integer, default=0, nullable=False)  # 분할된 청크 수
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)  # 처리 완료 시간
    
    # 소프트 삭제
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # 관계 설정
    project = relationship("Project", back_populates="documents")
    embeddings = relationship("Embedding", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', project_id={self.project_id})>"

    @property
    def file_size_mb(self):
        """파일 크기를 MB 단위로 반환"""
        return round(self.file_size / (1024 * 1024), 2)

    @property
    def is_processed(self):
        """문서가 처리 완료되었는지 확인"""
        return self.processing_status == ProcessingStatus.COMPLETED

    @property
    def is_processing(self):
        """문서가 현재 처리 중인지 확인"""
        return self.processing_status == ProcessingStatus.PROCESSING

    @property
    def has_failed(self):
        """문서 처리가 실패했는지 확인"""
        return self.processing_status == ProcessingStatus.FAILED

    def mark_processing(self):
        """문서를 처리 중으로 표시"""
        self.processing_status = ProcessingStatus.PROCESSING
        self.processing_error = None

    def mark_completed(self, content: str, chunk_count: int):
        """문서 처리 완료로 표시"""
        self.processing_status = ProcessingStatus.COMPLETED
        self.content = content
        self.content_length = len(content) if content else 0
        self.chunk_count = chunk_count
        self.processed_at = datetime.utcnow()
        self.processing_error = None

    def mark_failed(self, error_message: str):
        """문서 처리 실패로 표시"""
        self.processing_status = ProcessingStatus.FAILED
        self.processing_error = error_message
        self.processed_at = datetime.utcnow()

    def soft_delete(self):
        """소프트 삭제 실행"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    @classmethod
    def validate_file_size(cls, file_size: int) -> bool:
        """파일 크기 검증 (10MB 제한)"""
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
        return file_size <= MAX_FILE_SIZE

    @classmethod
    def validate_file_type(cls, filename: str) -> bool:
        """파일 타입 검증"""
        allowed_extensions = {'.pdf', '.txt'}
        return any(filename.lower().endswith(ext) for ext in allowed_extensions)
