from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Float, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


class Embedding(Base):
    """임베딩 모델 - 문서 청크별 벡터 임베딩 정보"""
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, index=True)
    
    # 문서 관계
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    
    # 청크 정보
    chunk_index = Column(Integer, nullable=False)  # 문서 내 청크 순서 (0부터 시작)
    chunk_text = Column(Text, nullable=False)  # 청크 텍스트 내용
    chunk_size = Column(Integer, nullable=False)  # 청크 크기 (문자 수)
    
    # 임베딩 벡터 정보
    embedding_vector = Column(JSON, nullable=False)  # 임베딩 벡터 (JSON 배열로 저장)
    embedding_model = Column(String(100), nullable=False, default="text-embedding-ada-002")  # 사용된 임베딩 모델
    vector_dimension = Column(Integer, nullable=False, default=1536)  # 벡터 차원
    
    # 메타데이터
    document_metadata = Column(JSON, nullable=True)  # 추가 메타데이터 (페이지 번호, 섹션 등)
    
    # 유사도 검색을 위한 인덱스 정보
    tokens = Column(Integer, nullable=False, default=0)  # 토큰 수
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 소프트 삭제
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # 관계 설정
    document = relationship("Document", back_populates="embeddings")

    def __repr__(self):
        return (f"<Embedding(id={self.id}, document_id={self.document_id}, "
                f"chunk_index={self.chunk_index})>")

    @property
    def chunk_preview(self):
        """청크 텍스트 미리보기 (처음 100자)"""
        if not self.chunk_text:
            return ""
        return self.chunk_text[:100] + "..." if len(self.chunk_text) > 100 else self.chunk_text

    @property
    def has_vector(self):
        """임베딩 벡터가 존재하는지 확인"""
        return self.embedding_vector is not None and len(self.embedding_vector) > 0

    def set_embedding_vector(self, vector: list, model: str = "text-embedding-ada-002"):
        """임베딩 벡터 설정"""
        self.embedding_vector = vector
        self.embedding_model = model
        self.vector_dimension = len(vector) if vector else 0

    def get_embedding_vector(self) -> list:
        """임베딩 벡터 반환"""
        return self.embedding_vector if self.embedding_vector else []

    def set_metadata(self, **kwargs):
        """메타데이터 설정"""
        if self.document_metadata is None:
            self.document_metadata = {}
        self.document_metadata.update(kwargs)

    def get_metadata(self, key: str = None):
        """메타데이터 조회"""
        if self.document_metadata is None:
            return None if key else {}
        return self.document_metadata.get(key) if key else self.document_metadata

    def soft_delete(self):
        """소프트 삭제 실행"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    @classmethod
    def create_from_chunk(cls, document_id: int, chunk_index: int, chunk_text: str, 
                         embedding_vector: list = None, metadata: dict = None):
        """청크로부터 임베딩 객체 생성"""
        embedding = cls(
            document_id=document_id,
            chunk_index=chunk_index,
            chunk_text=chunk_text,
            chunk_size=len(chunk_text),
            tokens=len(chunk_text.split()) if chunk_text else 0,  # 간단한 토큰 수 계산
            document_metadata=metadata or {}
        )
        
        if embedding_vector:
            embedding.set_embedding_vector(embedding_vector)
            
        return embedding

    @classmethod
    def get_by_document(cls, session, document_id: int, include_deleted: bool = False):
        """문서별 임베딩 조회"""
        query = session.query(cls).filter(cls.document_id == document_id)
        if not include_deleted:
            query = query.filter(cls.is_deleted == False)
        return query.order_by(cls.chunk_index).all()

    def calculate_similarity(self, other_vector: list) -> float:
        """다른 벡터와의 코사인 유사도 계산 (간단한 구현)"""
        if not self.has_vector or not other_vector:
            return 0.0
            
        vector_a = self.get_embedding_vector()
        vector_b = other_vector
        
        if len(vector_a) != len(vector_b):
            return 0.0
            
        # 코사인 유사도 계산
        dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
        magnitude_a = sum(a * a for a in vector_a) ** 0.5
        magnitude_b = sum(b * b for b in vector_b) ** 0.5
        
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
            
        return dot_product / (magnitude_a * magnitude_b)
